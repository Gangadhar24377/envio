"""Tests for the install command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from envio.commands.install import install


class TestInstallCommand:
    """Tests for envio install command."""

    def test_install_help(self):
        """Test that install --help works."""
        runner = CliRunner()
        result = runner.invoke(install, ["--help"])
        assert result.exit_code == 0
        assert "packages" in result.output.lower() or "install" in result.output.lower()

    def test_install_requires_packages(self):
        """Test that install without packages fails."""
        runner = CliRunner()
        result = runner.invoke(install, [])
        assert result.exit_code != 0

    def test_install_invalid_package_manager(self):
        """Test that invalid package manager falls back to uv."""
        runner = CliRunner()
        with (
            patch("envio.commands.install._load_dotenv"),
            patch("envio.commands.install._get_console") as mock_console,
            patch("envio.commands.install._get_profiler") as mock_profiler,
            patch(
                "envio.commands.install._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.install._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            mock_validate.return_value = ["requests"]
            mock_install.return_value = True
            # Provide path and name via input
            result = runner.invoke(
                install,
                ["requests", "-e", "invalid_pm", "-p", "/tmp/envs", "-n", "myenv"],
                input="\n",
            )
        assert result.exit_code == 0
        console.print_warning.assert_any_call("Invalid: invalid_pm. Using uv.")

    def test_install_dry_run(self):
        """Test install with --dry-run flag."""
        runner = CliRunner()
        with (
            patch("envio.commands.install._load_dotenv"),
            patch("envio.commands.install._get_console") as mock_console,
            patch("envio.commands.install._get_profiler") as mock_profiler,
            patch(
                "envio.commands.install._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.install._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            mock_validate.return_value = ["flask"]
            mock_install.return_value = True
            result = runner.invoke(
                install,
                ["flask", "--dry-run", "-p", "/tmp/envs", "-n", "myenv"],
            )
        assert result.exit_code == 0
        _, kwargs = mock_install.call_args
        assert kwargs.get("dry_run") is True or mock_install.call_args[0][7] is True

    def test_install_skip_confirm(self):
        """Test install with -y flag skips confirmation."""
        runner = CliRunner()
        with (
            patch("envio.commands.install._load_dotenv"),
            patch("envio.commands.install._get_console") as mock_console,
            patch("envio.commands.install._get_profiler") as mock_profiler,
            patch(
                "envio.commands.install._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.install._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            mock_validate.return_value = ["flask"]
            mock_install.return_value = True
            result = runner.invoke(
                install, ["flask", "-y", "-p", "/tmp/envs", "-n", "myenv"]
            )
        assert result.exit_code == 0

    def test_install_invalid_path_traversal(self):
        """Test install rejects path traversal in env path."""
        runner = CliRunner()
        with (
            patch("envio.commands.install._load_dotenv"),
            patch("envio.commands.install._get_console") as mock_console,
            patch("envio.commands.install._get_profiler") as mock_profiler,
            patch(
                "envio.commands.install._validate_and_normalize_packages"
            ) as mock_validate,
        ):
            console = MagicMock()
            mock_console.return_value = console
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            mock_validate.return_value = ["flask"]
            result = runner.invoke(
                install, ["flask", "-p", "/tmp/../etc/shadow", "-n", "myenv"]
            )
        assert result.exit_code == 0
        console.print_error.assert_called()

    def test_install_cpu_only_flag(self):
        """Test install with --cpu-only flag adds preference."""
        runner = CliRunner()
        with (
            patch("envio.commands.install._load_dotenv"),
            patch("envio.commands.install._get_console") as mock_console,
            patch("envio.commands.install._get_profiler") as mock_profiler,
            patch(
                "envio.commands.install._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.install._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            mock_validate.return_value = ["torch"]
            mock_install.return_value = True
            result = runner.invoke(
                install, ["torch", "--cpu-only", "-p", "/tmp/envs", "-n", "myenv"]
            )
        assert result.exit_code == 0
        # Verify preferences has cpu_only=True
        call_kwargs = mock_install.call_args[1]
        assert call_kwargs.get("preferences", {}).get("cpu_only") is True
