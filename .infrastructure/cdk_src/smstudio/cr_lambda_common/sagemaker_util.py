# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Shared utilities for CloudFormation Custom Resources working with SageMaker"""
# Python Built-Ins:
import logging
import time
from typing import Callable, TypeVar

# External Dependencies:
from botocore.exceptions import ClientError


logger = logging.getLogger("sagemaker_util")
TResponse = TypeVar("TResponse")


def retry_if_already_updating(fn: Callable[[], TResponse], delay_secs: float = 10) -> TResponse:
    """Retry `fn` every `delay_secs` if it fails because a SageMaker Domain is already updating"""
    while True:
        try:
            return fn()
        except ClientError as err:
            if "is already being updated" in err.response["Error"]["Message"]:
                logger.info("Domain already updating - waiting to retry...")
                time.sleep(delay_secs)
                continue
            else:
                raise err
