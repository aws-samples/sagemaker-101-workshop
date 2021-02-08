# Infrastructure for SageMaker Workshop with SageMaker Studio

While the standard CloudFormation template for this example uses [SageMaker Notebook Instances](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html), some users may wish to use the newer and more advanced, integrated [SageMaker Studio](https://docs.aws.amazon.com/sagemaker/latest/dg/studio.html) UI instead.

This presents a little more of a challenge to set up, because:

1. SageMaker Studio has a broader scope including user management and SSO integration, so there's a little more [first time setup](https://docs.aws.amazon.com/sagemaker/latest/dg/gs-studio-onboard.html) required.
2. At the time of writing, some of these constructs don't have native CloudFormation integrations - instead we use solutions [as explained in this blog post](https://aws.amazon.com/blogs/machine-learning/creating-amazon-sagemaker-studio-domains-and-user-profiles-using-aws-cloudformation/) to create the same resources via Lambda functions.

Here we provide a template which will stand up the resources for a workshop in SageMaker Studio.

## Prerequisites and Caveats

This stack **assumes that (in your target AWS Region)**:

- You have not yet onboarded to SageMaker Studio
- You have a default VPC you're willing to use with standard configuration, or else would like to use a custom VPC but are comfortable checking the compatibility of the stack with your VPC configuration.

> ⚠️ This stack is oriented towards convenience of **getting started** and first exploring SageMaker Studio. It is **not recommended for long-lived environments**.
>
> In particular, **be aware that:**
>
> - When you delete the stack, the SageMaker Studio setup for your target AWS Region will be deleted which will result in **permanent deletion of user data** that might have been stored.
> - For this reason, the stack is deliberately designed to *fail* to delete if you still have any users with running 'apps' in Studio (which you can manage and terminate e.g. through the [SageMaker console UI](https://console.aws.amazon.com/sagemaker/home?#/studio)).

...If these prerequisites are not true and you've already onboarded to SageMaker Studio - you can just `git clone` this repository into your Studio environment and start working through the exercises!

## Developing and Deploying Locally

In addition to having an AWS Account (of course), you'll need an environment with:

- The [AWS CLI](https://aws.amazon.com/cli/)
- The [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- A Docker-compatible container runtime such as [Docker Desktop](https://www.docker.com/products/docker-desktop)
- A `make` utility such as [GNU Make](https://www.gnu.org/software/make/) - probably already installed if you have some bundled build tools already.
- Honestly? Probably a UNIX-like (non-Windows) shell if you want things to run smoothly... But if not can always give it a try and resort to translating commands from the [Makefile](Makefile) if things go wrong.

You'll also need:

- Sufficient access (log in with `aws configure`) to be able to deploy the stacks in your target region
- An *[Amazon S3](https://s3.console.aws.amazon.com/s3/home) Bucket* to use for staging deployment assets (Lambda bundles, etc)

**Step 1: Build the Lambda bundles and final CloudFormation template with AWS SAM**

```sh
make build DEPLOYMENT_BUCKET_NAME=example-bucket
```

**Step 2: Deploy (create or update) the stack**

```sh
make deploy STACK_NAME=sm101stack
```

***Alternative: Build and create the stack in one go**

(This option only *creates* stacks, and disables rollback, for easier debugging)

```sh
make all DEPLOYMENT_BUCKET_NAME=example-bucket STACK_NAME=sm101stack
```

...There's also a `make delete` option for cleaning up - but it's basically just a call to delete the CF stack.

## Preparing Templates for Multi-Region Deployment

As of now, this SAM build process is pretty region-specific (as it uploads Lambda bundles to a specific S3 bucket and Lambda deployment will fail if that bucket isn't in the same region as the target stack).

It's possible to manually set up a multi-region deployable resource by:

- Including the region in the name of your original deployment bucket (e.g. `example-bucket-us-east-1`)
- Replicating the contents of this bucket to similarly named buckets in other regions you need to support (e.g. `example-bucket-ap-southeast-1`)
- Editing the **built** template (i.e. the `.tmp.yaml` file) to replace SAM-generated references to your actual bucket as follows:

Example:

```yaml
  # (Or CodeUri...)
  ContentUri: s3://example-bucket-us-east-1/sam/1234567890abcdef
```

...becomes:

```yaml
  # (Or CodeUri...)
  ContentUri:
    Bucket:
      Fn::Sub: 'example-bucket-${AWS::Region}'
    Key: sam/1234567890abcdef
```
