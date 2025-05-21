# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Constructs relating to AWS Service-Linked Roles

https://docs.aws.amazon.com/IAM/latest/UserGuide/using-service-linked-roles.html
"""

# External Dependencies:
from aws_cdk import aws_iam
from constructs import Construct


class SageMakerServiceRoles(Construct):
    """Construct to create SageMaker (Projects) default service roles

    These AWS Service Roles are typically created automatically when an administrator activates
    SageMaker Project Templates in an account, but may not be present in ephemeral accounts e.g.
    workshops - so this construct can create them for you if needed... But may fail deployment in
    an account where they already exist.
    """

    AmazonSageMakerServiceCatalogProductsApiGatewayRole: aws_iam.IRole
    AmazonSageMakerServiceCatalogProductsCloudformationRole: aws_iam.IRole
    AmazonSageMakerServiceCatalogProductsCodeBuildRole: aws_iam.IRole
    AmazonSageMakerServiceCatalogProductsCodePipelineRole: aws_iam.IRole
    AmazonSageMakerServiceCatalogProductsEventsRole: aws_iam.IRole
    AmazonSageMakerServiceCatalogProductsExecutionRole: aws_iam.IRole
    AmazonSageMakerServiceCatalogProductsFirehoseRole: aws_iam.IRole
    AmazonSageMakerServiceCatalogProductsGlueRole: aws_iam.IRole
    AmazonSageMakerServiceCatalogProductsLambdaRole: aws_iam.IRole
    AmazonSageMakerServiceCatalogProductsLaunchRole: aws_iam.IRole
    AmazonSageMakerServiceCatalogProductsUsePolicy: aws_iam.IManagedPolicy
    AmazonSageMakerServiceCatalogProductsUseRole: aws_iam.IRole

    def __init__(
        self,
        scope: Construct,
        id: str,
    ):
        super().__init__(scope, id)

        self.AmazonSageMakerServiceCatalogProductsApiGatewayRole = aws_iam.Role(
            assumed_by=aws_iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonSageMakerServiceCatalogProductsApiGatewayServiceRolePolicy"
                )
            ],
            path="/service-role/",
            role_name="AmazonSageMakerServiceCatalogProductsApiGatewayRole",
        )

        self.AmazonSageMakerServiceCatalogProductsCloudformationRole = aws_iam.Role(
            assumed_by=aws_iam.ServicePrincipal("cloudformation.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonSageMakerServiceCatalogProductsCloudformationServiceRolePolicy"
                )
            ],
            path="/service-role/",
            role_name="AmazonSageMakerServiceCatalogProductsCloudformationRole",
        )

        self.AmazonSageMakerServiceCatalogProductsCodeBuildRole = aws_iam.Role(
            assumed_by=aws_iam.ServicePrincipal("codebuild.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonSageMakerServiceCatalogProductsCodeBuildServiceRolePolicy"
                )
            ],
            path="/service-role/",
            role_name="AmazonSageMakerServiceCatalogProductsCodeBuildRole",
        )

        self.AmazonSageMakerServiceCatalogProductsCodePipelineRole = aws_iam.Role(
            assumed_by=aws_iam.ServicePrincipal("codepipeline.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonSageMakerServiceCatalogProductsCodePipelineServiceRolePolicy"
                )
            ],
            path="/service-role/",
            role_name="AmazonSageMakerServiceCatalogProductsCodePipelineRole",
        )

        self.AmazonSageMakerServiceCatalogProductsEventsRole = aws_iam.Role(
            assumed_by=aws_iam.ServicePrincipal("events.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonSageMakerServiceCatalogProductsEventsServiceRolePolicy"
                )
            ],
            path="/service-role/",
            role_name="AmazonSageMakerServiceCatalogProductsEventsRole",
        )

        self.AmazonSageMakerServiceCatalogProductsExecutionRole = aws_iam.Role(
            assumed_by=aws_iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")
            ],
            path="/service-role/",
            role_name="AmazonSageMakerServiceCatalogProductsExecutionRole",
        )

        self.AmazonSageMakerServiceCatalogProductsFirehoseRole = aws_iam.Role(
            assumed_by=aws_iam.ServicePrincipal("firehose.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonSageMakerServiceCatalogProductsFirehoseServiceRolePolicy"
                )
            ],
            path="/service-role/",
            role_name="AmazonSageMakerServiceCatalogProductsFirehoseRole",
        )

        self.AmazonSageMakerServiceCatalogProductsGlueRole = aws_iam.Role(
            assumed_by=aws_iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonSageMakerServiceCatalogProductsGlueServiceRolePolicy"
                )
            ],
            path="/service-role/",
            role_name="AmazonSageMakerServiceCatalogProductsGlueRole",
        )

        self.AmazonSageMakerServiceCatalogProductsLambdaRole = aws_iam.Role(
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonSageMakerServiceCatalogProductsLambdaServiceRolePolicy"
                )
            ],
            path="/service-role/",
            role_name="AmazonSageMakerServiceCatalogProductsLambdaRole",
        )

        self.AmazonSageMakerServiceCatalogProductsLaunchRole = aws_iam.Role(
            assumed_by=aws_iam.ServicePrincipal("servicecatalog.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerAdmin-ServiceCatalogProductsServiceRolePolicy"
                )
            ],
            path="/service-role/",
            role_name="AmazonSageMakerServiceCatalogProductsLaunchRole",
        )

        self.AmazonSageMakerServiceCatalogProductsUsePolicy = aws_iam.ManagedPolicy(
            scope,
            "AmazonSageMakerServiceCatalogProductsUsePolicy",
            document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        actions=[
                            "cloudformation:CreateChangeSet",
                            "cloudformation:CreateStack",
                            "cloudformation:DescribeChangeSet",
                            "cloudformation:DeleteChangeSet",
                            "cloudformation:DeleteStack",
                            "cloudformation:DescribeStacks",
                            "cloudformation:ExecuteChangeSet",
                            "cloudformation:SetStackPolicy",
                            "cloudformation:UpdateStack",
                        ],
                        resources=["arn:aws:cloudformation:*:*:stack/sagemaker-*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=["cloudwatch:PutMetricData"],
                        resources=["*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=["codebuild:BatchGetBuilds", "codebuild:StartBuild"],
                        resources=[
                            "arn:aws:codebuild:*:*:project/sagemaker-*",
                            "arn:aws:codebuild:*:*:build/sagemaker-*",
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "codecommit:CancelUploadArchive",
                            "codecommit:GetBranch",
                            "codecommit:GetCommit",
                            "codecommit:GetUploadArchiveStatus",
                            "codecommit:UploadArchive",
                        ],
                        resources=["arn:aws:codecommit:*:*:sagemaker-*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=["codepipeline:StartPipelineExecution"],
                        resources=["arn:aws:codepipeline:*:*:sagemaker-*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=["ec2:DescribeRouteTables"],
                        resources=["*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "ecr:BatchCheckLayerAvailability",
                            "ecr:BatchGetImage",
                            "ecr:Describe*",
                            "ecr:GetAuthorizationToken",
                            "ecr:GetDownloadUrlForLayer",
                        ],
                        resources=["*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "ecr:BatchDeleteImage",
                            "ecr:CompleteLayerUpload",
                            "ecr:CreateRepository",
                            "ecr:DeleteRepository",
                            "ecr:InitiateLayerUpload",
                            "ecr:PutImage",
                            "ecr:UploadLayerPart",
                        ],
                        resources=["arn:aws:ecr:*:*:repository/sagemaker-*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "events:DeleteRule",
                            "events:DescribeRule",
                            "events:PutRule",
                            "events:PutTargets",
                            "events:RemoveTargets",
                        ],
                        resources=["arn:aws:events:*:*:rule/sagemaker-*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=["firehose:PutRecord", "firehose:PutRecordBatch"],
                        resources=["arn:aws:firehose:*:*:deliverystream/sagemaker-*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "glue:BatchCreatePartition",
                            "glue:BatchDeletePartition",
                            "glue:BatchDeleteTable",
                            "glue:BatchDeleteTableVersion",
                            "glue:BatchGetPartition",
                            "glue:CreateDatabase",
                            "glue:CreatePartition",
                            "glue:CreateTable",
                            "glue:DeletePartition",
                            "glue:DeleteTable",
                            "glue:DeleteTableVersion",
                            "glue:GetDatabase",
                            "glue:GetPartition",
                            "glue:GetPartitions",
                            "glue:GetTable",
                            "glue:GetTables",
                            "glue:GetTableVersion",
                            "glue:GetTableVersions",
                            "glue:SearchTables",
                            "glue:UpdatePartition",
                            "glue:UpdateTable",
                            "glue:GetUserDefinedFunctions",
                        ],
                        resources=[
                            "arn:aws:glue:*:*:catalog",
                            "arn:aws:glue:*:*:database/default",
                            "arn:aws:glue:*:*:database/global_temp",
                            "arn:aws:glue:*:*:database/sagemaker-*",
                            "arn:aws:glue:*:*:table/sagemaker-*",
                            "arn:aws:glue:*:*:tableVersion/sagemaker-*",
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        actions=["iam:PassRole"],
                        resources=[
                            "arn:aws:iam::*:role/service-role/AmazonSageMakerServiceCatalogProductsUse*"
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        actions=["lambda:InvokeFunction"],
                        resources=["arn:aws:lambda:*:*:function:sagemaker-*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "logs:CreateLogDelivery",
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:DeleteLogDelivery",
                            "logs:Describe*",
                            "logs:GetLogDelivery",
                            "logs:GetLogEvents",
                            "logs:ListLogDeliveries",
                            "logs:PutLogEvents",
                            "logs:PutResourcePolicy",
                            "logs:UpdateLogDelivery",
                        ],
                        resources=["*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "s3:CreateBucket",
                            "s3:DeleteBucket",
                            "s3:GetBucketAcl",
                            "s3:GetBucketCors",
                            "s3:GetBucketLocation",
                            "s3:ListAllMyBuckets",
                            "s3:ListBucket",
                            "s3:ListBucketMultipartUploads",
                            "s3:PutBucketCors",
                            "s3:PutObjectAcl",
                        ],
                        resources=["arn:aws:s3:::aws-glue-*", "arn:aws:s3:::sagemaker-*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "s3:AbortMultipartUpload",
                            "s3:DeleteObject",
                            "s3:GetObject",
                            "s3:GetObjectVersion",
                            "s3:PutObject",
                        ],
                        resources=["arn:aws:s3:::aws-glue-*", "arn:aws:s3:::sagemaker-*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=["sagemaker:*"],
                        not_resources=[
                            "arn:aws:sagemaker:*:*:domain/*",
                            "arn:aws:sagemaker:*:*:user-profile/*",
                            "arn:aws:sagemaker:*:*:app/*",
                            "arn:aws:sagemaker:*:*:flow-definition/*",
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "states:DescribeExecution",
                            "states:DescribeStateMachine",
                            "states:DescribeStateMachineForExecution",
                            "states:GetExecutionHistory",
                            "states:ListExecutions",
                            "states:ListTagsForResource",
                            "states:StartExecution",
                            "states:StopExecution",
                            "states:TagResource",
                            "states:UntagResource",
                            "states:UpdateStateMachine",
                        ],
                        resources=[
                            "arn:aws:states:*:*:stateMachine:sagemaker-*",
                            "arn:aws:states:*:*:execution:sagemaker-*:*",
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        actions=["states:ListStateMachines"],
                        resources=["*"],
                    ),
                    aws_iam.PolicyStatement(
                        actions=["codestar-connections:UseConnection"],
                        resources=["arn:aws:codestar-connections:*:*:connection/*"],
                        conditions={
                            "StringEqualsIgnoreCase": {"aws:ResourceTag/sagemaker": "true"},
                        },
                    ),
                ],
            ),
            path="/service-role/",
            managed_policy_name="AmazonSageMakerServiceCatalogProductsUsePolicy",
        )

        self.AmazonSageMakerServiceCatalogProductsUseRole = aws_iam.Role(
            scope,
            "AmazonSageMakerServiceCatalogProductsUseRole",
            assumed_by=aws_iam.CompositePrincipal(
                aws_iam.ServicePrincipal("apigateway.amazonaws.com"),
                aws_iam.ServicePrincipal("cloudformation.amazonaws.com"),
                aws_iam.ServicePrincipal("codebuild.amazonaws.com"),
                aws_iam.ServicePrincipal("codepipeline.amazonaws.com"),
                aws_iam.ServicePrincipal("events.amazonaws.com"),
                aws_iam.ServicePrincipal("firehose.amazonaws.com"),
                aws_iam.ServicePrincipal("glue.amazonaws.com"),
                aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                aws_iam.ServicePrincipal("sagemaker.amazonaws.com"),
                aws_iam.ServicePrincipal("states.amazonaws.com"),
            ),
            managed_policy_arns=[
                self.AmazonSageMakerServiceCatalogProductsUsePolicy.managed_policy_arn
            ],
            path="/service-role/",
            role_name="AmazonSageMakerServiceCatalogProductsUseRole",
        )
