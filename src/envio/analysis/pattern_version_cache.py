"""Pattern version cache for AI-powered Python version inference."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_CACHE_FILE = Path.home() / ".envio" / "cache" / "pattern_versions.json"

_PATTERN_VERSION_CACHE: dict[str, dict[str, Any]] = {}


STATIC_MAPPINGS: dict[str, dict[str, Any]] = {
    "print_statement": {
        "min_python_version": "2.0",
        "confidence": "high",
        "source": "static",
    },
    "urllib2": {"min_python_version": "2.0", "confidence": "high", "source": "static"},
    "raw_input": {
        "min_python_version": "2.0",
        "confidence": "high",
        "source": "static",
    },
    "xrange": {"min_python_version": "2.0", "confidence": "high", "source": "static"},
    "python2_division": {
        "min_python_version": "2.0",
        "confidence": "high",
        "source": "static",
    },
    "python2_unicode": {
        "min_python_version": "2.0",
        "confidence": "high",
        "source": "static",
    },
    "f_string": {"min_python_version": "3.6", "confidence": "high", "source": "static"},
    "walrus_operator": {
        "min_python_version": "3.8",
        "confidence": "high",
        "source": "static",
    },
    "match_statement": {
        "min_python_version": "3.10",
        "confidence": "high",
        "source": "static",
    },
    "type_union": {
        "min_python_version": "3.10",
        "confidence": "high",
        "source": "static",
    },
    "typing_optional": {
        "min_python_version": "3.5",
        "confidence": "high",
        "source": "static",
    },
    "old_string_format": {
        "min_python_version": "2.0",
        "confidence": "high",
        "source": "static",
    },
    "old_django_urlresolvers": {
        "min_python_version": "2.0",
        "confidence": "medium",
        "source": "static",
    },
    "old_flask_script": {
        "min_python_version": "2.0",
        "confidence": "medium",
        "source": "static",
    },
    "six_compatibility": {
        "min_python_version": "2.0",
        "confidence": "medium",
        "source": "static",
    },
}


def _load_cache() -> dict[str, dict[str, Any]]:
    """Load pattern version cache from disk."""
    global _PATTERN_VERSION_CACHE
    if _PATTERN_VERSION_CACHE:
        return _PATTERN_VERSION_CACHE

    if _CACHE_FILE.exists():
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _PATTERN_VERSION_CACHE = {
                    k: v for k, v in data.items() if not k.startswith("_")
                }
                return _PATTERN_VERSION_CACHE
        except (json.JSONDecodeError, OSError):
            pass

    _PATTERN_VERSION_CACHE = {}
    return _PATTERN_VERSION_CACHE


def _save_cache(pattern: str, info: dict[str, Any]) -> None:
    """Save a single pattern's version info to cache."""
    global _PATTERN_VERSION_CACHE
    _PATTERN_VERSION_CACHE[pattern] = info

    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

        existing = {}
        if _CACHE_FILE.exists():
            try:
                with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        existing.update(_PATTERN_VERSION_CACHE)
        existing["_metadata"] = {
            "version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "source": "envio-pattern-inference",
        }

        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def get_pattern_version(pattern_name: str) -> dict[str, Any] | None:
    """Get minimum Python version for a pattern.

    Checks (in order):
    1. Static mappings (known patterns)
    2. Disk cache (previously AI-queried)

    Returns:
        Dict with min_python_version, confidence, source, cached_at
        or None if not found
    """
    if pattern_name in STATIC_MAPPINGS:
        return STATIC_MAPPINGS[pattern_name]

    cache = _load_cache()
    if pattern_name in cache:
        return cache[pattern_name]

    return None


def cache_pattern_version(
    pattern_name: str,
    min_python_version: str,
    confidence: str = "medium",
    source: str = "ai",
) -> None:
    """Cache a pattern's minimum Python version."""
    info = {
        "min_python_version": min_python_version,
        "confidence": confidence,
        "source": source,
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_cache(pattern_name, info)


def get_all_cached_patterns() -> dict[str, dict[str, Any]]:
    """Get all cached pattern versions."""
    result = dict(STATIC_MAPPINGS)
    result.update(_load_cache())
    return result


def clear_cache() -> None:
    """Clear the pattern version cache."""
    global _PATTERN_VERSION_CACHE
    _PATTERN_VERSION_CACHE = {}
    try:
        if _CACHE_FILE.exists():
            _CACHE_FILE.unlink()
    except OSError:
        pass
