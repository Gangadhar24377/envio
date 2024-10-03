import os
import subprocess
import sys
from prompt_toolkit import prompt
import litellm
import json
from datetime import datetime
from crewai import Crew, Task
from agents.nlp_agent import NLPAgent
from agents.dependency_resolution_agent import DependencyResolutionAgent
from agents.command_construction_agent import CommandConstructionAgent
from agents.bash_file_generator_agent import BashFileGeneratorAgent
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Enable verbose mode for LiteLLM
os.environ['LITELLM_LOG'] = 'DEBUG'
os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'

def create_bash_script(commands, env_path, env_name, use_conda=False):
    script_path = os.path.join(env_path, "setup_env.sh")
    package_manager = "conda" if use_conda else "pip"

    script_content = """#!/bin/bash

# Generate a timestamp for the log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="{env_path}/log_${{TIMESTAMP}}.txt"

# Redirect stdout and stderr to both console and log file
exec > >(tee -a "$LOG_FILE") 2>&1

echo 'Setting up environment: {env_name}'
cd {env_path}

# Create the virtual environment
VENV_NAME="{env_name}"
echo "Creating environment '${{VENV_NAME}}'..."
if [ "{package_manager}" == "conda" ]; then
    conda create -y -n $VENV_NAME python=3.9
else
    python3 -m venv $VENV_NAME
fi

# Check if the environment was created successfully
if [ ! -d "$VENV_NAME" ]; then
    echo "Failed to create environment at {env_path}/$VENV_NAME"
    exit 1
fi

# Activate the virtual environment
echo "Activating environment..."
if [ "{package_manager}" == "conda" ]; then
    source activate $VENV_NAME
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

# Message to indicate setup completion
echo 'Environment setup completed successfully!'

# Instructions for activating the environment
echo 'To activate the environment, run:'
if [ "{package_manager}" == "conda" ]; then
    echo "conda activate $VENV_NAME"
else
    echo "source {env_path}/$VENV_NAME/bin/activate"
fi

echo "Log file created at: $LOG_FILE"

read -p 'Press any key to close this terminal...'
""".format(
        env_name=env_name,
        env_path=env_path,
        package_manager=package_manager,
        commands="\n".join(commands)
    )

    with open(script_path, "w") as f:
        f.write(script_content)

    # Make the script executable
    os.chmod(script_path, 0o755)

    return script_path

def execute_setup_commands(commands, env_path, env_name, use_conda=False):
    try:
        # Create a bash script with the setup commands in the environment path
        script_path = create_bash_script(commands, env_path, env_name, use_conda)
        
        # Check if a tmux session with the given name already exists
        try:
            existing_sessions = subprocess.check_output(["tmux", "list-sessions"], stderr=subprocess.STDOUT).decode()
        except subprocess.CalledProcessError:
            existing_sessions = ""  # No sessions exist, so this can be an empty string

        if env_name in existing_sessions:
            print(f"Session '{env_name}' already exists. Attaching to the existing session...")
            subprocess.run(f"tmux attach -t {env_name}", shell=True)
            return
        
        # Create a tmux session and run the bash script in a new terminal, ensuring you see the output
        tmux_command = f'tmux new-session -d -s {env_name} "cd {env_path} && bash {script_path}; tmux kill-session -t {env_name}"'
        subprocess.run(tmux_command, shell=True, check=True)
        
        print(f"Environment setup started in new tmux session '{env_name}'.")
        print(f"To monitor, run: tmux attach -t {env_name}")
        
        # Automatically attach to the tmux session
        print("Attaching to the tmux session...")
        subprocess.run(f"tmux attach -t {env_name}", shell=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing bash script in new tmux session: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
    print("")

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

        task1 = Task(
            description=f"Extract package information from the following user input:\n{user_input}",
            agent=nlp_agent,
            expected_output="A structured list of package names, versions, environment type, and environment information extracted from the user input"
        )

        extracted_info = nlp_agent.execute_task(task1)
        print("Extracted info:", extracted_info)

        try:
            extracted_data = json.loads(extracted_info)
            env_type = extracted_data.get('environment_type', 'pip').lower()
            if env_type not in ['pip', 'conda']:
                print(f"Unsupported environment type: {env_type}. Defaulting to pip.")
                env_type = 'pip'
            print(f"Detected environment type: {env_type}")
        except json.JSONDecodeError:
            print("Warning: Could not parse extracted info as JSON. Defaulting to pip environment.")
            env_type = 'pip'

        task2 = Task(
            description=f"Resolve package dependencies based on the extracted information:\n{extracted_info}",
            agent=dependency_agent,
            expected_output="A list of resolved package dependencies with their versions"
        )

        resolved_dependencies = dependency_agent.execute_task(task2)
        print("Resolved dependencies:", resolved_dependencies)

        task3 = Task(
            description=f"Generate environment setup commands for a {env_type} environment based on the resolved dependencies:\n{resolved_dependencies}",
            agent=command_agent,
            expected_output=f'A JSON string containing only "commands" (list of command-line instructions) and "environment_type" (which must be {env_type})'
        )

        command_output = command_agent.execute_task(task3)
        print("Command output:", command_output)

        try:
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
        except json.JSONDecodeError as e:
            print(f"Error processing the output: {e}")
            print(f"Raw output: {command_output}")
            sys.exit(1)
        except ValueError as e:
            print(f"Error in command output: {e}")
            print(f"Raw output: {command_output}")
            sys.exit(1)

        task4 = Task(
            description=f"Create a bash script for {env_type} environment setup using the following commands:\n{json.dumps(commands)}",
            agent=bash_agent,
            expected_output=f"A complete bash script that sets up the {env_type} environment and installs all required packages"
        )

        bash_script_content = bash_agent.execute_task(task4)
        print("Bash script content:", bash_script_content)

        # Write the bash script to a file and get the environment path from the user
        env_path = prompt("Enter the directory path where you want to set up the environment:\n")
        print(f"Environment will be set up in: {env_path}")

        # Ask the user for the environment name (or use a default if none is provided)
        env_name = prompt("Enter the name for the environment (or press Enter for default):\n")
        if not env_name.strip():
            env_name = f"env_setup_{int(time.time())}"  # Default name with timestamp

        # Create the bash script in the specified directory
        script_path = create_bash_script(bash_script_content, env_path, env_name)

        # Automatically execute the bash script in the specified path and attach to tmux
        execute_setup_commands(commands, env_path, env_name)


    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check your API keys and network connection.")
        print("If the problem persists, please report this issue.")

if __name__ == "__main__":
    main()
