# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Shared (CloudFormation resource property) definitions"""
# Python Built-Ins:
from __future__ import annotations
import json
from typing import Optional, Union


class StudioUserSetupResourceProperties:
    """Parser for CloudFormation resource properties for this Custom Resource

    Resource Properties
    -------------------
    DomainId: str
        ID of the (already existing) target SageMaker Studio domain.
    HomeEfsFileSystemUid : Union[str, int]
        EFS user ID (numeric) of the target SageMaker Studio user. You can get this from the
        SageMaker DescribeUserProfile API.
    UserProfileName : str
        Name of the target SageMaker Studio user profile.
    TargetPath : Optional[str]
        Path (relative to Studio home folder) where the content should be loaded. If not set, this
        will default to the repository name or source file name. Trying to escape the Studio home
        folder with '../' is not supported and may have unintended consequences (including possibly
        writing to other users' folders).
    GitRepository : Optional[str]
        (Required if using git) A `git clone`able URL.
    GitCheckout : Optional[str]
        (Only used if `GitRepository` is set) A `git checkout`able name (e.g. branch name) in your
        target repository. If not provided, the cloned repository will remain on the default
        branch.
    ContentS3Uri : Optional[str]
        s3://doc-example-bucket/path URI for fetching the content. Currently only an individual
        object is supported (not folder prefix).
    AuthenticateS3 : Optional[bool]
        (Only if using `ContentS3Uri`) Set true to authenticate S3 requests with this Lambda's IAM
        identity. By default (false), requests will be anonymous/unsigned - which is appropriate
        for public buckets such as sample data and the AWS Open Data Registry.
    ExtractContent (bool, optional):
        (Only if using `ContentS3Uri`) Set true to unzip the content after download. By default
        (false), the object will simply be downloaded as-is. Tarballs and other archive formats
        apart from zip files are not currently supported.
    """

    # Common parameters:
    domain_id: str
    home_efs_file_system_uid: Union[str, int]
    user_profile_name: str
    target_path: Optional[str]
    # Parameters for Git content:
    git_repository: Optional[str]
    git_checkout: Optional[str]
    # Parameters for S3 content:
    content_s3_uri: Optional[str]
    authenticate_s3: bool
    extract_content: bool
    # Parameters for SageMaker projects:
    enable_projects: bool

    def __init__(self, resource_properties: dict):
        self.domain_id = resource_properties["DomainId"]
        self.home_efs_file_system_uid = resource_properties["HomeEfsFileSystemUid"]
        self.user_profile_name = resource_properties["UserProfileName"]
        self.target_path = resource_properties.get("TargetPath")

        # Git content:
        self.git_checkout = resource_properties.get("GitCheckout")
        self.git_repository = resource_properties.get("GitRepository")

        # S3 content:
        self.authenticate_s3 = resource_properties.get("AuthenticateS3", False)
        self.content_s3_uri = resource_properties.get("ContentS3Uri")
        self.extract_content = resource_properties.get("ExtractContent", False)

        # SageMaker projects:
        self.enable_projects = resource_properties.get("EnableProjects", False)

        # Validations:
        if self.git_repository and self.content_s3_uri:
            raise ValueError(
                "Cannot set both GitRepository and ContentS3Uri: Create a separate custom "
                "resource instance for your git and S3 content items"
            )
        if not (self.git_repository or self.content_s3_uri):
            raise ValueError(
                "Must set either GitRepository (git content) or ContentS3Uri (S3 content)"
            )

    def __str__(self):
        dict_val = {
            "DomainId": self.domain_id,
            "HomeEfsFileSystemUid": self.home_efs_file_system_uid,
            "UserProfileName": self.user_profile_name,
        }
        if self.target_path:
            dict_val["TargetPath"] = self.target_path
        if self.git_checkout:
            dict_val["GitCheckout"] = self.git_checkout
        if self.git_repository:
            dict_val["GitRepository"] = self.git_repository
        if self.content_s3_uri:
            dict_val["ContentS3Uri"] = self.content_s3_uri
        if self.authenticate_s3:
            dict_val["AuthenticateS3"] = self.authenticate_s3
        if self.extract_content:
            dict_val["ExtractContent"] = self.extract_content
        return json.dumps(dict_val)

    @classmethod
    def from_str(cls, str_val) -> StudioUserSetupResourceProperties:
        return cls(json.loads(str_val))
