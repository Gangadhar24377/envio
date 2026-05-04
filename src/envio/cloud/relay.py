"""Client-side relay to the Envio Cloud proxy.

Sends LLM requests to a Cloudflare Worker that holds the real
API key.  The user never sees or needs the key.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from envio import __version__
from envio.cloud.machine_id import get_machine_id

# Default proxy URL — update after deploying your Worker
DEFAULT_PROXY_URL = "https://envio-proxy.gangadharkambhamettu.workers.dev"


@dataclass
class RelayResponse:
    """Response from the cloud relay."""

    content: str
    model: str
    usage: dict[str, Any]
    error: str | None = None
    limit_reached: bool = False


class CloudRelay:
    """Client for the Envio Cloud LLM proxy."""

    def __init__(self, proxy_url: str | None = None, timeout: int = 60) -> None:
        self._proxy_url = (proxy_url or DEFAULT_PROXY_URL).rstrip("/")
        self._machine_id = get_machine_id()
        self._timeout = timeout

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> RelayResponse:
        """Send a chat completion through the cloud relay.

        Args:
            messages: List of {role, content} message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            RelayResponse with the model's reply or error info
        """
        payload = {
            "machine_id": self._machine_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            resp = requests.post(
                f"{self._proxy_url}/v1/chat",
                json=payload,
                headers={
                    "User-Agent": f"envio/{__version__}",
                    "Content-Type": "application/json",
                },
                timeout=self._timeout,
            )

            if resp.status_code == 429:
                data = resp.json()
                return RelayResponse(
                    content="",
                    model="",
                    usage={},
                    error=data.get("error", "Rate limit reached"),
                    limit_reached=True,
                )

            if resp.status_code != 200:
                return RelayResponse(
                    content="",
                    model="",
                    usage={},
                    error=f"Relay error: HTTP {resp.status_code}",
                )

            data = resp.json()

            # Parse OpenAI-compatible response format
            choices = data.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
            else:
                content = data.get("content", "")

            usage = data.get("usage", {})
            model = data.get("model", "cloud-relay")

            return RelayResponse(
                content=content,
                model=model,
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
            )

        except requests.exceptions.Timeout:
            return RelayResponse(
                content="",
                model="",
                usage={},
                error="Cloud relay timed out",
            )
        except requests.exceptions.ConnectionError:
            return RelayResponse(
                content="",
                model="",
                usage={},
                error="Could not reach cloud relay (no internet?)",
            )
        except Exception as e:
            return RelayResponse(
                content="",
                model="",
                usage={},
                error=f"Cloud relay error: {e}",
            )

    def is_available(self) -> bool:
        """Quick health check against the proxy."""
        try:
            resp = requests.get(
                f"{self._proxy_url}/health",
                headers={"User-Agent": f"envio/{__version__}"},
                timeout=5,
            )
            return resp.status_code == 200
        except Exception:
            return False
