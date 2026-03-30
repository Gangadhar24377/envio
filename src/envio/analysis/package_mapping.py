"""Dynamic import-to-package name mapping with PyPI lookup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests


# Known mappings that differ from import name to PyPI package name
# These are detected dynamically, but cached for common cases
_KNOWN_MAPPINGS_CACHE: dict[str, str] = {}

# Use user-writable cache directory instead of package directory
# This ensures cache works even when envio is installed via pip
_CACHE_FILE = Path.home() / ".envio" / "cache" / "package_mappings.json"


def _load_cache() -> dict[str, str]:
    """Load cached mappings from disk."""
    global _KNOWN_MAPPINGS_CACHE
    if _KNOWN_MAPPINGS_CACHE:
        return _KNOWN_MAPPINGS_CACHE

    if _CACHE_FILE.exists():
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                _KNOWN_MAPPINGS_CACHE = json.load(f)
            return _KNOWN_MAPPINGS_CACHE
        except (json.JSONDecodeError, OSError):
            pass

    _KNOWN_MAPPINGS_CACHE = {}
    return _KNOWN_MAPPINGS_CACHE


def _save_cache(mappings: dict[str, str]) -> None:
    """Save mappings to disk cache."""
    global _KNOWN_MAPPINGS_CACHE
    _KNOWN_MAPPINGS_CACHE.update(mappings)
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_KNOWN_MAPPINGS_CACHE, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def _query_pypi_for_import(import_name: str) -> str | None:
    """Query PyPI to find the package name for a given import name.

    Uses the PyPI JSON API to search for packages that provide the given import.
    """
    api_url = f"https://pypi.org/pypi/{import_name}/json"
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("info", {}).get("name", import_name)
    except Exception:
        pass
    return None


def find_package_for_import(import_name: str) -> str:
    """Find the PyPI package name for a given import name.

    Args:
        import_name: The import name (e.g., 'cv2', 'PIL', 'sklearn')

    Returns:
        The PyPI package name (e.g., 'opencv-python', 'Pillow', 'scikit-learn')
    """
    if not import_name:
        return import_name

    # 1. Check cache first
    cache = _load_cache()
    if import_name in cache:
        return cache[import_name]

    # 2. Query PyPI directly with the import name
    package_name = _query_pypi_for_import(import_name)
    if package_name and package_name.lower() != import_name.lower():
        # Found a different package name, cache it
        _save_cache({import_name: package_name})
        return package_name

    # 3. Try common variations (e.g., remove underscores, try with different case)
    common_variations = [
        import_name.replace("_", "-"),
        import_name.replace("-", "_"),
        import_name.lower(),
        import_name.upper(),
        import_name.title(),
    ]

    for variation in common_variations:
        if variation != import_name:
            result = _query_pypi_for_import(variation)
            if result:
                _save_cache({import_name: result})
                return result

    # 4. If not found, return the import name as-is (best guess)
    _save_cache({import_name: import_name})
    return import_name


def find_packages_for_imports(import_names: list[str]) -> dict[str, str]:
    """Find PyPI package names for multiple import names.

    Args:
        import_names: List of import names

    Returns:
        Dictionary mapping import names to package names
    """
    results = {}
    for name in import_names:
        results[name] = find_package_for_import(name)
    return results


def resolve_import_to_package(import_name: str) -> str:
    """Resolve an import name to its PyPI package name.

    This is an alias for find_package_for_import() for consistency with the plan.

    Args:
        import_name: The import name to resolve

    Returns:
        The PyPI package name
    """
    return find_package_for_import(import_name)


def get_cached_mappings() -> dict[str, str]:
    """Get all cached mappings.

    Returns:
        Dictionary of all cached import-to-package mappings
    """
    return _load_cache().copy()


def clear_cache() -> None:
    """Clear the package mapping cache."""
    global _KNOWN_MAPPINGS_CACHE
    _KNOWN_MAPPINGS_CACHE = {}
    try:
        if _CACHE_FILE.exists():
            _CACHE_FILE.unlink()
    except OSError:
        pass
