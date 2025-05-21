# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""CDK Custom Resource Lambda for a SageMaker Studio Lifecycle Configuration Script

See `StudioLCCResourceProperties` for expected CloudFormation resource properties.

CloudFormation Return Values
----------------------------
Direct .Ref :
    ARN of the created lifecycle configuration script
AppType :
    As per resource properties .AppType
Name :
    As per resource properties .Name
"""
# Python Built-Ins:
from __future__ import annotations
import json
import logging
import time
from typing import Optional

logging.getLogger().setLevel(logging.INFO)  # Set log level for AWS Lambda *BEFORE* other imports

# External Dependencies:
import boto3

# Local Dependencies
from cfn import CustomResourceEvent, CustomResourceRequestType
from sagemaker_util import retry_if_already_updating

logger = logging.getLogger("main")
smclient = boto3.client("sagemaker")


class StudioLCCResourceProperties:
    """Parser for CloudFormation resource properties for this Custom Resource

    Resource Properties
    -------------------

    AppType : str
        (Required) 'JupyterLab' or 'CodeEditor' for new-style (2024+) SMStudio Spaces, or else
        'JupyterServer' or 'KernelGateway' for SageMaker Studio Classic.
    Name : str
        (Required) Name of the lifecycle config script to create
    Content : str
        (Required) Base64-encoded script content, similar to the usage of
        `Properties.OnStart[].Content` in AWS::SageMaker::NotebookInstanceLifecycleConfig
    Tags : Optional[List[Dict['Key': str, 'Value': str]]]
        Optional AWS resource tags
    DomainId : Optional[str]
        Optional SageMaker Studio Domain ID to associate the script to. (You usually need to attach
        the script to a domain if you want to use it!).
    """

    app_type: str
    content: str
    name: str
    domain_id: Optional[str]
    tags: Optional[dict]

    def __init__(self, resource_properties: dict):
        self.app_type = resource_properties["AppType"]
        self.content = resource_properties["Content"]
        self.name = resource_properties["Name"]
        self.domain_id = resource_properties.get("DomainId")
        self.tags = resource_properties.get("Tags", [])

    def __str__(self):
        dict_val = {
            "AppType": self.app_type,
            "Content": self.content,
            "Name": self.name,
            "Tags": self.tags,
        }
        if self.domain_id:
            dict_val["DomainId"] = self.domain_id
        return json.dumps(dict_val)

    @classmethod
    def from_str(cls, str_val) -> StudioLCCResourceProperties:
        return cls(json.loads(str_val))


def lambda_handler(event_raw: dict, context: dict):
    """Main entry point for (CDK) Custom Resource Lambda"""
    logger.info(event_raw)
    event = CustomResourceEvent(event_raw, StudioLCCResourceProperties)
    if event.request_type == CustomResourceRequestType.create:
        return handle_create(event, context)
    elif event.request_type == CustomResourceRequestType.update:
        return handle_update(event, context)
    elif event.request_type == CustomResourceRequestType.delete:
        return handle_delete(event, context)
    else:
        raise ValueError(f"Unsupported CFn RequestType '{event_raw['RequestType']}'")


def handle_create(event: CustomResourceEvent[StudioLCCResourceProperties], context: dict):
    logger.info("**Received create request")

    logger.info("**Creating lifecycle config script")
    resp = smclient.create_studio_lifecycle_config(
        StudioLifecycleConfigName=event.props.name,
        StudioLifecycleConfigContent=event.props.content,
        StudioLifecycleConfigAppType=event.props.app_type,
        Tags=event.props.tags or [],
    )
    script_arn = resp["StudioLifecycleConfigArn"]
    domain_id = event.props.domain_id
    if domain_id is not None:
        try:
            attach_lcc_to_domain(
                domain_id=domain_id,
                script_arn=script_arn,
                app_type=event.props.app_type,
            )
        except Exception as e:
            # If creation succeeded but attachment failed, send explicit fail response to try and
            # make sure the physical resource ID is set correctly and therefore enable rollback of
            # the resource:
            logger.exception("Failed to attach LCC to SM domain")
            raise e

    return {
        "PhysicalResourceId": script_arn,
        "Data": {
            "AppType": event.props.app_type,
            "Name": event.props.name,
        },
    }


def handle_delete(event: CustomResourceEvent[StudioLCCResourceProperties], context: dict):
    logger.info("**Received delete event")
    lcc_id = event.physical_id
    lcc_name = lcc_id.rpartition("/")[2]

    domain_id = event.props.domain_id
    app_type = event.props.app_type
    if domain_id is not None and app_type is not None:
        try:
            remove_lcc_from_domain(domain_id=domain_id, script_arn=lcc_id, app_type=app_type)
        except:
            logger.exception("Failed to detach LCC from domain - trying to delete LCC anyway...")

    try:
        logger.info(f"Deleting lifecycle config script {lcc_name}")
        smclient.delete_studio_lifecycle_config(StudioLifecycleConfigName=lcc_name)
    except smclient.exceptions.ResourceNotFound:
        pass

    # Already does not exist -> deletion success
    return {
        "PhysicalResourceId": lcc_id,
        "Data": {},
    }


def handle_update(event: CustomResourceEvent[StudioLCCResourceProperties], context: dict):
    logger.info("**Received update event")

    script_location_modified = not (
        (event.props.name == event.old_props.name)
        and (event.props.app_type == event.old_props.app_type)
    )
    script_modified = script_location_modified or not (
        (event.props.content == event.old_props.content)
    )
    new_domain = event.props.domain_id
    old_domain = event.old_props.domain_id

    if old_domain and script_location_modified or (new_domain != old_domain):
        remove_lcc_from_domain(
            domain_id=old_domain,
            script_arn=event.physical_id,
            app_type=event.old_props.app_type,
        )

    if script_modified:
        # For any modification we have to replace the script:
        try:
            old_name = event.old_props.name
            logger.info(f"Deleting lifecycle config script {old_name}")
            smclient.delete_studio_lifecycle_config(StudioLifecycleConfigName=old_name)
        except smclient.exceptions.ResourceNotFound:
            pass
        resp = smclient.create_studio_lifecycle_config(
            StudioLifecycleConfigName=event.props.name,
            StudioLifecycleConfigContent=event.props.content,
            StudioLifecycleConfigAppType=event.props.app_type,
            Tags=event.props.tags or [],
        )

    if new_domain and (script_location_modified or (new_domain != old_domain)):
        attach_lcc_to_domain(
            domain_id=new_domain,
            script_arn=event.physical_id,
            app_type=event.props.app_type,
        )

    return {
        "PhysicalResourceId": resp["StudioLifecycleConfigArn"],
        "Data": {
            "AppType": event.props.app_type,
            "Name": event.props.name,
        },
    }


def attach_lcc_to_domain(domain_id: str, script_arn: str, app_type: str):
    domain_desc = smclient.describe_domain(DomainId=domain_id)

    default_settings = domain_desc["DefaultUserSettings"]

    app_settings_field = f"{app_type}AppSettings"  # e.g. "JupyterServerAppSettings"
    if not default_settings.get(app_settings_field):
        default_settings[app_settings_field] = {}
    if not default_settings[app_settings_field].get("LifecycleConfigArns"):
        default_settings[app_settings_field]["LifecycleConfigArns"] = []

    default_scripts = default_settings[app_settings_field]["LifecycleConfigArns"]
    if script_arn not in default_scripts:
        logger.info(f"Adding script to domain:\n{script_arn}")
        default_scripts.append(script_arn)
        retry_if_already_updating(
            lambda: smclient.update_domain(
                DomainId=domain_id,
                DefaultUserSettings=default_settings,
            ),
        )
        time.sleep(10)
    else:
        logger.info("Script already default on domain:\n{script_arn}")


def remove_lcc_from_domain(domain_id: str, script_arn: str, app_type: str):
    domain_desc = smclient.describe_domain(DomainId=domain_id)

    default_settings = domain_desc["DefaultUserSettings"]

    app_settings_field = f"{app_type}AppSettings"  # e.g. "JupyterServerAppSettings"
    if not default_settings.get(app_settings_field):
        default_settings[app_settings_field] = {}
    if not default_settings[app_settings_field].get("LifecycleConfigArns"):
        default_settings[app_settings_field]["LifecycleConfigArns"] = []

    default_scripts = default_settings[app_settings_field]["LifecycleConfigArns"]
    if script_arn in default_scripts:
        logger.info(f"Removing script from domain:\n{script_arn}")
        default_scripts.remove(script_arn)
        retry_if_already_updating(
            lambda: smclient.update_domain(
                DomainId=domain_id,
                DefaultUserSettings=default_settings,
            ),
        )
        time.sleep(10)
    else:
        logger.info("Script already deleted from domain:\n{script_arn}")
