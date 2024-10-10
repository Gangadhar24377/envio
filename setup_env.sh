#!/bin/bash
LOG_FILE="log.txt"
exec > >(tee -a $LOG_FILE) 2>&1
echo 'Setting up environment: conda'

# Create the virtual environment
VENV_NAME="conda"
echo "Creating environment '${VENV_NAME}'..."

if [ "conda" == "conda" ]; then
    conda create -y -n $VENV_NAME python=3.9
else
    cd 
    python3 -m venv $VENV_NAME
fi

# Activate the virtual environment
echo "Activating environment..."
if [ "conda" == "conda" ]; then
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate $VENV_NAME
else
    source $VENV_NAME/bin/activate
fi

# Upgrade pip to the latest version if using pip
if [ "conda" == "pip" ]; then
    echo "Upgrading pip..."
    pip install --upgrade pip
fi

# Install required packages
echo "Installing required packages..."
['conda create --name myenv numpy']

# Deactivate the environment
echo "Deactivating environment..."
if [ "conda" == "conda" ]; then
    conda deactivate
else
    deactivate
fi

echo 'Environment setup completed successfully!'

# Instructions for activating the environment
echo 'To activate the environment, run:'
if [ "conda" == "conda" ]; then
    echo "conda activate $VENV_NAME"
else
    echo "source /$VENV_NAME/bin/activate"
fi

read -p 'Press any key to close this terminal...'
