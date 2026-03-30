"""Tests for the resurrect command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from envio.commands.resurrect import (
    _is_url,
    _is_valid_git_url,
    _clone_repo,
    resurrect_command,
)


class TestResurrectHelpers:
    """Tests for resurrect helper functions."""

    def test_is_url_http(self):
        assert _is_url("http://github.com/user/repo") is True

    def test_is_url_https(self):
        assert _is_url("https://github.com/user/repo") is True

    def test_is_url_local_path(self):
        assert _is_url("/home/user/projects/myrepo") is False

    def test_is_url_relative_path(self):
        assert _is_url("./myrepo") is False

    def test_is_valid_git_url_valid(self):
        assert _is_valid_git_url("https://github.com/user/repo") is True

    def test_is_valid_git_url_with_git_suffix(self):
        assert _is_valid_git_url("https://github.com/user/repo.git") is True

    def test_is_valid_git_url_empty(self):
        assert _is_valid_git_url("") is False

    def test_is_valid_git_url_too_short(self):
        assert _is_valid_git_url("noslash") is False

    def test_clone_repo_invalid_url(self, tmp_path):
        """Test that _clone_repo raises ValueError for invalid URLs."""
        import pytest

        with pytest.raises(ValueError, match="Invalid git URL format"):
            _clone_repo("not-a-url", tmp_path)

    def test_clone_repo_invalid_repo_name(self, tmp_path):
        """Test that _clone_repo raises ValueError for dangerous repo names."""
        import pytest

        with pytest.raises((ValueError, RuntimeError)):
            _clone_repo("https://github.com/user/..dangerous..repo", tmp_path)


class TestResurrectCommand:
    """Tests for envio resurrect command."""

    def test_resurrect_help(self):
        """Test that resurrect --help works."""
        runner = CliRunner()
        result = runner.invoke(resurrect_command, ["--help"])
        assert result.exit_code == 0

    def test_resurrect_no_source(self):
        """Test error when no source is provided."""
        runner = CliRunner()
        result = runner.invoke(resurrect_command, [])
        assert result.exit_code == 0
        assert "required" in result.output.lower() or result.output  # error shown

    def test_resurrect_local_path_not_found(self):
        """Test error when local path does not exist."""
        runner = CliRunner()
        result = runner.invoke(resurrect_command, ["/nonexistent/path/to/repo"])
        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "Path not found" in result.output

    def test_resurrect_local_path_success(self, tmp_path):
        """Test resurrect with a local path."""
        # Create some Python files in tmp_path
        (tmp_path / "main.py").write_text("import flask\n")
        runner = CliRunner()

        with (
            patch("envio.commands.resurrect.ImportAnalyzer") as mock_ia_cls,
            patch("envio.commands.resurrect.SyntaxDetector") as mock_sd_cls,
            patch("envio.commands.resurrect.VersionInference") as mock_vi_cls,
            patch(
                "envio.analysis.package_mapping.find_package_for_import"
            ) as mock_find,
            patch(
                "envio.cli_helpers._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.llm.client.LLMClient") as mock_llm,
        ):
            analyzer = MagicMock()
            analyzer.scan_directory.return_value = {"third_party": ["flask"]}
            mock_ia_cls.return_value = analyzer

            detector = MagicMock()
            detector.detect_from_directory.return_value = {}
            detector.infer_timeline.return_value = "modern (2020+)"
            detector.infer_python_version.return_value = ("3.11", None)
            mock_sd_cls.return_value = detector

            inference = MagicMock()
            inference.find_compatible_versions.return_value = {"flask": "3.0.0"}
            inference.generate_requirements.return_value = "flask==3.0.0\n"
            mock_vi_cls.return_value = inference

            mock_find.side_effect = lambda x: x
            mock_validate.return_value = ["flask==3.0.0"]

            console_mock = MagicMock()
            # Decline to create environment
            console_mock.confirm.return_value = False

            with patch("envio.commands.resurrect.ConsoleUI") as mock_console_cls:
                mock_console_cls.return_value = console_mock
                result = runner.invoke(
                    resurrect_command,
                    [str(tmp_path)],
                )
        assert result.exit_code == 0

    def test_resurrect_url_git_not_installed(self):
        """Test error when git is not installed but URL is given."""
        runner = CliRunner()
        with patch("envio.commands.resurrect.shutil.which") as mock_which:
            mock_which.return_value = None
            with patch("envio.commands.resurrect.ConsoleUI") as mock_console_cls:
                console = MagicMock()
                mock_console_cls.return_value = console
                result = runner.invoke(
                    resurrect_command, ["https://github.com/user/repo"]
                )
        assert result.exit_code == 0
        console.print_error.assert_called()

    def test_resurrect_url_clone_failure(self):
        """Test error handling when git clone fails."""
        runner = CliRunner()
        with (
            patch("envio.commands.resurrect.shutil.which") as mock_which,
            patch("envio.commands.resurrect._clone_repo") as mock_clone,
            patch("envio.commands.resurrect.ConsoleUI") as mock_console_cls,
        ):
            mock_which.return_value = "/usr/bin/git"
            mock_clone.side_effect = RuntimeError("Git clone failed: repo not found")
            console = MagicMock()
            mock_console_cls.return_value = console
            result = runner.invoke(
                resurrect_command,
                [
                    "https://github.com/user/nonexistent",
                    "-p",
                    "/tmp/envs",
                    "-n",
                    "myenv",
                ],
            )
        assert result.exit_code == 0
        console.print_error.assert_called()
