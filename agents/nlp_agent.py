# agents/nlp_agent.py
from crewai import Agent
from langchain_openai import ChatOpenAI
import os

class NLPAgent(Agent):
    def __init__(self):
        super().__init__(
            name="NLP Agent",
            role="Natural Language Processing Expert",
            goal="Extract package information and environment type from user input",
            backstory="I am an AI specialized in understanding and processing natural language inputs related to package management.",
            verbose=True,
            llm=ChatOpenAI(model_name="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
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