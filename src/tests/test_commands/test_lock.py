"""Tests for the lock command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from envio.commands.lock import lock


class TestLockCommand:
    """Tests for envio lock command."""

    def test_lock_help(self):
        """Test that lock --help works."""
        runner = CliRunner()
        result = runner.invoke(lock, ["--help"])
        assert result.exit_code == 0
        assert "lockfile" in result.output.lower()

    def test_lock_env_not_found(self):
        """Test error when environment does not exist."""
        runner = CliRunner()
        with (
            patch("envio.commands.lock._load_dotenv"),
            patch("envio.commands.lock._get_console") as mock_console,
            patch("envio.commands.lock.EnvironmentRegistry") as mock_reg_cls,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
            patch("envio.commands.lock.get_default_envs_dir") as mock_default_dir,
        ):
            console = MagicMock()
            mock_console.return_value = console
            registry = MagicMock()
            registry.get.return_value = None
            mock_reg_cls.return_value = registry
            manager = MagicMock()
            manager.exists.return_value = False
            mock_vem_cls.return_value = manager
            mock_default_dir.return_value = (None, False)
            # Simulate user entering a nonexistent path
            result = runner.invoke(
                lock, ["-n", "ghost-env"], input="/nonexistent/path\n"
            )
        assert result.exit_code == 0
        console.print_error.assert_called()

    def test_lock_no_packages(self):
        """Test lock when no packages are installed."""
        runner = CliRunner()
        fake_env = MagicMock(spec=Path)
        fake_env.name = "myenv"
        fake_env.__str__ = lambda s: "/fake/envs/myenv"

        with (
            patch("envio.commands.lock._load_dotenv"),
            patch("envio.commands.lock._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
            patch("envio.commands.lock._get_profiler") as mock_profiler,
        ):
            console = MagicMock()
            mock_console.return_value = console
            manager = MagicMock()
            manager.exists.return_value = True
            manager.get_installed_packages_with_versions.return_value = (True, [])
            mock_vem_cls.return_value = manager
            profiler = MagicMock()
            mock_profiler.return_value = profiler
            result = runner.invoke(lock, ["-p", "/fake/envs/myenv"])
        assert result.exit_code == 0
        console.print_warning.assert_called()

    def test_lock_generates_json(self, tmp_path):
        """Test lock generates valid JSON lockfile."""
        runner = CliRunner()
        output_file = str(tmp_path / "envio.lock")
        packages = [
            {"name": "flask", "version": "3.0.0"},
            {"name": "requests", "version": "2.31.0"},
        ]

        with (
            patch("envio.commands.lock._load_dotenv"),
            patch("envio.commands.lock._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
            patch("envio.commands.lock._get_profiler") as mock_profiler,
            patch("envio.commands.lock._is_writable") as mock_writable,
        ):
            console = MagicMock()
            mock_console.return_value = console
            manager = MagicMock()
            manager.exists.return_value = True
            manager.get_installed_packages_with_versions.return_value = (True, packages)
            mock_vem_cls.return_value = manager
            profiler_instance = MagicMock()
            profile = MagicMock()
            profile.gpu.available = False
            profiler_instance.profile.return_value = profile
            mock_profiler.return_value = profiler_instance
            mock_writable.return_value = True
            result = runner.invoke(lock, ["-p", "/fake/env", "-o", output_file])
        assert result.exit_code == 0
        console.print_success.assert_called()
        import json

        with open(output_file) as f:
            data = json.load(f)
        assert data["version"] == "1.0"
        assert len(data["packages"]) == 2

    def test_lock_generates_text_format(self, tmp_path):
        """Test lock generates text lockfile."""
        runner = CliRunner()
        output_file = str(tmp_path / "envio.lock")
        packages = [{"name": "flask", "version": "3.0.0"}]

        with (
            patch("envio.commands.lock._load_dotenv"),
            patch("envio.commands.lock._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
            patch("envio.commands.lock._get_profiler") as mock_profiler,
            patch("envio.commands.lock._is_writable") as mock_writable,
        ):
            console = MagicMock()
            mock_console.return_value = console
            manager = MagicMock()
            manager.exists.return_value = True
            manager.get_installed_packages_with_versions.return_value = (True, packages)
            mock_vem_cls.return_value = manager
            profiler_instance = MagicMock()
            profile = MagicMock()
            profile.gpu.available = False
            profiler_instance.profile.return_value = profile
            mock_profiler.return_value = profiler_instance
            mock_writable.return_value = True
            result = runner.invoke(
                lock, ["-p", "/fake/env", "--format", "text", "-o", output_file]
            )
        assert result.exit_code == 0
        with open(output_file) as f:
            content = f.read()
        assert "flask==3.0.0" in content

    def test_lock_does_not_overwrite_without_confirm(self, tmp_path):
        """Test lock does not overwrite existing file when user says no."""
        runner = CliRunner()
        output_file = tmp_path / "envio.lock"
        output_file.write_text("existing content")
        packages = [{"name": "flask", "version": "3.0.0"}]

        with (
            patch("envio.commands.lock._load_dotenv"),
            patch("envio.commands.lock._get_console") as mock_console,
            patch("envio.core.virtualenv_manager.VirtualEnvManager") as mock_vem_cls,
            patch("envio.commands.lock._get_profiler") as mock_profiler,
        ):
            console = MagicMock()
            mock_console.return_value = console
            console.confirm.return_value = False
            manager = MagicMock()
            manager.exists.return_value = True
            manager.get_installed_packages_with_versions.return_value = (True, packages)
            mock_vem_cls.return_value = manager
            profiler_instance = MagicMock()
            profile = MagicMock()
            profile.gpu.available = False
            profiler_instance.profile.return_value = profile
            mock_profiler.return_value = profiler_instance
            result = runner.invoke(lock, ["-p", "/fake/env", "-o", str(output_file)])
        assert result.exit_code == 0
        # File should still have old content
        assert output_file.read_text() == "existing content"
        console.print_warning.assert_called()
