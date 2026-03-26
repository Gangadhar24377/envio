"""Version inference for finding compatible package versions."""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Semaphore
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from tqdm import tqdm


def get_stdlib_modules() -> set[str]:
    """Get all stdlib modules dynamically from Python.

    Returns:
        Set of stdlib module names
    """
    if hasattr(sys, "stdlib_module_names"):
        return set(sys.stdlib_module_names)
    return set()


# Dynamic stdlib detection
STDLIB_MODULES = get_stdlib_modules()


@dataclass
class PackageVersion:
    """A package version with metadata."""

    name: str
    version: str
    python_requires: str | None = None
    release_date: str | None = None


class VersionInference:
    """Infer compatible versions for packages based on timeline and Python version."""

    def __init__(self):
        self._semaphore = Semaphore(5)

    def query_pypi(self, package_name: str) -> dict | None:
        """Query PyPI for package information.

        Tries both underscore and dash versions of the name.
        PyPI uses dashes (pydantic-settings) but imports use underscores (pydantic_settings).

        Args:
            package_name: Package name to query

        Returns:
            PyPI JSON response or None if not found
        """
        # Try original name first
        data = self._query_pypi_name(package_name)
        if data:
            return data

        # Try with dash instead of underscore (e.g., pydantic_settings -> pydantic-settings)
        if "_" in package_name:
            dashed_name = package_name.replace("_", "-")
            data = self._query_pypi_name(dashed_name)
            if data:
                return data

        return None

    def _query_pypi_name(self, package_name: str) -> dict | None:
        """Query PyPI with exact package name.

        Args:
            package_name: Exact package name

        Returns:
            PyPI JSON response or None if not found
        """
        url = f"https://pypi.org/pypi/{package_name}/json"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    def get_available_versions(self, package_name: str) -> list[str]:
        """Get all available versions for a package.

        Args:
            package_name: Package name

        Returns:
            List of version strings
        """
        data = self.query_pypi(package_name)
        if not data:
            return []
        return list(data.get("releases", {}).keys())

    def find_compatible_versions(
        self,
        packages: list[str],
        timeline: str = "modern (2020+)",
        python_version: str = "3.11",
    ) -> dict[str, str]:
        """Find compatible versions for packages.

        Uses parallel PyPI queries with rate limiting.

        Args:
            packages: List of package names
            timeline: Detected timeline from syntax detection
            python_version: Target Python version

        Returns:
            Dictionary mapping package names to pinned versions
        """
        packages_to_query = [p for p in packages if p not in STDLIB_MODULES]

        if not packages_to_query:
            return {}

        results: dict[str, str] = {}

        try:
            from tqdm import tqdm

            use_progress = True
        except ImportError:
            use_progress = False

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(
                    self._find_version_safe, pkg, timeline, python_version
                ): pkg
                for pkg in packages_to_query
            }

            if use_progress:
                for future in tqdm(
                    as_completed(futures),
                    total=len(packages_to_query),
                    desc="Querying PyPI",
                    unit="pkg",
                ):
                    pkg = futures[future]
                    try:
                        version = future.result()
                        if version:
                            results[pkg] = version
                    except Exception:
                        continue
            else:
                for future in as_completed(futures):
                    pkg = futures[future]
                    try:
                        version = future.result()
                        if version:
                            results[pkg] = version
                    except Exception:
                        continue

        return results

    def _find_version_safe(
        self, package: str, timeline: str, python_version: str
    ) -> str | None:
        """Find version with rate limiting."""
        with self._semaphore:
            return self._find_version_for_package(package, timeline, python_version)

    def _find_version_for_package(
        self,
        package: str,
        timeline: str,
        python_version: str,
    ) -> str | None:
        """Find best version for a single package.

        Args:
            package: Package name
            timeline: Detected timeline
            python_version: Target Python version

        Returns:
            Best version string or None
        """
        data = self.query_pypi(package)
        if not data:
            return None

        latest_version = data.get("info", {}).get("version")
        releases = data.get("releases", {})

        if not releases:
            return latest_version

        if "python2" in timeline or "2008-2015" in timeline:
            python2_versions = self._filter_python2_versions(releases)
            if python2_versions:
                return python2_versions[-1]

        return latest_version

    def _filter_python2_versions(self, releases: dict) -> list[str]:
        """Filter releases to Python 2 compatible versions.

        Args:
            releases: Dictionary of releases from PyPI

        Returns:
            List of Python 2 compatible versions
        """
        py2_versions: list[str] = []

        for version, files in releases.items():
            if any(
                "py2" in f.get("filename", "") or "cp27" in f.get("filename", "")
                for f in files
            ):
                py2_versions.append(version)

        if not py2_versions:
            return self._get_older_versions(list(releases.keys()), count=10)

        return sorted(py2_versions)

    def _get_older_versions(self, versions: list[str], count: int = 10) -> list[str]:
        """Get older versions from list.

        Args:
            versions: List of version strings
            count: Number of versions to return

        Returns:
            List of older versions
        """
        try:
            from packaging.version import Version

            sorted_versions = sorted(versions, key=Version)
            return sorted_versions[:count]
        except ImportError:
            return versions[:count]

    def generate_requirements(self, packages: dict[str, str]) -> str:
        """Generate requirements.txt content.

        Args:
            packages: Dictionary of package name to version

        Returns:
            Formatted requirements.txt content
        """
        lines = []
        for package, version in sorted(packages.items()):
            if version:
                lines.append(f"{package}=={version}")
            else:
                lines.append(package)
        return "\n".join(lines) + "\n"
