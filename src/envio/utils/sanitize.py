"""Sanitization utilities for shell command safety."""

from __future__ import annotations

import re
import shlex


def validate_package_name(name: str) -> bool:
    """Validate package name contains only safe characters.

    Allows: letters, numbers, underscore, dash, dot, brackets
    Rejects: semicolon, ampersand, pipe, dollar, etc.

    Args:
        name: Package name to validate

    Returns:
        True if package name is safe
    """
    if not name:
        return False

    # Remove version specifiers for validation
    base_name = re.split(r"[<>=!~\[]", name)[0]

    # Allow: letters, numbers, underscore, dash, dot
    pattern = r"^[a-zA-Z0-9_\-\.]+$"
    return bool(re.match(pattern, base_name))


def sanitize_path(path: str) -> str:
    """Sanitize a file path for safe shell interpolation.

    Args:
        path: Path to sanitize

    Returns:
        Quoted path safe for shell use
    """
    return shlex.quote(path)


def sanitize_package_name(pkg: str) -> str:
    """Sanitize a package name for safe shell interpolation.

    Args:
        pkg: Package name to sanitize

    Returns:
        Quoted package name safe for shell use
    """
    if not validate_package_name(pkg):
        raise ValueError(f"Invalid package name: {pkg}")
    return shlex.quote(pkg)


def sanitize_packages(packages: list[str]) -> list[str]:
    """Sanitize a list of package names.

    Args:
        packages: List of package names

    Returns:
        List of sanitized package names

    Raises:
        ValueError: If any package name is invalid
    """
    sanitized = []
    for pkg in packages:
        if not validate_package_name(pkg):
            raise ValueError(f"Invalid package name: {pkg}")
        sanitized.append(shlex.quote(pkg))
    return sanitized


def escape_shell_string(s: str) -> str:
    """Escape a string for safe shell interpolation.

    Args:
        s: String to escape

    Returns:
        Escaped string safe for shell use
    """
    return shlex.quote(s)


def build_safe_command(parts: list[str]) -> list[str]:
    """Build a safe command list for subprocess.run().

    Args:
        parts: Command parts

    Returns:
        List of command parts safe for subprocess.run()
    """
    return [str(part) for part in parts]
