"""AI query for pattern-to-Python-version mapping."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from envio.llm.client import LLMClient

from envio.utils.version_utils import _is_valid_version_string

_SYSTEM_PROMPT = """You are a Python syntax expert.
Given a Python syntax pattern name and description, return the minimum Python version that first introduced or supports this syntax.
Respond with ONLY valid JSON: {"min_version": "X.Y", "confidence": "high|medium|low"}
Use semantic versioning (e.g., "3.6", "3.8", "3.10").
If unsure, set confidence to "low"."""


_USER_PROMPT_TEMPLATE = """Pattern: {pattern_name}
Description: {description}
What is the minimum Python version that supports this syntax?"""


def query_ai_for_pattern(
    pattern_name: str,
    description: str,
    llm_client: LLMClient,
) -> dict[str, str] | None:
    """Query AI for a pattern's minimum Python version.

    Supports both OpenAI API and Ollama through LLMClient.

    Args:
        pattern_name: Name of the pattern (e.g., "f_string")
        description: Pattern description (e.g., "f-string (Python 3.6+)")
        llm_client: LLMClient instance (supports OpenAI or Ollama)

    Returns:
        Dict with min_python_version and confidence, or None on failure
    """
    try:
        user_prompt = _USER_PROMPT_TEMPLATE.format(
            pattern_name=pattern_name,
            description=description,
        )

        response = llm_client.chat_json(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.0,
        )

        min_version = response.get("min_version", "")
        confidence = response.get("confidence", "low")

        if not _is_valid_version_string(min_version):
            return None

        if confidence not in ("high", "medium", "low"):
            confidence = "low"

        return {
            "min_python_version": min_version,
            "confidence": confidence,
            "source": "ai",
        }

    except Exception:
        return None


def query_patterns_batch(
    patterns: list[dict[str, str]],
    llm_client: LLMClient,
) -> dict[str, dict[str, str]]:
    """Query AI for multiple patterns.

    Args:
        patterns: List of dicts with 'name' and 'description' keys
        llm_client: LLMClient instance

    Returns:
        Dict mapping pattern names to version info
    """
    results = {}

    for pattern_info in patterns:
        name = pattern_info.get("name", "")
        description = pattern_info.get("description", "")

        if not name:
            continue

        result = query_ai_for_pattern(name, description, llm_client)
        if result:
            results[name] = result

    return results
