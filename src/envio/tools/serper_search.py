"""Serper Search Tool for web search fallback."""

from __future__ import annotations

import os

import requests


class SerperSearchTool:
    """Tool for searching the web using Serper API."""

    def __init__(self, num_results: int = 5):
        """Initialize the search tool.

        Args:
            num_results: Number of results to return (default: 5)
        """
        self.num_results = num_results

    def run(self, query: str, num_results: int | None = None) -> str:
        """Search the web using Serper API.

        Args:
            query: Search query
            num_results: Override default number of results
        """
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return (
                "Serper API key not found. Please set SERPER_API_KEY in your .env file."
            )

        n = num_results or self.num_results

        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": n}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get("organic", [])
                if not results:
                    return "No search results found."

                output_lines = []
                for i, result in enumerate(results[:n]):
                    title = result.get("title", "N/A")
                    snippet = result.get("snippet", "N/A")
                    link = result.get("link", "")
                    output_lines.append(f"{i + 1}. {title}: {snippet} [{link}]")

                return "\n".join(output_lines)
            return f"Search failed with status code: {response.status_code}"
        except Exception as e:
            return f"Error during search: {str(e)}"
