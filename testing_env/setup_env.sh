#!/bin/bash
LOG_FILE="/Users/saieeshwar/College/capstone/envio/testing_env/log.txt"

# Set up logging with timestamps
exec > >(tee -a "$LOG_FILE" | while IFS= read -r line; do echo "$(date +'%Y-%m-%d %H:%M:%S') $line"; done) 2>&1

echo "Setting up environment: blamnk"

# Create the virtual environment
VENV_NAME="blamnk"
echo "Creating environment '$blamnk'..."

if [ "pip" == "conda" ]; then
    conda create -y -n "$VENV_NAME" python=3.9
else
    cd "/Users/saieeshwar/College/capstone/envio/testing_env"
    python3 -m venv "$VENV_NAME"
fi

# Activate the virtual environment
echo "Activating environment..."
if [ "pip" == "conda" ]; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$VENV_NAME"
else
    source "$VENV_NAME/bin/activate"
fi

# Upgrade pip if using pip package manager
if [ "pip" == "pip" ]; then
    echo "Upgrading pip..."
    pip install --upgrade pip
fi

# Install required packages
echo "Installing required packages..."
['pip install --upgrade pip', 'python -m pip install pandas --source https://github.com/psf/coins.git#egg=pandas', 'python -m pip install matplotlib --source https://github.com/matplotlib/matplotlib.git#egg=matplotlib']

# Deactivate the environment
echo "Deactivating environment..."
if [ "pip" == "conda" ]; then
    conda deactivate
else
    deactivate
fi

echo "Environment setup completed successfully!"

# Instructions for activating the environment
echo "To activate the environment, run:"
if [ "pip" == "conda" ]; then
    echo "conda activate $VENV_NAME"
else
    echo "source /Users/saieeshwar/College/capstone/envio/testing_env/$VENV_NAME/bin/activate"
fi

read -p "Press any key to close this terminal..."
