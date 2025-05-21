#!/bin/bash
set -e

# Install extension for interactive canvas drawing:
# ipywidgets is already present on al2-v2 NBIs. Pin versions to avoid reinstallations
sudo -u ec2-user -i <<'EOF'
source /home/ec2-user/anaconda3/bin/activate JupyterSystemEnv
JUPYTERSERVER_VER=`pip show jupyter-server | grep 'Version:' | sed 's/Version: //'`
IPYWIDGETS_VER=`pip show ipywidgets | grep 'Version:' | sed 's/Version: //'`
pip install \
  jupyter-server==$JUPYTERSERVER_VER \
  ipywidgets==$IPYWIDGETS_VER \
  'ipycanvas<0.13'
source /home/ec2-user/anaconda3/bin/deactivate
EOF
