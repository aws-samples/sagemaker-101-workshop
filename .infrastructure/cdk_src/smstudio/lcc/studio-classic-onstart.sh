#!/bin/bash
set -eu

echo "Checking conda environments"
if conda info --envs | grep ^studio; then
    # Standard on JLv3 image at time of writing
    CONDA_ENV=studio
else
    # Standard on JLv1 image at time of writing
    exit 0
fi
echo "Activating conda env $CONDA_ENV"
source activate $CONDA_ENV

BOTO3_VER=`pip show boto3 | grep 'Version:' | sed 's/Version: //'`
BOTOCORE_VER=`pip show botocore | grep 'Version:' | sed 's/Version: //'`
JUPYTERSERVER_VER=`pip show jupyter-server | grep 'Version:' | sed 's/Version: //'`

echo "Installing CodeWhisperer, jupyterlab-lsp, language tools, canvas widget"
pip install amazon-codewhisperer-jupyterlab-ext \
    jupyterlab-lsp \
    'python-lsp-server[flake8,mccabe,pycodestyle,pydocstyle,pyflakes,pylint,rope]' \
    jupyterlab-spellchecker \
    jupyterlab-code-formatter black isort \
    jupyterlab-s3-browser \
    boto3==$BOTO3_VER \
    botocore==$BOTOCORE_VER \
    jupyter-server==$JUPYTERSERVER_VER \
    'ipycanvas<0.13'
# bash-language-server v5+ requires Node v16+ (not yet available):
jlpm add --dev bash-language-server@"<5.0.0" dockerfile-language-server-nodejs

# CodeWhisperer should be specifically enabled:
jupyter server extension enable amazon_codewhisperer_jupyterlab_ext

CMP_CONFIG_DIR=.jupyter/lab/user-settings/@krassowski/jupyterlab-lsp/
CMP_CONFIG_FILE=completion.jupyterlab-settings
CMP_CONFIG_PATH="$CMP_CONFIG_DIR/$CMP_CONFIG_FILE"
if test -f $CMP_CONFIG_PATH; then
    echo "jupyterlab-lsp config file already exists: Skipping default config setup"
else
    echo "Setting continuous hinting to enabled by default"
    mkdir -p $CMP_CONFIG_DIR
    echo '{ "continuousHinting": true }' > $CMP_CONFIG_PATH
fi

FMT_CONFIG_DIR=~/.jupyter/lab/user-settings/@ryantam626/jupyterlab_code_formatter
FMT_CONFIG_FILE=settings.jupyterlab-settings
FMT_CONFIG_PATH="$FMT_CONFIG_DIR/$FMT_CONFIG_FILE"
if test -f $FMT_CONFIG_PATH; then
    echo "jupyterlab-code-formatter config file already exists: Skipping default config setup"
else
    echo "Configuring jupyterlab-code-formatter format on save and line width"
    mkdir -p $FMT_CONFIG_DIR
    # Could turn on "formatOnSave": true here, but would raise error messages for partial nbks
    cat > $FMT_CONFIG_PATH <<EOF
{"black": {"line_length": 100}, "isort": {"line_length": 100}}
EOF
fi
echo "Configuring pycodestyle linter max line width"
mkdir -p ~/.config
cat > ~/.config/pycodestyle <<EOF
[pycodestyle]
max-line-length = 100
EOF

echo "Restarting Jupyter server..."
nohup supervisorctl -c /etc/supervisor/conf.d/supervisord.conf restart jupyterlabserver \
    > /dev/null 2>&1