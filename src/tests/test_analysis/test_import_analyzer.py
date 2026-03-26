"""Tests for ImportAnalyzer."""

import pytest
from pathlib import Path

from envio.analysis.import_analyzer import ImportAnalyzer, get_stdlib_modules


class TestImportAnalyzer:
    """Tests for ImportAnalyzer."""

    def test_scan_directory(self, tmp_path):
        """Test scanning directory for imports."""
        analyzer = ImportAnalyzer()
        test_file = tmp_path / "test.py"
        test_file.write_text("import numpy\nimport pandas\n")
        result = analyzer.scan_directory(tmp_path)
        assert "third_party" in result
        assert "numpy" in result["third_party"]
        assert "pandas" in result["third_party"]

    def test_categorize_imports(self):
        """Test categorizing imports into stdlib and third-party."""
        analyzer = ImportAnalyzer()
        imports = {"os", "sys", "numpy", "pandas", "json"}
        result = analyzer.categorize_imports(imports)
        assert "stdlib" in result
        assert "third_party" in result
        assert "os" in result["stdlib"]
        assert "sys" in result["stdlib"]
        assert "json" in result["stdlib"]
        assert "numpy" in result["third_party"]
        assert "pandas" in result["third_party"]

    def test_parse_file(self, tmp_path):
        """Test parsing imports from a file."""
        analyzer = ImportAnalyzer()
        test_file = tmp_path / "test.py"
        test_file.write_text("import numpy\nimport pandas\n")
        imports = analyzer.parse_file(test_file)
        assert "numpy" in imports
        assert "pandas" in imports

    def test_is_virtual_environment(self, tmp_path):
        """Test checking if path is inside a virtual environment."""
        analyzer = ImportAnalyzer()
        # Create a venv-like structure
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "pyvenv.cfg").touch()

        # Path inside venv should be detected
        test_file = venv_dir / "test.py"
        test_file.write_text("import numpy")
        assert analyzer.is_virtual_environment(test_file) is True

        # Path outside venv should not be detected
        outside_file = tmp_path / "test.py"
        outside_file.write_text("import numpy")
        assert analyzer.is_virtual_environment(outside_file) is False

    def test_should_scan_file(self, tmp_path):
        """Test deciding whether to scan a file."""
        analyzer = ImportAnalyzer()
        test_file = tmp_path / "test.py"
        test_file.write_text("import numpy")
        assert analyzer.should_scan_file(test_file) is True

    def test_is_local_module(self, tmp_path):
        """Test checking if module is local."""
        analyzer = ImportAnalyzer()
        # Create a local module
        local_module = tmp_path / "mymodule.py"
        local_module.write_text("# Local module")
        assert analyzer.is_local_module("mymodule", tmp_path) is True
        assert analyzer.is_local_module("nonexistent", tmp_path) is False

    def test_extract_package_name(self):
        """Test extracting package name from import."""
        analyzer = ImportAnalyzer()
        assert analyzer.extract_package_name("numpy") == "numpy"
        assert analyzer.extract_package_name("numpy.core") == "numpy"
        assert analyzer.extract_package_name("openai.types.chat") == "openai"

    def test_get_stdlib_modules(self):
        """Test getting stdlib modules dynamically."""
        stdlib = get_stdlib_modules()
        assert "os" in stdlib
        assert "sys" in stdlib
        assert "json" in stdlib
        assert "numpy" not in stdlib
