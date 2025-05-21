# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""AWS CDK constructs for creating SageMaker Studio Users with advanced configuration options
"""
# Python Built-Ins:
import os
from typing import Any, Dict, Optional, Sequence, Union

# External Dependencies:
from aws_cdk import CustomResource, Duration, RemovalPolicy, Stack
import aws_cdk.aws_ec2 as aws_ec2
import aws_cdk.aws_iam as aws_iam
import aws_cdk.aws_kms as aws_kms
from aws_cdk.aws_lambda import ILayerVersion, Runtime as LambdaRuntime
from aws_cdk.aws_lambda_python_alpha import PythonFunction
import aws_cdk.aws_logs as aws_logs
import aws_cdk.custom_resources as cr
from constructs import Construct

# Local Dependencies:
from ..region_config import CfnSageMakerAppsByRegionMapping


LAMBDA_PATH = os.path.join(os.path.dirname(__file__), "fn_user")


class SMStudioUserCustomResourceProvider(cr.Provider):
    """Provider (AWS Lambda) for a CFn Custom Resource for SMStudio User Profile

    If you're only creating one LCC in your stack, you probably don't need to create this
    explicitly: Just use `SageMakerStudioUser` direct.
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
        """Create a SMStudioUserCustomResourceProvider

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
            By default, we'll create a role with required SageMaker and IAM accesses. If you
            provide your own role, you'll need to ensure these permissions are set up. This role is
            used for the Custom Resource event handler function, not the CDK CR framework function.
        """
        if not role:
            role = aws_iam.Role(
                scope,
                "SMUserProviderRole",
                assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                description=(
                    "Execution role for CFN Custom Resource Lambda providing SageMaker Studio "
                    "User Profiles"
                ),
                inline_policies={
                    "SageMakerLCCAdmin": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                actions=[
                                    "sagemaker:CreateUserProfile",
                                    "sagemaker:DeleteUserProfile",
                                    "sagemaker:DescribeUserProfile",
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
            "SMUserEventHandler",
            description=("CFn custom resource handler to create SageMaker Studio User Profiles"),
            entry=LAMBDA_PATH,
            environment_encryption=provider_function_env_encryption,
            index="main.py",
            handler="lambda_handler",
            layers=[smcr_helper_layer],
            memory_size=128,
            role=role,
            runtime=LambdaRuntime.PYTHON_3_12,
            timeout=Duration.minutes(10),  # Can take some time to wait for create/delete
            vpc=vpc,
            vpc_subnets=vpc_subnets,
        )
        super().__init__(
            scope,
            id,
            on_event_handler=on_event_handler,
            log_retention=log_retention,
            provider_function_env_encryption=provider_function_env_encryption,
            provider_function_name=provider_function_name,
            security_groups=security_groups,
            total_timeout=total_timeout,
            vpc=vpc,
            vpc_subnets=vpc_subnets,
        )


class SageMakerStudioUser(CustomResource):
    """AWS CDK Construct for a SageMaker Studio User Profile with additional features

    Unlike the CDK's built-in construct for a SMStudio User, this construct is backed by a Custom
    Resource Lambda and:
    - Exposes the EFS POSIX user ID mapped for the created SageMaker Studio user profile
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        app_arn_map: CfnSageMakerAppsByRegionMapping,
        domain_id: str,
        name: str,
        role_arn: str,  # TODO: Support default role creation?
        *,
        lcc_classic_arn: Optional[str] = None,
        lcc_jupyterlab_arn: Optional[str] = None,
        provider: Optional[SMStudioUserCustomResourceProvider] = None,
        removal_policy: Optional[RemovalPolicy] = None,
        resource_type: str = "Custom::SageMakerStudioUserProfile",
        smcr_helper_layer: Optional[ILayerVersion] = None,
    ) -> None:
        """Create a SageMakerStudioLifecycleConfig

        Parameters
        ----------
        app_arn_map :
            CFn mapping by AWS Region containing "jlabv3" default (classic) SageMaker Studio
            JupyterServer app image. See `..smstudio.region_config.STUDIO_APP_ARNS_BY_REGION`.
        domain_id :
            SageMaker Studio Domain ID to create the User Profile in
        name :
            (Domain-unique) name of the user profile
        role_arn :
            ARN of the SageMaker execution role to assign the user (which dictates their
            permissions once logged in to the notebook environment)
        lcc_classic_arn :
            Optional JupyterServer (classic) LifeCycle Configuration Script to enable for the user.
        lcc_jupyterlab_arn :
            Optional (new-style) JupyterLab space LifeCycle Configuration Script to enable for the
            user.
        enable_content_substitution :
            Set `True` to enable CloudFormation `!Sub` substitution on the provided script content,
            or `False` to disable.
        provider :
            Optional `SMStudioUserCustomResourceProvider` if you'd like to customize provider
            configuration or re-use the Custom Resource Lambda across multiple LCCs in your CDK app
        smcr_helper_layer :
            (Required if `provider` is not set) Shared Lambda layer with helper functions for
            SageMaker custom resources (see `cr_lambda_common`).
        """
        if not domain_id:
            raise ValueError("You must provide a SageMaker Studio domain_id")
        if not name:
            raise ValueError("You must provide a Domain-unique user profile name")
        if not provider:
            provider = SMStudioUserCustomResourceProvider(
                scope, "StudioUserProvider", smcr_helper_layer=smcr_helper_layer
            )

        resource_props = {
            "DomainId": domain_id,
            "UserProfileName": name,
            "UserSettings": {
                "ExecutionRole": role_arn,
                # Set new-style JupyterLab space defaults:
                "JupyterLabAppSettings": {
                    "DefaultResourceSpec": {
                        # TODO: Is this necessary or can we omit it?
                        "InstanceType": "ml.t3.medium",
                    },
                },
                # Set classic JupyterLabv3 default and attach the lifecycle configuration script:
                "JupyterServerAppSettings": {
                    "DefaultResourceSpec": {
                        "SageMakerImageArn": app_arn_map.find_in_map(
                            Stack.of(scope).region, "jlabv3"
                        ),
                        "InstanceType": "system",
                    },
                },
            },
        }
        if lcc_classic_arn:
            resource_props["UserSettings"]["JupyterServerAppSettings"]["DefaultResourceSpec"][
                "LifecycleConfigArn"
            ] = lcc_classic_arn
        if lcc_jupyterlab_arn:
            resource_props["UserSettings"]["JupyterLabAppSettings"]["DefaultResourceSpec"][
                "LifecycleConfigArn"
            ] = lcc_jupyterlab_arn

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
    def home_efs_file_system_uid(self):
        return self.get_att("HomeEfsFileSystemUid")

    @property
    def name(self):
        return self.ref
