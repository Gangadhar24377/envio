"""LiteLLM client wrapper for multi-provider LLM support."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import litellm


@dataclass
class LLMConfig:
    """Configuration for LLM client."""

    model: str = "gpt-4o-mini"
    api_key: str | None = None
    api_base: str | None = None
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout: int = 60

    @classmethod
    def from_env(cls) -> LLMConfig:
        """Create config from environment variables."""
        return cls(
            model=os.getenv("ENVIO_LLM_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("ENVIO_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
            api_base=os.getenv("ENVIO_LLM_API_BASE"),
            temperature=float(os.getenv("ENVIO_LLM_TEMPERATURE", "0")),
            max_tokens=int(os.getenv("ENVIO_LLM_MAX_TOKENS", "4096")),
        )


@dataclass
class LLMResponse:
    """Response from LLM."""

    content: str
    model: str
    usage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
        }


class LLMClient:
    """LiteLLM wrapper for multi-provider LLM support."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig.from_env()
        litellm.suppress_debug_info = True

    def chat(
        self,
        system_prompt: str | None = None,
        user_prompt: str = "",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Send a chat completion request.

        Args:
            system_prompt: System message for context
            user_prompt: User message content
            temperature: Override temperature (uses config default if None)
            max_tokens: Override max_tokens (uses config default if None)

        Returns:
            LLMResponse with the model's reply
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature
            if temperature is not None
            else self.config.temperature,
            "max_tokens": max_tokens
            if max_tokens is not None
            else self.config.max_tokens,
            "timeout": self.config.timeout,
        }

        if self.config.api_key:
            kwargs["api_key"] = self.config.api_key

        if self.config.api_base:
            kwargs["api_base"] = self.config.api_base

        response = litellm.completion(**kwargs)

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens
                if response.usage
                else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
        )

    def chat_json(
        self,
        system_prompt: str | None = None,
        user_prompt: str = "",
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Send a chat request expecting JSON response.

        Args:
            system_prompt: System message
            user_prompt: User message
            temperature: Override temperature

        Returns:
            Parsed JSON dictionary
        """
        response = self.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )

        return self._extract_json(response.content)

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from response text."""
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        text = text.strip()
        return json.loads(text)

    @staticmethod
    def list_providers() -> list[str]:
        """List supported LLM providers."""
        return [
            "openai",
            "anthropic",
            "azure",
            "google",
            "ollama",
            "local",
            "cohere",
            "mistral",
        ]

    @staticmethod
    def validate_model(model: str) -> bool:
        """Validate if a model string is supported."""
        try:
            litellm.supports_completion(model=model)
            return True
        except Exception:
            return False
