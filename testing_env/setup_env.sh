#!/bin/bash
LOG_FILE="/Users/saieeshwar/College/capstone/envio/testing_env/log.txt"
exec > >(tee -a $LOG_FILE) 2>&1
echo 'Setting up environment: test4'

# Create the virtual environment
VENV_NAME="test4"
echo "Creating environment '${VENV_NAME}'..."

if [ "pip" == "conda" ]; then
    conda create -y -n $VENV_NAME python=3.9
else
    cd /Users/saieeshwar/College/capstone/envio/testing_env
    python3 -m venv $VENV_NAME
fi

# Activate the virtual environment
echo "Activating environment..."
if [ "pip" == "conda" ]; then
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate $VENV_NAME
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
['pip install numpy==2.1.2', 'pip install matplotlib==3.9.2']

# Deactivate the environment
echo "Deactivating environment..."
if [ "pip" == "conda" ]; then
    conda deactivate
else
    deactivate
fi

echo 'Environment setup completed successfully!'

# Instructions for activating the environment
echo 'To activate the environment, run:'
if [ "pip" == "conda" ]; then
    echo "conda activate $VENV_NAME"
else
    echo "source /Users/saieeshwar/College/capstone/envio/testing_env/$VENV_NAME/bin/activate"
fi

read -p 'Press any key to close this terminal...'
