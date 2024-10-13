from crewai import Agent, LLM
import json

class CommandConstructionAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Command Construction Agent",
            role="Command Line Expert",
            goal="Generate appropriate environment setup commands for pip or conda",
            backstory="I am an AI specialized in creating command-line instructions for setting up development environments using pip or conda.",
            verbose=True,
            llm=LLM(model="ollama/deepseek-coder-v2:latest", base_url="http://localhost:11434")  # Indicating usage of Ollama for local LLM
        )

    def generate_commands(self, env_type, python_version, packages, env_name):
            prompt = f"""
            Generate the appropriate commands to set up a {env_type} environment with the following details:

            Environment type: {env_type}
            Python version: {python_version}
            Environment name: {env_name}
            Packages:
            {packages}

            IMPORTANT: The environment type MUST be {env_type}. Do not change this under any circumstances.

            For pip environments:
            1. Use 'python -m venv' to create the virtual environment
            2. Use 'source' to activate the environment on Unix or 'call' on Windows
            3. Use 'pip install' commands for package installation

            For conda environments:
            1. Use 'conda create' to create the environment with Python
            2. Use 'conda activate' to activate the environment
            3. Use 'conda install' commands for package installation

            Return your response as a JSON string with two keys:
            1. 'commands': A list of strings, each representing a single command.
            2. 'environment_type': Must be exactly '{env_type}'.

            IMPORTANT: Do not include any backticks (`), newlines, or additional text. Only return the JSON string.
            """
            response = self.run(prompt)
            try:
                # Clean and parse the response
                cleaned_response = response.strip().strip('`').replace('\n', '').replace('\\n', '')
                parsed_response = json.loads(cleaned_response)
                
                # Ensure the environment type matches
                if parsed_response.get('environment_type', '').lower() != env_type.lower():
                    raise ValueError(f"Environment type mismatch. Expected {env_type}, got {parsed_response.get('environment_type')}")
                
                return parsed_response
            except json.JSONDecodeError as e:
                return {"error": "Failed to generate valid JSON", "raw_output": response}
            except ValueError as e:
                return {"error": str(e), "raw_output": response}