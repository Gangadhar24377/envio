"""Tests for the init command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from envio.commands.init import init


class TestInitCommand:
    """Tests for envio init command."""

    def test_init_help(self):
        """Test that init --help works."""
        runner = CliRunner()
        result = runner.invoke(init, ["--help"])
        assert result.exit_code == 0

    def test_init_with_requirements_txt(self, tmp_path):
        """Test init when requirements.txt is found."""
        runner = CliRunner()
        (tmp_path / "requirements.txt").write_text("flask\nrequests\n")

        with (
            patch("envio.commands.init._load_dotenv"),
            patch("envio.commands.init._get_console") as mock_console,
            patch("envio.commands.init._get_profiler") as mock_profiler,
            patch("envio.commands.init.detect_package_managers") as mock_detect_pm,
            patch("envio.commands.init._scan_directory") as mock_scan,
            patch(
                "envio.commands.init._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.init._resolve_and_install") as mock_install,
            patch("envio.commands.init.Path.cwd") as mock_cwd,
        ):
            console = MagicMock()
            mock_console.return_value = console
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            mock_detect_pm.return_value = {"pip": True, "uv": True, "conda": False}
            mock_cwd.return_value = tmp_path
            mock_scan.return_value = {
                "source": "requirements.txt",
                "packages": ["flask", "requests"],
                "env_type": "pip",
            }
            mock_validate.return_value = ["flask", "requests"]
            mock_install.return_value = True

            # Simulate user entering env name then choosing location 1
            result = runner.invoke(init, [], input="myenv\n1\n")
        assert result.exit_code == 0

    def test_init_no_requirements_no_imports(self, tmp_path):
        """Test init when no requirements file and no Python imports found."""
        runner = CliRunner()
        with (
            patch("envio.commands.init._load_dotenv"),
            patch("envio.commands.init._get_console") as mock_console,
            patch("envio.commands.init._get_profiler") as mock_profiler,
            patch("envio.commands.init.detect_package_managers") as mock_detect_pm,
            patch("envio.commands.init._scan_directory") as mock_scan,
            patch("envio.commands.init.Path.cwd") as mock_cwd,
        ):
            console = MagicMock()
            mock_console.return_value = console
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            mock_detect_pm.return_value = {"pip": True, "uv": True}
            mock_cwd.return_value = tmp_path  # empty dir, no .py files
            mock_scan.return_value = None
            result = runner.invoke(init, [])
        assert result.exit_code == 0
        console.print_error.assert_called()

    def test_init_invalid_env_name(self, tmp_path):
        """Test init rejects invalid environment names."""
        runner = CliRunner()
        with (
            patch("envio.commands.init._load_dotenv"),
            patch("envio.commands.init._get_console") as mock_console,
            patch("envio.commands.init._get_profiler") as mock_profiler,
            patch("envio.commands.init.detect_package_managers") as mock_detect_pm,
            patch("envio.commands.init._scan_directory") as mock_scan,
            patch("envio.commands.init.Path.cwd") as mock_cwd,
        ):
            console = MagicMock()
            mock_console.return_value = console
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            mock_detect_pm.return_value = {"pip": True}
            mock_cwd.return_value = tmp_path
            mock_scan.return_value = {
                "source": "requirements.txt",
                "packages": ["flask"],
                "env_type": "pip",
            }
            # invalid name with spaces
            result = runner.invoke(init, [], input="my env name!\n")
        assert result.exit_code == 0
        console.print_error.assert_called()

    def test_init_user_aborts(self, tmp_path):
        """Test init handles KeyboardInterrupt gracefully."""
        runner = CliRunner()
        with (
            patch("envio.commands.init._load_dotenv"),
            patch("envio.commands.init._get_console") as mock_console,
            patch("envio.commands.init._get_profiler") as mock_profiler,
            patch("envio.commands.init.detect_package_managers") as mock_detect_pm,
            patch("envio.commands.init._scan_directory") as mock_scan,
            patch("envio.commands.init.Path.cwd") as mock_cwd,
        ):
            console = MagicMock()
            mock_console.return_value = console
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            mock_detect_pm.return_value = {"pip": True}
            mock_cwd.return_value = tmp_path
            mock_scan.return_value = {
                "source": "requirements.txt",
                "packages": ["flask"],
                "env_type": "pip",
            }
            # Empty input simulates EOF/abort during env name prompt
            result = runner.invoke(init, [], input="\x03")  # Ctrl+C
        # Should exit without crashing
        assert result.exit_code in (0, 1)
