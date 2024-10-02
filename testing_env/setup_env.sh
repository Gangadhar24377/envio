#!/bin/bash
echo 'Setting up environment: shuttler'
cd /home/kambhamettu.s/Projects/envio/aI-package-manager/testing_env

# Create the virtual environment
VENV_NAME="shuttler"
echo "Creating environment '${VENV_NAME}'..."

if [ "pip" == "conda" ]; then
    conda create -y -n $VENV_NAME python=3.9
else
    python3 -m venv $VENV_NAME
fi

# Check if the environment was created successfully
if [ ! -d "$VENV_NAME" ]; then
    echo "Failed to create environment at /home/kambhamettu.s/Projects/envio/aI-package-manager/testing_env/$VENV_NAME"
    exit 1
fi

# Activate the virtual environment
echo "Activating environment..."
if [ "pip" == "conda" ]; then
    source activate $VENV_NAME
else
    source $VENV_NAME/bin/activate
fi

# Upgrade pip to the latest version if using pip
if [ "pip" == "pip" ]; then
    echo "Upgrading pip..."
    pip install --upgrade pip
fi

# Install required packages
echo "Installing required packages..."
pip install scipy==1.14.1
pip install librosa==0.10.2.post1
pip install seaborn==0.13.2
pip install wave==0.0.2

# Deactivate the environment
echo "Deactivating environment..."
if [ "pip" == "conda" ]; then
    conda deactivate
else
    deactivate
fi

# Message to indicate setup completion
echo 'Environment setup completed successfully!'

# Instructions for activating the environment
echo 'To activate the environment, run:'
if [ "pip" == "conda" ]; then
    echo "conda activate $VENV_NAME"
else
    echo "source /home/kambhamettu.s/Projects/envio/aI-package-manager/testing_env/$VENV_NAME/bin/activate"
fi

read -p 'Press any key to close this terminal...'
