"""LiteLLM client wrapper for multi-provider LLM support."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import litellm
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OLLAMA_MODEL = "llama3"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-sonnet-20240229",
    "together": "together-ai-7b",
    "cohere": "command",
    "replicate": "replicate-7b",
    "ollama": "llama3",
}


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
        """Create config from config file, environment variables, or auto-detection.

        Priority:
        1. Config file (~/.envio/config.json)
        2. Environment variables
        3. Auto-detection (Ollama)
        """
        from envio.config import get_api_key, get_model, get_provider, load_config

        config = load_config()

        # Try config file first
        api_key = get_api_key()
        provider = get_provider()
        model = get_model()

        # Get Ollama host from config or env
        ollama_host = config.get("ollama_host") or os.getenv(
            "ENVIO_OLLAMA_HOST", DEFAULT_OLLAMA_HOST
        )

        # Get temperature and max_tokens from env (or defaults)
        try:
            temperature = float(os.getenv("ENVIO_LLM_TEMPERATURE", "0"))
        except (ValueError, TypeError):
            temperature = 0.0
        try:
            max_tokens = int(os.getenv("ENVIO_LLM_MAX_TOKENS", "4096"))
        except (ValueError, TypeError):
            max_tokens = 4096

        # Handle Ollama (no API key needed)
        if provider == "ollama":
            ollama_available, available_models = _check_ollama(
                str(ollama_host) if ollama_host else DEFAULT_OLLAMA_HOST
            )
            if not ollama_available:
                raise ValueError(
                    "Ollama is not running. Please start Ollama or use a different provider:\n"
                    "  envio config api <your-key>"
                )

            # Validate model exists
            if model and model not in available_models:
                if available_models:
                    model = available_models[0]
                else:
                    raise ValueError(
                        "Ollama is running but no models found.\n"
                        "Please pull a model: ollama pull <model_name>"
                    )

            return cls(
                provider="ollama",
                model=model,
                api_base=ollama_host,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        # Handle API-based providers
        if not api_key:
            # Check environment variables as fallback
            openai_key = os.getenv("OPENAI_API_KEY")
            custom_api_key = os.getenv("ENVIO_LLM_API_KEY")
            api_key = custom_api_key or openai_key

            if api_key:
                # Determine provider from key
                if api_key.startswith("sk-ant-"):
                    provider = "anthropic"
                else:
                    provider = "openai"

                # Get model from env if not in config
                env_model = os.getenv("ENVIO_LLM_MODEL", "").strip()
                if not model:
                    model = env_model or DEFAULT_MODELS.get(
                        provider, DEFAULT_OPENAI_MODEL
                    )

        if not api_key:
            # Check if Ollama is available as fallback
            ollama_available, available_models = _check_ollama(
                str(ollama_host) if ollama_host else DEFAULT_OLLAMA_HOST
            )
            if ollama_available and available_models:
                return cls(
                    provider="ollama",
                    model=available_models[0],
                    api_base=ollama_host,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            raise ValueError(
                "No LLM provider configured. Please set one:\n"
                "  envio config api <your-api-key>  # For OpenAI, Anthropic, etc.\n"
                "  Or ensure Ollama is running with a model pulled"
            )

        # Build API base from config or env
        api_base = config.get("api_base") or os.getenv("ENVIO_LLM_API_BASE")

        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            api_base=api_base,
            temperature=temperature,
            max_tokens=max_tokens,
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        reraise=True,
    )
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
        # Check for API key
        if not self.config.api_key:
            raise ValueError(
                "No API key configured. Please set ENVIO_LLM_API_KEY or OPENAI_API_KEY"
            )

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
        from envio.llm.parser import ResponseParser

        response = self.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )

        return ResponseParser.extract_json(response.content)

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
