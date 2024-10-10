import os
from crewai import Agent, LLM
import litellm  # Assuming you're using LiteLLM to interface with Ollama locally

class BashFileGeneratorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Bash File Generator Agent",
            role="Bash Scripting Expert",
            goal="Create executable bash scripts for environment setup",
            backstory="I am an AI specialized in writing bash scripts for automating environment setup and package installation.",
            verbose=True,
            llm=LLM(model="ollama/deepseek-coder-v2:latest", base_url="http://localhost:11434")
  # Indicating usage of Ollama for local LLM
        )

    def generate_bash_file(self, commands):
        return self.run(f"Create a bash script with the following commands: {commands}")                           