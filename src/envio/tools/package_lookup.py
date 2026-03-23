"""Package Lookup Tool for PyPI and Conda."""

from __future__ import annotations

import requests


class PackageLookupTool:
    """Tool for looking up package information from PyPI or Conda."""

    def run(
        self, package_name: str, env_type: str = "pip", version: str | None = None
    ) -> str:
        """Look up package information based on the environment type and version."""
        if env_type == "pip":
            return self._pypi_lookup(package_name, version)
        elif env_type == "conda":
            return self._conda_lookup(package_name, version)
        else:
            return f"Unsupported environment type: {env_type}"

    def _pypi_lookup(self, package_name: str, version: str | None) -> str:
        """Fetch package info from PyPI with optional version."""
        pypi_url = f"https://pypi.org/pypi/{package_name}/json"
        try:
            response = requests.get(pypi_url)
            if response.status_code == 200:
                data = response.json()
                latest_version = data["info"]["version"]

                if version:
                    if version in data["releases"]:
                        return f"Package: {package_name}, Version: {version} (exists)"
                    else:
                        return (
                            f"Package {package_name} version {version} not found. "
                            f"Latest version: {latest_version}"
                        )
                else:
                    return f"Package: {package_name}, Latest version: {latest_version}"
            else:
                return f"Package {package_name} not found on PyPI"
        except Exception as e:
            return f"Error looking up package {package_name} on PyPI: {str(e)}"

    def _conda_lookup(self, package_name: str, version: str | None) -> str:
        """Fetch package info from Conda with optional version."""
        conda_url = f"https://api.anaconda.org/package/conda-forge/{package_name}"
        try:
            response = requests.get(conda_url)
            if response.status_code == 200:
                data = response.json()
                latest_version = data["latest_version"]
                versions = data.get("versions", [])

                if version:
                    if version in versions:
                        return f"Package: {package_name}, Version: {version} (exists)"
                    else:
                        return (
                            f"Package {package_name} version {version} not found on Conda. "
                            f"Latest version: {latest_version}"
                        )
                else:
                    return f"Package: {package_name}, Latest version: {latest_version}"
            else:
                return f"Package {package_name} not found on Conda"
        except Exception as e:
            return f"Error looking up package {package_name} on Conda: {str(e)}"
