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
        prompt = f"""
        Analyze the following user input and extract the package information:

        {user_input}

        Please provide the following information:
        1. Environment type (pip or conda)
        2. Python version (if specified)
        3. List of packages with their version requirements (if any)
        4. Any specific environment name or setup instructions

        Format your response as a structured list, like this:
        Environment type: [pip/conda]
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