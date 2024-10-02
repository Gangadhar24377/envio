```bash
#!/bin/bash

# This script sets up a Python virtual environment and installs the required packages.

# Define the name of the virtual environment
VENV_NAME="myenv"

# Create a virtual environment
echo "Creating virtual environment: $VENV_NAME"
python3 -m venv $VENV_NAME

# Activate the virtual environment
echo "Activating virtual environment: $VENV_NAME"
source $VENV_NAME/bin/activate

# Upgrade pip to the latest version
echo "Upgrading pip to the latest version"
pip install --upgrade pip

# Install required packages
echo "Installing required packages..."
pip install torch==1.0.2
pip install scikit-learn==1.5.2
pip install numpy==2.1.1
pip install pandas==2.2.3
pip install matplotlib==3.9.2

# Deactivate the virtual environment
echo "Deactivating virtual environment"
deactivate

echo "Environment setup complete. To activate the environment, run: source $VENV_NAME/bin/activate"
```