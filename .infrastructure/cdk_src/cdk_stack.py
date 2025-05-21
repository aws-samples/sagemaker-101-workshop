# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""CDK stack for AWS workshop with Amazon SageMaker"""
# Python Built-Ins:
from typing import Optional

# External Dependencies:
from aws_cdk import Stack
from constructs import Construct
from aws_cdk import aws_ec2

# Local Dependencies:
from .smstudio import WorkshopSageMakerEnvironment


class WorkshopStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        sagemaker_code_checkout: Optional[str] = None,
        sagemaker_code_repo: Optional[str] = None,
    ) -> None:
        super().__init__(scope, construct_id)

        # Shared VPC:
        vpc = aws_ec2.Vpc(self, "Vpc")

        # Deploy SageMaker Studio environment:
        sagemaker_env = WorkshopSageMakerEnvironment(
            self,
            "SageMakerEnvironment",
            vpc=vpc,
            code_checkout=sagemaker_code_checkout,
            code_repo=sagemaker_code_repo,
            create_nbi=False,  # Don't create a 'Notebook Instance' (save costs, use Studio)
            domain_name="WorkshopDomain",
            instance_type="ml.t3.large",
            studio_classic=False,  # Keep SMStudio classic disabled (save costs)
        )
