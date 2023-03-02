##########################
# Bootstrapping variables
##########################

STACK_NAME?="sm101stack"
DEPLOYMENT_BUCKET_NAME?="UNDEFINED"
DEPLOYMENT_BUCKET_PREFIX?=""
SAM_BUILD_EXTRA_ARGS?=""

target:
	$(info ${HELP_MESSAGE})
	@exit 0

init: ##=> Install OS deps and dev tools
	$(info [*] Bootstrapping CI system...)
	@$(MAKE) _install_os_packages

build: ##=> Build SAM template & assets to CloudFormation on S3
	$(info [*] Building AWS SAM stack...)
	sam build \
			--use-container \
			--template template.sam.yaml \
			$(SAM_BUILD_EXTRA_ARGS) && \
		sam package \
			--s3-bucket $(DEPLOYMENT_BUCKET_NAME) \
			--s3-prefix $(DEPLOYMENT_BUCKET_PREFIX)sam \
			--use-json \
			--output-template-file template.tmp.json && \
		python sam-indirect.py \
			template.tmp.json \
			template.tmp.json \
			--source-s3-prefix $(DEPLOYMENT_BUCKET_PREFIX) && \
		aws s3 cp template.tmp.json \
			s3://$(DEPLOYMENT_BUCKET_NAME)/$(DEPLOYMENT_BUCKET_PREFIX)SM101.cf.json

create: ##=> Create services stack (only)
	$(info [*] Deploying...)
	aws cloudformation create-stack \
			--template-body file://template.tmp.json \
			--stack-name $(STACK_NAME) \
			--capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
			--disable-rollback
			# (disable rollback for debugging)
			# TODO: Support --parameter-overrides through MAKE?

deploy: ##=> Deploy services (flexible create or update)
	$(info [*] Deploying...)
	sam deploy \
			--template-file template.tmp.json \
			--stack-name $(STACK_NAME) \
			--capabilities CAPABILITY_IAM
			# TODO: Support --parameter-overrides through MAKE?

all: ##=> Build and create stack
	@$(MAKE) build
	@$(MAKE) create

delete: ##=> Delete services
	$(info [*] Deleting stack...)
	aws cloudformation delete-stack --stack-name $(STACK_NAME)


#############
#  Helpers  #
#############

_install_os_packages:
	$(info [*] Installing jq...)
	yum install jq -y
	$(info [*] Checking currently installed Python version...)
	python3 --version
	$(info [*] Upgrading Python SAM CLI and CloudFormation linter to the latest version...)
	python3 -m pip install --upgrade --user cfn-lint aws-sam-cli
	npm -g install aws-cdk

define HELP_MESSAGE

	Environment variables:

	DEPLOYMENT_BUCKET_NAME: "my-bucket"
		Description: (Required) Amazon S3 bucket for staging built SAM Lambda bundles and assets
	DEPLOYMENT_BUCKET_PREFIX: "a/prefix/"
		Description: For publishing to a prefix in your deployment bucket, instead of root
	STACK_NAME: "sm101stack"
		Description: Stack Name to deploy/redeploy to
	SAM_BUILD_EXTRA_ARGS: ""
		Description: Extra arguments to pass to AWS SAM build, if necessary

	Common usage:

	...::: Bootstraps environment with necessary tools like SAM CLI, cfn-lint, etc. :::...
	$ make init

	...::: Build all SAM based services :::...
	$ make build

	...::: Deploy or re-deploy all SAM based services :::...
	$ make deploy

	...::: Delete all SAM based services :::...
	$ make delete
endef
