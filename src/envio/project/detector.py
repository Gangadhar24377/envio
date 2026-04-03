"""Project mode detection for Envio.

Determines which dependency file is authoritative for a given directory.
Rule: pyproject.toml always wins if present, regardless of requirements.txt.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path


class ProjectMode(Enum):
    """The authoritative dependency format for a project directory."""

    PYPROJECT = "pyproject"
    """pyproject.toml exists — always preferred over requirements.txt."""

    REQUIREMENTS = "requirements"
    """requirements.txt exists and no pyproject.toml."""

    NEW = "new"
    """Neither file exists — brand new project."""


class ProjectDetector:
    """Detects the project mode for a directory.

    Decision tree:
        1. pyproject.toml present → PYPROJECT  (even if requirements.txt also exists)
        2. requirements.txt present, no pyproject.toml → REQUIREMENTS
        3. Neither → NEW
    """

    # Ordered list of (filename, mode) — first match wins.
    _PRIORITY: list[tuple[str, ProjectMode]] = [
        ("pyproject.toml", ProjectMode.PYPROJECT),
        ("requirements.txt", ProjectMode.REQUIREMENTS),
    ]

    def detect(self, cwd: Path) -> ProjectMode:
        """Return the ProjectMode for *cwd*.

        Args:
            cwd: Directory to inspect (typically Path.cwd()).

        Returns:
            ProjectMode enum value.
        """
        for filename, mode in self._PRIORITY:
            if (cwd / filename).exists():
                return mode
        return ProjectMode.NEW

    def get_project_file(self, cwd: Path) -> Path | None:
        """Return the path to the authoritative project file, or None for NEW.

        Args:
            cwd: Directory to inspect.

        Returns:
            Path to the project file, or None if no file exists.
        """
        for filename, _ in self._PRIORITY:
            candidate = cwd / filename
            if candidate.exists():
                return candidate
        return None

    def is_pyproject(self, cwd: Path) -> bool:
        """Convenience: True when pyproject.toml is authoritative."""
        return self.detect(cwd) == ProjectMode.PYPROJECT

    def is_requirements(self, cwd: Path) -> bool:
        """Convenience: True when requirements.txt is authoritative."""
        return self.detect(cwd) == ProjectMode.REQUIREMENTS

    def is_new(self, cwd: Path) -> bool:
        """Convenience: True when no project file exists."""
        return self.detect(cwd) == ProjectMode.NEW
