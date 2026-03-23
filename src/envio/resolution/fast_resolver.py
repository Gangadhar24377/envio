"""Fast resolver using uv for millisecond dependency resolution."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import requests


class ResolutionStatus(Enum):
    """Status of the resolution attempt."""

    SUCCESS = "success"
    CONFLICT = "conflict"
    NOT_FOUND = "not_found"
    ERROR = "error"


@dataclass
class ConflictInfo:
    """Information about a dependency conflict."""

    package1: str
    package2: str
    reason: str
    suggestion: str | None = None


@dataclass
class ResolutionResult:
    """Result of a dependency resolution attempt."""

    status: ResolutionStatus
    packages: list[str] = field(default_factory=list)
    conflicts: list[ConflictInfo] = field(default_factory=list)
    error_message: str | None = None
    stderr: str | None = None
    stdout: str | None = None

    def is_success(self) -> bool:
        """Check if resolution was successful."""
        return self.status == ResolutionStatus.SUCCESS

    def has_conflicts(self) -> bool:
        """Check if there are conflicts."""
        return len(self.conflicts) > 0


class FastResolver:
    """Fast dependency resolver using uv."""

    def __init__(self) -> None:
        self._uv_available: bool | None = None

    def check_uv_available(self) -> bool:
        """Check if uv is available."""
        if self._uv_available is not None:
            return self._uv_available

        try:
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            self._uv_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._uv_available = False

        return self._uv_available

    def resolve(
        self,
        packages: list[str],
        python_version: str | None = None,
        dry_run: bool = True,
    ) -> ResolutionResult:
        """
        Resolve dependencies using uv.

        Args:
            packages: List of package specifications
            python_version: Python version to use
            dry_run: If True, only check resolution without installing

        Returns:
            ResolutionResult with status and details
        """
        if not self.check_uv_available():
            return ResolutionResult(
                status=ResolutionStatus.ERROR,
                error_message="uv is not installed. Please install uv: pip install uv",
            )

        cmd = ["uv", "pip", "install", "--dry-run", "--strict"]
        cmd.extend(packages)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                return ResolutionResult(
                    status=ResolutionStatus.SUCCESS,
                    packages=packages,
                    stdout=result.stdout,
                )
            else:
                return self._parse_uv_error(result.stderr, result.stdout, packages)

        except subprocess.TimeoutExpired:
            return ResolutionResult(
                status=ResolutionStatus.ERROR,
                error_message="Resolution timed out",
            )
        except Exception as e:
            return ResolutionResult(
                status=ResolutionStatus.ERROR,
                error_message=str(e),
            )

    def _parse_uv_error(
        self, stderr: str, stdout: str, packages: list[str]
    ) -> ResolutionResult:
        """Parse uv error output to extract conflict information."""
        conflicts: list[ConflictInfo] = []

        stderr_lower = stderr.lower()

        if "conflict" in stderr_lower or "conflicting" in stderr_lower:
            conflict_info = self._extract_conflict_details(stderr, packages)
            conflicts.extend(conflict_info)
            return ResolutionResult(
                status=ResolutionStatus.CONFLICT,
                packages=packages,
                conflicts=conflicts,
                stderr=stderr,
                stdout=stdout,
            )

        if "not found" in stderr_lower or "package not found" in stderr_lower:
            return ResolutionResult(
                status=ResolutionStatus.NOT_FOUND,
                packages=packages,
                error_message=stderr,
                stderr=stderr,
                stdout=stdout,
            )

        return ResolutionResult(
            status=ResolutionStatus.ERROR,
            packages=packages,
            error_message=stderr,
            stderr=stderr,
            stdout=stdout,
        )

    def _extract_conflict_details(
        self, stderr: str, packages: list[str]
    ) -> list[ConflictInfo]:
        """Extract conflict details from error message."""
        conflicts = []
        lines = stderr.split("\n")

        for line in lines:
            if "requires" in line.lower() and "conflicts" in line.lower():
                parts = line.split()
                if len(parts) >= 4:
                    conflicts.append(
                        ConflictInfo(
                            package1=parts[0] if parts else "unknown",
                            package2=parts[2] if len(parts) > 2 else "unknown",
                            reason=line,
                        )
                    )
            elif "cannot install" in line.lower():
                conflicts.append(
                    ConflictInfo(
                        package1=" ".join(packages),
                        package2="environment",
                        reason=line,
                        suggestion="Try removing conflicting packages or use AI resolver",
                    )
                )

        if not conflicts and any("conflict" in line.lower() for line in lines):
            conflicts.append(
                ConflictInfo(
                    package1=" ".join(packages),
                    package2="unknown",
                    reason="Dependency conflict detected",
                    suggestion="Use AI resolver to find compatible versions",
                )
            )

        return conflicts

    def get_package_info(self, package_name: str) -> dict[str, Any]:
        """Get package information from PyPI."""
        try:
            response = requests.get(
                f"https://pypi.org/pypi/{package_name}/json", timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "name": data["info"]["name"],
                    "version": data["info"]["version"],
                    "summary": data["info"].get("summary", ""),
                    "requires_python": data["info"].get("requires_python"),
                }
        except Exception:
            pass
        return {}

    def find_alternative(
        self, package_name: str, conflicts_with: str | None = None
    ) -> list[str]:
        """Find alternative packages."""
        alternatives: dict[str, list[str]] = {
            "requests": ["httpx", "aiohttp"],
            "tensorflow": ["torch", "jax"],
            "selenium": ["playwright", "pyppeteer"],
            "beautifulsoup4": ["lxml", "selectolax"],
        }

        return alternatives.get(package_name.lower(), [])
