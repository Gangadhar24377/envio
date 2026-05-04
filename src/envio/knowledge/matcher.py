"""Keyword-based matcher for local package recipe resolution.

Uses token overlap scoring to find the best matching recipe(s)
for a user's natural language input, without any LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from envio.knowledge.recipes import PACKAGE_RECIPES

# Stopwords to ignore during matching
_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall",
    "can", "need", "want", "like", "using", "use", "set", "up",
    "setup", "create", "make", "build", "develop", "start", "new",
    "project", "environment", "env", "python", "pip", "install",
    "i", "me", "my", "we", "our", "you", "your", "it", "its",
    "that", "this", "some", "any", "all", "get", "put",
})


def _tokenize(text: str) -> set[str]:
    """Tokenize text into lowercase word tokens, removing stopwords."""
    words = re.findall(r"[a-z0-9]+(?:[-_.][a-z0-9]+)*", text.lower())
    return {w for w in words if w not in _STOPWORDS}


@dataclass
class MatchResult:
    """Result of a recipe match."""

    recipe_key: str
    score: float
    packages: list[str] = field(default_factory=list)


class RecipeMatcher:
    """Match user input to package recipes using token overlap scoring."""

    def __init__(
        self,
        recipes: dict[str, list[str]] | None = None,
    ) -> None:
        self._recipes = recipes or PACKAGE_RECIPES
        # Pre-tokenize all recipe keys
        self._tokenized_keys: dict[str, set[str]] = {
            key: _tokenize(key) for key in self._recipes
        }

    def match(
        self,
        user_input: str,
        top_k: int = 3,
        min_score: float = 0.3,
    ) -> list[MatchResult]:
        """Find best matching recipes for user input.

        Args:
            user_input: Natural language request
            top_k: Maximum number of results to return
            min_score: Minimum score threshold (0-1)

        Returns:
            Sorted list of MatchResults (best first)
        """
        input_tokens = _tokenize(user_input)
        if not input_tokens:
            return []

        results: list[MatchResult] = []

        for key, key_tokens in self._tokenized_keys.items():
            if not key_tokens:
                continue

            # Jaccard-like overlap score
            overlap = input_tokens & key_tokens
            if not overlap:
                continue

            # Score = overlap / min(len(input), len(key))
            # This favors exact matches while being flexible
            score = len(overlap) / min(len(input_tokens), len(key_tokens))

            # Bonus: if ALL key tokens are in input, boost score
            if key_tokens <= input_tokens:
                score = min(1.0, score * 1.5)

            if score >= min_score:
                results.append(MatchResult(
                    recipe_key=key,
                    score=score,
                    packages=self._recipes[key],
                ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def resolve(self, user_input: str) -> dict[str, Any]:
        """Resolve user input to packages using local recipes.

        This is the main entry point, returning a result dict
        compatible with NLPProcessor.extract() output.

        Args:
            user_input: Natural language request

        Returns:
            Dict with packages, project_type, preferences, reasoning
        """
        matches = self.match(user_input)

        if not matches:
            return {
                "packages": [],
                "project_type": "unknown",
                "environment_type": "uv",
                "preferences": {},
                "reasoning": "No matching recipe found in local knowledge base.",
            }

        # Merge packages from top matches, preserving order
        seen: set[str] = set()
        merged_packages: list[str] = []
        for m in matches:
            for pkg in m.packages:
                if pkg not in seen:
                    seen.add(pkg)
                    merged_packages.append(pkg)

        best = matches[0]
        recipe_names = ", ".join(m.recipe_key for m in matches)

        # Detect preferences from input
        input_lower = user_input.lower()
        preferences: dict[str, Any] = {
            "cpu_only": "cpu" in input_lower and "gpu" not in input_lower,
            "gpu_optimized": "gpu" in input_lower or "cuda" in input_lower,
        }

        return {
            "packages": merged_packages,
            "project_type": best.recipe_key,
            "environment_type": "uv",
            "preferences": preferences,
            "reasoning": (
                f"Matched local recipes: [{recipe_names}] "
                f"(best score: {best.score:.2f}). "
                f"No AI was used — results from built-in knowledge base."
            ),
        }
