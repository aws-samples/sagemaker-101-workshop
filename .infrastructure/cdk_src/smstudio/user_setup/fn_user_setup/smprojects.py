# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Custom CloudFormation Resource for SageMaker Projects setup

See `.base.StudioUserSetupResourceProperties` for CloudFormation input Properties, and main.py
docstring for CloudFormation return values.

This sub-resource handles granting (existing) SMStudio user profiles permission to view and launch
SageMaker Project Templates, from CloudFormation.
"""
# Python Built-Ins:
from logging import getLogger

# External Dependencies:
import boto3  # AWS SDK for Python

# Local Dependencies:
from base import StudioUserSetupResourceProperties
from cfn import CustomResourceEvent


scclient = boto3.client("servicecatalog")
smclient = boto3.client("sagemaker")
logger = getLogger("smprojects")


def enable_sm_projects_for_role(studio_role_arn: str) -> None:
    """Enable SageMaker Projects for a SageMaker Execution Role
    This function assumes you've already run Boto SageMaker
    enable_sagemaker_servicecatalog_portfolio() for the account as a whole
    """
    portfolios_resp = scclient.list_accepted_portfolio_shares()

    portfolio_ids = set()
    for portfolio in portfolios_resp["PortfolioDetails"]:
        if portfolio["ProviderName"] == "Amazon SageMaker":
            portfolio_ids.add(portfolio["Id"])

    logger.info(f"Adding {len(portfolio_ids)} SageMaker SC portfolios to role {studio_role_arn}")
    for portfolio_id in portfolio_ids:
        scclient.associate_principal_with_portfolio(
            PortfolioId=portfolio_id, PrincipalARN=studio_role_arn, PrincipalType="IAM"
        )


def disable_sm_projects_for_role(studio_role_arn: str) -> None:
    """Enable SageMaker Projects for a SageMaker Execution Role
    This function assumes you've already run Boto SageMaker
    enable_sagemaker_servicecatalog_portfolio() for the account as a whole
    """
    portfolios_resp = scclient.list_accepted_portfolio_shares()

    portfolio_ids = set()
    for portfolio in portfolios_resp["PortfolioDetails"]:
        if portfolio["ProviderName"] == "Amazon SageMaker":
            portfolio_ids.add(portfolio["Id"])

    logger.info(
        f"Removing {len(portfolio_ids)} SageMaker SC portfolios from role {studio_role_arn}"
    )
    for portfolio_id in portfolio_ids:
        scclient.disassociate_principal_from_portfolio(
            PortfolioId=portfolio_id,
            PrincipalARN=studio_role_arn,
        )


def get_user_profile_role_arn(domain_id: str, user_profile_name: str) -> str:
    user_desc = smclient.describe_user_profile(
        DomainId=domain_id, UserProfileName=user_profile_name
    )
    return user_desc["UserSettings"]["ExecutionRole"]


def on_create_update(event: CustomResourceEvent[StudioUserSetupResourceProperties]) -> bool:
    logger.info("**Received create/update request")
    if event.props.enable_projects:
        logger.info("**Setting up SageMaker projects for user")
        role_arn = get_user_profile_role_arn(event.props.domain_id, event.props.user_profile_name)
        enable_sm_projects_for_role(role_arn)
        return True
    else:
        logger.info("**Skipping removing SM Projects from user")
        return False
