"""LiteLLM client wrapper for multi-provider LLM support."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import litellm

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OLLAMA_MODEL = "llama3"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"


@dataclass
class LLMConfig:
    """Configuration for LLM client."""

    provider: str
    model: str
    api_key: str | None = None
    api_base: str | None = None
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout: int = 60

    @classmethod
    def from_env(cls) -> LLMConfig:
        """Create config from environment variables with auto-detection."""
        openai_key = os.getenv("OPENAI_API_KEY")
        custom_api_key = os.getenv("ENVIO_LLM_API_KEY")
        env_model = os.getenv("ENVIO_LLM_MODEL", "").strip()
        ollama_host = os.getenv("ENVIO_OLLAMA_HOST", DEFAULT_OLLAMA_HOST)

        ollama_available, available_models = _check_ollama(ollama_host)

        if openai_key or custom_api_key:
            provider = "openai"
            model = env_model if env_model else DEFAULT_OPENAI_MODEL
            return cls(
                provider=provider,
                model=model,
                api_key=custom_api_key or openai_key,
                api_base=os.getenv("ENVIO_LLM_API_BASE"),
                temperature=float(os.getenv("ENVIO_LLM_TEMPERATURE", "0")),
                max_tokens=int(os.getenv("ENVIO_LLM_MAX_TOKENS", "4096")),
            )

        if ollama_available:
            provider = "ollama"
            if env_model:
                model = env_model
            elif available_models:
                model = (
                    DEFAULT_OLLAMA_MODEL
                    if DEFAULT_OLLAMA_MODEL in available_models
                    else available_models[0]
                )
            else:
                raise ValueError(
                    "Ollama is running but no models found. "
                    "Please pull a model: ollama pull <model_name>"
                )
            return cls(
                provider=provider,
                model=model,
                api_base=ollama_host,
                temperature=float(os.getenv("ENVIO_LLM_TEMPERATURE", "0")),
                max_tokens=int(os.getenv("ENVIO_LLM_MAX_TOKENS", "4096")),
            )

        raise ValueError(
            f"No LLM provider available. Please set one of:\n"
            f"  - OPENAI_API_KEY in .env (recommended: {DEFAULT_OPENAI_MODEL})\n"
            f"  - Or ensure Ollama is running with a model pulled"
        )


def _check_ollama(host: str) -> tuple[bool, list[str]]:
    """Check if Ollama is running and list available models."""
    try:
        import requests

        response = requests.get(f"{host}/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return True, [m["name"] for m in models]
    except Exception:
        pass
    return False, []


def list_ollama_models(host: str = DEFAULT_OLLAMA_HOST) -> list[str]:
    """List available Ollama models."""
    _, models = _check_ollama(host)
    return models


def is_ollama_available(host: str = DEFAULT_OLLAMA_HOST) -> bool:
    """Check if Ollama is running."""
    available, _ = _check_ollama(host)
    return available


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
        self._setup_provider()

    def _setup_provider(self) -> None:
        """Configure the model for the detected provider."""
        if self.config.provider == "ollama":
            self.config.model = f"ollama/{self.config.model}"

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
