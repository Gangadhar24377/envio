"""Tests for VersionInference."""

from unittest.mock import MagicMock, patch

from envio.analysis.version_inference import VersionInference, get_stdlib_modules


class TestVersionInference:
    """Tests for VersionInference."""

    def test_query_pypi_success(self):
        """Test querying PyPI for package info."""
        inference = VersionInference()
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "info": {"name": "numpy", "version": "1.24.0"},
                "releases": {"1.24.0": [], "1.23.0": []},
            }
            mock_get.return_value = mock_response
            data = inference.query_pypi("numpy")
            assert data is not None
            assert data["info"]["version"] == "1.24.0"

    def test_query_pypi_not_found(self):
        """Test querying PyPI for non-existent package."""
        inference = VersionInference()
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            data = inference.query_pypi("nonexistent")
            assert data is None

    def test_query_pypi_with_underscore(self):
        """Test querying PyPI with underscore in name."""
        inference = VersionInference()
        with patch.object(inference, "_query_pypi_name") as mock_query:
            # First call (original name) returns None
            # Second call (dashed name) returns data
            mock_query.side_effect = [
                None,
                {"info": {"name": "pydantic-settings", "version": "2.0.0"}},
            ]
            data = inference.query_pypi("pydantic_settings")
            assert data is not None
            assert mock_query.call_count == 2

    def test_get_available_versions(self):
        """Test getting available versions."""
        inference = VersionInference()
        with patch.object(inference, "query_pypi") as mock_query:
            mock_query.return_value = {
                "releases": {"1.24.0": [], "1.23.0": [], "1.22.0": []}
            }
            versions = inference.get_available_versions("numpy")
            assert len(versions) == 3
            assert "1.24.0" in versions

    def test_get_available_versions_empty(self):
        """Test getting versions for non-existent package."""
        inference = VersionInference()
        with patch.object(inference, "query_pypi", return_value=None):
            versions = inference.get_available_versions("nonexistent")
            assert versions == []

    def test_find_compatible_versions(self):
        """Test finding compatible versions."""
        inference = VersionInference()
        with patch.object(inference, "query_pypi") as mock_query:
            mock_query.return_value = {
                "info": {"name": "numpy", "version": "1.24.0"},
                "releases": {"1.24.0": [], "1.23.0": []},
            }
            result = inference.find_compatible_versions(["numpy"])
            assert "numpy" in result
            assert result["numpy"] == "1.24.0"

    def test_find_compatible_versions_skips_stdlib(self):
        """Test that stdlib modules are skipped."""
        inference = VersionInference()
        result = inference.find_compatible_versions(["os", "sys", "numpy"])
        # os and sys should be skipped, only numpy should be processed
        assert "os" not in result
        assert "sys" not in result

    def test_generate_requirements(self):
        """Test generating requirements.txt content."""
        inference = VersionInference()
        packages = {"numpy": "1.24.0", "pandas": "2.0.0", "requests": ""}
        requirements = inference.generate_requirements(packages)
        assert "numpy==1.24.0" in requirements
        assert "pandas==2.0.0" in requirements
        assert "requests" in requirements
        assert "requests==" not in requirements

    def test_get_older_versions(self):
        """Test getting older versions."""
        inference = VersionInference()
        versions = ["1.0.0", "2.0.0", "3.0.0", "4.0.0", "5.0.0"]
        older = inference._get_older_versions(versions, count=3)
        assert len(older) == 3
        assert "1.0.0" in older

    def test_get_stdlib_modules(self):
        """Test getting stdlib modules."""
        stdlib = get_stdlib_modules()
        assert "os" in stdlib
        assert "sys" in stdlib
        assert "json" in stdlib
