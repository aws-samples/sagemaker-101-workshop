# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Shared Lambda constructs to help with SageMaker Studio CDK"""
# Python Built-Ins:
import os
from typing import Any, Dict, Sequence

# External Dependencies:
from aws_cdk import RemovalPolicy
from aws_cdk.aws_lambda import Architecture, Runtime
from aws_cdk.aws_lambda_python_alpha import BundlingOptions, PythonLayerVersion
from constructs import Construct

LAYER_CODE_PATH = os.path.join(os.path.dirname(__file__), "cr_lambda_common")


class SMCustomResourceHelperLayer(PythonLayerVersion):
    """Lambda layer with helper functions/classes for SageMaker CloudFormation Custom Resources

    It works like a regular aws_cdk.aws_lambda_python_alpha.PythonLayerVersion, but the code
    location is already specified for you. You probably don't need to specify
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        bundling: BundlingOptions | Dict[str, Any] | None = None,
        compatible_architectures: Sequence[Architecture] | None = None,
        compatible_runtimes: Sequence[Runtime] | None = None,
        description: str | None = (
            "Helper functions & classes for SageMaker CloudFormation custom resources"
        ),
        layer_version_name: str | None = None,
        license: str | None = None,
        removal_policy: RemovalPolicy | None = None,
    ) -> None:
        super().__init__(
            scope,
            id,
            entry=LAYER_CODE_PATH,
            bundling=bundling,
            compatible_architectures=compatible_architectures,
            compatible_runtimes=[
                Runtime.PYTHON_3_8,
                Runtime.PYTHON_3_9,
                Runtime.PYTHON_3_10,
                Runtime.PYTHON_3_11,
                Runtime.PYTHON_3_12,
            ],
            description=description,
            layer_version_name=layer_version_name,
            license=license,
            removal_policy=removal_policy,
        )
