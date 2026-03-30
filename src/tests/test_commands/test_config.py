"""Tests for the config command group."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from envio.commands.config import config


class TestConfigCommand:
    """Tests for envio config command group."""

    def test_config_help(self):
        """Test that config --help works."""
        runner = CliRunner()
        result = runner.invoke(config, ["--help"])
        assert result.exit_code == 0

    def test_config_show(self):
        """Test that config show calls show_config."""
        runner = CliRunner()
        with patch("envio.config.show_config") as mock_show:
            result = runner.invoke(config, ["show"])
        assert result.exit_code == 0
        mock_show.assert_called_once()

    def test_config_api_sets_key(self):
        """Test that config api saves the API key."""
        runner = CliRunner()
        with (
            patch("envio.config.detect_provider_from_key") as mock_detect,
            patch("envio.config.set_api_key") as mock_set_key,
            patch("envio.config.set_provider"),
        ):
            mock_detect.return_value = "openai"
            result = runner.invoke(config, ["api", "sk-test1234567890abcdef"])
        assert result.exit_code == 0
        mock_set_key.assert_called_once()

    def test_config_api_unknown_key_format(self):
        """Test config api with an unknown key format (requires user input)."""
        runner = CliRunner()
        with (
            patch("envio.config.detect_provider_from_key") as mock_detect,
            patch("envio.config.set_api_key") as mock_set_key,
            patch("envio.config.set_provider"),
            patch(
                "envio.config.AVAILABLE_PROVIDERS", ["openai", "anthropic", "ollama"]
            ),
        ):
            mock_detect.return_value = None
            # Provide "1" as input to select first provider
            result = runner.invoke(config, ["api", "unknown-key-format"], input="1\n")
        assert result.exit_code == 0
        mock_set_key.assert_called_once()

    def test_config_model(self):
        """Test that config model saves the model name."""
        runner = CliRunner()
        with (
            patch("envio.config.get_provider") as mock_get_provider,
            patch("envio.config.set_model") as mock_set_model,
        ):
            mock_get_provider.return_value = "openai"
            result = runner.invoke(config, ["model", "gpt-4o"])
        assert result.exit_code == 0
        mock_set_model.assert_called_once_with("gpt-4o")

    def test_config_set_default_envs_dir(self):
        """Test config set default_envs_dir."""
        runner = CliRunner()
        with patch("envio.config.set_default_envs_dir") as mock_set:
            result = runner.invoke(config, ["set", "default_envs_dir", "/tmp/envs"])
        assert result.exit_code == 0
        mock_set.assert_called_once_with("/tmp/envs")

    def test_config_set_preferred_package_manager(self):
        """Test config set preferred_package_manager."""
        runner = CliRunner()
        with patch("envio.config.set_preferred_package_manager") as mock_set:
            result = runner.invoke(config, ["set", "preferred_package_manager", "uv"])
        assert result.exit_code == 0
        mock_set.assert_called_once_with("uv")

    def test_config_set_unknown_key(self):
        """Test config set with unknown key prints error."""
        runner = CliRunner()
        result = runner.invoke(config, ["set", "unknown_key", "value"])
        assert result.exit_code == 0
        assert "unknown" in result.output.lower() or "Unknown" in result.output

    def test_config_unset_api(self):
        """Test config unset api clears the API key."""
        runner = CliRunner()
        with (
            patch("envio.config.load_config") as mock_load,
            patch("envio.config.save_config") as mock_save,
        ):
            mock_load.return_value = {"api_key": "sk-test", "provider": "openai"}
            result = runner.invoke(config, ["unset", "api"])
        assert result.exit_code == 0
        mock_save.assert_called_once()

    def test_config_unset_model(self):
        """Test config unset model clears the model."""
        runner = CliRunner()
        with (
            patch("envio.config.load_config") as mock_load,
            patch("envio.config.save_config") as mock_save,
        ):
            mock_load.return_value = {"model": "gpt-4o"}
            result = runner.invoke(config, ["unset", "model"])
        assert result.exit_code == 0
        mock_save.assert_called_once()

    def test_config_unset_not_set_key(self):
        """Test config unset a key that is not in config."""
        runner = CliRunner()
        with (
            patch("envio.config.load_config") as mock_load,
            patch("envio.config.save_config"),
        ):
            mock_load.return_value = {}
            result = runner.invoke(config, ["unset", "nonexistent"])
        assert result.exit_code == 0

    def test_config_serper_api(self):
        """Test config serper-api sets the serper API key."""
        runner = CliRunner()
        with patch("envio.config.set_serper_api_key") as mock_set:
            result = runner.invoke(config, ["serper-api", "serper-test-key-1234"])
        assert result.exit_code == 0
        mock_set.assert_called_once_with("serper-test-key-1234")
