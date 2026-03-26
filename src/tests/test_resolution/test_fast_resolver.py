"""Tests for FastResolver."""

import pytest
from unittest.mock import patch, MagicMock

from envio.resolution.fast_resolver import FastResolver, ResolutionStatus


class TestFastResolver:
    """Tests for FastResolver."""

    def test_resolve_success(self):
        """Test successful resolution."""
        resolver = FastResolver()
        with patch.object(resolver, "check_uv_available", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout="Successfully resolved", stderr=""
                )
                result = resolver.resolve(["numpy", "pandas"])
                assert result.is_success()
                assert result.status == ResolutionStatus.SUCCESS

    def test_resolve_conflict(self):
        """Test resolution with conflict."""
        resolver = FastResolver()
        with patch.object(resolver, "check_uv_available", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1,
                    stdout="",
                    stderr="conflict detected: numpy conflicts with pandas",
                )
                result = resolver.resolve(["numpy", "pandas"])
                assert result.has_conflicts()
                assert result.status == ResolutionStatus.CONFLICT

    def test_resolve_not_found(self):
        """Test resolution with package not found."""
        resolver = FastResolver()
        with patch.object(resolver, "check_uv_available", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1, stdout="", stderr="package not found: nonexistent"
                )
                result = resolver.resolve(["nonexistent"])
                assert result.status == ResolutionStatus.NOT_FOUND

    def test_resolve_uv_not_available(self):
        """Test resolution when uv is not available."""
        resolver = FastResolver()
        with patch.object(resolver, "check_uv_available", return_value=False):
            result = resolver.resolve(["numpy"])
            assert result.status == ResolutionStatus.ERROR

    def test_get_package_info(self):
        """Test getting package info."""
        resolver = FastResolver()
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "info": {
                    "name": "numpy",
                    "version": "1.24.0",
                    "summary": "Scientific computing",
                    "requires_python": ">=3.8",
                }
            }
            mock_get.return_value = mock_response
            info = resolver.get_package_info("numpy")
            assert info["name"] == "numpy"
            assert info["version"] == "1.24.0"

    def test_find_alternative(self):
        """Test finding alternative packages."""
        resolver = FastResolver()
        alternatives = resolver.find_alternative("requests")
        assert "httpx" in alternatives
        assert "aiohttp" in alternatives
