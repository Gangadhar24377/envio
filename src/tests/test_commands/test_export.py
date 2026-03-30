"""Tests for the export command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from click.testing import CliRunner

from envio.commands.export import (
    _generate_devcontainer_export,
    _generate_dockerfile_export,
    _generate_requirements_export,
    export,
)


class TestExportHelpers:
    """Tests for export helper functions."""

    def test_generate_requirements(self):
        """Test requirements.txt generation."""
        packages = [
            {"name": "requests", "version": "2.31.0"},
            {"name": "numpy", "version": "1.24.0"},
        ]
        content = _generate_requirements_export(packages, "0.3.1")
        assert "requests==2.31.0" in content
        assert "numpy==1.24.0" in content
        assert "envio 0.3.1" in content

    def test_generate_requirements_sorted(self):
        """Test that requirements are sorted alphabetically."""
        packages = [
            {"name": "zlib", "version": "1.0"},
            {"name": "aiohttp", "version": "3.8.0"},
        ]
        content = _generate_requirements_export(packages, "0.3.1")
        assert content.index("aiohttp") < content.index("zlib")

    def test_generate_dockerfile(self):
        """Test Dockerfile generation."""
        packages = [{"name": "flask", "version": "3.0.0"}]
        content = _generate_dockerfile_export(packages, "3.11.0", "0.3.1")
        assert "FROM python:3.11-slim" in content
        assert "flask==3.0.0" in content

    def test_generate_devcontainer(self):
        """Test devcontainer.json generation."""
        import json

        packages = [{"name": "flask", "version": "3.0.0"}]
        content = _generate_devcontainer_export(packages, "3.11.0", "myenv", "0.3.1")
        data = json.loads(content)
        assert data["name"] == "myenv"
        assert "flask==3.0.0" in data["postCreateCommand"]


class TestExportCommand:
    """Tests for envio export command."""

    def test_export_help(self):
        """Test that export --help works."""
        runner = CliRunner()
        result = runner.invoke(export, ["--help"])
        assert result.exit_code == 0
        assert "format" in result.output.lower()

    def test_export_env_not_found(self):
        """Test error when environment is not found."""
        runner = CliRunner()
        with (
            patch("envio.commands.export._load_dotenv"),
            patch("envio.commands.export._get_console") as mock_console,
            patch("envio.commands.export._find_environment") as mock_find,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_find.return_value = None
            result = runner.invoke(export, ["-n", "nonexistent"])
        assert result.exit_code == 0

    def test_export_requirements_format(self, tmp_path):
        """Test exporting in requirements format."""
        runner = CliRunner()
        fake_env_path = MagicMock()
        packages = [{"name": "flask", "version": "3.0.0"}]
        output_file = str(tmp_path / "requirements.txt")

        with (
            patch("envio.commands.export._load_dotenv"),
            patch("envio.commands.export._get_console") as mock_console,
            patch("envio.commands.export._find_environment") as mock_find,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
            patch("envio.commands.export._is_writable") as mock_writable,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_find.return_value = fake_env_path
            manager = MagicMock()
            manager.get_installed_packages_with_versions.return_value = (True, packages)
            mock_vem_cls.return_value = manager
            mock_writable.return_value = True
            result = runner.invoke(
                export, ["-n", "myenv", "--format", "requirements", "-o", output_file]
            )
        assert result.exit_code == 0
        console.print_success.assert_called()

    def test_export_no_packages(self):
        """Test export when no packages are installed."""
        runner = CliRunner()
        fake_env_path = MagicMock()

        with (
            patch("envio.commands.export._load_dotenv"),
            patch("envio.commands.export._get_console") as mock_console,
            patch("envio.commands.export._find_environment") as mock_find,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_find.return_value = fake_env_path
            manager = MagicMock()
            manager.get_installed_packages_with_versions.return_value = (True, [])
            mock_vem_cls.return_value = manager
            result = runner.invoke(export, ["-n", "myenv"])
        assert result.exit_code == 0
        console.print_warning.assert_called()

    def test_export_dockerfile_format(self, tmp_path):
        """Test exporting in dockerfile format."""
        runner = CliRunner()
        fake_env_path = MagicMock()
        packages = [{"name": "flask", "version": "3.0.0"}]
        output_file = str(tmp_path / "Dockerfile")

        with (
            patch("envio.commands.export._load_dotenv"),
            patch("envio.commands.export._get_console") as mock_console,
            patch("envio.commands.export._find_environment") as mock_find,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
            patch("envio.commands.export._is_writable") as mock_writable,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_find.return_value = fake_env_path
            manager = MagicMock()
            manager.get_installed_packages_with_versions.return_value = (True, packages)
            mock_vem_cls.return_value = manager
            mock_writable.return_value = True
            result = runner.invoke(
                export, ["-n", "myenv", "--format", "dockerfile", "-o", output_file]
            )
        assert result.exit_code == 0
        console.print_success.assert_called()
