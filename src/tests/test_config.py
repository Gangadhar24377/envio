"""Tests for config.py - configuration management."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from envio import config


@pytest.fixture
def temp_config_dir(monkeypatch):
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        monkeypatch.setattr(config, "get_config_dir", lambda: tmp_path)
        yield tmp_path


class TestDetectProviderFromKey:
    """Tests for detect_provider_from_key function."""

    def test_openai_key_detected(self):
        """OpenAI keys (sk-) should be detected."""
        assert config.detect_provider_from_key("sk-abc123") == "openai"

    def test_anthropic_key_detected(self):
        """Anthropic keys (sk-ant-) should be detected."""
        assert config.detect_provider_from_key("sk-ant-abc123") == "anthropic"

    def test_empty_key_returns_ollama(self):
        """Empty key should return 'ollama'."""
        assert config.detect_provider_from_key("") == "ollama"

    def test_none_key_returns_ollama(self):
        """None key should return 'ollama'."""
        assert config.detect_provider_from_key(None) == "ollama"

    def test_unknown_key_returns_none(self):
        """Unknown key format should return None."""
        assert config.detect_provider_from_key("unknown-key") is None


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_empty_config(self, temp_config_dir):
        """Loading non-existent config should return empty dict."""
        result = config.load_config()
        assert result == {}

    def test_load_existing_config(self, temp_config_dir):
        """Loading existing config should return parsed JSON."""
        config_path = temp_config_dir / "config.json"
        test_data = {"provider": "openai", "model": "gpt-4o"}
        config_path.write_text(json.dumps(test_data))

        result = config.load_config()
        assert result == test_data

    def test_load_invalid_json(self, temp_config_dir):
        """Loading invalid JSON should return empty dict."""
        config_path = temp_config_dir / "config.json"
        config_path.write_text("invalid json {")

        result = config.load_config()
        assert result == {}


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_config(self, temp_config_dir):
        """Saving config should write JSON to file."""
        test_data = {"provider": "openai", "model": "gpt-4o"}
        config.save_config(test_data)

        config_path = temp_config_dir / "config.json"
        assert config_path.exists()

        with open(config_path) as f:
            result = json.load(f)
        assert result == test_data

    def test_save_creates_directory(self, temp_config_dir):
        """Saving config should create parent directory if needed."""
        nested_dir = temp_config_dir / "nested" / "dir"
        test_data = {"key": "value"}

        with patch.object(config, "get_config_dir", return_value=nested_dir):
            config.save_config(test_data)

        assert nested_dir.exists()
        assert (nested_dir / "config.json").exists()


class TestSetApiKey:
    """Tests for set_api_key function."""

    def test_set_openai_key(self, temp_config_dir):
        """Setting OpenAI key should auto-detect provider."""
        result = config.set_api_key("sk-test-key-12345")
        assert result == "openai"

        cfg = config.load_config()
        assert cfg["api_key"] == "sk-test-key-12345"
        assert cfg["provider"] == "openai"

    def test_set_key_with_explicit_provider(self, temp_config_dir):
        """Setting key with explicit provider should use it."""
        result = config.set_api_key("my-key", provider="anthropic")
        assert result == "anthropic"

        cfg = config.load_config()
        assert cfg["provider"] == "anthropic"

    def test_set_empty_key(self, temp_config_dir):
        """Setting empty key should configure for Ollama."""
        result = config.set_api_key("")
        assert result == "ollama"

        cfg = config.load_config()
        assert cfg["api_key"] == ""
        assert cfg["provider"] == "ollama"


class TestSetModel:
    """Tests for set_model function."""

    def test_set_model(self, temp_config_dir):
        """Setting model should save to config."""
        config.set_model("gpt-4o")

        cfg = config.load_config()
        assert cfg["model"] == "gpt-4o"


class TestSetProvider:
    """Tests for set_provider function."""

    def test_set_valid_provider(self, temp_config_dir):
        """Setting valid provider should save to config."""
        config.set_provider("anthropic")

        cfg = config.load_config()
        assert cfg["provider"] == "anthropic"

    def test_set_invalid_provider(self, temp_config_dir):
        """Setting invalid provider should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            config.set_provider("invalid-provider")


class TestGetApiKey:
    """Tests for get_api_key function."""

    def test_get_from_config(self, temp_config_dir):
        """Getting API key should return from config."""
        config.set_api_key("sk-test-key")
        key = config.get_api_key()
        assert key == "sk-test-key"

    def test_get_from_env(self, temp_config_dir):
        """Getting API key when not in config should return None."""
        key = config.get_api_key()
        assert key is None


class TestGetProvider:
    """Tests for get_provider function."""

    def test_get_from_config(self, temp_config_dir):
        """Getting provider should return from config."""
        config.set_provider("anthropic")
        provider = config.get_provider()
        assert provider == "anthropic"

    def test_get_default_openai(self, temp_config_dir):
        """Getting provider with no config should return 'openai' as default."""
        with patch("envio.llm.client.is_ollama_available", return_value=False):
            provider = config.get_provider()
        assert provider == "openai"


class TestGetModel:
    """Tests for get_model function."""

    def test_get_from_config(self, temp_config_dir):
        """Getting model should return from config."""
        config.set_model("gpt-4o")
        model = config.get_model()
        assert model == "gpt-4o"

    def test_get_default_for_provider(self, temp_config_dir):
        """Getting model with no config should return default for provider."""
        config.set_provider("openai")
        model = config.get_model()
        assert model == "gpt-4o-mini"


class TestDefaultModels:
    """Tests for DEFAULT_MODELS constant."""

    def test_all_providers_have_defaults(self):
        """All providers should have default models."""
        for provider in config.AVAILABLE_PROVIDERS:
            assert provider in config.DEFAULT_MODELS

    def test_openai_default(self):
        """OpenAI should have gpt-4o-mini as default."""
        assert config.DEFAULT_MODELS["openai"] == "gpt-4o-mini"

    def test_ollama_default(self):
        """Ollama should have llama3 as default."""
        assert config.DEFAULT_MODELS["ollama"] == "llama3"


class TestGetConfigPath:
    """Tests for get_config_path function."""

    def test_returns_config_json(self, temp_config_dir):
        """Config path should end with config.json."""
        with patch.object(config, "get_config_dir", return_value=temp_config_dir):
            path = config.get_config_path()
            assert path.name == "config.json"
            assert path.parent == temp_config_dir
