"""Typosquatting and suspicious pattern detection.

Optimized with set-based lookups and prefix filtering to avoid
O(n) Levenshtein scans through all 10k packages.
"""

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


def _load_top_packages(top_n: int = 10000) -> tuple[list[str], set[str]]:
    """Load top N PyPI packages by download count.

    Returns both a list (for ordered iteration) and a set (for O(1) lookups).
    """
    try:
        with urllib.request.urlopen(TOP_PACKAGES_URL, timeout=15) as resp:
            data = json.loads(resp.read())
        names = [row["project"].lower() for row in data["rows"][:top_n]]
        return names, set(names)
    except Exception:
        return [], set()


def _get_top_packages() -> tuple[list[str], set[str]]:
    cache = SupplyChainCache.get_instance()
    cached = cache.get("top_packages", "detector")
    if cached is not None and isinstance(cached, dict) and "list" in cached:
        return cached["list"], set(cached["set"])
    pkg_list, pkg_set = _load_top_packages()
    if pkg_list:
        cache.set("top_packages", "detector", {"list": pkg_list, "set": list(pkg_set)})
    return pkg_list, pkg_set


def check_typosquatting(package_name: str) -> DetectionResult:
    """Check if a package name is a likely typo of a popular package.

    Optimized: uses set for O(1) membership, prefix filter before Levenshtein.
    """
    pkg = package_name.lower().strip()

    top_list, top_set = _get_top_packages()

    if pkg in top_set:
        return DetectionResult(
            is_typo=False,
            suggested_package=None,
            confidence=0.0,
            reason="Package is in the top 10k list",
        )

    # Prefix filter: only check packages that share the first 2 characters
    # This reduces the search space from 10k to ~200-500 candidates
    prefix = pkg[:2]
    candidates = [p for p in top_list if p.startswith(prefix)]

    best_match: str | None = None
    best_distance = float("inf")
    best_len = 0

    for known_pkg in candidates:
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

    _, top_set = _get_top_packages()

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
        if pkg.startswith(prefix) and pkg[len(prefix) :] in top_set:
            flags.append(f"Suspicious prefix '{prefix}' mimicking a known package")

    for suffix in known_suspicious_suffixes:
        if pkg.endswith(suffix) and pkg[: -len(suffix)] in top_set:
            flags.append(f"Suspicious suffix '{suffix}' mimicking a known package")

    if "-" in pkg and pkg.replace("-", "") in top_set:
        flags.append("Name differs from a top package only by hyphen placement")

    return flags
