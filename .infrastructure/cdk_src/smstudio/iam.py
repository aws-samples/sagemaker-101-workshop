# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""AWS CDK constructs for IAM roles in Amazon SageMaker workshops
"""
# Python Built-Ins:
from typing import Mapping, Optional, Sequence

# External Dependencies:
from aws_cdk import Duration
import aws_cdk.aws_iam as iam
from aws_cdk.aws_iam import IManagedPolicy, IPrincipal, PolicyDocument
from constructs import Construct


class WorkshopSageMakerExecutionRole(iam.Role):
    """An IAM role set up for Amazon SageMaker execution in workshops

    This construct sets permissive permissions by default and is not recommended for production use
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        assumed_by_extra: Optional[IPrincipal] = None,
        description: Optional[str] = None,
        enable_bedrock: bool = True,
        enable_codewhisperer: bool = True,
        enable_glueis: bool = True,
        enable_iamfullaccess: bool = False,
        enable_s3fullaccess: bool = True,
        enable_sagemakerfullaccess: bool = True,
        external_ids: Optional[Sequence[str]] = None,
        extras_inline_policy_name: str = "WorkshopExtras",
        inline_policies: Optional[Mapping[str, PolicyDocument]] = None,
        managed_policies: Optional[Sequence[IManagedPolicy]] = None,
        max_session_duration: Optional[Duration] = None,
        path: Optional[str] = None,
        permissions_boundary: Optional[IManagedPolicy] = None,
        role_name: Optional[str] = None,
    ) -> None:
        """Create a WorkshopSageMakerExecutionRole

        Parameters are generally as per CDK iam.Role, but with customized default values.

        Parameters
        ----------
        scope :
            CDK construct scope
        id :
            CDK construct ID
        assumed_by_extra :
            Optionally provide an extra Principal this role should trust. SageMaker and (if
            `enable_glueis` is set) AWS Glue principals will already be trusted: You only need to
            set this parameter if needing to add an additional principal.
        description :
            A description of the role
        enable_bedrock :
            This construct will grant bedrock:* permissions in an inline policy by default. Set
            False to prevent this.
        enable_codewhisperer :
            This construct will grant the codewhisperer:GenerateRecommendations permission in an
            inline policy by default. Set False to prevent this.
        enable_glueis :
            This construct will trust the AWS Glue service and apply the AWS Managed
            AwsGlueSessionUserRestrictedServiceRole by default, for using Glue Interactive Sessions
            within SageMaker Studio notebooks. Set False to prevent this.
        enable_iamfullaccess :
            You can attach the AWS Managed IAMFullAccess policy to your role by setting this to
            `True`... But since this is a very broad permission, it's `False` by default.
        enable_s3fullaccess :
            By default, this construct will append the AmazonS3FullAccess AWS Managed Policy to
            your `managed_policies`. Set False to prevent this.
        enable_sagemakerfullaccess :
            By default, this construct will append the AmazonSageMakerFullAccess AWS Managed Policy
            to your `managed_policies`. Set False to prevent this.
        external_ids :
            A list of external IDs that are allowed to assume the role
        extras_inline_policy_name :
            The name to use for the auto-generated Inline Policy of extra permissions for
            SageMaker workshops.
        inline_policies :
            Inline policies to attach to the role
        managed_policies :
            By default, we'll apply AWS policies AmazonSageMakerFullAccess, AmazonS3FullAccess,
            AwsGlueSessionUserRestrictedServiceRole, and IAMFullAccess. You only need to set this
            parameter if you want to override this.
        max_session_duration :
            The maximum session duration for the role
        path :
            The path for the role
        permissions_boundary :
            The permissions boundary for the role
        role_name :
            The name of the role
        """
        principals = [iam.ServicePrincipal("sagemaker.amazonaws.com")]
        extra_managed_policies = []
        inline_policy_statements = []

        # Parse required extra principals/policies/statements from the config options:
        if enable_bedrock:
            inline_policy_statements.append(
                iam.PolicyStatement(actions=["bedrock:*"], resources=["*"], sid="BedrockAccess")
            )
        if enable_codewhisperer:
            inline_policy_statements.append(
                iam.PolicyStatement(
                    actions=["codewhisperer:GenerateRecommendations"],
                    resources=["*"],
                    sid="CodeWhispererPermissions",
                )
            )
        if enable_glueis:
            principals.append(iam.ServicePrincipal("glue.amazonaws.com"))
            extra_managed_policies.append(
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AwsGlueSessionUserRestrictedServiceRole"
                )
            )
            inline_policy_statements.append(
                # TODO: Scope this down better
                iam.PolicyStatement(
                    actions=["iam:GetRole", "iam:PassRole", "sts:GetCallerIdentity"],
                    resources=["*"],
                    sid="GlueSessionsIAMPerms",
                )
            )
        if enable_iamfullaccess:
            extra_managed_policies.append(
                iam.ManagedPolicy.from_aws_managed_policy_name("IAMFullAccess")
            )
        if enable_s3fullaccess:
            extra_managed_policies.append(
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
            )
        if enable_sagemakerfullaccess:
            extra_managed_policies.append(
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")
            )

        # Apply the extras to the core iam.Role arguments:
        if assumed_by_extra:
            principals.append(assumed_by_extra)
        assumed_by = iam.CompositePrincipal(*principals)
        if len(extra_managed_policies):
            if not managed_policies:
                managed_policies = []
            managed_policies = [*managed_policies, *extra_managed_policies]
        if len(inline_policy_statements):
            if not inline_policies:
                inline_policies = {}
            if extras_inline_policy_name in inline_policies:
                inline_policies[extras_inline_policy_name].add_statements(inline_policy_statements)
            else:
                inline_policies[extras_inline_policy_name] = iam.PolicyDocument(
                    statements=inline_policy_statements,
                )

        # Call iam.Role with the updated args:
        super().__init__(
            scope,
            id,
            assumed_by=assumed_by,
            description=description,
            external_ids=external_ids,
            inline_policies=inline_policies,
            managed_policies=managed_policies,
            max_session_duration=max_session_duration,
            path=path,
            permissions_boundary=permissions_boundary,
            role_name=role_name,
        )
