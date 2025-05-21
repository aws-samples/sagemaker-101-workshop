# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""CDK constructs for cross-regional configuration mapping of SageMaker resources
"""
# Python Built-Ins:
from typing import Optional, Tuple

# External Dependencies:
from aws_cdk import CfnMapping
from constructs import Construct


STUDIO_APP_ARNS_BY_REGION = {
    "us-east-1": {
        "datascience": "arn:aws:sagemaker:us-east-1:081325390199:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:us-east-1:081325390199:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:us-east-1:081325390199:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:us-east-1:081325390199:image/jupyter-server-3",
    },
    "us-east-2": {
        "datascience": "arn:aws:sagemaker:us-east-2:429704687514:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:us-east-2:429704687514:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:us-east-2:429704687514:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:us-east-2:429704687514:image/jupyter-server-3",
    },
    "us-west-1": {
        "datascience": "arn:aws:sagemaker:us-west-1:742091327244:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:us-west-1:742091327244:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:us-west-1:742091327244:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:us-west-1:742091327244:image/jupyter-server-3",
    },
    "us-west-2": {
        "datascience": "arn:aws:sagemaker:us-west-2:236514542706:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:us-west-2:236514542706:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:us-west-2:236514542706:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:us-west-2:236514542706:image/jupyter-server-3",
    },
    "af-south-1": {
        "datascience": "arn:aws:sagemaker:af-south-1:559312083959:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:af-south-1:559312083959:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:af-south-1:559312083959:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:af-south-1:559312083959:image/jupyter-server-3",
    },
    "ap-east-1": {
        "datascience": "arn:aws:sagemaker:ap-east-1:493642496378:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:ap-east-1:493642496378:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:ap-east-1:493642496378:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:ap-east-1:493642496378:image/jupyter-server-3",
    },
    "ap-south-1": {
        "datascience": "arn:aws:sagemaker:ap-south-1:394103062818:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:ap-south-1:394103062818:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:ap-south-1:394103062818:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:ap-south-1:394103062818:image/jupyter-server-3",
    },
    "ap-northeast-2": {
        "datascience": "arn:aws:sagemaker:ap-northeast-2:806072073708:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:ap-northeast-2:806072073708:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:ap-northeast-2:806072073708:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:ap-northeast-2:806072073708:image/jupyter-server-3",
    },
    "ap-southeast-1": {
        "datascience": "arn:aws:sagemaker:ap-southeast-1:492261229750:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:ap-southeast-1:492261229750:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:ap-southeast-1:492261229750:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:ap-southeast-1:492261229750:image/jupyter-server-3",
    },
    "ap-southeast-2": {
        "datascience": "arn:aws:sagemaker:ap-southeast-2:452832661640:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:ap-southeast-2:452832661640:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:ap-southeast-2:452832661640:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:ap-southeast-2:452832661640:image/jupyter-server-3",
    },
    "ap-southeast-3": {
        "datascience": "arn:aws:sagemaker:ap-southeast-3:276181064229:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:ap-southeast-3:276181064229:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:ap-southeast-3:276181064229:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:ap-southeast-3:276181064229:image/jupyter-server-3",
    },
    "ap-northeast-1": {
        "datascience": "arn:aws:sagemaker:ap-northeast-1:102112518831:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:ap-northeast-1:102112518831:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:ap-northeast-1:102112518831:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:ap-northeast-1:102112518831:image/jupyter-server-3",
    },
    # TODO: ap-northeast-2 and ap-northeast-3 if available?
    "ca-central-1": {
        "datascience": "arn:aws:sagemaker:ca-central-1:310906938811:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:ca-central-1:310906938811:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:ca-central-1:310906938811:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:ca-central-1:310906938811:image/jupyter-server-3",
    },
    "eu-central-1": {
        "datascience": "arn:aws:sagemaker:eu-central-1:936697816551:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:eu-central-1:936697816551:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:eu-central-1:936697816551:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:eu-central-1:936697816551:image/jupyter-server-3",
    },
    # TODO: eu-central-2 if available?
    "eu-west-1": {
        "datascience": "arn:aws:sagemaker:eu-west-1:470317259841:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:eu-west-1:470317259841:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:eu-west-1:470317259841:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:eu-west-1:470317259841:image/jupyter-server-3",
    },
    "eu-west-2": {
        "datascience": "arn:aws:sagemaker:eu-west-2:712779665605:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:eu-west-2:712779665605:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:eu-west-2:712779665605:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:eu-west-2:712779665605:image/jupyter-server-3",
    },
    "eu-west-3": {
        "datascience": "arn:aws:sagemaker:eu-west-3:615547856133:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:eu-west-3:615547856133:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:eu-west-3:615547856133:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:eu-west-3:615547856133:image/jupyter-server-3",
    },
    "eu-north-1": {
        "datascience": "arn:aws:sagemaker:eu-north-1:243637512696:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:eu-north-1:243637512696:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:eu-north-1:243637512696:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:eu-north-1:243637512696:image/jupyter-server-3",
    },
    "eu-south-1": {
        "datascience": "arn:aws:sagemaker:eu-south-1:592751261982:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:eu-south-1:592751261982:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:eu-south-1:592751261982:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:eu-south-1:592751261982:image/jupyter-server-3",
    },
    # TODO: me-central-1 and me-south-1 if available?
    "sa-east-1": {
        "datascience": "arn:aws:sagemaker:sa-east-1:782484402741:image/datascience-1.0",
        "datascience2": "arn:aws:sagemaker:sa-east-1:782484402741:image/sagemaker-data-science-38",
        "datascience3": "arn:aws:sagemaker:sa-east-1:782484402741:image/sagemaker-data-science-310-v1",
        "jlabv3": "arn:aws:sagemaker:sa-east-1:782484402741:image/jupyter-server-3",
    },
}


class CfnSageMakerAppsByRegionMapping(CfnMapping):
    """Construct for a CloudFormation Mapping of common SMStudio app ARNs by region"""

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        lazy: Optional[bool] = None,
    ) -> None:
        super().__init__(scope, id, lazy=lazy, mapping=STUDIO_APP_ARNS_BY_REGION)

    @property
    def supported_regions(self) -> Tuple[str]:
        """Alphabetically sorted list of all regions supported in the map"""
        return tuple(sorted(STUDIO_APP_ARNS_BY_REGION.keys()))

    @property
    def supported_apps(self) -> Tuple[str]:
        """Alphabetically sorted list of all Studio app names supported in the map"""
        return next(tuple(sorted(vals)) for _, vals in STUDIO_APP_ARNS_BY_REGION)
