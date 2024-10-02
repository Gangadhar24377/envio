# agents/dependency_resolution_agent.py
from crewai import Agent
from langchain_openai import ChatOpenAI
from tools.package_lookup import PackageLookupTool
from tools.serper_search import SerperSearchTool
import os

class DependencyResolutionAgent(Agent):
    def __init__(self):
        # Initialize the tools
        package_lookup_tool = PackageLookupTool()
        serper_search_tool = SerperSearchTool()

        super().__init__(
            name="Dependency Resolution Agent",
            role="Package Dependency Expert",
            goal="Resolve package dependencies and conflicts",
            backstory="I am an AI specialized in managing package dependencies and resolving conflicts.",
            verbose=True,
            llm=ChatOpenAI(model_name="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY")),
            tools=[package_lookup_tool, serper_search_tool]
        )

    def resolve_dependencies(self, packages, env_type):
        result = {}
        for package in packages:
            # First, try to look up the package using PyPI or Conda
            lookup_result = self.tools[0]._run(package, env_type)
            
            # Check if the lookup returned a valid dictionary or JSON response
            if isinstance(lookup_result, dict) and lookup_result.get("version"):
                result[package] = lookup_result["version"]
            else:
                # If not found in PyPI/Conda, use Serper search as a fallback
                search_result = self.tools[1]._run(f"{package} python package {env_type}")
                result[package] = f"Not found in official repositories. Web search result: {search_result}"

        # Now use the LLM to analyze the results and resolve any conflicts
        analysis_prompt = f"""
        Analyze the following package information and resolve any potential conflicts:
        {result}
        
        Environment type: {env_type}
        
        Provide a list of packages with their recommended versions, ensuring compatibility.
        If there are any conflicts or special instructions, please note them.
        """
        
        return self.run(analysis_prompt)
