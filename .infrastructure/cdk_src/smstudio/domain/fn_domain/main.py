# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Custom CloudFormation Resource for a SageMaker Studio Domain (with additional outputs)

As well as creating a SMStudio domain, this implementation:
- Defaults to the default VPC, or to any VPC when exactly one is present, if not explicitly configured
- Defaults to all default subnets if any are present, or else all subnets in VPC, if not explicitly set
- Discovers and outputs a list of security group IDs (default+SM-generated) that downstream resources may use
  to perform user setup actions on the Elastic File System
- Optionally proposes a new VPC Subnet CIDR to create for administrative tasks (e.g. Lambda functions that
  will mount the Studio EFS)

See `StudioDomainResourceProperties` for expected CloudFormation resource properties.

CloudFormation Return Values
----------------------------
Direct .Ref : str
    Amazon SageMaker Domain ID
DomainId : str
    Amazon SageMaker Domain ID
DomainName : str
    Amazon SageMaker Domain Name
HomeEfsFileSystemId : str
    FileSystemId of the domain's EFS File System (used by Studio classic)
InboundEFSSecurityGroupId : str
    Security Group ID of the inbound EFS security group (used by Studio classic)
OutboundEFSSecurityGroupId : str
    Security Group ID of the inbound EFS security group (used by Studio classic)
SubnetIds : str
    Comma-separated list of VPC subnet IDs to which the Studio Domain is associated
VpcId : str
    VPC ID to which the Studio Domain is associated
ProposedAdminSubnetCidr : Optional[str]
    IPv4 CIDR of the proposed new VPC subnet for administrative tasks, IF input properties
    `ProposeAdminSubnet` was set.
"""
# Python Built-Ins:
from __future__ import annotations
import json
import logging
import time
from typing import List, Optional

logging.getLogger().setLevel(logging.INFO)  # Set log level for AWS Lambda *BEFORE* other imports

# External Dependencies:
import boto3

# Local Dependencies:
from cfn import CustomResourceEvent, CustomResourceRequestType, parse_cfn_boolean
from sagemaker_util import retry_if_already_updating
import vpctools

logger = logging.getLogger("main")
ec2 = boto3.client("ec2")
smclient = boto3.client("sagemaker")


class StudioDomainResourceProperties:
    """Parser for CloudFormation resource properties for this Custom Resource

    Resource Properties
    -------------------

    DomainName : str
        The name of the SageMaker Studio Domain to create
    DefaultSpaceSettings : Optional[dict]
        The SageMaker CreateDomain DefaultSpaceSettings to apply, if any
    DefaultUserSettings : Optional[dict]
        The SageMaker CreateDomain DefaultUserSettings to apply, if any
    DomainSettings : Optional[dict]
        The SageMaker CreateDomain DomainSettings to apply, if any
    EnableProjects : Optional[bool]
        Whether to enable SageMaker Projects on the created domain. Default: True.
    ProposeAdminSubnet : Optional[bool]
        Whether to analyze the domain's VPC to propose a new administrative subnet IPv4 CIDR, or
        not. Default: False.
    SubnetIds : Optional[Union[str,List[str]]]
        The list (or comma-separated list) of VPC Subnet IDs to associate the SageMaker Domain
        with. If not set, will default to all the VPC's "default subnets" (if any are present) or
        otherwise all available subnets in the VPC.
    UseVpcNetworking : Optional[bool]
        Whether to configure the SageMaker Domain's spaces to access the internet directly (False)
        or through the assigned VPC (True). Note: SageMaker Studio requires a VPC to be configured
        for EFS access, even if direct internet access is used for spaces. Default: False.
    VpcId : Optional[str]
        ID of the VPC to deploy SageMaker Studio in. If not set, will default to the account's
        Default VPC (if one exists) or else the first VPC returned by `ec2:DescribeVpcs`.
    """

    default_space_settings: dict
    default_user_settings: dict
    domain_name: str
    domain_setings: dict
    enable_projects: bool
    propose_admin_subnet: bool
    subnet_ids: Optional[List[str]]
    use_vpc_networking: bool
    vpc_id: Optional[str]

    def __init__(self, resource_properties: dict):
        """Parse resource properties from CloudFormation-provided dict"""
        self.default_space_settings = resource_properties.get("DefaultSpaceSettings", {})
        self.default_user_settings = resource_properties.get("DefaultUserSettings", {})
        if self.default_user_settings.get("ExecutionRole") and not self.default_space_settings.get(
            "ExecutionRole"
        ):
            self.default_space_settings["ExecutionRole"] = self.default_user_settings[
                "ExecutionRole"
            ]
        elif self.default_space_settings.get(
            "ExecutionRole"
        ) and not self.default_user_settings.get("ExecutionRole"):
            self.default_user_settings["ExecutionRole"] = self.default_space_settings[
                "ExecutionRole"
            ]
        self.domain_name = resource_properties["DomainName"]
        self.domain_settings = resource_properties.get("DomainSettings", {})
        self.enable_projects = parse_cfn_boolean(
            resource_properties.get("EnableProjects", True), "EnableProjects"
        )
        self.propose_admin_subnet = parse_cfn_boolean(
            resource_properties.get("ProposeAdminSubnet", False), "ProposeAdminSubnet"
        )
        subnet_ids_raw = resource_properties.get("SubnetIds")
        if subnet_ids_raw is None:
            self.subnet_ids = None
        elif isinstance(subnet_ids_raw, str):
            self.subnet_ids = subnet_ids_raw.split(",")
        else:
            self.subnet_ids = subnet_ids_raw
        self.use_vpc_networking = parse_cfn_boolean(
            resource_properties.get("UseVpcNetworking", False), "UseVpcNetworking"
        )
        self.vpc_id = resource_properties.get("VpcId")

    def __str__(self):
        dict_val = {
            "DomainName": self.domain_name,
            "DefaultSpaceSettings": self.default_space_settings,
            "DefaultUserSettings": self.default_user_settings,
            "DomainSettings": self.domain_settings,
            "EnableProjects": self.enable_projects,
            "ProposeAdminSubnet": self.propose_admin_subnet,
            "UseVpcNetworking": self.use_vpc_networking,
        }
        if self.subnet_ids:
            dict_val["SubnetIds"] = self.subnet_ids
        if self.vpc_id:
            dict_val["VpcId"] = self.vpc_id
        return json.dumps(dict_val)

    @classmethod
    def from_str(cls, str_val) -> StudioDomainResourceProperties:
        return cls(json.loads(str_val))


def lambda_handler(event_raw: dict, context: dict):
    """Main entry point for (CDK) Custom Resource Lambda"""
    logger.info(event_raw)
    event = CustomResourceEvent(event_raw, StudioDomainResourceProperties)
    if event.request_type == CustomResourceRequestType.create:
        return handle_create(event, context)
    elif event.request_type == CustomResourceRequestType.update:
        return handle_update(event, context)
    elif event.request_type == CustomResourceRequestType.delete:
        return handle_delete(event, context)
    else:
        raise ValueError(f"Unsupported CFn RequestType '{event_raw['RequestType']}'")


def handle_create(event: CustomResourceEvent[StudioDomainResourceProperties], context):
    logger.info("**Received create request")

    # We split out pre- and post-processing because we'd like to always report our correct physicalResourceId
    # if erroring out after the actual creation, so that the subsequent deletion request can clean up.
    logger.info("**Preparing studio domain creation parameters")
    create_domain_args = preprocess_create_domain_args(event.props)
    logger.info("**Creating studio domain")
    creation = smclient.create_domain(**create_domain_args)
    _, _, domain_id = creation["DomainArn"].rpartition("/")

    result = post_domain_create(
        domain_id,
        enable_projects=event.props.enable_projects,
        propose_admin_subnet=event.props.propose_admin_subnet,
    )
    domain_desc = result["DomainDescription"]
    return {
        "PhysicalResourceId": domain_id,
        "Data": {
            "DomainId": domain_desc["DomainId"],
            "DomainName": domain_desc["DomainName"],
            "HomeEfsFileSystemId": domain_desc["HomeEfsFileSystemId"],
            "SubnetIds": ",".join(domain_desc["SubnetIds"]),
            "Url": domain_desc["Url"],
            "VpcId": domain_desc["VpcId"],
            "ProposedAdminSubnetCidr": result["ProposedAdminSubnetCidr"],
            "InboundEFSSecurityGroupId": result["InboundEFSSecurityGroupId"],
            "OutboundEFSSecurityGroupId": result["OutboundEFSSecurityGroupId"],
        },
    }


def handle_delete(event: CustomResourceEvent[StudioDomainResourceProperties], context):
    logger.info("**Received delete event for domain %s", event.physical_id)
    # TODO: This DOES NOT WORK on create fail in CDK because Phys ID is masked by provider-framework
    try:
        smclient.describe_domain(DomainId=event.physical_id)
    except smclient.exceptions.ResourceNotFound as exception:
        logger.info(f"Domain {event.physical_id} not found - returning success")
        # Already does not exist -> deletion success
        return {"PhysicalResourceId": event.physical_id, "Data": {}}
    logger.info("**Deleting studio domain")
    delete_domain(event.physical_id)
    return {"PhysicalResourceId": event.physical_id, "Data": {}}


def handle_update(event: CustomResourceEvent[StudioDomainResourceProperties], context):
    logger.info("**Received update event")
    update_domain_args = preprocess_update_domain_args(
        new_props=event.props, old_props=event.old_props
    )
    logger.info("**Updating studio domain")
    update_domain(event.physical_id, **update_domain_args)

    if event.props.enable_projects and not event.old_props.enable_projects:
        smclient.enable_sagemaker_servicecatalog_portfolio()

    return {"PhysicalResourceId": event.physical_id, "Data": {"DomainId": event.physical_id}}


def preprocess_create_domain_args(config: StudioDomainResourceProperties):
    default_space_settings = config.default_space_settings
    default_user_settings = config.default_user_settings
    domain_name = config.domain_name
    domain_settings = config.domain_settings
    vpc_id = config.vpc_id
    subnet_ids = config.subnet_ids
    network_mode = "VpcOnly" if config.use_vpc_networking else "PublicInternetOnly"

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
            Filters=[
                {
                    "Name": "vpc-id",
                    "Values": [vpc_id],
                }
            ],
        )["Subnets"]
        default_subnets = list(filter(lambda n: n["DefaultForAz"], available_subnets))
        subnet_ids = [
            n["SubnetId"]
            for n in (default_subnets if len(default_subnets) > 0 else available_subnets)
        ]
    elif isinstance(subnet_ids, str):
        subnet_ids = subnet_ids.split(",")

    return {
        "AppNetworkAccessType": network_mode,
        "DomainName": domain_name,
        "AuthMode": "IAM",
        "DefaultSpaceSettings": default_space_settings,
        "DefaultUserSettings": default_user_settings,
        "DomainSettings": domain_settings,
        "SubnetIds": subnet_ids,
        "VpcId": vpc_id,
    }


def preprocess_update_domain_args(
    new_props: StudioDomainResourceProperties, old_props: StudioDomainResourceProperties
):
    update_args = {
        # TODO: AppSecurityGroupManagement not yet supported for update
        "DefaultSpaceSettings": new_props.default_space_settings,
        "DefaultUserSettings": new_props.default_user_settings,
        # TODO: SubnetIds not yet supported for update
    }
    if new_props.use_vpc_networking != old_props.use_vpc_networking:
        update_args["AppNetworkAccessType"] = (
            "VpcOnly" if new_props.use_vpc_networking else "PublicInternetOnly"
        )
    if new_props.domain_settings:
        old_settings = old_props.domain_settings or {}
        domain_updates = {}
        for key, new_value in new_props.domain_settings.items():
            changed = new_value != old_settings.get(key)
            update_key = (
                "RStudioServerProDomainSettingsForUpdate"
                if key == "RStudioServerProDomainSettings"
                else key
            )
            if changed:
                domain_updates[update_key] = new_value
        update_args["DomainSettingsForUpdate"] = domain_updates

    return update_args


def post_domain_create(domain_id: str, enable_projects=False, propose_admin_subnet=False):
    created = False
    time.sleep(0.2)
    while not created:
        description = smclient.describe_domain(DomainId=domain_id)
        status_lower = description["Status"].lower()
        if status_lower == "inservice":
            created = True
            break
        elif "fail" in status_lower:
            raise ValueError(f"Domain {domain_id} entered failed status")
        time.sleep(5)
    logging.info("**SageMaker domain created successfully: %s", domain_id)

    if enable_projects:
        smclient.enable_sagemaker_servicecatalog_portfolio()

    vpc_id = description["VpcId"]
    # Retrieve the VPC security groups set up by SageMaker for EFS communication:
    inbound_efs_sg_id, outbound_efs_sg_id = vpctools.get_studio_efs_security_group_ids(
        domain_id, vpc_id
    )
    # Propose a valid subnet to create in this VPC for managing further setup actions:
    if propose_admin_subnet:
        proposed_admin_subnet_cidr = vpctools.propose_subnet(vpc_id)["CidrBlock"]
    else:
        proposed_admin_subnet_cidr = None
    return {
        "DomainDescription": description,
        "ProposedAdminSubnetCidr": proposed_admin_subnet_cidr,
        "InboundEFSSecurityGroupId": inbound_efs_sg_id,
        "OutboundEFSSecurityGroupId": outbound_efs_sg_id,
    }


def delete_domain(domain_id: str):
    response = smclient.delete_domain(
        DomainId=domain_id,
        RetentionPolicy={"HomeEfsFileSystem": "Delete"},
    )
    deleted = False
    time.sleep(0.5)
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
        lambda: smclient.update_domain(DomainId=domain_id, **update_domain_kwargs),
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
