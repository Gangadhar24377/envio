"""Tests for the list_envs command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from envio.commands.list_envs import list_envs


class TestListEnvsCommand:
    """Tests for envio list command."""

    def test_list_help(self):
        """Test that list --help works."""
        runner = CliRunner()
        result = runner.invoke(list_envs, ["--help"])
        assert result.exit_code == 0

    def test_list_empty_registry(self):
        """Test that list shows message when no environments registered."""
        runner = CliRunner()
        with (
            patch("envio.commands.list_envs._load_dotenv"),
            patch("envio.commands.list_envs._get_console") as mock_console,
            patch("envio.core.registry.EnvironmentRegistry") as mock_reg_cls,
        ):
            console = MagicMock()
            mock_console.return_value = console
            registry = MagicMock()
            registry.list_all.return_value = []
            mock_reg_cls.return_value = registry
            result = runner.invoke(list_envs, [])
        assert result.exit_code == 0
        console.print_info.assert_any_call("No environments created by envio yet.")

    def test_list_with_environments(self, tmp_path):
        """Test that list displays registered environments."""
        runner = CliRunner()
        fake_env_path = str(tmp_path / "myenv")
        (tmp_path / "myenv").mkdir()

        envs = [
            {
                "name": "myenv",
                "path": fake_env_path,
                "packages": ["flask", "requests"],
                "manager": "uv",
                "created_at": "2024-01-15T10:00:00",
                "command": "envio install flask requests",
            }
        ]

        with (
            patch("envio.commands.list_envs._load_dotenv"),
            patch("envio.commands.list_envs._get_console") as mock_console,
            patch("envio.core.registry.EnvironmentRegistry") as mock_reg_cls,
        ):
            console = MagicMock()
            mock_console.return_value = console
            registry = MagicMock()
            registry.list_all.return_value = envs
            mock_reg_cls.return_value = registry
            result = runner.invoke(list_envs, [])
        assert result.exit_code == 0
        console._safe_print.assert_called()

    def test_list_missing_environment(self, tmp_path):
        """Test list marks environments whose paths no longer exist."""
        runner = CliRunner()
        envs = [
            {
                "name": "ghost-env",
                "path": "/nonexistent/path/ghost-env",
                "packages": ["numpy"],
                "manager": "pip",
                "created_at": "2023-06-01T12:00:00",
                "command": "envio install numpy",
            }
        ]

        with (
            patch("envio.commands.list_envs._load_dotenv"),
            patch("envio.commands.list_envs._get_console") as mock_console,
            patch("envio.core.registry.EnvironmentRegistry") as mock_reg_cls,
        ):
            console = MagicMock()
            mock_console.return_value = console
            registry = MagicMock()
            registry.list_all.return_value = envs
            mock_reg_cls.return_value = registry
            result = runner.invoke(list_envs, [])
        assert result.exit_code == 0
        # The table should be printed with the (missing) label
        console._safe_print.assert_called()

    def test_list_registry_exception(self):
        """Test list handles registry exceptions gracefully."""
        runner = CliRunner()
        with (
            patch("envio.commands.list_envs._load_dotenv"),
            patch("envio.commands.list_envs._get_console") as mock_console,
            patch("envio.core.registry.EnvironmentRegistry") as mock_reg_cls,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_reg_cls.side_effect = RuntimeError("registry error")
            result = runner.invoke(list_envs, [])
        assert result.exit_code == 0
        console.print_error.assert_called()

    def test_list_verbose_flag(self):
        """Test that list accepts -v/--verbose flag."""
        runner = CliRunner()
        with (
            patch("envio.commands.list_envs._load_dotenv"),
            patch("envio.commands.list_envs._get_console") as mock_console,
            patch("envio.core.registry.EnvironmentRegistry") as mock_reg_cls,
        ):
            console = MagicMock()
            mock_console.return_value = console
            registry = MagicMock()
            registry.list_all.return_value = []
            mock_reg_cls.return_value = registry
            result = runner.invoke(list_envs, ["--verbose"])
        assert result.exit_code == 0
        mock_console.assert_called_once_with(True)
