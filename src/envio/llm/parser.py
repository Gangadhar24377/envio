"""Response parser for LLM outputs."""

from __future__ import annotations

import json
import re
from typing import Any


class ResponseParser:
    """Parser for LLM responses."""

    @staticmethod
    def extract_json(text: str) -> dict[str, Any]:
        """Extract JSON from LLM response text.

        Handles responses wrapped in markdown code blocks or plain text.
        """
        text = text.strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 3:
                text = parts[1]

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Could not parse JSON from response: {e}") from None

    @staticmethod
    def parse_packages(response: dict[str, Any]) -> list[str]:
        """Extract package list from various response formats."""
        packages = []

        for key in [
            "packages",
            "resolved_packages",
            "suggested_packages",
            "fixed_packages",
        ]:
            raw = response.get(key, [])
            if raw:
                if isinstance(raw, list):
                    for pkg in raw:
                        if isinstance(pkg, str):
                            packages.append(pkg)
                        elif isinstance(pkg, dict):
                            name = pkg.get("name", "")
                            version = pkg.get("version", "")
                            if name:
                                if version and version != "latest":
                                    packages.append(f"{name}=={version}")
                                else:
                                    packages.append(name)
                break

        return packages

    @staticmethod
    def parse_commands(response: dict[str, Any]) -> list[str]:
        """Extract commands from response."""
        return response.get("commands", [])

    @staticmethod
    def parse_conflicts(response: dict[str, Any]) -> list[dict[str, str]]:
        """Extract conflict information from response."""
        conflicts = []
        raw = response.get("conflicts", [])

        for item in raw:
            if isinstance(item, str):
                conflicts.append({"reason": item})
            elif isinstance(item, dict):
                conflicts.append(item)

        return conflicts

    @staticmethod
    def parse_warnings(response: dict[str, Any]) -> list[str]:
        """Extract warnings from response."""
        return response.get("warnings", [])

    @staticmethod
    def extract_packages_from_text(text: str) -> list[str]:
        """Extract package names from free text."""
        pattern = r"([a-zA-Z0-9_\-]+)(?:==([0-9.]+))?"
        matches = re.findall(pattern, text)
        return [f"{m[0]}=={m[1]}" if m[1] else m[0] for m in matches]
