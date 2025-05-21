#!/bin/bash

#### Clone sample code for labs
# For new-style SMStudio we can't use EFS mounts to initialize user content, so have to use
# this LCC. Repo name (and possibly branch config) below is populated by CDK.
# `|| true` to swallow any errors (e.g. if folder already exists) - `set +e` doesn't work
git clone {{CODE_REPO}} || true

#### Docker installation (for SageMaker Local Mode)
# As per: https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get -y install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

#### JupyterLab extensions / etc
# MNIST exercises require ipycanvas
pip install "ipycanvas>=0.12,<0.14"
restart-jupyter-server
