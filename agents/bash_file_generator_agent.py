# agents/bash_file_generator_agent.py
import os
from crewai import Agent
from langchain_openai import ChatOpenAI

class BashFileGeneratorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Bash File Generator Agent",
            role="Bash Scripting Expert",
            goal="Create executable bash scripts for environment setup",
            backstory="I am an AI specialized in writing bash scripts for automating environment setup and package installation.",
            verbose=True,
            llm=ChatOpenAI(model_name='gpt-4o-mini',temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
        )

    def generate_bash_file(self, commands):
        return self.run(f"Create a bash script with the following commands: {commands}")