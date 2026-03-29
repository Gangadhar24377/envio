"""Version detection and comparison utilities."""

from __future__ import annotations

import platform
import shutil
import subprocess
from typing import Optional

from packaging.version import Version


def detect_system_python_version() -> str | None:
    """Detect the system Python version.

    Tries multiple methods in order:
    1. Current interpreter (platform.python_version())
    2. python3 --version
    3. python --version

    Returns:
        Version string like "3.11.5" or None if detection fails
    """
    version = _get_current_interpreter_version()
    if version:
        return version

    version = _get_python_version_from_command("python3")
    if version:
        return version

    version = _get_python_version_from_command("python")
    if version:
        return version

    return None


def _get_current_interpreter_version() -> str | None:
    """Get version from current Python interpreter."""
    try:
        version = platform.python_version()
        if version and _is_valid_version_string(version):
            return version
    except Exception:
        pass
    return None


def _get_python_version_from_command(command: str) -> str | None:
    """Get Python version from a command."""
    if not shutil.which(command):
        return None

    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            output = result.stdout.strip() or result.stderr.strip()
            parts = output.split()
            for part in parts:
                if _is_valid_version_string(part):
                    return part
    except Exception:
        pass

    return None


def _is_valid_version_string(s: str) -> bool:
    """Check if string looks like a valid version number."""
    try:
        Version(s)
        return True
    except Exception:
        return False


def compare_versions(v1: str, v2: str) -> int:
    """Compare two version strings.

    Returns:
        -1 if v1 < v2
         0 if v1 == v2
         1 if v1 > v2
    """
    try:
        ver1 = Version(v1)
        ver2 = Version(v2)
        if ver1 < ver2:
            return -1
        elif ver1 > ver2:
            return 1
        return 0
    except Exception:
        t1 = _version_to_tuple(v1)
        t2 = _version_to_tuple(v2)
        return (t1 > t2) - (t1 < t2)


def max_version(versions: list[str]) -> str:
    """Return the maximum version from a list."""
    if not versions:
        return "3.8"

    valid_versions = [v for v in versions if _is_valid_version_string(v)]
    if not valid_versions:
        return "3.8"

    try:
        return str(max(Version(v) for v in valid_versions))
    except Exception:
        return valid_versions[-1]


def _version_to_tuple(version_str: str) -> tuple[int, ...]:
    """Convert version string to tuple of ints."""
    try:
        return tuple(int(x) for x in version_str.split(".")[:3])
    except (ValueError, AttributeError):
        return (0, 0, 0)


def version_at_least(version: str, minimum: str) -> bool:
    """Check if version is at least minimum."""
    return compare_versions(version, minimum) >= 0


def major_minor(version: str) -> str:
    """Extract major.minor from a version string."""
    try:
        v = Version(version)
        return f"{v.major}.{v.minor}"
    except Exception:
        parts = version.split(".")
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        return version
