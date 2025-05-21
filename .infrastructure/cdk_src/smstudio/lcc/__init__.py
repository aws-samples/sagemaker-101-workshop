# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""AWS CDK constructs for LifeCycle Configurations in Amazon SageMaker
"""
# Python Built-Ins:
import os
from typing import Any, Dict, Optional, Sequence, TextIO, Union

# External Dependencies:
from aws_cdk import CustomResource, Duration, Fn, RemovalPolicy, Stack
import aws_cdk.aws_ec2 as aws_ec2
import aws_cdk.aws_iam as aws_iam
import aws_cdk.aws_kms as aws_kms
from aws_cdk.aws_lambda import ILayerVersion, Runtime as LambdaRuntime
from aws_cdk.aws_lambda_python_alpha import PythonFunction
import aws_cdk.aws_logs as aws_logs
import aws_cdk.aws_sagemaker as sagemaker_cdk
import aws_cdk.custom_resources as cr
from constructs import Construct


CR_LAMBDA_PATH = os.path.join(os.path.dirname(__file__), "fn_studio_lcconfig")


class SageMakerNotebookLifecycleConfig(Construct):
    """AWS CDK Construct for a SageMaker Notebook Instance Lifecycle Configuration Script

    See also
    --------
    https://docs.aws.amazon.com/sagemaker/latest/dg/notebook-lifecycle-config.html
    https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-sagemaker-notebookinstancelifecycleconfig.html
    """

    cfn_construct: sagemaker_cdk.CfnNotebookInstanceLifecycleConfig

    def __init__(
        self,
        scope: Construct,
        id: str,
        *args,
        name: Optional[str] = None,
        on_create_script: Optional[Union[str, TextIO]] = None,
        on_start_script: Optional[Union[str, TextIO]] = None,
    ) -> None:
        """Create a SageMakerNotebookLifecycleConfig

        Parameters
        ----------
        name :
            If not provided, a default will be generated based on the stack name
        on_create_script :
            The text of the shell script you'd like to run on Notebook Instance creation (one-off),
            or an open file handle from which the script may be `.read()`. This script may contain
            placeholder variables to be filled in by `Fn::Sub`.
        on_start_script :
            The text of the shell script you'd like to run on Notebook Instance start (every time),
            or an open file handle from which the script may be `.read()`. This script may contain
            placeholder variables to be filled in by `Fn::Sub`.
        """
        super().__init__(scope, id)
        stack = Stack.of(self)

        self.to_string()
        if name is None:
            # TODO: How to get fully qualified construct name?
            name = f"{stack.stack_name}-LCC"

        self.cfn_construct = sagemaker_cdk.CfnNotebookInstanceLifecycleConfig(
            self,
            id,
            notebook_instance_lifecycle_config_name=name,  # (Name prop is mandatory)
            on_create=(
                [self._script_to_lcc_hook_property(on_create_script)] if on_create_script else None
            ),
            on_start=(
                [self._script_to_lcc_hook_property(on_start_script)] if on_start_script else None
            ),
        )

    @staticmethod
    def _script_to_lcc_hook_property(script: Union[str, TextIO], enable_substitution: bool = True):
        """Convert a LCC script (string or file handle) to a CFn LCC hook property

        Parameters
        ----------
        script :
            String content of the shell script, or an open file from which the content may be
            `.read()`
        enable_substitution :
            Whether to pass the script content through CloudFormation Fn::Sub variable resolution.
            Default True.
        """
        content = script if isinstance(script, str) else script.read()

        if enable_substitution:
            content = Fn.sub(content)
        return (
            sagemaker_cdk.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
                content=Fn.base64(content)
            )
        )
        # return {
        #     "content": Fn.base64(content)
        # }

    @property
    def name(self) -> str:
        return self.cfn_construct.attr_notebook_instance_lifecycle_config_name


class SMStudioLCCCustomResourceProvider(cr.Provider):
    """Provider (AWS Lambda) for a CFn Custom Resource for SMStudio Lifecycle Configuration

    If you're only creating one LCC in your stack, you probably don't need to create this
    explicitly: Just use `SageMakerStudioLifecycleConfig` direct.
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
        """Create a SMStudioLCCCustomResourceProvider

        Most parameters are as per parent aws_cdk.custom_resources.Provider, with the below
        exceptions:

        Parameters
        ----------
        eligible_domain_execution_role_arns :
            Set this optional ARN pattern to restrict the iam:PassRole permissions of the provider
            to a particular SageMaker Execution Role or wildcard pattern. By default (`None`), the
            provider will be created with permission to create Domains using any IAM Role
        role :
            By default, we'll create a role with required SageMaker and IAM accesses. If you
            provide your own role, you'll need to ensure these permissions are set up. This role is
            used for the Custom Resource event handler function, not the CDK CR framework function.
        smcr_helper_layer :
            Shared Lambda layer with helper functions for SageMaker custom resources (see
            `cr_lambda_common`)
        """
        if not role:
            role = aws_iam.Role(
                scope,
                "Role",
                assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                description=(
                    "Execution role for CFN Custom Resource Lambda providing SageMaker Studio "
                    "Lifecycle Configuration Scripts"
                ),
                inline_policies={
                    "SageMakerLCCAdmin": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                actions=[
                                    "sagemaker:CreateStudioLifecycleConfig",
                                    "sagemaker:DeleteStudioLifecycleConfig",
                                    "sagemaker:DescribeDomain",
                                    "sagemaker:UpdateDomain",
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
            "EventHandler",
            description=(
                "CFn custom resource handler to create SageMaker Studio Lifecycle Configurations"
            ),
            entry=CR_LAMBDA_PATH,
            environment_encryption=provider_function_env_encryption,
            index="main.py",
            handler="lambda_handler",
            layers=[smcr_helper_layer],
            memory_size=128,
            role=role,
            runtime=LambdaRuntime.PYTHON_3_12,
            security_groups=security_groups,
            timeout=Duration.minutes(10),  # Can take a while if it has to wait for updating domain
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
            # TODO: Add support for `role` without circular dependency
            # role=role,
            security_groups=security_groups,
            total_timeout=total_timeout,
            vpc=vpc,
            vpc_subnets=vpc_subnets,
        )


class SageMakerStudioLifecycleConfig(CustomResource):
    """AWS CDK Construct for a SageMaker Studio Lifecycle Configuration Script"""

    def __init__(
        self,
        scope: Construct,
        id: str,
        content: Union[str, TextIO],
        *,
        app_type: str = "JupyterServer",
        domain_id: Optional[str] = None,
        enable_content_substitution: bool = True,
        name: Optional[str] = None,
        provider: Optional[SMStudioLCCCustomResourceProvider] = None,
        removal_policy: Optional[RemovalPolicy] = None,
        resource_type: str = "Custom::SageMakerStudioLifecycleConfiguration",
        smcr_helper_layer: Optional[ILayerVersion] = None,
    ) -> None:
        """Create a SageMakerStudioLifecycleConfig

        Parameters
        ----------
        app_type :
            SageMaker Studio App Type e.g. "JupyterServer" or "KernelGateway"
        domain_id :
            SageMaker Studio Domain ID to associate the LCC to (will not be associated, if not set)
        enable_content_substitution :
            Set `True` to enable CloudFormation `!Sub` substitution on the provided script content,
            or `False` to disable.
        name :
            (Account+region unique) name of the LifeCycle Configuration script to create
        propose_admin_subnet :
            Whether to propose a new administrative subnet IPv4 CIDR at deploy-time
        provider :
            Optional `SMStudioLCCCustomResourceProvider` if you'd like to customize provider
            configuration or re-use the Custom Resource Lambda across multiple LCCs in your CDK app
        smcr_helper_layer :
            (Required if `provider` is not set) Shared Lambda layer with helper functions for
            SageMaker custom resources (see `cr_lambda_common`).
        """
        if not isinstance(content, str):
            content = content.read()
        if enable_content_substitution:
            content = Fn.sub(content)
        if not provider:
            provider = SMStudioLCCCustomResourceProvider(
                scope, "StudioLCCProvider", smcr_helper_layer=smcr_helper_layer
            )
        if not name:
            raise NotImplementedError("TODO: generate a name by default!")

        props = {"AppType": app_type, "Name": name, "Content": Fn.base64(content)}
        if domain_id:
            props["DomainId"] = domain_id

        super().__init__(
            scope,
            id,
            service_token=provider.service_token,
            # pascal_case_properties=None,
            properties=props,
            removal_policy=removal_policy,
            resource_type=resource_type,
        )

    @property
    def arn(self):
        return self.ref
