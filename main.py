import os
import subprocess
import sys
import json
import time
from prompt_toolkit import prompt
from dotenv import load_dotenv
import litellm
from crewai import Crew, Task
from agents.nlp_agent import NLPAgent
from agents.dependency_resolution_agent import DependencyResolutionAgent
from agents.command_construction_agent import CommandConstructionAgent
from agents.bash_file_generator_agent import BashFileGeneratorAgent

# Load environment variables
load_dotenv()

# Enable verbose mode for LiteLLM
os.environ['LITELLM_LOG'] = 'DEBUG'
os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'

def create_bash_script(commands, env_path, env_name, use_conda=False):
    script_path = os.path.join(env_path, "setup_env.sh") if not use_conda else "setup_env.sh"
    package_manager = "conda" if use_conda else "pip"

    script_content = f"""#!/bin/bash
LOG_FILE="{os.path.join(env_path, 'log.txt') if not use_conda else 'log.txt'}"
exec > >(tee -a $LOG_FILE) 2>&1
echo 'Setting up environment: {env_name}'

# Create the virtual environment
VENV_NAME="{env_name}"
echo "Creating environment '${{VENV_NAME}}'..."

if [ "{package_manager}" == "conda" ]; then
    conda create -y -n $VENV_NAME python=3.9
else
    cd {env_path}
    python3 -m venv $VENV_NAME
fi

# Activate the virtual environment
echo "Activating environment..."
if [ "{package_manager}" == "conda" ]; then
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate $VENV_NAME
else
    source $VENV_NAME/bin/activate
fi

# Upgrade pip to the latest version if using pip
if [ "{package_manager}" == "pip" ]; then
    echo "Upgrading pip..."
    pip install --upgrade pip
fi

# Install required packages
echo "Installing required packages..."
{commands}

# Deactivate the environment
echo "Deactivating environment..."
if [ "{package_manager}" == "conda" ]; then
    conda deactivate
else
    deactivate
fi

echo 'Environment setup completed successfully!'

# Instructions for activating the environment
echo 'To activate the environment, run:'
if [ "{package_manager}" == "conda" ]; then
    echo "conda activate $VENV_NAME"
else
    echo "source {env_path}/$VENV_NAME/bin/activate"
fi

read -p 'Press any key to close this terminal...'
"""

    with open(script_path, "w") as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    return script_path

def execute_setup_commands(commands, env_path, env_name, use_conda=False):
    try:
        script_path = create_bash_script(commands, env_path, env_name, use_conda)
        
        try:
            existing_sessions = subprocess.check_output(["tmux", "list-sessions"], stderr=subprocess.STDOUT).decode()
        except subprocess.CalledProcessError:
            existing_sessions = ""

        if env_name in existing_sessions:
            print(f"Session '{env_name}' already exists. Attaching to the existing session...")
            subprocess.run(f"tmux attach -t {env_name}", shell=True)
            return
        
        tmux_command = f'tmux new-session -d -s {env_name} "bash {script_path}; tmux kill-session -t {env_name}"'
        subprocess.run(tmux_command, shell=True, check=True)
        
        print(f"Environment setup started in new tmux session '{env_name}'.")
        print(f"To monitor, run: tmux attach -t {env_name}")
        
        print("Attaching to the tmux session...")
        subprocess.run(f"tmux attach -t {env_name}", shell=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing bash script in new tmux session: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

def main():
    try:
        nlp_agent = NLPAgent()
        dependency_agent = DependencyResolutionAgent()
        command_agent = CommandConstructionAgent()
        bash_agent = BashFileGeneratorAgent()

        user_input = prompt(
            "Enter your package management request (Press Esc followed by Enter to finish):\n",
            multiline=True
        )
        print(f"User Input:\n{user_input}\n")

        # # Determine environment type
        task_resolve_env_type = Task(
            description=f"Determine the environment type (pip/conda) based on matching with keywords such as conda,anaconda are for conda"
            "and pip, python and venv are for pip, based on: {user_input}",
            agent=nlp_agent,
            expected_output="A JSON string containing the environment type (either 'pip' or 'conda')"
        )
        env_type = nlp_agent.execute_task(task_resolve_env_type).lower()
        
        if not env_type or env_type not in ['pip', 'conda']:
            env_type = input("Could not determine environment type. Please specify (pip/conda): ").lower()
            while env_type not in ['pip', 'conda']:
                env_type = input("Invalid input. Please enter either 'pip' or 'conda': ").lower()
        
        print(f"Using environment type: {env_type}")

        # Extract package information
        task1 = Task(
            description=f"Extract package information from the following user input: {user_input}, and take the environment type from {env_type}",
            agent=nlp_agent,
            expected_output="A structured list of package names, versions, environment type, and environment information extracted from the user input."
        )
        extracted_info = nlp_agent.execute_task(task1)
        print("Extracted info:", extracted_info)

        # Resolve package dependencies
        task2 = Task(
            description=f"Resolve package dependencies based on the extracted information: {extracted_info}",
            agent=dependency_agent,
            expected_output="A list of resolved package dependencies with their versions"
        )
        resolved_dependencies = dependency_agent.execute_task(task2)
        print("Resolved dependencies:", resolved_dependencies)

        # Generate setup commands
        task3 = Task(
            description=f"Generate environment setup commands for a {env_type} environment based on the resolved dependencies: {resolved_dependencies}",
            agent=command_agent,
            expected_output=f'A JSON string containing only "commands" (list of command-line instructions) and "environment_type" (which must be {env_type})'
        )
        command_output = command_agent.execute_task(task3)
        print("Command output:", command_output)

        cleaned_output = command_output.strip('`')
        output = json.loads(cleaned_output)
        
        commands = output.get('commands')
        output_env_type = output.get('environment_type', '').lower()
        
        if not commands:
            raise ValueError("Missing 'commands' in the output")
        if output_env_type != env_type:
            raise ValueError(f"Environment type mismatch. Expected {env_type}, got {output_env_type}")
        
        print(f"Environment type: {env_type}")
        print("Commands:")
        for cmd in commands:
            print(f"  {cmd}")

        # Create a bash script
        task4 = Task(
            description=f"Create a bash script for {env_type} environment setup using the following commands: {json.dumps(commands)}",
            agent=bash_agent,
            expected_output=f"A complete bash script that sets up the {env_type} environment and installs all required packages"
        )
        bash_script_content = bash_agent.execute_task(task4)
        print("Bash script content:", bash_script_content)

        env_path = ""
        if env_type == 'pip':
            env_path = prompt("Enter the directory path where you want to set up the pip environment:\n")
            print(f"Environment will be set up in: {env_path}")
        else:
            print("Conda environment will be set up in the default Conda directory.")

        env_name = prompt("Enter the name for the environment (or press Enter for default):\n")
        if not env_name.strip():
            env_name = f"env_setup_{int(time.time())}"

        execute_setup_commands(commands, env_path, env_name, use_conda=(env_type == 'conda'))

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check your API keys and network connection.")
        print("If the problem persists, please report this issue.")

if __name__ == "__main__":
    main()
