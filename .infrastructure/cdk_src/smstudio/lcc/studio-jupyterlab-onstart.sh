#!/bin/bash

#### Clone sample code for labs
# For new-style SMStudio we can't use EFS mounts to initialize user content, so have to use
# this LCC. Repo name (and possibly branch config) below is populated by CDK.
# `|| true` to swallow any errors (e.g. if folder already exists) - `set +e` doesn't work
git clone {{CODE_REPO}} || true
