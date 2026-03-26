"""Tests for LLM ResponseParser."""

import pytest

from envio.llm.parser import ResponseParser


class TestResponseParser:
    """Tests for ResponseParser."""

    def test_parse_packages_from_list(self):
        """Test parsing packages from a list."""
        parser = ResponseParser()
        response = {"packages": ["numpy", "pandas", "scikit-learn"]}
        packages = parser.parse_packages(response)
        assert packages == ["numpy", "pandas", "scikit-learn"]

    def test_parse_packages_from_string(self):
        """Test parsing packages from a string - currently not supported."""
        parser = ResponseParser()
        response = {"packages": "numpy,pandas,scikit-learn"}
        packages = parser.parse_packages(response)
        # The parser expects a list, not a comma-separated string
        assert len(packages) == 0  # Will be empty because it's a string, not a list

    def test_parse_packages_empty(self):
        """Test parsing empty packages."""
        parser = ResponseParser()
        response = {}
        packages = parser.parse_packages(response)
        assert packages == []

    def test_parse_packages_with_version(self):
        """Test parsing packages with version info."""
        parser = ResponseParser()
        response = {"packages": [{"name": "numpy", "version": "1.24.0"}]}
        packages = parser.parse_packages(response)
        assert len(packages) == 1
        assert packages[0] == "numpy==1.24.0"

    def test_parse_packages_with_latest(self):
        """Test parsing packages with 'latest' version."""
        parser = ResponseParser()
        response = {"packages": [{"name": "numpy", "version": "latest"}]}
        packages = parser.parse_packages(response)
        assert len(packages) == 1
        assert packages[0] == "numpy"  # Should not include version for 'latest'

    def test_parse_warnings(self):
        """Test parsing warnings."""
        parser = ResponseParser()
        response = {"warnings": ["Warning 1", "Warning 2"]}
        warnings = parser.parse_warnings(response)
        assert len(warnings) == 2
        assert "Warning 1" in warnings

    def test_parse_warnings_empty(self):
        """Test parsing empty warnings."""
        parser = ResponseParser()
        response = {}
        warnings = parser.parse_warnings(response)
        assert warnings == []

    def test_extract_json_from_code_block(self):
        """Test extracting JSON from markdown code block."""
        parser = ResponseParser()
        text = '```json\n{"packages": ["numpy"]}\n```'
        result = parser.extract_json(text)
        assert result == {"packages": ["numpy"]}

    def test_extract_json_from_plain(self):
        """Test extracting JSON from plain text."""
        parser = ResponseParser()
        text = '{"packages": ["numpy"]}'
        result = parser.extract_json(text)
        assert result == {"packages": ["numpy"]}

    def test_extract_json_invalid(self):
        """Test extracting invalid JSON."""
        parser = ResponseParser()
        text = "not json"
        with pytest.raises(ValueError):
            parser.extract_json(text)

    def test_parse_commands(self):
        """Test parsing commands from response."""
        parser = ResponseParser()
        response = {"commands": ["pip install numpy", "pip install pandas"]}
        commands = parser.parse_commands(response)
        assert len(commands) == 2

    def test_parse_conflicts(self):
        """Test parsing conflicts from response."""
        parser = ResponseParser()
        response = {"conflicts": [{"package1": "numpy", "package2": "pandas"}]}
        conflicts = parser.parse_conflicts(response)
        assert len(conflicts) == 1

    def test_extract_packages_from_text(self):
        """Test extracting package names from free text."""
        parser = ResponseParser()
        text = "You should install numpy==1.24.0 and pandas>=2.0.0"
        packages = parser.extract_packages_from_text(text)
        assert "numpy==1.24.0" in packages
        assert "pandas" in packages
