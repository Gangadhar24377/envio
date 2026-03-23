"""NLP processor for extracting package information from user input."""

from __future__ import annotations

from typing import Any

from envio.llm.client import LLMClient, LLMConfig
from envio.llm.parser import ResponseParser
from envio.llm.prompts import NLP_SYSTEM_PROMPT, NLP_USER_PROMPT


class NLPProcessor:
    """Processor for natural language package extraction."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self._llm = LLMClient(config)
        self._parser = ResponseParser()

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

        return response

    def extract_packages(self, user_input: str) -> list[str]:
        """Extract just package names from user input."""
        result = self.extract(user_input)
        return self._parser.parse_packages(result)
