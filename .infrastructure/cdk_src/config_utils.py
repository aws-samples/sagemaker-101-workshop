#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Utilities for configuring the stack (e.g. environment variable parsing)
"""
# Python Built-Ins:
import os
from typing import Optional


def bool_env_var(env_var_name: str, default: Optional[bool] = None) -> bool:
    """Parse a boolean environment variable

    Raises
    ------
    ValueError :
        If environment variable `env_var_name` is not found and no `default` is specified, or if the
        raw value string could not be interpreted as a boolean.

    Returns
    -------
    parsed :
        True if the env var has values such as `1`, `true`, `y`, `yes` (case-insensitive). False if
        opposite values `0`, `false`, `n`, `no` or empty string.
    """
    raw = os.environ.get(env_var_name)
    if raw is None:
        if default is None:
            raise ValueError(f"Mandatory boolean env var '{env_var_name}' not found")
        return default
    raw = raw.lower()
    if raw in ("1", "true", "y", "yes"):
        return True
    elif raw in ("", "0", "false", "n", "no"):
        return False
    else:
        raise ValueError(
            "Couldn't interpret env var '%s' as boolean. Got: '%s'" % (env_var_name, raw)
        )
