"""Tests for llm/client.py - LLM client wrapper."""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        from envio.llm.client import LLMConfig

        config = LLMConfig(provider="openai", model="gpt-4o")
        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.api_key is None
        assert config.api_base is None
        assert config.temperature == 0.0
        assert config.max_tokens == 4096
        assert config.timeout == 60

    def test_custom_values(self):
        """Test custom values can be set."""
        from envio.llm.client import LLMConfig

        config = LLMConfig(
            provider="anthropic",
            model="claude-3",
            api_key="sk-key",
            api_base="https://api.anthropic.com",
            temperature=0.5,
            max_tokens=2048,
            timeout=120,
        )
        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.timeout == 120


class TestDefaultModels:
    """Tests for DEFAULT_MODELS constant."""

    def test_all_providers_have_defaults(self):
        """All providers should have default models."""
        from envio.llm.client import DEFAULT_MODELS

        expected_providers = [
            "openai",
            "anthropic",
            "together",
            "cohere",
            "replicate",
            "ollama",
        ]
        for provider in expected_providers:
            assert provider in DEFAULT_MODELS
            assert DEFAULT_MODELS[provider]

    def test_openai_default(self):
        """OpenAI should have gpt-4o-mini as default."""
        from envio.llm.client import DEFAULT_MODELS

        assert DEFAULT_MODELS["openai"] == "gpt-4o-mini"


class TestOllamaDetection:
    """Tests for Ollama detection functions."""

    @patch("requests.get")
    def test_check_ollama_available(self, mock_get):
        """Test Ollama availability check when running."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3"},
                {"name": "mistral"},
            ]
        }
        mock_get.return_value = mock_response

        from envio.llm.client import _check_ollama

        available, models = _check_ollama("http://localhost:11434")
        assert available is True
        assert models == ["llama3", "mistral"]

    @patch("requests.get")
    def test_check_ollama_not_running(self, mock_get):
        """Test Ollama availability check when not running."""
        mock_get.side_effect = Exception("Connection refused")

        from envio.llm.client import _check_ollama

        available, models = _check_ollama("http://localhost:11434")
        assert available is False
        assert models == []

    @patch("requests.get")
    def test_check_ollama_no_models(self, mock_get):
        """Test Ollama availability check with no models."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_get.return_value = mock_response

        from envio.llm.client import _check_ollama

        available, models = _check_ollama("http://localhost:11434")
        assert available is True
        assert models == []


class TestIsOllamaAvailable:
    """Tests for is_ollama_available function."""

    @patch("envio.llm.client._check_ollama")
    def test_returns_true_when_available(self, mock_check):
        """Should return True when Ollama is available."""
        mock_check.return_value = (True, ["llama3"])

        from envio.llm.client import is_ollama_available

        result = is_ollama_available()
        assert result is True

    @patch("envio.llm.client._check_ollama")
    def test_returns_false_when_not_available(self, mock_check):
        """Should return False when Ollama is not available."""
        mock_check.return_value = (False, [])

        from envio.llm.client import is_ollama_available

        result = is_ollama_available()
        assert result is False


class TestListOllamaModels:
    """Tests for list_ollama_models function."""

    @patch("envio.llm.client._check_ollama")
    def test_returns_model_list(self, mock_check):
        """Should return list of available models."""
        mock_check.return_value = (True, ["llama3", "mistral", "codellama"])

        from envio.llm.client import list_ollama_models

        models = list_ollama_models()
        assert models == ["llama3", "mistral", "codellama"]

    @patch("envio.llm.client._check_ollama")
    def test_returns_empty_list_when_unavailable(self, mock_check):
        """Should return empty list when Ollama is not available."""
        mock_check.return_value = (False, [])

        from envio.llm.client import list_ollama_models

        models = list_ollama_models()
        assert models == []


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        from envio.llm.client import LLMResponse

        response = LLMResponse(
            content="Hello, world!",
            model="gpt-4o-mini",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
        )
        result = response.to_dict()

        assert result["content"] == "Hello, world!"
        assert result["model"] == "gpt-4o-mini"
        assert result["usage"]["prompt_tokens"] == 10
        assert result["usage"]["completion_tokens"] == 5


class TestLLMConfigFromEnv:
    """Tests for LLMConfig.from_env() class method."""

    @patch("envio.config.get_model", return_value="gpt-4o")
    @patch("envio.config.get_provider", return_value="openai")
    @patch("envio.config.get_api_key", return_value="sk-test-key")
    @patch("envio.config.load_config", return_value={})
    def test_from_env_with_openai_key(
        self, mock_load_config, mock_get_api_key, mock_get_provider, mock_get_model
    ):
        """Test creating config from environment with OpenAI key."""
        from envio.llm.client import LLMConfig

        config = LLMConfig.from_env()
        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.api_key == "sk-test-key"

    @patch("envio.llm.client._check_ollama", return_value=(True, ["llama3", "mistral"]))
    @patch("envio.config.get_model", return_value="llama3")
    @patch("envio.config.get_provider", return_value="ollama")
    @patch("envio.config.get_api_key", return_value=None)
    @patch("envio.config.load_config", return_value={})
    def test_from_env_with_ollama(
        self,
        mock_load_config,
        mock_get_api_key,
        mock_get_provider,
        mock_get_model,
        mock_check_ollama,
    ):
        """Test creating config from environment with Ollama."""
        from envio.llm.client import LLMConfig

        config = LLMConfig.from_env()
        assert config.provider == "ollama"
        assert "llama3" in config.model

    @patch("envio.llm.client._check_ollama", return_value=(False, []))
    @patch("envio.config.get_model", return_value="")
    @patch("envio.config.get_provider", return_value="openai")
    @patch("envio.config.get_api_key", return_value=None)
    @patch("envio.config.load_config", return_value={})
    def test_from_env_raises_when_no_provider(
        self,
        mock_load_config,
        mock_get_api_key,
        mock_get_provider,
        mock_get_model,
        mock_check_ollama,
    ):
        """Test that ValueError is raised when no provider is configured."""
        from envio.llm.client import LLMConfig

        # Patch out env vars so no API key bleeds in from the environment
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("ENVIO_LLM_API_KEY", None)
            with pytest.raises(ValueError, match="No LLM provider configured"):
                LLMConfig.from_env()
