from crewai import Agent, LLM
import os

class NLPAgent(Agent):
    def __init__(self):
        super().__init__(
            name="NLP Agent",
            role="Natural Language Processing Expert",
            goal="Extract package information and environment type from user input",
            backstory="I am an AI specialized in understanding and processing natural language inputs related to package management.",
            verbose=True,
            llm=LLM(model="ollama/deepseek-coder-v2:latest", base_url="http://localhost:11434")  # Indicating usage of Ollama for local LLM
        )

    def extract_package_info(self, user_input):
        # Determine environment type based on keywords
        environment_type = "pip"  # Default to pip
        if any(keyword in user_input.lower() for keyword in ["conda", "anaconda", "create conda", "install conda"]):
            environment_type = "conda"
        
        prompt = f"""
        Analyze the following user input and extract the package information:

        {user_input}

        Please provide the following information:
        1. Environment type: {environment_type}
        2. Python version (if specified)
        3. List of packages with their version requirements (if any)
        4. Any specific environment name or setup instructions

        Format your response as a structured list, like this:
        Environment type: [{environment_type}]
        Python version: [version]
        Packages:
        - [package1]: [version requirement]
        - [package2]: [version requirement]
        ...
        Environment name: [name]
        Additional instructions: [any other relevant information]

        If any information is not provided in the input, omit that field.
        """
        return self.run(prompt)

    def determine_env_type(self, user_input):
            """
            Determines whether the user input specifies a conda or pip environment
            based on relevant keywords.
            """
            user_input = user_input.lower()

            # Keywords to detect conda environment
            conda_keywords = ["conda create", "conda install", "conda activate", "environment.yml", "conda list", "conda env"]

            # Keywords to detect pip environment
            pip_keywords = ["pip install", "virtualenv", "requirements.txt", "python -m venv", "pip freeze", "pip uninstall"]

            # Check for conda-related keywords
            if any(keyword in user_input for keyword in conda_keywords):
                return 'conda'
            # Check for pip-related keywords
            elif any(keyword in user_input for keyword in pip_keywords):
                return 'pip'
            else:
                # Default to pip if no specific keywords are found
                return 'pip'

# Example usage of the NLPAgent
if __name__ == "__main__":
    nlp_agent = NLPAgent()

    # Example user input for a Conda environment
    user_input_conda = "I want to create a conda environment with Python 3.8 and install numpy 1.21.0 and pandas 1.3.0."
    package_info_conda = nlp_agent.extract_package_info(user_input_conda)
    print("Package Information (Conda):")
    print(package_info_conda)

    # Example user input for a pip environment
    user_input_pip = "I need to set up a virtual environment using pip with Python 3.9 and install requests."
    package_info_pip = nlp_agent.extract_package_info(user_input_pip)
    print("\nPackage Information (Pip):")
    print(package_info_pip)
