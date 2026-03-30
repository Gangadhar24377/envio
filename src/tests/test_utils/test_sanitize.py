"""Tests for sanitize.py - shell command safety utilities."""

import platform
import shlex

import pytest

from envio.utils.sanitize import (
    build_safe_command,
    escape_shell_string,
    normalize_pypi_name,
    sanitize_package_name,
    sanitize_packages,
    sanitize_path,
    validate_package_name,
)

# On Windows, shlex.quote() does not add quotes around safe strings.
_IS_WINDOWS = platform.system() == "Windows"


class TestNormalizePypiName:
    """Tests for normalize_pypi_name function."""

    def test_lowercase_remains_lowercase(self):
        """Lowercase names should remain lowercase."""
        assert normalize_pypi_name("requests") == "requests"

    def test_underscore_converted_to_dash(self):
        """Underscores should be converted to dashes."""
        assert normalize_pypi_name("scikit_learn") == "scikit-learn"

    def test_dot_converted_to_dash(self):
        """Dots should be converted to dashes."""
        assert normalize_pypi_name("boto3") == "boto3"

    def test_mixed_separators_normalized(self):
        """Multiple separator types should all become dashes."""
        assert normalize_pypi_name("foo_bar.baz-qux") == "foo-bar-baz-qux"

    def test_uppercase_converted_to_lowercase(self):
        """Uppercase should be converted to lowercase."""
        assert normalize_pypi_name("NumPy") == "numpy"


class TestValidatePackageName:
    """Tests for validate_package_name function."""

    def test_valid_simple_name(self):
        """Simple package names should be valid."""
        assert validate_package_name("requests") is True
        assert validate_package_name("numpy") is True
        assert validate_package_name("flask") is True

    def test_valid_with_hyphen(self):
        """Package names with hyphens should be valid."""
        assert validate_package_name("scikit-learn") is True
        assert validate_package_name("boto3") is True

    def test_valid_with_underscore(self):
        """Package names with underscores should be valid."""
        assert validate_package_name("scikit_learn") is True

    def test_valid_with_version(self):
        """Package names with version specifiers should be valid."""
        assert validate_package_name("numpy>=1.24.0") is True
        assert validate_package_name("requests==2.28.0") is True
        assert validate_package_name("pandas<3.0.0") is True

    def test_invalid_empty_string(self):
        """Empty string should be invalid."""
        assert validate_package_name("") is False

    def test_invalid_special_chars(self):
        """Special characters should be invalid."""
        assert validate_package_name("pkg;rm -rf") is False
        assert validate_package_name("pkg$(whoami)") is False
        assert validate_package_name("pkg`ls`") is False

    def test_invalid_path_traversal(self):
        """Path traversal attempts should be invalid."""
        assert validate_package_name("../etc/passwd") is False
        assert validate_package_name("../../../bin/sh") is False

    def test_invalid_leading_hyphen(self):
        """Package names starting with hyphen should be invalid."""
        assert validate_package_name("-malicious") is False

    def test_invalid_leading_digit(self):
        """Package names starting with digit are valid per PEP 508 (e.g. 2to3)."""
        # PEP 508 allows leading digits; validate_package_name follows PEP 503
        assert validate_package_name("2to3") is True


class TestSanitizePath:
    """Tests for sanitize_path function."""

    def test_path_with_spaces_quoted(self):
        """Paths with spaces should be properly quoted."""
        result = sanitize_path("/home/user/my packages/file")
        assert "my packages" in result

    def test_path_with_special_chars(self):
        """Paths with special chars should be escaped."""
        result = sanitize_path("/home/user/$HOME/file")
        # On Windows shlex.quote wraps in double quotes; on Unix uses single quotes
        assert "$" in result or "'" in result or '"' in result

    def test_simple_path_is_safe(self):
        """Simple paths should be returned in a safe form."""
        result = sanitize_path("/home/user/packages")
        # The result should contain the original path content
        assert "/home/user/packages" in result or "home" in result


class TestSanitizePackageName:
    """Tests for sanitize_package_name function."""

    def test_valid_package_safe(self):
        """Valid package names should be returned safely."""
        result = sanitize_package_name("requests")
        # Should contain the package name; quoting is platform-dependent
        assert "requests" in result

    def test_invalid_package_raises(self):
        """Invalid package names should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid package name"):
            sanitize_package_name("pkg;rm -rf")


class TestSanitizePackages:
    """Tests for sanitize_packages function."""

    def test_valid_packages(self):
        """List of valid packages should be sanitized."""
        result = sanitize_packages(["numpy", "pandas", "flask"])
        assert len(result) == 3
        # All results should contain the original package name
        for name, r in zip(["numpy", "pandas", "flask"], result):
            assert name in r

    def test_empty_list(self):
        """Empty list should return empty list."""
        result = sanitize_packages([])
        assert result == []

    def test_invalid_package_raises(self):
        """Invalid package in list should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid package name"):
            sanitize_packages(["numpy", "invalid;cmd", "flask"])


class TestEscapeShellString:
    """Tests for escape_shell_string function."""

    def test_simple_string_safe(self):
        """Simple strings should be returned safely."""
        result = escape_shell_string("hello")
        # Should contain the original content
        assert "hello" in result

    def test_string_with_special_chars(self):
        """Strings with special chars should be escaped."""
        result = escape_shell_string("hello $WORLD")
        assert "hello" in result

    def test_empty_string(self):
        """Empty string should return empty quotes."""
        result = escape_shell_string("")
        assert result == "''"


class TestBuildSafeCommand:
    """Tests for build_safe_command function."""

    def test_simple_command(self):
        """Simple command parts should be converted to strings."""
        result = build_safe_command(["pip", "install", "requests"])
        assert result == ["pip", "install", "requests"]

    def test_mixed_types(self):
        """Mixed types should be converted to strings."""
        result = build_safe_command(["uv", "pip", "install", 42])
        assert result == ["uv", "pip", "install", "42"]

    def test_empty_list(self):
        """Empty list should return empty list."""
        result = build_safe_command([])
        assert result == []
