# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""AWS CDK constructs for creating SageMaker Domains with advanced configuration options
"""
# Python Built-Ins:
import os
from typing import Any, Dict, List, Optional, Sequence, Union

# External Dependencies:
from aws_cdk import CustomResource, Duration, RemovalPolicy
import aws_cdk.aws_ec2 as aws_ec2
import aws_cdk.aws_iam as aws_iam
from aws_cdk.aws_lambda import ILayerVersion
import aws_cdk.aws_kms as aws_kms
from aws_cdk.aws_lambda import Runtime as LambdaRuntime
from aws_cdk.aws_lambda_python_alpha import PythonFunction
import aws_cdk.aws_logs as aws_logs
import aws_cdk.custom_resources as cr
from constructs import Construct


LAMBDA_PATH = os.path.join(os.path.dirname(__file__), "fn_domain")


class SMStudioDomainCustomResourceProvider(cr.Provider):
    """Provider (AWS Lambda) for a CFn Custom Resource for SMStudio Domain

    If you're only creating one Domain in your stack, you probably don't need to create this
    explicitly: Just use `SageMakerStudioDomain` direct.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        smcr_helper_layer: ILayerVersion,
        *,
        eligible_domain_execution_role_arns: Optional[str] = None,
        log_retention: Optional[aws_logs.RetentionDays] = None,
        provider_function_env_encryption: Optional[aws_kms.IKey] = None,
        provider_function_name: Optional[str] = None,
        role: Optional[aws_iam.IRole] = None,
        security_groups: Optional[Sequence[aws_ec2.ISecurityGroup]] = None,
        total_timeout: Optional[Duration] = None,
        vpc: Optional[aws_ec2.IVpc] = None,
        vpc_subnets: Optional[Union[aws_ec2.SubnetSelection, Dict[str, Any]]] = None,
    ) -> None:
        """Create a SMStudioDomainCustomResourceProvider

        Most parameters are as per parent aws_cdk.custom_resources.Provider, with the below
        exceptions:

        Parameters
        ----------
        smcr_helper_layer :
            Shared Lambda layer with helper functions for SageMaker custom resources (see
            `cr_lambda_common`)
        eligible_domain_execution_role_arns :
            Set this optional ARN pattern to restrict the iam:PassRole permissions of the provider
            to a particular SageMaker Execution Role or wildcard pattern. By default (`None`), the
            provider will be created with permission to create Domains using any IAM Role
        role :
            By default, we'll create a role with required SageMaker, VPC, and IAM accesses. If you
            provide your own role, you'll need to ensure these permissions are set up. This role is
            used for the Custom Resource event handler function, not the CDK CR framework function.
        """
        if not role:
            role = aws_iam.Role(
                scope,
                "SMDomainProviderRole",
                assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                description=(
                    "Execution role for CFN Custom Resource Lambda providing SageMaker Studio "
                    "Domains"
                ),
                inline_policies={
                    "SageMakerDomainAdmin": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                actions=[
                                    "ec2:DescribeSecurityGroups",
                                    "ec2:DescribeSubnets",
                                    "ec2:DescribeVpcs",
                                    # IAM access to create service roles if not already existing:
                                    # (e.g. 'AWSServiceRoleForAmazonSageMakerNotebooks')
                                    "iam:CreateServiceLinkedRole",
                                    "iam:DeleteServiceLinkedRole",
                                    "iam:ListRoles",
                                    "sagemaker:CreateDomain",
                                    "sagemaker:DeleteDomain",
                                    "sagemaker:DescribeDomain",
                                    # TODO: Any other service catalog / IAM / etc permissions needed?
                                    "sagemaker:EnableSagemakerServicecatalogPortfolio",
                                    "sagemaker:UpdateDomain",
                                    # For enabling SageMaker Project Templates:
                                    "servicecatalog:AcceptPortfolioShare",
                                    "servicecatalog:AssociatePrincipalWithPortfolio",
                                    "servicecatalog:ListAcceptedPortfolioShares",
                                ],
                                resources=["*"],
                            ),
                            aws_iam.PolicyStatement(
                                actions=["iam:PassRole"],
                                resources=[eligible_domain_execution_role_arns or "*"],
                            ),
                        ],
                    ),
                },
                managed_policies=[
                    aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                        "service-role/AWSLambdaBasicExecutionRole",
                    ),
                    aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                        "AWSXRayDaemonWriteAccess",
                    ),
                ],
            )
        if not smcr_helper_layer:
            raise ValueError("smcr_helper_layer is required")
        on_event_handler = PythonFunction(
            scope,
            "SMDomainEventHandler",
            description=("CFn custom resource handler to create SageMaker Studio Domains"),
            entry=LAMBDA_PATH,
            environment_encryption=provider_function_env_encryption,
            index="main.py",
            handler="lambda_handler",
            layers=[smcr_helper_layer],
            memory_size=128,
            role=role,
            runtime=LambdaRuntime.PYTHON_3_12,
            timeout=Duration.seconds(895),  # Needs to wait for domain so can take a while
            vpc=vpc,
            vpc_subnets=vpc_subnets,
        )
        super().__init__(
            scope,
            id,
            on_event_handler=on_event_handler,
            # is_complete_handler=is_complete_handler,
            log_retention=log_retention,
            provider_function_env_encryption=provider_function_env_encryption,
            provider_function_name=provider_function_name,
            # query_interval=query_interval,
            # TODO: Add support for `role` without circular dependency
            # role=role,
            security_groups=security_groups,
            total_timeout=total_timeout,
            vpc=vpc,
            vpc_subnets=vpc_subnets,
        )


class SageMakerStudioDomain(CustomResource):
    """AWS CDK Construct for a SageMaker Studio Domain with additional features

    Unlike the CDK's built-in construct for a SMStudio Domain, this construct is backed by a Custom
    Resource Lambda and:
    - Defaults to the Default VPC (or else the first available VPC) in the account automatically,
        if a VPC is not specified.
    - Defaults to all default subnets (or else all available subnets in the VPC) if VPC subnets are
        not specified.
    - Optionally proposes a new small IPv4 CIDR for administrative tasks (e.g. EFS), compatible
        with the seleted VPC, at deploy time if `propose_admin_subnet` is set to `True`. (This is
        not so useful in CDK because of how constructs deal with VPC, but can be useful for SAM).
    - Optionally enables SageMaker Projects (SageMaker Service Catalog portfolio)
    """

    _propose_admin_subnet: bool

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        default_space_settings: Optional[dict] = None,
        default_user_settings: Optional[dict] = None,
        enable_docker_access: bool = True,
        enable_projects: bool = True,
        name: Optional[str] = None,
        propose_admin_subnet: bool = False,
        provider: Optional[SMStudioDomainCustomResourceProvider] = None,
        removal_policy: Optional[RemovalPolicy] = None,
        resource_type: str = "Custom::SageMakerStudioDomain",
        smcr_helper_layer: Optional[ILayerVersion] = None,
        subnet_ids: Optional[List[str]] = None,
        use_vpc_internet: bool = False,
        vpc_id: Optional[str] = None,
    ) -> None:
        """Create a SageMakerStudioDomain

        Parameters
        ----------
        default_space_settings :
            Dictionary as per SageMaker CreateDomain/UpdateDomain API
        default_user_settings :
            Dictionary as per SageMaker CreateDomain/UpdateDomain API
        enable_docker_access :
            Enable docker access within Studio (Does not *install* docker by itself)
        name :
            Name for the SageMaker Studio Domain to create (must be unique in account+region)
        propose_admin_subnet :
            Whether to propose a new administrative subnet IPv4 CIDR at deploy-time
        provider :
            Optional `SMStudioDomainCustomResourceProvider` if you'd like to customize provider
            configuration or re-use the Custom Resource Lambda across multiple Domains in your CDK
            app
        smcr_helper_layer :
            (Required if `provider` is not set) Shared Lambda layer with helper functions for
            SageMaker custom resources (see `cr_lambda_common`).
        use_vpc_internet :
            Whether spaces in the SageMaker Studio Domain should use the VPC (True) or direct
            connections (False) to access the internet
        """
        if not provider:
            provider = SMStudioDomainCustomResourceProvider(
                scope, "StudioDomainProvider", smcr_helper_layer=smcr_helper_layer
            )
        if not name:
            raise NotImplementedError("TODO: generate a name by default!")

        self._propose_admin_subnet = propose_admin_subnet
        resource_props = {
            "DomainName": name,
            "DomainSettings": {
                "DockerSettings": {
                    "EnableDockerAccess": "ENABLED" if enable_docker_access else "DISABLED",
                },
            },
            "AppNetworkAccessType": "VpcOnly" if use_vpc_internet else "PublicInternetOnly",
            "EnableProjects": enable_projects,
            "ProposeAdminSubnet": propose_admin_subnet,
        }
        if default_space_settings:
            resource_props["DefaultSpaceSettings"] = default_space_settings
        if default_user_settings:
            resource_props["DefaultUserSettings"] = default_user_settings
        if subnet_ids:
            resource_props["SubnetIds"] = subnet_ids
        if vpc_id:
            resource_props["VpcId"] = vpc_id

        super().__init__(
            scope,
            id,
            service_token=provider.service_token,
            # pascal_case_properties=None,
            properties=resource_props,
            removal_policy=removal_policy,
            resource_type=resource_type,
        )

    @property
    def domain_id(self) -> str:
        return self.get_att_string("DomainId")

    @property
    def domain_name(self) -> str:
        return self.get_att_string("DomainName")

    @property
    def home_efs_filesystem_id(self) -> str:
        return self.get_att_string("HomeEfsFileSystemId")

    @property
    def subnet_ids(self) -> str:
        """Returns *comma-separated string* of subnet IDs

        TODO: Refer to underlying subnets construct instead?
        """
        return self.get_att_string("SubnetIds")

    @property
    def url(self) -> str:
        return self.get_att_string("Url")

    @property
    def vpc_id(self) -> str:
        return self.get_att_string("VpcId")

    @property
    def proposed_admin_subnet_cidr(self) -> str:
        """Deploy-time-generated IPv4 CIDR of the proposed administrative subnet"""
        if self._propose_admin_subnet:
            return self.get_att_string("ProposedAdminSubnetCidr")
        raise ValueError(
            "ProposedAdminSubnetCidr attr not available if property propose_admin_subnet=False"
        )

    @property
    def inbound_efs_security_group_id(self) -> str:
        return self.get_att_string("InboundEFSSecurityGroupId")

    @property
    def outbound_efs_security_group_id(self) -> str:
        return self.get_att_string("OutboundEFSSecurityGroupId")
