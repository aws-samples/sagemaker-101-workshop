"""Custom CloudFormation Resource for a SageMaker Studio Domain (with additional outputs)

As well as creating a SMStudio domain, this implementation:
- Defaults to the default VPC, or to any VPC when exactly one is present, if not explicitly configured
- Defaults to all default subnets if any are present, or else all subnets in VPC, if not explicitly set
- Discovers and outputs a list of security group IDs (default+SM-generated) that downstream resources may use
  to perform user setup actions on the Elastic File System
"""

# Python Built-Ins:
import logging
import time
import traceback

# External Dependencies:
import boto3
import cfnresponse

# Local Dependencies:
from sagemaker_util import retry_if_already_updating
import vpctools

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
        logging.error("Uncaught exception in CFN custom resource handler - reporting failure")
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
    logging.info("**Received create request")
    resource_config = event["ResourceProperties"]

    # We split out pre- and post-processing because we'd like to always report our correct physicalResourceId
    # if erroring out after the actual creation, so that the subsequent deletion request can clean up.
    logging.info("**Preparing studio domain creation parameters")
    create_domain_args = preprocess_create_domain_args(resource_config)
    logging.info("**Creating studio domain")
    creation = smclient.create_domain(**create_domain_args)
    _, _, domain_id = creation["DomainArn"].rpartition("/")
    try:
        result = post_domain_create(domain_id, enable_projects=resource_config.get("EnableProjects", False))
        domain_desc = result["DomainDescription"]
        response = {
            "DomainId": domain_desc["DomainId"],
            "DomainName": domain_desc["DomainName"],
            "HomeEfsFileSystemId": domain_desc["HomeEfsFileSystemId"],
            "SubnetIds": ",".join(domain_desc["SubnetIds"]),
            "Url": domain_desc["Url"],
            "VpcId": domain_desc["VpcId"],
            "ProposedAdminSubnetCidr": result["ProposedAdminSubnetCidr"],
            "InboundEFSSecurityGroupId": result["InboundEFSSecurityGroupId"],
            "OutboundEFSSecurityGroupId": result["OutboundEFSSecurityGroupId"],
        }
        print(response)
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response, physicalResourceId=domain_id)
    except Exception as e:
        logging.error("Uncaught exception in post-creation processing")
        traceback.print_exc()
        cfnresponse.send(
            event,
            context,
            cfnresponse.FAILED,
            {},
            physicalResourceId=domain_id,
            error=str(e),
        )


def handle_delete(event, context):
    logging.info("**Received delete event")
    domain_id = event["PhysicalResourceId"]
    try:
        smclient.describe_domain(DomainId=domain_id)
    except smclient.exceptions.ResourceNotFound as exception:
        # Already does not exist -> deletion success
        cfnresponse.send(
            event,
            context,
            cfnresponse.SUCCESS,
            {},
            physicalResourceId=event["PhysicalResourceId"],
        )
        return
    logging.info("**Deleting studio domain")
    delete_domain(domain_id)
    cfnresponse.send(
        event,
        context,
        cfnresponse.SUCCESS,
        {},
        physicalResourceId=event["PhysicalResourceId"],
    )


def handle_update(event, context):
    logging.info("**Received update event")
    domain_id = event["PhysicalResourceId"]
    update_kwargs = preprocess_update_domain_args(
        event["ResourceProperties"], event.get("OldResourceProperties")
    )
    
    logging.info("**Updating studio domain")
    update_domain(domain_id, **update_kwargs)

    if (
        event["ResourceProperties"].get("EnableProjects")
        and not event["OldResourceProperties"].get("EnableProjects")
    ):
        smclient.enable_sagemaker_servicecatalog_portfolio()

    # TODO: Should we wait here for the domain to enter active state again?
    # TODO: Not returning all data props from Create is messing up some update operations
    # Not sure if there's a way for us to log/cache the ones that're only visible at create?
    cfnresponse.send(
        event,
        context,
        cfnresponse.SUCCESS,
        { "DomainId" : domain_id },
        physicalResourceId=event["PhysicalResourceId"],
    )


def preprocess_create_domain_args(config):
    default_user_settings = config["DefaultUserSettings"]
    domain_name = config["DomainName"]
    default_space_settings = config.get("DefaultSpaceSettings", {})
    domain_settings = config.get("DomainSettings", {})
    vpc_id = config.get("VPC")
    subnet_ids = config.get("SubnetIds")
    network_mode = config.get("AppNetworkAccessType", "PublicInternetOnly")
    if network_mode not in ("PublicInternetOnly", "VpcOnly"):
        raise ValueError(
            "AppNetworkAccessType, if provided, must be either 'PublicInternetOnly' or 'VpcOnly' "
            "as per SageMaker CreateDomain API."
        )

    if not vpc_id:
        # Try to look up the default VPC ID:
        # TODO: NextToken handling on this list API?
        available_vpcs = ec2.describe_vpcs()["Vpcs"]
        if len(available_vpcs) <= 0:
            raise ValueError("No default VPC exists - cannot create SageMaker Studio Domain")

        default_vpcs = list(filter(lambda v: v["IsDefault"], available_vpcs))
        if len(default_vpcs) == 1:
            vpc = default_vpcs[0]
        elif len(default_vpcs) > 1:
            raise ValueError("'VPC' not specified in config, and multiple default VPCs found")
        else:
            if len(available_vpcs) == 1:
                vpc = available_vpcs[0]
                logging.warning(f"Found exactly one (non-default) VPC: Using {vpc['VpcId']}")
            else:
                raise ValueError(
                    "'VPC' not specified in config, and multiple VPCs found with no 'default' VPC"
                )
        vpc_id = vpc["VpcId"]

    if not subnet_ids:
        # Use all the subnets
        # TODO: NextToken handling on this list API?
        available_subnets = ec2.describe_subnets(
            Filters=[{
                "Name": "vpc-id",
                "Values": [vpc_id],
            }],
        )["Subnets"]
        default_subnets = list(filter(lambda n: n["DefaultForAz"], available_subnets))
        subnet_ids = [
            n["SubnetId"] for n in
            (default_subnets if len(default_subnets) > 0 else available_subnets)
        ]
    elif isinstance(subnet_ids, str):
        subnet_ids = subnet_ids.split(",")

    if default_user_settings.get("ExecutionRole") and not default_space_settings.get("ExecutionRole"):
        default_space_settings["ExecutionRole"] = default_user_settings["ExecutionRole"]
    if default_space_settings.get("ExecutionRole") and not default_user_settings.get("ExecutionRole"):
        default_user_settings["ExecutionRole"] = default_space_settings["ExecutionRole"]
    return {
        "AppNetworkAccessType": network_mode,
        "DomainName": domain_name,
        "DomainSettings": domain_settings,
        "AuthMode": "IAM",
        "DefaultSpaceSettings": default_space_settings,
        "DefaultUserSettings": default_user_settings,
        "SubnetIds": subnet_ids,
        "VpcId": vpc_id,
    }


def preprocess_update_domain_args(new_props: dict, old_props: dict):
    update_args = {
        # TODO: AppSecurityGroupManagement not yet supported for update
        "DefaultSpaceSettings": new_props.get("DefaultSpaceSettings", {}),
        "DefaultUserSettings": new_props["DefaultUserSettings"],
        # TODO: SubnetIds not yet supported for update
    }
    if update_args["DefaultUserSettings"].get("ExecutionRole") and not update_args["DefaultSpaceSettings"].get("ExecutionRole"):
        update_args["DefaultSpaceSettings"]["ExecutionRole"] = update_args["DefaultUserSettings"]["ExecutionRole"]
    if update_args["DefaultSpaceSettings"].get("ExecutionRole") and not update_args["DefaultUserSettings"].get("ExecutionRole"):
        update_args["DefaultUserSettings"]["ExecutionRole"] = update_args["DefaultSpaceSettings"]["ExecutionRole"]
    if "AppNetworkAccessType" in new_props:
        update_args["AppNetworkAccessType"] = new_props["AppNetworkAccessType"]
    if "DomainSettings" in new_props:
        old_settings = old_props.get("DomainSettings", {}) if old_props else {}
        domain_updates = {}
        for key, new_value in new_props["DomainSettings"].items():
            changed = new_value != old_settings.get(key)
            update_key = "RStudioServerProDomainSettingsForUpdate" if key == "RStudioServerProDomainSettings" else key
            if changed:
                domain_updates[update_key] = new_value
        update_args["DomainSettingsForUpdate"] = domain_updates

    return update_args


def post_domain_create(domain_id, enable_projects=False):
    created = False
    time.sleep(0.2)
    while not created:
        description = smclient.describe_domain(DomainId=domain_id)
        status_lower = description["Status"].lower()
        if status_lower == "inservice":
            created = True
            break
        elif "fail" in status_lower:
            raise ValueError(
                f"Domain {domain_id} entered failed status"
            )
        time.sleep(5)
    logging.info("**SageMaker domain created successfully: %s", domain_id)

    if enable_projects:
        smclient.enable_sagemaker_servicecatalog_portfolio()

    vpc_id = description["VpcId"]
    # Retrieve the VPC security groups set up by SageMaker for EFS communication:
    inbound_efs_sg_id, outbound_efs_sg_id = vpctools.get_studio_efs_security_group_ids(domain_id, vpc_id)
    # Propose a valid subnet to create in this VPC for managing further setup actions:
    proposed_admin_subnet = vpctools.propose_subnet(vpc_id)
    return {
        "DomainDescription": description,
        "ProposedAdminSubnetCidr": proposed_admin_subnet["CidrBlock"],
        "InboundEFSSecurityGroupId": inbound_efs_sg_id,
        "OutboundEFSSecurityGroupId": outbound_efs_sg_id,
    }


def delete_domain(domain_id):
    response = smclient.delete_domain(
        DomainId=domain_id,
        RetentionPolicy={
            "HomeEfsFileSystem": "Delete"
        },
    )
    deleted = False
    time.sleep(0.2)
    while not deleted:
        try:
            smclient.describe_domain(DomainId=domain_id)
        except smclient.exceptions.ResourceNotFound:
            logging.info(f"Deleted domain {domain_id}")
            deleted = True
            break
        time.sleep(5)
    return response


def update_domain(domain_id: str, **update_domain_kwargs):
    retry_if_already_updating(
        lambda: smclient.update_domain(
            DomainId=domain_id,
            **update_domain_kwargs
        ),
    )
    updated = False
    time.sleep(0.5)
    while not updated:
        response = smclient.describe_domain(DomainId=domain_id)
        if response["Status"] == "InService":
            updated = True
        else:
            logging.info("Updating domain %s.. %s", domain_id, response["Status"])
        time.sleep(5)
    return response
