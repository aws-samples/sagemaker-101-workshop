"""Custom CloudFormation Resource for loading content to a SageMaker Studio user

This resource either clones a (public) git repository or downloads content from Amazon S3, into
a SageMaker Studio user's home folder on create. Updating and Deleting the resource currently do
nothing as it's designed for one-off account setup. CloudFormation resource properties are as
follows:

Common Parameters:

- DomainId (str, required): ID of the (already existing) target SageMaker Studio domain.
- HomeEfsFileSystemUid (Union[str, int], required): EFS user ID (numeric) of the target SageMaker
    Studio user. You can get this from the SageMaker DescribeUserProfile API.
- UserProfileName (str, required): Name of the target SageMaker Studio user profile.
- TargetPath (str, optional): Path (relative to Studio home folder) where the content should be
    loaded. If not set, this will default to the repository name or source file name. Trying to
    escape the Studio home folder with '../' is not supported and may have unintended consequences
    (including possibly writing to other users' folders).

Parameters for Git Content:

- GitRepository (str, required): A `git clone`able URL.
- GitCheckout (str, optional): A `git checkout`able name (e.g. branch name) in your target.
    repository. If not provided, the cloned repository will remain on the default branch.

Parameters for S3 Content:

- ContentS3Uri (str, required): s3://doc-example-bucket/path URI for fetching the content.
    Currently only an individual object is supported (not folder prefix).
- AuthenticateS3 (bool, optional): Set true to authenticate S3 requests with this Lambda's IAM
    identity. By default (false), requests will be anonymous/unsigned - which is appropriate for
    public buckets such as sample data and the AWS Open Data Registry.
- ExtractContent (bool, optional): Set true to unzip the content after download. By default
    (false), the object will simply be downloaded as-is. Tarballs and other archive formats apart
    from zip files are not currently supported.
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
import cfnresponse
from git import Repo


anons3config = Config(signature_version=UNSIGNED)
smclient = boto3.client("sagemaker")


class ResourceProperties:
    """Parser and initial validator for custom resource properties"""
    domain_id: str
    efs_uid: str
    user_profile_name: str
    git_repo: Optional[str]
    git_checkout: Optional[str]
    target_path: Optional[str]
    content_s3uri: Optional[str]
    extract: Optional[bool]
    authenticate_s3: Optional[bool]

    def __init__(self, cfnprops: dict):
        try:
            self.domain_id = cfnprops["DomainId"]
            self.efs_uid = cfnprops["HomeEfsFileSystemUid"]
            self.user_profile_name = cfnprops["UserProfileName"]
        except KeyError as ke:
            raise ValueError(f"Missing required resource property {ke}") from ke
        
        self.target_path = cfnprops.get("TargetPath")
        
        self.git_repo = cfnprops.get("GitRepository")
        self.git_checkout = cfnprops.get("GitCheckout")
        if (self.git_checkout and not self.git_repo):
            raise ValueError("Specified GitCheckout (branch, etc) but not GitRepository")

        self.content_s3uri = cfnprops.get("ContentS3Uri")
        self.authenticate_s3 = cfnprops.get("AuthenticateS3")
        if (self.authenticate_s3 and not self.content_s3uri):
            raise ValueError("AuthenticateS3 option only works with ContentS3Uri")
        self.extract = cfnprops.get("ExtractContent")
        if (self.extract and not self.content_s3uri):
            raise ValueError("ExtractContent option only works with ContentS3Uri")


def handle_create(event, context):
    """Handle a resource creation Lambda event from CloudFormation"""
    logging.info("**Received create request")
    resource_config = ResourceProperties(event["ResourceProperties"])
    logging.info("**Setting up user content")
    try:
        # Check home folder exists and is assigned to correct EFS owner:
        home_folder = ensure_home_dir(resource_config.efs_uid)

        # Now ready to clone in Git content (or whatever else...)
        if resource_config.git_repo:
            output_content_path = clone_git_repository(
                home_folder,
                resource_config.git_repo,
                resource_config.target_path,
                resource_config.git_checkout
            )
        elif resource_config.content_s3uri:
            output_content_path = copy_s3_content(
                home_folder,
                resource_config.content_s3uri,
                resource_config.target_path,
                resource_config.extract,
                resource_config.authenticate_s3,
            )
        else:
            logging.warning("Neither GitRepository nor ContentS3Uri set - nothing to create")

        # Remember to set ownership/permissions for all the stuff we just created, to give the
        # user write access:
        chown_recursive(output_content_path, uid=resource_config.efs_uid)
        print("All done")
    except Exception as e:
        # Don't bring the entire CF stack down just because we couldn't copy a repo:
        print("IGNORING CONTENT SETUP ERROR")
        traceback.print_exc()

    logging.info(
        "**SageMaker Studio user '%s' set up successfully",
        resource_config.user_profile_name
    )
    result = { "UserProfileName": resource_config.user_profile_name }
    cfnresponse.send(
        event,
        context,
        cfnresponse.SUCCESS,
        result,
        physicalResourceId=result["UserProfileName"],
    )


def handle_delete(event, context):
    """Handle a resource deletion Lambda event from CloudFormation (a no-op for this resource)"""
    logging.info("**Received delete event")
    # Since this is a no-op, there's no point strictly parsing the props (risking failures):
    user_profile_name = event["PhysicalResourceId"]
    domain_id = event["ResourceProperties"].get("DomainId")
    user_profile_name = event["ResourceProperties"].get("UserProfileName")
    logging.info(
        "**Deleting user setup is a no-op: user '%s' on domain '%s",
        user_profile_name,
        domain_id,
    )
    cfnresponse.send(
        event,
        context,
        cfnresponse.SUCCESS,
        {},
        physicalResourceId=event["PhysicalResourceId"],
    )


def handle_update(event, context):
    """Handle a resource update Lambda event from CloudFormation (a no-op for this resource)"""
    logging.info("**Received update event")
    # Since this is a no-op, there's no point strictly parsing the props (risking failures):
    domain_id = event["ResourceProperties"].get("DomainId")
    user_profile_name = event["ResourceProperties"].get("UserProfileName")
    logging.info(
        "**Updating user setup is a no-op: user '%s' on domain '%s",
        user_profile_name,
        domain_id,
    )
    cfnresponse.send(
        event,
        context,
        cfnresponse.SUCCESS,
        {},
        physicalResourceId=event["PhysicalResourceId"],
    )


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
    base_folder: str,
    git_repo: str,
    as_folder: Optional[str] = None,
    checkout: Optional[str] = None
) -> str:
    """Clone a git repository into `base_folder/as_folder` and optionally check out `checkout`

    DOES NOT CONFIGURE FILE OWNERSHIP PERMISSIONS! Run chown_recursive if required.
    """
    print(f"Cloning code... {git_repo}")
    if not as_folder:
        # Infer target folder name from repo URL if not specified:
        as_folder = git_repo.rpartition("/")[2]
        if as_folder.lower().endswith(".git"):
            as_folder = as_folder[:-len(".git")]
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
    bucket_name, _, key_prefix = content_s3uri[len("s3://"):].partition("/")

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


def chown_recursive(path: str, uid: Union[str, int]=-1, gid: Union[str, int]=-1):
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
