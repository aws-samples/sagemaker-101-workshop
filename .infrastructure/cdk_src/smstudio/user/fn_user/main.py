# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Custom CloudFormation Resource for a SageMaker Studio User Profile

See `StudioUserResourceProperties` for expected CloudFormation resource properties.

CloudFormation Return Values
----------------------------
Direct .Ref :
    Name of the created SageMaker Studio user profile
UserProfileName :
    Name of the created SageMaker Studio user profile
HomeEfsFileSystemUid :
    Home EFS File System POSIX user ID allocated for the created SageMaker Studio user (the UID
    they'll appear as when mounting the Studio Domain EFS).
"""
# Python Built-Ins:
from __future__ import annotations
import json
import logging
import time

logging.getLogger().setLevel(logging.INFO)  # Set log level for AWS Lambda *BEFORE* other imports

# External Dependencies:
import boto3

# Local Dependencies:
from cfn import CustomResourceEvent, CustomResourceRequestType

logger = logging.getLogger("main")
smclient = boto3.client("sagemaker")


class StudioUserResourceProperties:
    """Parser for CloudFormation resource properties for this Custom Resource

    Resource Properties
    -------------------

    DomainId : str
        (Required) SageMaker Studio Domain ID to create the profile on.
    UserProfileName : str
        (Required) Domain-unique name to give the user profile (update requires replacement).
    UserSettings : dict
        Optional user settings object to apply to the user profile. Default `{}`.
    """

    domain_id: str
    user_profile_name: str
    user_settings: dict

    def __init__(self, resource_properties: dict):
        self.domain_id = resource_properties["DomainId"]
        self.user_profile_name = resource_properties["UserProfileName"]
        self.user_settings = resource_properties.get("UserSettings", {})

    def __str__(self):
        dict_val = {
            "DomainId": self.domain_id,
            "UserProfileName": self.user_profile_name,
            "UserSettings": self.user_settings,
        }
        return json.dumps(dict_val)

    @classmethod
    def from_str(cls, str_val) -> StudioUserResourceProperties:
        return cls(json.loads(str_val))


def lambda_handler(event_raw: dict, context: dict):
    """Main entry point for (CDK) Custom Resource Lambda"""
    logger.info(event_raw)
    event = CustomResourceEvent(event_raw, StudioUserResourceProperties)
    if event.request_type == CustomResourceRequestType.create:
        return handle_create(event, context)
    elif event.request_type == CustomResourceRequestType.update:
        return handle_update(event, context)
    elif event.request_type == CustomResourceRequestType.delete:
        return handle_delete(event, context)
    else:
        raise ValueError(f"Unsupported CFn RequestType '{event_raw['RequestType']}'")


def handle_create(event: CustomResourceEvent[StudioUserResourceProperties], context):
    logging.info("**Received create request")

    logging.info("**Creating user profile")
    result = create_user_profile(event.props)
    # TODO: Do we need to wait for completion?
    response = {
        "UserProfileName": result["UserProfileName"],
        "HomeEfsFileSystemUid": result["HomeEfsFileSystemUid"],
    }
    print(response)
    return {
        "PhysicalResourceId": result["UserProfileName"],
        "Data": response,
    }


def handle_delete(event: CustomResourceEvent[StudioUserResourceProperties], context):
    logging.info("**Received delete event")
    domain_id = event.props.domain_id
    try:
        smclient.describe_user_profile(DomainId=domain_id, UserProfileName=event.physical_id)
    except smclient.exceptions.ResourceNotFound:
        # Not found -> Treat as deletion successful
        return {"PhysicalResourceId": event.physical_id, "Data": {}}
    delete_user_profile(domain_id, event.physical_id)
    return {"PhysicalResourceId": event.physical_id, "Data": {}}


def handle_update(event: CustomResourceEvent[StudioUserResourceProperties], context):
    logging.info("**Received update event")
    update_user_profile(
        domain_id=event.props.domain_id,
        user_profile_name=event.physical_id,
        user_settings=event.props.user_settings,
    )
    return {"PhysicalResourceId": event.physical_id, "Data": {}}


def create_user_profile(config: StudioUserResourceProperties):
    domain_id = config.domain_id
    user_profile_name = config.user_profile_name

    response = smclient.create_user_profile(
        DomainId=domain_id,
        UserProfileName=user_profile_name,
        UserSettings=config.user_settings,
    )
    created = False
    time.sleep(0.2)
    while not created:
        response = smclient.describe_user_profile(
            DomainId=domain_id, UserProfileName=user_profile_name
        )
        status_lower = response["Status"].lower()
        if status_lower == "inservice":
            created = True
            break
        elif "failed" in status_lower:
            raise ValueError(
                f"User '{user_profile_name}' entered Failed state during creation (domain {domain_id})",
            )
        time.sleep(5)

    logging.info("**SageMaker domain created successfully: %s", domain_id)
    return response


def delete_user_profile(domain_id: str, user_profile_name: str):
    response = smclient.delete_user_profile(
        DomainId=domain_id,
        UserProfileName=user_profile_name,
    )
    deleted = False
    time.sleep(0.2)
    while not deleted:
        try:
            response = smclient.describe_user_profile(
                DomainId=domain_id, UserProfileName=user_profile_name
            )
            status_lower = response["Status"].lower()
            if "failed" in status_lower:
                raise ValueError(
                    f"User '{user_profile_name}' entered Failed state during deletion (domain {domain_id})",
                )
            elif "deleting" not in status_lower:
                raise ValueError(
                    f"User '{user_profile_name}' no longer 'Deleting' but not deleted (domain {domain_id})",
                )
        except smclient.exceptions.ResourceNotFound:
            logging.info("Deleted user %s from domain %s", user_profile_name, domain_id)
            deleted = True
            break
        time.sleep(5)
    return response


def update_user_profile(domain_id: str, user_profile_name: str, user_settings: dict):
    response = smclient.update_user_profile(
        DomainId=domain_id,
        UserProfileName=user_profile_name,
        UserSettings=user_settings,
    )
    updated = False
    time.sleep(0.2)
    while not updated:
        response = smclient.describe_user_profile(
            DomainId=domain_id, UserProfileName=user_profile_name
        )
        status_lower = response["Status"].lower()
        if status_lower == "inservice":
            updated = True
            break
        elif "failed" in status_lower:
            raise ValueError(
                f"User '{user_profile_name}' entered Failed state during deletion (domain {domain_id})",
            )
        time.sleep(5)
    return response
