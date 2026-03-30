"""Tests for cli_helpers module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from envio.cli_helpers import (
    _ENV_NAME_RE,
    _is_conda_active,
    _is_writable,
    _parse_nlp_result,
    _scan_directory,
    _validate_path,
    detect_package_managers,
    get_hardware_context,
)


class TestValidatePath:
    """Tests for _validate_path."""

    def test_valid_absolute_path(self):
        assert _validate_path("/home/user/envs") is True

    def test_valid_relative_path(self):
        assert _validate_path("envs/myenv") is True

    def test_path_traversal_blocked(self):
        assert _validate_path("/home/user/../etc/shadow") is False

    def test_path_traversal_windows_style(self):
        assert _validate_path("C:\\Users\\..\\secret") is False

    def test_empty_path(self):
        assert _validate_path("") is False

    def test_null_byte(self):
        assert _validate_path("/home/user\x00/secret") is False


class TestIsWritable:
    """Tests for _is_writable."""

    def test_existing_writable_dir(self, tmp_path):
        assert _is_writable(tmp_path) is True

    def test_nonexistent_path_writable_parent(self, tmp_path):
        new_file = tmp_path / "newfile.txt"
        assert _is_writable(new_file) is True

    def test_nonexistent_path_nonexistent_parent(self):
        path = Path("/nonexistent/deep/path/file.txt")
        assert _is_writable(path) is False


class TestEnvNameRegex:
    """Tests for _ENV_NAME_RE pattern."""

    def test_valid_name_alphanumeric(self):
        assert _ENV_NAME_RE.match("myenv123") is not None

    def test_valid_name_with_hyphen(self):
        assert _ENV_NAME_RE.match("my-env") is not None

    def test_valid_name_with_underscore(self):
        assert _ENV_NAME_RE.match("my_env") is not None

    def test_valid_name_with_dot(self):
        assert _ENV_NAME_RE.match(".venv") is not None

    def test_invalid_name_with_space(self):
        assert _ENV_NAME_RE.match("my env") is None

    def test_invalid_name_with_slash(self):
        assert _ENV_NAME_RE.match("my/env") is None

    def test_invalid_name_with_bang(self):
        assert _ENV_NAME_RE.match("my!env") is None


class TestDetectPackageManagers:
    """Tests for detect_package_managers."""

    def test_returns_dict_with_keys(self):
        with patch("envio.cli_helpers.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/pip"
            result = detect_package_managers()
        assert "pip" in result
        assert "conda" in result
        assert "uv" in result

    def test_pip_found(self):
        with (
            patch("envio.cli_helpers.shutil.which") as mock_which,
            patch("envio.cli_helpers._is_conda_active") as mock_conda,
        ):
            mock_which.side_effect = lambda cmd: (
                "/usr/bin/pip" if cmd == "pip" else None
            )
            mock_conda.return_value = False
            result = detect_package_managers()
        assert result["pip"] is True
        assert result["uv"] is False

    def test_nothing_found(self):
        with (
            patch("envio.cli_helpers.shutil.which") as mock_which,
            patch("envio.cli_helpers._is_conda_active") as mock_conda,
        ):
            mock_which.return_value = None
            mock_conda.return_value = False
            result = detect_package_managers()
        assert all(not v for v in result.values())


class TestIsCondaActive:
    """Tests for _is_conda_active."""

    def test_conda_active_via_prefix(self, monkeypatch):
        monkeypatch.setenv("CONDA_PREFIX", "/opt/conda/envs/myenv")
        monkeypatch.delenv("CONDA_DEFAULT_ENV", raising=False)
        assert _is_conda_active() is True

    def test_conda_active_via_env(self, monkeypatch):
        monkeypatch.delenv("CONDA_PREFIX", raising=False)
        monkeypatch.setenv("CONDA_DEFAULT_ENV", "myenv")
        assert _is_conda_active() is True

    def test_conda_not_active(self, monkeypatch):
        monkeypatch.delenv("CONDA_PREFIX", raising=False)
        monkeypatch.delenv("CONDA_DEFAULT_ENV", raising=False)
        assert _is_conda_active() is False


class TestGetHardwareContext:
    """Tests for get_hardware_context."""

    def test_with_gpu(self):
        profile = MagicMock()
        profile.gpu.available = True
        profile.gpu.name = "NVIDIA RTX 4090"
        profile.gpu.vram_mb = 24576
        profile.gpu.cuda_version = "12.4"
        result = get_hardware_context(profile)
        assert "NVIDIA RTX 4090" in result
        assert "24576" in result
        assert "12.4" in result

    def test_cpu_only(self):
        profile = MagicMock()
        profile.gpu.available = False
        result = get_hardware_context(profile)
        assert "CPU-only" in result


class TestParseNlpResult:
    """Tests for _parse_nlp_result."""

    def test_parses_packages(self):
        with patch("envio.cli_helpers._get_response_parser") as mock_parser_fn:
            parser = MagicMock()
            parser.parse_packages.return_value = ["flask", "sqlalchemy"]
            mock_parser_fn.return_value = parser
            result = {"environment_type": "pip", "preferences": {"cpu_only": True}}
            packages, env_type, prefs = _parse_nlp_result(result)
        assert packages == ["flask", "sqlalchemy"]
        assert env_type == "pip"
        assert prefs == {"cpu_only": True}

    def test_defaults_to_uv_for_invalid_env_type(self):
        with patch("envio.cli_helpers._get_response_parser") as mock_parser_fn:
            parser = MagicMock()
            parser.parse_packages.return_value = []
            mock_parser_fn.return_value = parser
            result = {"environment_type": "unknown_pm", "preferences": {}}
            _, env_type, _ = _parse_nlp_result(result)
        assert env_type == "uv"

    def test_missing_env_type_defaults_to_uv(self):
        with patch("envio.cli_helpers._get_response_parser") as mock_parser_fn:
            parser = MagicMock()
            parser.parse_packages.return_value = []
            mock_parser_fn.return_value = parser
            result = {}
            _, env_type, _ = _parse_nlp_result(result)
        assert env_type == "uv"


class TestScanDirectory:
    """Tests for _scan_directory."""

    def test_detects_requirements_txt(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("flask\nrequests\n")
        result = _scan_directory(tmp_path)
        assert result is not None
        assert result["source"] == "requirements.txt"
        assert "flask" in result["packages"]
        assert "requests" in result["packages"]

    def test_detects_pyproject_toml(self, tmp_path):
        toml = tmp_path / "pyproject.toml"
        toml.write_text('[project]\ndependencies = ["flask>=3.0", "requests"]\n')
        result = _scan_directory(tmp_path)
        assert result is not None
        assert result["source"] == "pyproject.toml"

    def test_returns_none_when_nothing_found(self, tmp_path):
        result = _scan_directory(tmp_path)
        assert result is None

    def test_requirements_takes_priority_over_pyproject(self, tmp_path):
        """requirements.txt is listed first and should be preferred."""
        (tmp_path / "requirements.txt").write_text("flask\n")
        (tmp_path / "pyproject.toml").write_text(
            '[project]\ndependencies = ["django"]\n'
        )
        result = _scan_directory(tmp_path)
        assert result["source"] == "requirements.txt"
