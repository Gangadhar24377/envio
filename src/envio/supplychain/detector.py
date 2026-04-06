"""Typosquatting and suspicious pattern detection."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass

from envio.supplychain.cache import SupplyChainCache

TOP_PACKAGES_URL = (
    "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json"
)


@dataclass
class DetectionResult:
    is_typo: bool
    suggested_package: str | None
    confidence: float
    reason: str


def _levenshtein_distance(a: str, b: str) -> int:
    """Compute Levenshtein distance between two strings."""
    if len(a) < len(b):
        return _levenshtein_distance(b, a)
    if not b:
        return len(a)
    prev_row = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr_row = [i + 1]
        for j, cb in enumerate(b):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (ca != cb)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def _load_top_packages(top_n: int = 10000) -> list[str]:
    """Load top N PyPI packages by download count."""
    try:
        with urllib.request.urlopen(TOP_PACKAGES_URL, timeout=15) as resp:
            data = json.loads(resp.read())
        return [row["project"].lower() for row in data["rows"][:top_n]]
    except Exception:
        return []


def _get_top_packages() -> list[str]:
    cache = SupplyChainCache.get_instance()
    cached = cache.get("top_packages", "detector")
    if cached is not None:
        return cached
    packages = _load_top_packages()
    if packages:
        cache.set("top_packages", "detector", packages)
    return packages


def check_typosquatting(package_name: str) -> DetectionResult:
    """Check if a package name is a likely typo of a popular package.

    Returns DetectionResult with typo status, suggested package, and confidence.
    """
    pkg = package_name.lower().strip()

    top_packages = _get_top_packages()

    if pkg in top_packages:
        return DetectionResult(
            is_typo=False,
            suggested_package=None,
            confidence=0.0,
            reason="Package is in the top 10k list",
        )

    best_match: str | None = None
    best_distance = float("inf")
    best_len = 0

    for known_pkg in top_packages:
        dist = _levenshtein_distance(pkg, known_pkg)
        pkg_len = max(len(pkg), len(known_pkg))
        if pkg_len == 0:
            continue
        ratio = dist / pkg_len

        if ratio <= 0.25 and dist <= 3 and dist < best_distance:
            best_distance = dist
            best_match = known_pkg
            best_len = pkg_len

    if best_match is None:
        return DetectionResult(
            is_typo=False,
            suggested_package=None,
            confidence=0.0,
            reason="No similar top packages found",
        )

    confidence = 1.0 - (best_distance / best_len)

    return DetectionResult(
        is_typo=True,
        suggested_package=best_match,
        confidence=round(confidence, 2),
        reason=f"Levenshtein distance {best_distance} from '{best_match}'",
    )


def check_suspicious_patterns(package_name: str) -> list[str]:
    """Check for suspicious naming patterns."""
    pkg = package_name.lower().strip()
    flags = []

    known_suspicious_prefixes = [
        "py-",
        "python-",
        "real-",
        "official-",
        "legit-",
        "secure-",
        "safe-",
    ]

    known_suspicious_suffixes = [
        "-update",
        "-patch",
        "-fix",
        "-security",
        "-hotfix",
        "-v2",
        "-new",
        "-official",
        "-real",
    ]

    for prefix in known_suspicious_prefixes:
        if pkg.startswith(prefix) and pkg[len(prefix) :] in _get_top_packages():
            flags.append(f"Suspicious prefix '{prefix}' mimicking a known package")

    for suffix in known_suspicious_suffixes:
        if pkg.endswith(suffix) and pkg[: -len(suffix)] in _get_top_packages():
            flags.append(f"Suspicious suffix '{suffix}' mimicking a known package")

    if "-" in pkg and pkg.replace("-", "") in _get_top_packages():
        flags.append("Name differs from a top package only by hyphen placement")

    return flags
