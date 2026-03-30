"""Tests for the doctor command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from envio.commands.doctor import doctor


class TestDoctorCommand:
    """Tests for envio doctor command."""

    def test_doctor_help(self):
        """Test that doctor --help works."""
        runner = CliRunner()
        result = runner.invoke(doctor, ["--help"])
        assert result.exit_code == 0
        assert "hardware" in result.output.lower() or "system" in result.output.lower()

    def test_doctor_runs_profiler(self):
        """Test that doctor calls the system profiler."""
        runner = CliRunner()
        with (
            patch("envio.commands.doctor._load_dotenv"),
            patch("envio.commands.doctor._get_console") as mock_console,
            patch("envio.commands.doctor._get_profiler") as mock_get_profiler,
            patch("envio.commands.doctor.detect_package_managers") as mock_detect_pm,
            patch("envio.config.get_api_key") as mock_api_key,
            patch("envio.config.get_model") as mock_get_model,
        ):
            console = MagicMock()
            mock_console.return_value = console
            profiler = MagicMock()
            profile = MagicMock()
            profile.gpu = MagicMock()
            profile.gpu.available = False
            profiler.profile.return_value = profile
            mock_get_profiler.return_value = profiler
            mock_detect_pm.return_value = {"pip": True, "conda": False, "uv": True}
            mock_api_key.return_value = "sk-test"
            mock_get_model.return_value = "gpt-4o"
            result = runner.invoke(doctor, [])
        assert result.exit_code == 0
        profiler.profile.assert_called_once()

    def test_doctor_no_api_key(self):
        """Test that doctor shows API key not set when missing."""
        runner = CliRunner()
        with (
            patch("envio.commands.doctor._load_dotenv"),
            patch("envio.commands.doctor._get_console") as mock_console,
            patch("envio.commands.doctor._get_profiler") as mock_get_profiler,
            patch("envio.commands.doctor.detect_package_managers") as mock_detect_pm,
            patch("envio.config.get_api_key") as mock_api_key,
            patch("envio.config.get_model") as mock_get_model,
        ):
            console = MagicMock()
            mock_console.return_value = console
            profiler = MagicMock()
            profile = MagicMock()
            profile.gpu = MagicMock()
            profile.gpu.available = False
            profiler.profile.return_value = profile
            mock_get_profiler.return_value = profiler
            mock_detect_pm.return_value = {"pip": True, "conda": False, "uv": False}
            mock_api_key.return_value = None
            mock_get_model.return_value = "gpt-4o"
            result = runner.invoke(doctor, [])
        assert result.exit_code == 0
        safe_print_calls = [str(c) for c in console._safe_print.call_args_list]
        assert any("not set" in c for c in safe_print_calls)

    def test_doctor_verbose_flag(self):
        """Test that doctor accepts -v/--verbose flag."""
        runner = CliRunner()
        with (
            patch("envio.commands.doctor._load_dotenv"),
            patch("envio.commands.doctor._get_console") as mock_console,
            patch("envio.commands.doctor._get_profiler") as mock_get_profiler,
            patch("envio.commands.doctor.detect_package_managers") as mock_detect_pm,
            patch("envio.config.get_api_key") as mock_api_key,
            patch("envio.config.get_model") as mock_get_model,
        ):
            console = MagicMock()
            mock_console.return_value = console
            profiler = MagicMock()
            profile = MagicMock()
            profile.gpu = MagicMock()
            profile.gpu.available = False
            profiler.profile.return_value = profile
            mock_get_profiler.return_value = profiler
            mock_detect_pm.return_value = {}
            mock_api_key.return_value = "key"
            mock_get_model.return_value = "gpt-4o"
            result = runner.invoke(doctor, ["--verbose"])
        assert result.exit_code == 0
        mock_console.assert_called_once_with(True)

    def test_doctor_exception_handling(self):
        """Test that doctor handles exceptions gracefully."""
        runner = CliRunner()
        with (
            patch("envio.commands.doctor._load_dotenv"),
            patch("envio.commands.doctor._get_console") as mock_console,
            patch("envio.commands.doctor._get_profiler") as mock_get_profiler,
        ):
            console = MagicMock()
            mock_console.return_value = console
            profiler = MagicMock()
            profiler.profile.side_effect = RuntimeError("hardware detection failed")
            mock_get_profiler.return_value = profiler
            result = runner.invoke(doctor, [])
        assert result.exit_code == 0
        console.print_error.assert_called()
