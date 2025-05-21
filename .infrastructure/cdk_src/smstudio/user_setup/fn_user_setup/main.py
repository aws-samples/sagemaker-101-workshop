# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Custom CloudFormation Resource for loading content to a SageMaker Studio user

Updating or deleting this resource does not currently do anything. Errors in the setup process are
also ignored (typically don't want to roll back the whole stack just because we couldn't clone a
repo - as users can always do it manually!)

For input CloudFormation resource properties, see `StudioUserSetupResourceProperties` in base.py.

CloudFormation Return Values
----------------------------
Direct .Ref : string
    SageMaker user profile name
"""
# Python Built-Ins:
import logging

logging.getLogger().setLevel(logging.INFO)  # Set log level for AWS Lambda *BEFORE* other imports

# Local Dependencies:
from base import StudioUserSetupResourceProperties
from cfn import CustomResourceEvent, CustomResourceRequestType
import content
import smprojects

logger = logging.getLogger("main")


def lambda_handler(event_raw: dict, context: dict):
    logger.info(event_raw)
    event = CustomResourceEvent(event_raw, StudioUserSetupResourceProperties)
    if event.request_type == CustomResourceRequestType.create:
        try:
            smprojects.on_create_update(event)
        except:
            logging.exception("Failed to set up user for SageMaker Projects")
        return content.handle_create(event, context)
    elif event.request_type == CustomResourceRequestType.update:
        try:
            smprojects.on_create_update(event)
        except:
            logging.exception("Failed to set up user for SageMaker Projects")
        return content.handle_update(event, context)
    elif event.request_type == CustomResourceRequestType.delete:
        return content.handle_delete(event, context)
    else:
        raise ValueError(f"Unsupported CFn RequestType '{event_raw['RequestType']}'")
