#!/bin/bash

# If you'd like to run this repository in SageMaker Studio instead of a SageMaker Notebook Instance, you can
# run this script in a *System Terminal* (from the launcher page or the toolbar "Plus" button) to perform the
# same extension installation that would usually happen via instance lifecycle configuration script specified
# in .ee.tpl.yaml

set -e

# Colorization (needs -e switch on echo, or to use printf):
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color (end)

echo -e "${CYAN}Installing IPyWidgets labextension${NC}"
jupyter labextension install @jupyter-widgets/jupyterlab-manager

echo -e "${CYAN}Restarting jupyterlabserver${NC}"
nohup supervisorctl -c /etc/supervisor/conf.d/supervisord.conf restart jupyterlabserver
