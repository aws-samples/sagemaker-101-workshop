"""Custom CloudFormation Resource for a SageMaker Studio Lifecycle Configuration Script

Resource Properties
-------------------
AppType : str
    (Required) Usually either 'JupyterServer' or 'KernelGateway'
Name : str
    (Required) Name of the lifecycle config script to create
Content : str
    (Required) Base64-encoded script content, similar to the usage of Properties.OnStart[].Content
    in AWS::SageMaker::NotebookInstanceLifecycleConfig
Tags : Optional[List[Dict['Key': str, 'Value': str]]]
    Optional AWS resource tags
DomainId : Optional[str]
    Optional SageMaker Studio Domain ID to associate the script to. (You usually need to attach the
    script to a domain if you want to use it!).

Return Values
-------------
Direct .Ref :
    ARN of the created lifecycle configuration script
AppType :
    As per resource properties .AppType
Name :
    As per resource properties .Name
"""

# Python Built-Ins:
from logging import getLogger
import time
import traceback

# External Dependencies:
import boto3
import cfnresponse

logger = getLogger("main")
ec2 = boto3.client("ec2")
smclient = boto3.client("sagemaker")


def lambda_handler(event, context):
    try:
        request_type = event["RequestType"]
        if request_type == "Create":
            handle_create(event, context)
        elif request_type == "Update":
            handle_update(event, context)
        elif request_type == "Delete":
            handle_delete(event, context)
        else:
            cfnresponse.send(
                event,
                context,
                cfnresponse.FAILED,
                {},
                error=f"Unsupported CFN RequestType '{request_type}'",
            )
    except Exception as e:
        logger.error("Uncaught exception in CFN custom resource handler - reporting failure")
        traceback.print_exc()
        cfnresponse.send(
            event,
            context,
            cfnresponse.FAILED,
            {},
            error=str(e),
        )
        raise e


def handle_create(event, context):
    logger.info("**Received create request")
    resource_config = event["ResourceProperties"]

    logger.info("**Creating lifecycle config script")
    resp = smclient.create_studio_lifecycle_config(
        StudioLifecycleConfigName=resource_config["Name"],
        StudioLifecycleConfigContent=resource_config["Content"],
        StudioLifecycleConfigAppType=resource_config["AppType"],
        Tags=resource_config.get("Tags", []),
    )
    script_arn = resp["StudioLifecycleConfigArn"]
    domain_id = resource_config.get("DomainId")
    if domain_id is not None:
        attach_lcc_to_domain(
            domain_id=domain_id,
            script_arn=script_arn,
            app_type=resource_config["AppType"],
        )

    cfnresponse.send(
        event,
        context,
        cfnresponse.SUCCESS,
        {
            "AppType": resource_config["AppType"],
            "Name": resource_config["Name"],
        },
        physicalResourceId=script_arn,
    )
    return


def handle_delete(event, context):
    logger.info("**Received delete event")
    lcc_id = event["PhysicalResourceId"]
    lcc_name = lcc_id.rpartition("/")[2]

    resource_config = event["ResourceProperties"]
    domain_id = resource_config.get("DomainId")
    app_type = resource_config.get("AppType")
    if domain_id is not None and app_type is not None:
        remove_lcc_from_domain(domain_id=domain_id, script_arn=lcc_id, app_type=app_type)

    try:
        logger.info(f"Deleting lifecycle config script {lcc_name}")
        smclient.delete_studio_lifecycle_config(StudioLifecycleConfigName=lcc_name)
    except smclient.exceptions.ResourceNotFound:
        pass

    # Already does not exist -> deletion success
    cfnresponse.send(
        event,
        context,
        cfnresponse.SUCCESS,
        {},
        physicalResourceId=lcc_id,
    )
    return


def handle_update(event, context):
    logger.info("**Received update event")
    new_config = event["ResourceProperties"]
    old_config = event["OldResourceProperties"]

    script_location_modified = not (
        (new_config["Name"] == old_config["Name"])
        and (new_config["AppType"] == old_config["AppType"])
    )
    script_modified = script_location_modified or not (
        (new_config["Content"] == old_config["Content"])
    )
    new_domain = new_config.get("DomainId")
    old_domain = old_config.get("DomainId")

    if old_domain and script_location_modified or (new_domain != old_domain):
        remove_lcc_from_domain(
            domain_id=old_domain,
            script_arn=event["PhysicalResourceId"],
            app_type=old_config["AppType"]
        )

    if script_modified:
        # For any modification we have to replace the script:
        try:
            old_name = old_config["Name"]
            logging.info(f"Deleting lifecycle config script {old_name}")
            smclient.delete_studio_lifecycle_config(StudioLifecycleConfigName=old_name)
        except smclient.exceptions.ResourceNotFound:
            pass
        resp = smclient.create_studio_lifecycle_config(
            StudioLifecycleConfigName=new_config["Name"],
            StudioLifecycleConfigContent=new_config["Content"],
            StudioLifecycleConfigAppType=new_config["AppType"],
            Tags=new_config.get("Tags", []),
        )

    if new_domain and (script_location_modified or (new_domain != old_domain)):
        attach_lcc_to_domain(
            domain_id=new_domain,
            script_arn=event["PhysicalResourceId"],
            app_type=new_config["AppType"],
        )

    cfnresponse.send(
        event,
        context,
        cfnresponse.SUCCESS,
        {
            "AppType": new_config["AppType"],
            "Name": new_config["Name"],
        },
        physicalResourceId=resp["StudioLifecycleConfigArn"]
    )
    return


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
        smclient.update_domain(
            DomainId=domain_id,
            DefaultUserSettings=default_settings,
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
        smclient.update_domain(
            DomainId=domain_id,
            DefaultUserSettings=default_settings,
        )
        time.sleep(5)
    else:
        logger.info("Script already deleted from domain:\n{script_arn}")