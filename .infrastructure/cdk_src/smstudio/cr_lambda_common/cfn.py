# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Types/classes for working with CloudFormation Custom Resource events in Python Lambda functions

TODO: Assess `aws-lambda-powertools` and/or `crhelper` instead

https://docs.powertools.aws.dev/lambda/python/
https://github.com/aws-cloudformation/custom-resource-helper
"""
# Python Built-Ins:
from enum import Enum
from logging import getLogger
from typing import Generic, Optional, Type, TypeVar, Union

logger = getLogger("cfn")


class CustomResourceRequestType(str, Enum):
    "Enumeration of CloudFormation event 'RequestType's received by a custom resource"
    create = "Create"
    update = "Update"
    delete = "Delete"


def parse_cfn_boolean(raw: Union[bool, str], var_name: Optional[str] = None) -> bool:
    """Parse a boolean value from (potentially stringified/text) CloudFormation event properties

    Common text values like 'true', 'yes', etc are supported. Raises a ValueError if the raw
    value is `None` or cannot be interpreted as boolean.

    Parameters
    ----------
    raw :
        The raw value from CloudFormation, which might be a string
    var_name :
        Optional name of the variable to be parsed (only used for error messages)
    """
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        if raw in ("1", "t", "true", "y", "yes"):
            return True
        elif raw in ("0", "f", "false", "n", "no"):
            return False
        else:
            raise ValueError(
                f"Invalid {(var_name + ' ') if var_name else ''}string value '{raw}' (expected boolean)"
            )
    else:
        raise ValueError(
            f"Invalid {(var_name + ' ') if var_name else ''}value type '{type(raw)}' (expected boolean)"
        )


TResourceProps = TypeVar("TResourceProps")


class CustomResourceEvent(Generic[TResourceProps]):
    """Class to parse a CFn Custom Resource event

    This is a generic class: TResourceProps should be a class that can be initialized with the
    dict of CloudFormation resource properties for your specific custom resource - and raises an
    exception if the properties are invalid.
    """

    physical_id: Optional[str]
    props: Optional[TResourceProps]
    old_props: Optional[TResourceProps]
    request_type: CustomResourceRequestType
    resource_type: str

    def __init__(self, event: dict, PropertiesClass: Type[TResourceProps]):
        """Create a CustomResourceEvent

        Parameters
        ----------
        event :
            Raw event dict from AWS Lambda
        PropertiesClass :
            Python class that should be created for the resource properties. Your class will be
            instantiated with one constructor argument - the raw properties dictionary. If this
            is an 'Update' event, another instance will be created from the OldResourceProperties.
            If the OldResourceProperties cannot be parsed, an exception will be logged but not
            raised.
        """
        self.physical_id = event.get("PhysicalResourceId")
        self.request_type = CustomResourceRequestType(event["RequestType"])
        self.resource_type = event["ResourceType"]
        resource_properties = event.get("ResourceProperties")
        if resource_properties:
            self.props = PropertiesClass(resource_properties)
        else:
            self.props = None
        # Only present for 'Update' requests:
        old_resource_properties = event.get("OldResourceProperties")
        if old_resource_properties:
            try:
                self.old_props = PropertiesClass(old_resource_properties)
            except Exception:
                logger.exception("Failed to parse OldResourceProperties of Update event")
                self.old_props = None
        else:
            self.old_props = None
