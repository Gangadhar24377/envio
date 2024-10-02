from langchain.tools import BaseTool
import requests
import os
from typing import Optional

class SerperSearchTool(BaseTool):
    name: str = "Serper Search"
    description: str = "Search the web for package information using Serper API"

    def _run(self, query: str) -> str:
        api_key = os.getenv("SERPER_API_KEY")
        url = "https://google.serper.dev/search"
        payload = {"q": query}
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Error searching for {query}"

    async def _arun(self, query: str) -> str:
        # Implement async version if needed
        raise NotImplementedError("SerperSearchTool does not support async")