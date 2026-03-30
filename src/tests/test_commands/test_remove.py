"""Tests for the remove command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from envio.commands.remove import remove


class TestRemoveCommand:
    """Tests for envio remove command."""

    def test_remove_help(self):
        """Test that remove --help works."""
        runner = CliRunner()
        result = runner.invoke(remove, ["--help"])
        assert result.exit_code == 0

    def test_remove_requires_packages(self):
        """Test that remove without packages fails."""
        runner = CliRunner()
        result = runner.invoke(remove, ["-e", "myenv"])
        assert result.exit_code != 0

    def test_remove_no_env_no_path(self):
        """Test error when neither --env nor --path is given."""
        runner = CliRunner()
        with (
            patch("envio.commands.remove._load_dotenv"),
            patch("envio.commands.remove._get_console") as mock_console,
        ):
            console = MagicMock()
            mock_console.return_value = console
            result = runner.invoke(remove, ["numpy"])
        assert result.exit_code == 0
        console.print_error.assert_called_with("Please specify --env or --path")

    def test_remove_env_not_found(self):
        """Test error when environment does not exist."""
        runner = CliRunner()
        with (
            patch("envio.commands.remove._load_dotenv"),
            patch("envio.commands.remove._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
        ):
            console = MagicMock()
            mock_console.return_value = console
            manager = MagicMock()
            manager.exists.return_value = False
            mock_vem_cls.return_value = manager
            result = runner.invoke(remove, ["numpy", "-e", "nonexistent"])
        assert result.exit_code == 0
        console.print_error.assert_called()

    def test_remove_success(self):
        """Test successful package removal."""
        runner = CliRunner()
        with (
            patch("envio.commands.remove._load_dotenv"),
            patch("envio.commands.remove._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
        ):
            console = MagicMock()
            mock_console.return_value = console
            manager = MagicMock()
            manager.exists.return_value = True
            manager.uninstall_packages.return_value = (True, "", "")
            mock_vem_cls.return_value = manager
            result = runner.invoke(remove, ["numpy", "-e", "myenv", "-y"])
        assert result.exit_code == 0
        console.print_success.assert_called()

    def test_remove_failure(self):
        """Test that remove command reports failure."""
        runner = CliRunner()
        with (
            patch("envio.commands.remove._load_dotenv"),
            patch("envio.commands.remove._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
        ):
            console = MagicMock()
            mock_console.return_value = console
            manager = MagicMock()
            manager.exists.return_value = True
            manager.uninstall_packages.return_value = (
                False,
                "",
                "error: package not found",
            )
            mock_vem_cls.return_value = manager
            result = runner.invoke(remove, ["nonexistent-pkg", "-e", "myenv", "-y"])
        assert result.exit_code == 0
        console.print_error.assert_called_with("Failed to remove packages")

    def test_remove_prompts_confirmation(self):
        """Test that remove prompts for confirmation when -y not given."""
        runner = CliRunner()
        with (
            patch("envio.commands.remove._load_dotenv"),
            patch("envio.commands.remove._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
        ):
            console = MagicMock()
            mock_console.return_value = console
            manager = MagicMock()
            manager.exists.return_value = True
            manager.uninstall_packages.return_value = (True, "", "")
            mock_vem_cls.return_value = manager
            # Answer 'y' to the confirmation prompt
            result = runner.invoke(remove, ["numpy", "-e", "myenv"], input="y\n")
        assert result.exit_code == 0
        console.print_success.assert_called()

    def test_remove_aborts_on_no(self):
        """Test that remove aborts when user says no."""
        runner = CliRunner()
        with (
            patch("envio.commands.remove._load_dotenv"),
            patch("envio.commands.remove._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
        ):
            console = MagicMock()
            mock_console.return_value = console
            manager = MagicMock()
            manager.exists.return_value = True
            mock_vem_cls.return_value = manager
            result = runner.invoke(remove, ["numpy", "-e", "myenv"], input="n\n")
        assert result.exit_code == 0
        manager.uninstall_packages.assert_not_called()
        console.print_warning.assert_called()

    def test_remove_by_path(self):
        """Test remove with explicit --path flag."""
        runner = CliRunner()
        with (
            patch("envio.commands.remove._load_dotenv"),
            patch("envio.commands.remove._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
        ):
            console = MagicMock()
            mock_console.return_value = console
            manager = MagicMock()
            manager.exists.return_value = True
            manager.uninstall_packages.return_value = (True, "", "")
            mock_vem_cls.return_value = manager
            result = runner.invoke(remove, ["numpy", "-p", "/fake/envs/myenv", "-y"])
        assert result.exit_code == 0
        console.print_success.assert_called()
