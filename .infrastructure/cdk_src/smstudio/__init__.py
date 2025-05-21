# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""CDK construct for a SageMaker Studio domain for demos and workshops
"""
# Python Built-Ins:
import os
from typing import Literal, Optional

# External Dependencies:
from aws_cdk import aws_ec2, aws_efs, aws_iam, CfnParameter, Stack
import aws_cdk.aws_sagemaker as sagemaker_cdk
from constructs import Construct

# Local Dependencies:
from .cr_lambda_common import SMCustomResourceHelperLayer
from .domain import SageMakerStudioDomain
from .iam import WorkshopSageMakerExecutionRole
from .lcc import (
    SageMakerNotebookLifecycleConfig,
    SageMakerStudioLifecycleConfig,
    SMStudioLCCCustomResourceProvider,
)
from .region_config import CfnSageMakerAppsByRegionMapping
from .service_roles import SageMakerServiceRoles
from .user import SageMakerStudioUser
from .user_setup import SageMakerStudioUserSetup


class WorkshopSageMakerEnvironment(Construct):
    """CDK construct for a basic SageMaker Studio domain for demos and workshops"""

    _execution_role: aws_iam.IRole
    notebook_instance: Optional[sagemaker_cdk.CfnNotebookInstance]
    stack_param_notebook_name: Optional[CfnParameter]

    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: aws_ec2.IVpc,
        code_checkout: Optional[str] = None,
        code_repo: Optional[str] = None,
        create_nbi: bool = True,
        create_service_roles: bool = False,
        domain_name: Optional[str] = None,
        enable_sm_projects: bool = True,
        execution_role: Optional[aws_iam.IRole] = None,
        instance_type: str = "ml.t3.medium",
        studio_classic: Literal["enable", "force", False] = False,
    ):
        """Create a WorkshopSageMakerEnvironment

        Parameters
        ----------
        scope :
            CDK construct scope
        id :
            CDK construct ID
        vpc :
            Due to the way CDK handles VPCs, this is a required parameter for now... Most of the
            underlying resources should support discovering default VPC automatically though.
        code_checkout :
            (Only when `code_repo` is set) the `git checkout`able specifier for what version of
            `code_repo` to copy into user's SageMaker environment. If unset, users will receive
            the default branch (usuall `main`). Could also be set to e.g. a commit hash.
        code_repo :
            Optional `git clone`able repository of code to copy in to SageMaker user's environment
        create_nbi :
            If set `False`, neither the classic `notebook_instance` nor its associated Lifecycle
            Configuration Script will be created: Users will need to use SM Studio.
        create_service_roles :
            Set `True` to create required AWS Service Roles for Amazon SageMaker Projects - which
            may fail to deploy if your AWS Account already contains them.
        domain_name :
            Optional name for the SageMaker Studio Domain (otherwise a default name will be used)
        enable_sm_projects :
            Set `True` to enable SageMaker Projects (which requires `create_service_roles` to be
            set or for the related AWS Service Roles to already exsit in the target account) for
            created SageMaker Domain/Users.
        execution_role :
            Optional custom SageMaker Execution Role to assign to users. By default, a
            `.iam.WorkshopSageMakerExecutionRole` will be created automatically.
        studio_classic :
            If `False`, SageMaker Studio Classic LCCs and apps will not be created. If 'enable',
            the environment will be set up for both classic and new (2023-12 re:Invent) Studio. If
            'force', force the classic (JupyterLab-based) experience instead as described in the
            below link, and skip creating the new-Studio resources and LCCs.
            https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-migrate.html#studio-updated-migrate-revert
        instance_type :
            Instance type to use for SageMaker notebooks (same across Studio and NBIs)
        **kwargs :
            Other arguments passed through to base `Construct` class.
        """
        super().__init__(scope, id)
        stack = Stack.of(self)

        app_region_map = CfnSageMakerAppsByRegionMapping(self, "SageMakerAppArnMapping")

        service_roles = (
            SageMakerServiceRoles(self, "ServiceRoles") if create_service_roles else None
        )

        smcr_helper_layer = SMCustomResourceHelperLayer(self, "SMCRLayer")

        if not execution_role:
            execution_role = WorkshopSageMakerExecutionRole(
                self, "NotebookRole", enable_iamfullaccess=True
            )
        self._execution_role = execution_role

        domain_user_settings = {"ExecutionRole": self._execution_role.role_arn}
        if studio_classic == "force":
            domain_user_settings["StudioWebPortal"] = "DISABLED"

        # Although SageMakerStudioDomain supports auto-detecting vpc_id and subnet_ids and
        # providing them in its outputs, some other constructs here require an `aws_ec2.Vpc`.
        # Creating a CDK Vpc object from deploy-time parameters (either `from_lookup(vpc_id=...)`
        # or `from_vpc_attributes()` does not fully work: So we can't rely on
        # SageMakerStudioDomain's automatic assignment.
        studio_domain = SageMakerStudioDomain(
            self,
            "StudioDomain",
            # TODO: Proper automatic default e.g. with Lazy.string?
            name=domain_name or "WorkshopDomain",
            default_user_settings=domain_user_settings,
            enable_projects=enable_sm_projects,
            smcr_helper_layer=smcr_helper_layer,
            subnet_ids=[sub.subnet_id for sub in vpc.private_subnets],
            vpc_id=vpc.vpc_id,
        )
        studio_efs_inbound_sg = aws_ec2.SecurityGroup.from_security_group_id(
            self, "StudioEFSInboundSG", studio_domain.inbound_efs_security_group_id
        )
        studio_efs_outbound_sg = aws_ec2.SecurityGroup.from_security_group_id(
            self, "StudioEFSOutboundSG", studio_domain.outbound_efs_security_group_id
        )
        studio_efs = aws_efs.FileSystem.from_file_system_attributes(
            self,
            "StudioEFS",
            security_group=studio_efs_inbound_sg,
            file_system_id=studio_domain.home_efs_filesystem_id,
        )

        # Likewise we'll just use the Vpc's subnets instead of the domain's
        # `proposed_admin_subnet_cidr`:
        admin_subnets = vpc.private_subnets
        # admin_subnets = [aws_ec2.Subnet(
        #     self,
        #     "StudioAdminSubnet",
        #     availability_zone=vpc.availability_zones[0],
        #     cidr_block=studio_domain.proposed_admin_subnet_cidr,
        #     vpc_id=studio_domain.vpc_id,
        #     map_public_ip_on_launch=True,
        # )]

        studio_lcc_provider = SMStudioLCCCustomResourceProvider(
            self, "StudioLCCProvider", smcr_helper_layer=smcr_helper_layer
        )

        if studio_classic:
            with open(
                os.path.join(os.path.dirname(__file__), "lcc", "studio-classic-onstart.sh")
            ) as fclassic:
                studio_classic_lcc = SageMakerStudioLifecycleConfig(
                    self,
                    "StudioClassicLCC",
                    app_type="JupyterServer",
                    content=fclassic,
                    domain_id=studio_domain.domain_id,
                    name="workshop-dev-features",
                    provider=studio_lcc_provider,
                )
        else:
            studio_classic_lcc = None

        if studio_classic == "force":
            studio_jlab_lcc = None
        else:
            with open(
                os.path.join(os.path.dirname(__file__), "lcc", "studio-jupyterlab-onstart.sh")
            ) as fstudio:
                # TODO: This doesn't provide commit hash flexibility like the classic one does
                content = fstudio.read().replace(
                    "{{CODE_REPO}}",
                    f"-b {code_checkout} {code_repo}" if code_checkout else code_repo,
                )
                studio_jlab_lcc = SageMakerStudioLifecycleConfig(
                    self,
                    "StudioLCC",
                    app_type="JupyterLab",
                    content=content,
                    domain_id=studio_domain.domain_id,
                    name="workshop-code",
                    provider=studio_lcc_provider,
                )

        studio_user = SageMakerStudioUser(
            self,
            "StudioUser",
            app_arn_map=app_region_map,
            domain_id=studio_domain.domain_id,
            role_arn=self._execution_role.role_arn,
            lcc_classic_arn=None if studio_classic_lcc is None else studio_classic_lcc.arn,
            lcc_jupyterlab_arn=None if studio_jlab_lcc is None else studio_jlab_lcc.arn,
            name="workshop-user",
            smcr_helper_layer=smcr_helper_layer,
        )

        if studio_classic:
            user_content = SageMakerStudioUserSetup(
                self,
                "StudioUserContent",
                domain_id=studio_domain.domain_id,
                efs_file_system=studio_efs,
                efs_security_group=studio_efs_outbound_sg,
                enable_projects=enable_sm_projects,
                git_checkout=code_checkout,
                git_repository=code_repo,
                home_efs_file_system_uid=studio_user.home_efs_file_system_uid,
                smcr_helper_layer=smcr_helper_layer,
                user_profile_name=studio_user.name,
                vpc=vpc,
                vpc_subnets=aws_ec2.SubnetSelection(subnets=admin_subnets),
            )

            # Pre-warm the JupyterServer app to make initially opening Studio faster:
            classic_jupyter_app = sagemaker_cdk.CfnApp(
                self,
                "SMJupyterApp",
                app_name="default",
                app_type="JupyterServer",
                domain_id=studio_domain.domain_id,
                user_profile_name=studio_user.name,
            )
            classic_jupyter_app.node.add_dependency(studio_user)

            # Pre-warm the Data Science 3.0 kernel for faster start-up:
            classic_dsci3_app = sagemaker_cdk.CfnApp(
                self,
                "SMDataScience3App",
                app_name=f"instance-prewarm-datascience3-{instance_type.replace('.', '-')}",
                app_type="KernelGateway",
                domain_id=studio_domain.domain_id,
                resource_spec=sagemaker_cdk.CfnApp.ResourceSpecProperty(
                    instance_type=instance_type,
                    sage_maker_image_arn=app_region_map.find_in_map(stack.region, "datascience3"),
                ),
                user_profile_name=studio_user.name,
            )
            classic_dsci3_app.node.add_dependency(studio_user)

            # Pre-warm the Data Science 2.0 kernel for faster start-up:
            classic_dsci2_app = sagemaker_cdk.CfnApp(
                self,
                "SMDataScience2App",
                app_name=f"instance-prewarm-datascience2-{instance_type.replace('.', '-')}",
                app_type="KernelGateway",
                domain_id=studio_domain.domain_id,
                resource_spec=sagemaker_cdk.CfnApp.ResourceSpecProperty(
                    instance_type=instance_type,
                    sage_maker_image_arn=app_region_map.find_in_map(stack.region, "datascience2"),
                ),
                user_profile_name=studio_user.name,
            )
            classic_dsci2_app.node.add_dependency(studio_user)

        if studio_classic != "force":
            # TODO: Remove workarounds when CfnSpace construct is updated in CDK
            # https://github.com/aws/aws-cdk/issues/28985
            personal_space = sagemaker_cdk.CfnSpace(
                self,
                "PersonalSpace",
                domain_id=studio_domain.domain_id,
                space_name=studio_user.name + "-space",
            )
            personal_space.add_override("Properties.SpaceSettings.AppType", "JupyterLab")
            # TODO: This does not actually pre-clone the repo... Need to do something else.
            personal_space.add_override(
                # Although the documentation page lists a `.0.` notation:
                # https://docs.aws.amazon.com/cdk/v2/guide/cfn_layer.html#cfn_layer_raw
                # ...It doesn't work for adding new arrays: Renders to {"0": "..."}
                "Properties.SpaceSettings.JupyterLabAppSettings.CodeRepositories",
                [{"RepositoryUrl": code_repo}],
            )
            personal_space.add_override(
                "Properties.SpaceSettings.JupyterLabAppSettings.DefaultResourceSpec.InstanceType",
                instance_type,
            )
            personal_space.add_override(
                "Properties.SpaceSettings.SpaceStorageSettings.EbsStorageSettings.EbsVolumeSizeInGb",
                10,
            )
            personal_space.add_override(
                "Properties.OwnershipSettings.OwnerUserProfileName", studio_user.name
            )
            personal_space.add_override("Properties.SpaceSharingSettings.SharingType", "Private")
            # We can't "start" this space (by creating an "app" for it) because AWS::SageMaker::App
            # doesn't support new-style JupyterLab spaces at the time of writing (unlike the
            # CreateApp API)
            # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-sagemaker-app.html
            # https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_CreateApp.html

        if create_nbi:
            # Classic Notebook Instance as a fallback:
            self.stack_param_notebook_name = CfnParameter(
                self,
                "NotebookName",
                default="LLMEvalNotebook",
                description="Enter the name of the SageMaker notebook instance. Default is LLMEvalNotebook.",
                type="String",
            )

            with open(os.path.join(os.path.dirname(__file__), "lcc", "nbi-onstart.sh")) as fnbi:
                nbi_lcc = SageMakerNotebookLifecycleConfig(self, "NBILCC", on_start_script=fnbi)
            self.notebook_instance = sagemaker_cdk.CfnNotebookInstance(
                self,
                "NotebookInstance",
                instance_type=instance_type,
                lifecycle_config_name=nbi_lcc.name,
                notebook_instance_name=self.stack_param_notebook_name.value_as_string,
                platform_identifier="notebook-al2-v2",
                role_arn=self._execution_role.role_arn,
                volume_size_in_gb=20,
            )
        else:
            self.stack_param_notebook_name = None
            self.notebook_instance = None

    @property
    def execution_role(self) -> WorkshopSageMakerExecutionRole:
        return self._execution_role
