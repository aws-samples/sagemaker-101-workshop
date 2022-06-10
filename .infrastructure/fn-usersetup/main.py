"""Custom CloudFormation Resource for loading content to a SageMaker Studio user

This entrypoint is a thin wrapper to ensure even import/syntax errors from the main code result in
sending a failure response to CloudFormation (because if no response is sent, the resource will
wait for 1hr timeout before failing). See content.py for main functionality docs.

Clones a (public) 'GitRepository' into the user's home folder.

Updating or deleting this resource does not currently do anything. Errors in the setup process are
also ignored (typically don't want to roll back the whole stack just because we couldn't clone a
repo - as users can always do it manually!)
"""

# Python Built-Ins:
import logging
import traceback

# External Dependencies:
import cfnresponse


def lambda_handler(event, context):
    try:
        # Local imports *inside* try/catch so any syntax errors or other basic stuff still send a
        # failed cfnresponse instead of just timing out the CFn resource (which takes an hour!)
        import content

        request_type = event["RequestType"]
        if request_type == "Create":
            content.handle_create(event, context)
        elif request_type == "Update":
            content.handle_update(event, context)
        elif request_type == "Delete":
            content.handle_delete(event, context)
        else:
            cfnresponse.send(
                event,
                context,
                cfnresponse.FAILED,
                {},
                error=f"Unsupported CFN RequestType '{request_type}'",
            )
    except Exception as e:
        logging.error("Uncaught exception in CFN custom resource handler - reporting failure")
        traceback.print_exc()
        cfnresponse.send(
            event,
            context,
            cfnresponse.FAILED,
            {},
            error=str(e),
        )
        raise e
