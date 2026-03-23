"""Serper Search Tool for web search fallback."""

from __future__ import annotations

import os

import requests


class SerperSearchTool:
    """Tool for searching the web using Serper API."""

    def run(self, query: str) -> str:
        """Search the web using Serper API."""
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return (
                "Serper API key not found. Please set SERPER_API_KEY in your .env file."
            )

        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        payload = {"q": query}

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                results = data.get("organic", [])
                if results:
                    first_result = results[0]
                    title = first_result.get("title", "N/A")
                    snippet = first_result.get("snippet", "N/A")
                    return f"{title}: {snippet}"
                return "No search results found."
            return f"Search failed with status code: {response.status_code}"
        except Exception as e:
            return f"Error during search: {str(e)}"
