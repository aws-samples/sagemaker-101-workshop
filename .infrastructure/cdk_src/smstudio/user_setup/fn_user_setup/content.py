# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Custom CloudFormation Resource for loading content to a SageMaker Studio user

See `.base.StudioUserSetupResourceProperties` for CloudFormation input Properties, and main.py
docstring for CloudFormation return values.

This sub-resource either clones a (public) git repository or downloads content from Amazon S3, into
a SageMaker Studio user's home folder on create. Updating and Deleting the resource currently do
nothing as it's designed for one-off account setup.
"""
# Python Built-Ins:
import logging
import os
import traceback
from typing import Optional, Union
import zipfile

# External Dependencies:
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from git import Repo

# Local Dependencies:
from base import StudioUserSetupResourceProperties
from cfn import CustomResourceEvent

anons3config = Config(signature_version=UNSIGNED)
smclient = boto3.client("sagemaker")


def handle_create(event: CustomResourceEvent[StudioUserSetupResourceProperties], context):
    """Handle a resource creation Lambda event from CloudFormation"""
    logging.info("**Received create request")
    logging.info("**Setting up user content")
    try:
        # Check home folder exists and is assigned to correct EFS owner:
        home_folder = ensure_home_dir(event.props.home_efs_file_system_uid)

        # Now ready to clone in Git content (or whatever else...)
        if event.props.git_repository:
            output_content_path = clone_git_repository(
                home_folder,
                event.props.git_repository,
                event.props.target_path,
                event.props.git_checkout,
            )
        elif event.props.content_s3_uri:
            output_content_path = copy_s3_content(
                home_folder,
                event.props.content_s3_uri,
                event.props.target_path,
                event.props.extract_content,
                event.props.authenticate_s3,
            )
        else:
            logging.warning("Neither GitRepository nor ContentS3Uri set - nothing to create")

        # Remember to set ownership/permissions for all the stuff we just created, to give the
        # user write access:
        chown_recursive(output_content_path, uid=event.props.home_efs_file_system_uid)
        print("All done")
    except Exception as e:
        # Don't bring the entire CF stack down just because we couldn't copy a repo:
        print("IGNORING CONTENT SETUP ERROR")
        traceback.print_exc()

    logging.info("**SageMaker Studio user '%s' set up successfully", event.props.user_profile_name)
    return {
        "PhysicalResourceId": event.props.user_profile_name,
        "Data": {"UserProfileName": event.props.user_profile_name},
    }


def handle_delete(event: CustomResourceEvent[StudioUserSetupResourceProperties], context):
    """Handle a resource deletion Lambda event from CloudFormation (a no-op for this resource)"""
    logging.info("**Received delete event")
    # Since this is a no-op, there's no point strictly parsing the props (risking failures):
    logging.info(
        "**Deleting user setup is a no-op: user '%s' on domain '%s",
        event.physical_id,
        event.props.domain_id,
    )
    return {"PhysicalResourceId": event.physical_id, "Data": {}}


def handle_update(event: CustomResourceEvent[StudioUserSetupResourceProperties], context):
    """Handle a resource update Lambda event from CloudFormation (a no-op for this resource)"""
    logging.info("**Received update event")
    # Since this is a no-op, there's no point strictly parsing the props (risking failures):
    logging.info(
        "**Updating user setup is a no-op: user '%s' on domain '%s",
        event.physical_id,
        event.props.domain_id,
    )
    return {"PhysicalResourceId": event.physical_id, "Data": {}}


def ensure_home_dir(efs_uid: Union[int, str]) -> str:
    """Check the EFS home folder for the given user ID exists with correct ownership

    The root of the EFS contains folders named for each user UID, but these may not be created
    before the user has first logged in (could os.listdir("/mnt/efs") to check).
    """
    print("Creating/checking home folder...")
    home_folder = f"/mnt/efs/{efs_uid}"
    os.makedirs(home_folder, exist_ok=True)
    # Set correct ownership permissions for this folder straight away, in case a later process errors out
    os.chown(home_folder, int(efs_uid), -1)
    return home_folder


def clone_git_repository(
    base_folder: str, git_repo: str, as_folder: Optional[str] = None, checkout: Optional[str] = None
) -> str:
    """Clone a git repository into `base_folder/as_folder` and optionally check out `checkout`

    DOES NOT CONFIGURE FILE OWNERSHIP PERMISSIONS! Run chown_recursive if required.
    """
    print(f"Cloning code... {git_repo}")
    if not as_folder:
        # Infer target folder name from repo URL if not specified:
        as_folder = git_repo.rpartition("/")[2]
        if as_folder.lower().endswith(".git"):
            as_folder = as_folder[: -len(".git")]
    target_folder = os.path.join(base_folder, as_folder)
    repo = Repo.clone_from(git_repo, target_folder)
    if checkout:
        print(f"Checking out '{checkout}'...")
        repo.git.checkout(checkout)
    else:
        print("No specific checkout branch/commit specified - keeping default")
    return target_folder


def copy_s3_content(
    base_folder: str,
    content_s3uri: str,
    target_path: Optional[str] = None,
    extract: Optional[bool] = False,
    authenticate_s3: Optional[bool] = False,
) -> str:
    """Download content from Amazon S3 to `base_folder/target_path`

    DOES NOT CONFIGURE FILE OWNERSHIP PERMISSIONS! Run chown_recursive if required.
    """
    if not content_s3uri.lower().startswith("s3://"):
        raise ValueError("Content URI must start with 's3://'")
    bucket_name, _, key_prefix = content_s3uri[len("s3://") :].partition("/")

    # Set up S3 client as anonymous or authenticated, depending on resource config:
    s3 = boto3.resource("s3", config=(None if authenticate_s3 else anons3config))
    s3client = boto3.client("s3", config=(None if authenticate_s3 else anons3config))

    # Check if the provided content URI is a valid object (vs folder/prefix):
    bucket = s3.Bucket(bucket_name)
    print(f"Checking s3://{bucket_name}/{key_prefix}")
    try:
        content_type = bucket.Object(key_prefix).content_type
        if content_type and content_type.lower() == "application/x-directory":
            is_object = False
        else:
            is_object = True
    except s3client.exceptions.ClientError as err:
        if err.response["Error"]["Code"] == "404":
            is_object = False
        else:
            raise err

    if is_object:
        if target_path is None:
            target_path = os.path.basename(key_prefix)
        full_target_path = os.path.join(base_folder, target_path)
        print(f"Downloading {content_s3uri}")
        bucket.download_file(key_prefix, full_target_path)

        if not extract:
            return full_target_path
        # Otherwise, extract compressed file:
        # A file without a dot/extension will produce ("", "", "wholename"):
        basename, _, file_ext = key_prefix.rpartition(".")
        file_ext = file_ext.lower()
        extract_path = full_target_path + "-tmp"
        if file_ext == "zip" or not basename:
            # (Assume zip for files with no extension if extract specified)
            print(f"Extracting to {extract_path}")
            with zipfile.ZipFile(full_target_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)
        else:
            raise NotImplementedError(f"File extension '{file_ext}' not supported for extraction")
        print(f"Replacing compressed {full_target_path} with {extract_path}")
        os.remove(full_target_path)
        os.rename(extract_path, full_target_path)
        return full_target_path

    # Otherwise looks like a folder
    raise NotImplementedError(
        f"Object not found and prefix/folder download not yet supported: ${content_s3uri}"
    )


def chown_recursive(path: str, uid: Union[str, int] = -1, gid: Union[str, int] = -1):
    """Workaround for os.chown() not having a recursive option for folders"""
    uid = int(uid)
    gid = int(gid)
    if os.path.isfile(path):
        os.chown(path, uid, gid)
    else:
        for dirpath, dirnames, filenames in os.walk(path):
            os.chown(dirpath, uid, gid)
            for filename in filenames:
                os.chown(os.path.join(dirpath, filename), uid, gid)
