"""Tests for CLI."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from envio.cli import cli
from envio.cli_helpers import _validate_and_normalize_packages


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
        validated = _validate_and_normalize_packages(packages, console)
        assert isinstance(validated, list)

    def test_validate_packages_empty(self):
        """Test validating empty packages list."""
        console = MagicMock()
        packages = []
        validated = _validate_and_normalize_packages(packages, console)
        assert validated == []

    def test_validate_packages_returns_list(self):
        """Test that validation returns a list."""
        console = MagicMock()
        packages = ["requests"]
        validated = _validate_and_normalize_packages(packages, console)
        assert isinstance(validated, list)

    def test_doctor_command(self):
        """Test doctor command."""
        runner = CliRunner()
        with patch("envio.cli_helpers._get_profiler") as mock_profiler:
            mock_profiler.return_value = MagicMock()
            result = runner.invoke(cli, ["doctor"])
            assert result.exit_code == 0
