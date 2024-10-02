from langchain.tools import BaseTool
import requests
from typing import Optional

class PackageLookupTool(BaseTool):
    name: str = "Package Lookup"
    description: str = "Look up package information from PyPI or Conda. Specify a package name and optionally a version."

    def _run(self, package_name: str, env_type: str = 'pip', version: Optional[str] = None) -> str:
        """
        Look up package information based on the environment type and version.
        If no version is specified, it fetches the latest version.
        """
        if env_type == 'pip':
            return self._pypi_lookup(package_name, version)
        elif env_type == 'conda':
            return self._conda_lookup(package_name, version)
        else:
            return f"Unsupported environment type: {env_type}"

    def _pypi_lookup(self, package_name: str, version: Optional[str]) -> str:
        """Fetch package info from PyPI with optional version."""
        pypi_url = f"https://pypi.org/pypi/{package_name}/json"
        try:
            response = requests.get(pypi_url)
            if response.status_code == 200:
                data = response.json()
                latest_version = data['info']['version']
                
                if version:
                    # If the user requested a specific version, validate if it exists
                    if version in data['releases']:
                        return f"Package: {package_name}, Version: {version} (exists)"
                    else:
                        return f"Package {package_name} version {version} not found. Latest version: {latest_version}"
                else:
                    # No version specified, return the latest version
                    return f"Package: {package_name}, Latest version: {latest_version}"
            else:
                return f"Package {package_name} not found on PyPI"
        except Exception as e:
            return f"Error looking up package {package_name} on PyPI: {str(e)}"

    def _conda_lookup(self, package_name: str, version: Optional[str]) -> str:
        """Fetch package info from Conda with optional version."""
        conda_url = f"https://api.anaconda.org/package/conda-forge/{package_name}"
        try:
            response = requests.get(conda_url)
            if response.status_code == 200:
                data = response.json()
                latest_version = data['latest_version']
                versions = data.get('versions', [])

                if version:
                    # Check if the specified version exists
                    if version in versions:
                        return f"Package: {package_name}, Version: {version} (exists)"
                    else:
                        return f"Package {package_name} version {version} not found on Conda. Latest version: {latest_version}"
                else:
                    # No version specified, return the latest version
                    return f"Package: {package_name}, Latest version: {latest_version}"
            else:
                return f"Package {package_name} not found on Conda"
        except Exception as e:
            return f"Error looking up package {package_name} on Conda: {str(e)}"

    async def _arun(self, package_name: str) -> str:
        # Implement async version if needed
        raise NotImplementedError("PackageLookupTool does not support async")
