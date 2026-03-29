"""Self-healing loop for AI-powered dependency resolution."""

from __future__ import annotations

import hashlib
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
    strategy: str = "default"


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
    FALLBACK_STRATEGIES = [
        "relax_version_constraints",
        "find_alternative_packages",
        "skip_optional_dependencies",
    ]

    def __init__(self) -> None:
        self._attempts: list[HealingAttempt] = []
        self._seen_errors: set[str] = set()
        self._current_strategy_index = 0

    def _error_hash(self, error: str) -> str:
        """Generate hash for error message to detect duplicate errors."""
        # Normalize the error message to ignore minor variations
        normalized = re.sub(r"\s+", " ", error.lower().strip())
        # Remove version numbers which might vary
        normalized = re.sub(r"==[\d.]+", "", normalized)
        normalized = re.sub(r">=[\d.]+", "", normalized)
        normalized = re.sub(r"<=[\d.]+", "", normalized)
        return hashlib.md5(normalized.encode(), usedforsecurity=False).hexdigest()

    def _get_next_strategy(self) -> str:
        """Get the next fallback strategy to try."""
        if self._current_strategy_index < len(self.FALLBACK_STRATEGIES):
            strategy = self.FALLBACK_STRATEGIES[self._current_strategy_index]
            self._current_strategy_index += 1
            return strategy
        return "default"

    def _apply_strategy(
        self,
        strategy: str,
        packages: list[str],
        error: str,
        resolution: ResolutionResult,
    ) -> list[str]:
        """Apply a specific healing strategy."""
        if strategy == "relax_version_constraints":
            return self._relax_version_constraints(packages, error)
        elif strategy == "find_alternative_packages":
            return self._find_alternative_packages(packages, error)
        elif strategy == "skip_optional_dependencies":
            return self._skip_optional_dependencies(packages, error)
        else:
            # Default strategy: analyze and fix
            return self._analyze_and_fix(packages, error, resolution, 1)

    def _relax_version_constraints(self, packages: list[str], error: str) -> list[str]:
        """Relax version constraints to find compatible versions."""
        modified = []
        for pkg in packages:
            if "==" in pkg:
                # Remove exact version constraint
                base_pkg = pkg.split("==")[0]
                modified.append(base_pkg)
            elif ">=" in pkg or "<=" in pkg:
                # Remove any version constraint
                base_pkg = re.split(r"[<>=]", pkg)[0]
                modified.append(base_pkg)
            else:
                modified.append(pkg)
        return modified

    def _find_alternative_packages(self, packages: list[str], error: str) -> list[str]:
        """Try to find alternative packages for conflicting ones."""
        # Common package alternatives
        alternatives = {
            "requests": ["httpx", "aiohttp"],
            "tensorflow": ["torch", "jax"],
            "selenium": ["playwright", "pyppeteer"],
            "beautifulsoup4": ["lxml", "selectolax"],
            "pillow": ["Pillow"],
            "opencv-python": ["opencv-python-headless"],
            "scikit-learn": ["scikit-learn"],
            "sklearn": ["scikit-learn"],
        }

        modified = []
        for pkg in packages:
            base_pkg = pkg.split("==")[0].split(">=")[0].split("<=")[0].lower()
            if base_pkg in alternatives:
                # Use first alternative
                modified.append(alternatives[base_pkg][0])
            else:
                modified.append(pkg)
        return modified

    def _skip_optional_dependencies(self, packages: list[str], error: str) -> list[str]:
        """Remove packages that might be optional dependencies.

        Instead of dropping packages with extras entirely, strip the extras
        and keep the base package (e.g., torch[dev] → torch).
        """
        modified = []
        for pkg in packages:
            if "[" in pkg:
                base_pkg = pkg.split("[")[0]
                modified.append(base_pkg)
            else:
                modified.append(pkg)
        return modified

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
        self._seen_errors = set()
        self._current_strategy_index = 0
        current_packages = packages.copy()

        for attempt_num in range(1, self.MAX_ATTEMPTS + 1):
            # Check if we've seen this error before
            error_hash = self._error_hash(error_message)
            if error_hash in self._seen_errors:
                # Try a different strategy
                strategy = self._get_next_strategy()
                modified = self._apply_strategy(
                    strategy, current_packages, error_message, resolution
                )
            else:
                strategy = "default"
                modified = self._analyze_and_fix(
                    current_packages, error_message, resolution, attempt_num
                )

            self._seen_errors.add(error_hash)

            attempt = HealingAttempt(
                attempt_number=attempt_num,
                original_packages=packages,
                modified_packages=modified,
                error=error_message,
                resolution=resolution,
                strategy=strategy,
            )

            if modified == current_packages:
                # No change made - try next strategy
                self._attempts.append(attempt)
                strategy = self._get_next_strategy()
                if strategy == "default":
                    # No more strategies to try
                    return HealingResult(
                        success=False,
                        final_packages=current_packages,
                        attempts=self._attempts,
                        final_error="Could not find compatible package versions",
                    )
                # Try the next strategy
                continue

            # Re-validate the fix with fast resolver
            from envio.resolution.fast_resolver import FastResolver

            fast_resolver = FastResolver()
            recheck = fast_resolver.resolve(modified)

            if recheck.is_success():
                # Fix worked!
                self._attempts.append(attempt)
                return HealingResult(
                    success=True,
                    final_packages=modified,
                    attempts=self._attempts,
                )

            # Fix didn't work, continue with modified packages
            current_packages = modified
            self._attempts.append(attempt)

            # Update error message for next iteration
            if recheck.error_message:
                error_message = recheck.error_message

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

        def get_base_name(pkg: str) -> str:
            """Extract base package name, stripping version specifiers."""
            return pkg.split("==")[0].split(">=")[0].split("<=")[0].split("[")[0]

        pkg1_base = get_base_name(pkg1)
        pkg2_base = get_base_name(pkg2) if pkg2 else None

        if pkg1_base in [get_base_name(p) for p in packages] and pkg2_base in [
            get_base_name(p) for p in packages
        ]:
            versions = self._find_compatible_versions(pkg1, pkg2)
            if versions:
                modified = []
                for pkg in packages:
                    pkg_base = get_base_name(pkg)
                    if pkg_base == pkg1_base and versions.get(pkg1):
                        modified.append(f"{pkg1_base}=={versions[pkg1]}")
                    elif pkg_base == pkg2_base and pkg2_base and versions.get(pkg2):
                        modified.append(f"{pkg2_base}=={versions[pkg2]}")
                    else:
                        modified.append(pkg)
                return modified

        if pkg1_base in [get_base_name(p) for p in packages]:
            compatible = self._find_single_compatible(pkg1)
            if compatible:
                return [
                    f"{pkg1_base}=={compatible}" if get_base_name(p) == pkg1_base else p
                    for p in packages
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
