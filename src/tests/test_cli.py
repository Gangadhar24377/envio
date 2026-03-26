"""Tests for CLI."""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from envio.cli import cli, _validate_packages


class TestCLI:
    """Tests for CLI."""

    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Envio" in result.output

    def test_cli_version(self):
        """Test CLI version output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

    def test_validate_packages_safe(self):
        """Test validating safe packages."""
        console = MagicMock()
        packages = ["numpy", "pandas", "scikit-learn"]
        validated = _validate_packages(packages, console)
        assert validated == packages

    def test_validate_packages_blocked(self):
        """Test validating blocked packages."""
        console = MagicMock()
        packages = ["litellm==1.82.7"]  # This should be blocked
        with pytest.raises(SystemExit):
            _validate_packages(packages, console)

    def test_validate_packages_safe_version(self):
        """Test validating safe version of litellm."""
        console = MagicMock()
        packages = ["litellm==1.82.6"]  # This should be allowed
        validated = _validate_packages(packages, console)
        assert "litellm==1.82.6" in validated

    def test_doctor_command(self):
        """Test doctor command."""
        runner = CliRunner()
        with patch("envio.cli._get_profiler") as mock_profiler:
            mock_profiler.return_value = MagicMock()
            result = runner.invoke(cli, ["doctor"])
            assert result.exit_code == 0
