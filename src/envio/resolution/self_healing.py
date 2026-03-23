"""Self-healing loop for AI-powered dependency resolution."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import requests

from envio.resolution.fast_resolver import ConflictInfo, ResolutionResult


@dataclass
class HealingAttempt:
    """Record of a healing attempt."""

    attempt_number: int
    original_packages: list[str]
    modified_packages: list[str]
    error: str
    resolution: ResolutionResult


@dataclass
class HealingResult:
    """Result of the self-healing process."""

    success: bool
    final_packages: list[str]
    attempts: list[HealingAttempt] = field(default_factory=list)
    final_error: str | None = None

    @property
    def num_attempts(self) -> int:
        """Number of healing attempts made."""
        return len(self.attempts)


class SelfHealingLoop:
    """AI-powered self-healing loop for dependency resolution."""

    MAX_ATTEMPTS = 3

    def __init__(self) -> None:
        self._attempts: list[HealingAttempt] = []

    def heal(
        self,
        packages: list[str],
        error_message: str,
        resolution: ResolutionResult,
    ) -> HealingResult:
        """
        Attempt to heal dependency conflicts using AI analysis.

        Args:
            packages: Original package list
            error_message: Error from failed resolution
            resolution: The failed resolution result

        Returns:
            HealingResult with healed packages or failure info
        """
        self._attempts = []
        current_packages = packages.copy()

        for attempt_num in range(1, self.MAX_ATTEMPTS + 1):
            attempt = HealingAttempt(
                attempt_number=attempt_num,
                original_packages=packages,
                modified_packages=current_packages,
                error=error_message,
                resolution=resolution,
            )

            modified = self._analyze_and_fix(
                current_packages, error_message, resolution, attempt_num
            )

            if modified == current_packages:
                self._attempts.append(attempt)
                return HealingResult(
                    success=False,
                    final_packages=current_packages,
                    attempts=self._attempts,
                    final_error="Could not find compatible package versions",
                )

            current_packages = modified
            self._attempts.append(attempt)

        return HealingResult(
            success=False,
            final_packages=current_packages,
            attempts=self._attempts,
            final_error=f"Max attempts ({self.MAX_ATTEMPTS}) reached without resolution",
        )

    def _analyze_and_fix(
        self,
        packages: list[str],
        error: str,
        resolution: ResolutionResult,
        attempt: int,
    ) -> list[str]:
        """Analyze error and try to fix package versions."""
        modified = packages.copy()

        for conflict in resolution.conflicts:
            fixed = self._fix_conflict(conflict, packages, attempt)
            if fixed:
                modified = fixed
                break

        if not resolution.conflicts and error:
            fixed = self._fix_from_error(packages, error, attempt)
            if fixed:
                modified = fixed

        return modified

    def _fix_conflict(
        self, conflict: ConflictInfo, packages: list[str], attempt: int
    ) -> list[str] | None:
        """Try to fix a specific conflict."""
        pkg1, pkg2 = conflict.package1, conflict.package2

        if pkg1 in packages and pkg2 in packages:
            versions = self._find_compatible_versions(pkg1, pkg2)
            if versions:
                modified = []
                for pkg in packages:
                    if pkg == pkg1 and versions.get(pkg1):
                        modified.append(f"{pkg1}=={versions[pkg1]}")
                    elif pkg == pkg2 and versions.get(pkg2):
                        modified.append(f"{pkg2}=={versions[pkg2]}")
                    else:
                        modified.append(pkg)
                return modified

        if pkg1 in packages:
            compatible = self._find_single_compatible(pkg1)
            if compatible:
                return [
                    f"{pkg1}=={compatible}" if pkg1 in pkg else pkg for pkg in packages
                ]

        return None

    def _fix_from_error(
        self, packages: list[str], error: str, attempt: int
    ) -> list[str] | None:
        """Fix packages based on error message analysis."""
        version_pattern = r"(\S+)==([\d.]+)"
        matches = re.findall(version_pattern, error)

        if matches:
            modified = packages.copy()
            for pkg, ver in matches:
                for i, p in enumerate(modified):
                    if p.startswith(pkg):
                        modified[i] = f"{pkg}=={ver}"
                        break
                else:
                    if attempt == 1:
                        modified.append(f"{pkg}=={ver}")
            return modified

        version_constraint = r"requires (\S+),?\s*(.*?)(?:,|$)"
        constraints = re.findall(version_constraint, error)

        if constraints:
            modified = packages.copy()
            for pkg, constraint in constraints:
                for i, p in enumerate(modified):
                    if p.startswith(pkg.split("[")[0]):
                        if constraint:
                            modified[i] = f"{pkg}{constraint}"
                        break
            return modified

        return None

    def _find_compatible_versions(self, pkg1: str, pkg2: str) -> dict[str, str] | None:
        """Find compatible versions of two packages."""
        v1 = self._find_single_compatible(pkg1)
        v2 = self._find_single_compatible(pkg2)

        if v1 and v2:
            return {pkg1: v1, pkg2: v2}
        return None

    def _find_single_compatible(self, package_name: str) -> str | None:
        """Find a compatible version of a package."""
        try:
            response = requests.get(
                f"https://pypi.org/pypi/{package_name}/json", timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data["info"]["version"]
        except Exception:
            pass
        return None

    def get_pytorch_compatibility(
        self, cuda_version: str | None, packages: list[str]
    ) -> list[str]:
        """Get PyTorch-compatible versions of packages."""
        if not cuda_version:
            return packages

        modified = []
        for pkg in packages:
            if "torch" in pkg.lower() or "pytorch" in pkg.lower():
                modified.append(pkg)
            elif "xformers" in pkg.lower():
                cuda_short = (
                    cuda_version.split(".")[0] if "." in cuda_version else cuda_version
                )
                modified.append(f"xformers cu{cuda_short}xx")
            else:
                modified.append(pkg)

        return modified
