"""NLP processor for extracting package information from user input."""

from __future__ import annotations

from typing import Any

from envio.llm.client import LLMClient, LLMConfig
from envio.llm.parser import ResponseParser
from envio.llm.prompts import NLP_SYSTEM_PROMPT, NLP_USER_PROMPT


class NLPProcessor:
    """Processor for natural language package extraction."""

    # Generic packages that might indicate the LLM didn't understand the request
    # and defaulted to safe/common packages instead of domain-specific ones
    GENERIC_PACKAGES = {
        "requests",
        "flask",
        "fastapi",
        "django",
        "pandas",
        "numpy",
        "matplotlib",
        "jupyter",
        "httpx",
        "aiohttp",
        "scikit-learn",
        "seaborn",
        "tensorflow",
        "pytorch",
        "torch",
        "ray",
        "scipy",
        "pillow",
        "beautifulsoup4",
        "sqlalchemy",
        "pytest",
        "black",
        "pylint",
    }

    def __init__(self, config: LLMConfig | None = None) -> None:
        self._llm = LLMClient(config)
        self._parser = ResponseParser()
        self._search_tool = None

    def _get_search_tool(self):
        """Lazy load search tool."""
        if self._search_tool is None:
            from envio.tools.serper_search import SerperSearchTool

            self._search_tool = SerperSearchTool()
        return self._search_tool

    def _search_for_packages(self, user_input: str, callback: Any = None) -> str:
        """Search the web for relevant packages for the user's request.

        Args:
            user_input: User's request
            callback: Optional callback for streaming updates

        Returns:
            Search results string
        """
        search_tool = self._get_search_tool()

        # Create a targeted search query
        search_query = f"best python packages for {user_input}"
        if callback:
            callback(f"  -> Searching for: {search_query}")

        result = search_tool.run(search_query)
        return result

    def _enhance_with_search(
        self,
        user_input: str,
        initial_packages: list[str],
        callback: Any = None,
    ) -> list[str]:
        """Enhance package suggestions with web search if needed.

        Args:
            user_input: User's request
            initial_packages: Initial package suggestions from LLM
            callback: Optional callback for streaming updates

        Returns:
            Enhanced package list
        """
        # Check if packages seem generic
        generic_count = sum(
            1 for pkg in initial_packages if pkg.lower() in self.GENERIC_PACKAGES
        )
        is_mostly_generic = generic_count > len(initial_packages) * 0.5

        if not is_mostly_generic:
            # Packages look good, no need to search
            return initial_packages

        # Try to search for better packages
        try:
            search_results = self._search_for_packages(user_input, callback)

            if (
                "API key not found" in search_results
                or "No search results" in search_results
                or "Search failed" in search_results
                or "Error during search" in search_results
                or not search_results.strip()
            ):
                # No search available or search failed, return initial packages
                return initial_packages

            # Use LLM to parse search results and suggest packages
            search_prompt = f"""Based on these search results, suggest Python packages for: {user_input}

Search results:
{search_results}

Current suggestions (may be incomplete): {", ".join(initial_packages)}

Based on the search results, provide a list of packages that would be appropriate.
Consider both the current suggestions AND the search results.

Respond with JSON:
{{
    "packages": ["package1", "package2", ...],
    "reasoning": "why these packages"
}}"""

            response = self._llm.chat_json(
                system_prompt="You are a Python package expert. Suggest packages based on search results.",
                user_prompt=search_prompt,
            )

            enhanced_packages = response.get("packages", initial_packages)
            if enhanced_packages:
                if callback:
                    callback(
                        f"  -> Enhanced suggestions: {', '.join(enhanced_packages)}"
                    )
                return enhanced_packages

        except Exception:
            # If search fails, just return initial packages
            pass

        return initial_packages

    def extract(
        self,
        user_input: str,
        hardware_context: str = "",
        callback: Any = None,
    ) -> dict[str, Any]:
        """Extract package information from user input.

        Args:
            user_input: Natural language request (e.g., "set up pytorch env with cuda")
            hardware_context: Hardware information string (optional)
            callback: Optional callback function for streaming updates

        Returns:
            Dictionary with packages, environment_type, project_type, preferences
        """
        prompt = NLP_USER_PROMPT.format(
            user_input=user_input,
            hardware_context=hardware_context,
        )

        if callback:
            callback("[NLP] Understanding your request...")

        response = self._llm.chat_json(
            system_prompt=NLP_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if callback:
            if response.get("project_type"):
                callback(f"  -> Detected: {response['project_type']} project")
            if response.get("preferences", {}).get("cpu_only"):
                callback("  -> Detected: CPU-only preference")
            elif response.get("preferences", {}).get("gpu_optimized"):
                callback("  -> Detected: GPU-optimized mode")
            if response.get("reasoning"):
                callback(f"  -> {response['reasoning']}")

        # Enhance packages with web search if they seem generic
        packages = response.get("packages", [])
        if packages:
            enhanced_packages = self._enhance_with_search(
                user_input, packages, callback
            )
            response["packages"] = enhanced_packages

        return response

    def extract_packages(self, user_input: str) -> list[str]:
        """Extract just package names from user input."""
        result = self.extract(user_input)
        return self._parser.parse_packages(result)
