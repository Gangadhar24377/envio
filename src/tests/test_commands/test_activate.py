"""Tests for the activate command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envio.commands.activate import activate


class TestActivateCommand:
    """Tests for envio activate command."""

    def test_activate_help(self):
        """Test that activate --help works."""
        runner = CliRunner()
        result = runner.invoke(activate, ["--help"])
        assert result.exit_code == 0
        assert "activation" in result.output.lower()

    def test_activate_no_env_no_path(self):
        """Test that missing --env and --path prints an error."""
        runner = CliRunner()
        with (
            patch("envio.commands.activate._load_dotenv"),
            patch("envio.commands.activate._get_console") as mock_console,
        ):
            console = MagicMock()
            mock_console.return_value = console
            result = runner.invoke(activate, [])
        assert result.exit_code == 0
        console.print_error.assert_called_once_with("Please specify --env or --path")

    def test_activate_env_not_found(self):
        """Test error when environment does not exist."""
        runner = CliRunner()
        with (
            patch("envio.commands.activate._load_dotenv"),
            patch("envio.commands.activate._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
        ):
            console = MagicMock()
            mock_console.return_value = console
            manager = MagicMock()
            manager.exists.return_value = False
            mock_vem_cls.return_value = manager
            result = runner.invoke(activate, ["--env", "nonexistent"])
        assert result.exit_code == 0
        console.print_error.assert_called()

    def test_activate_unix_path(self):
        """Test that activation shows bash/zsh command on non-Windows."""
        runner = CliRunner()
        fake_path = Path("/fake/envs/myenv")
        with (
            patch("envio.commands.activate._load_dotenv"),
            patch("envio.commands.activate._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
            patch("envio.core.system_profiler.SystemProfiler") as mock_profiler_cls,
        ):
            from envio.core.system_profiler import OSType

            console = MagicMock()
            mock_console.return_value = console
            manager = MagicMock()
            manager.exists.return_value = True
            mock_vem_cls.return_value = manager
            profiler_instance = MagicMock()
            profiler_instance.detect_os.return_value = OSType.LINUX
            mock_profiler_cls.return_value = profiler_instance
            result = runner.invoke(activate, ["--path", str(fake_path)])
        assert result.exit_code == 0
        # Should have called _safe_print with a source activate command
        calls = [str(c) for c in console._safe_print.call_args_list]
        assert any("activate" in c for c in calls)

    def test_activate_windows_path(self):
        """Test that activation shows PowerShell/CMD/Git Bash commands on Windows."""
        runner = CliRunner()
        fake_path = Path("/fake/envs/myenv")
        with (
            patch("envio.commands.activate._load_dotenv"),
            patch("envio.commands.activate._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
            patch("envio.core.system_profiler.SystemProfiler") as mock_profiler_cls,
        ):
            from envio.core.system_profiler import OSType

            console = MagicMock()
            mock_console.return_value = console
            manager = MagicMock()
            manager.exists.return_value = True
            mock_vem_cls.return_value = manager
            profiler_instance = MagicMock()
            profiler_instance.detect_os.return_value = OSType.WINDOWS
            mock_profiler_cls.return_value = profiler_instance
            result = runner.invoke(activate, ["--path", str(fake_path)])
        assert result.exit_code == 0
        info_calls = [str(c) for c in console.print_info.call_args_list]
        assert any("PowerShell" in c for c in info_calls)

    def test_activate_with_name_option(self):
        """Test activate with -n/--env name option."""
        runner = CliRunner()
        with (
            patch("envio.commands.activate._load_dotenv"),
            patch("envio.commands.activate._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
            patch("envio.core.system_profiler.SystemProfiler") as mock_profiler_cls,
        ):
            from envio.core.system_profiler import OSType

            console = MagicMock()
            mock_console.return_value = console
            manager = MagicMock()
            manager.exists.return_value = True
            mock_vem_cls.return_value = manager
            profiler_instance = MagicMock()
            profiler_instance.detect_os.return_value = OSType.LINUX
            mock_profiler_cls.return_value = profiler_instance
            result = runner.invoke(activate, ["-e", "myenv"])
        assert result.exit_code == 0
