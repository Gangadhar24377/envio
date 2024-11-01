#!/bin/bash
LOG_FILE="log.txt"

# Set up logging with timestamps
exec > >(tee -a "$LOG_FILE" | while IFS= read -r line; do echo "$(date +'%Y-%m-%d %H:%M:%S') $line"; done) 2>&1

echo "Setting up environment: eesh"

# Create the virtual environment
VENV_NAME="eesh"
echo "Creating environment '$eesh'..."

if [ "conda" == "conda" ]; then
    conda create -y -n "$VENV_NAME" python=3.9
else
    cd ""
    python3 -m venv "$VENV_NAME"
fi

# Activate the virtual environment
echo "Activating environment..."
if [ "conda" == "conda" ]; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$VENV_NAME"
else
    source "$VENV_NAME/bin/activate"
fi

# Upgrade pip if using pip package manager
if [ "conda" == "pip" ]; then
    echo "Upgrading pip..."
    pip install --upgrade pip
fi

# Install required packages
echo "Installing required packages..."
['conda create --name env_name python=3.9', 'conda activate env_name', 'conda install numpy==2.1.2 matplotlib==3.9.2']

# Deactivate the environment
echo "Deactivating environment..."
if [ "conda" == "conda" ]; then
    conda deactivate
else
    deactivate
fi

echo "Environment setup completed successfully!"

# Instructions for activating the environment
echo "To activate the environment, run:"
if [ "conda" == "conda" ]; then
    echo "conda activate $VENV_NAME"
else
    echo "source /$VENV_NAME/bin/activate"
fi

read -p "Press any key to close this terminal..."
