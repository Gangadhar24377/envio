"""Supply chain scanner - orchestrates all security checks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from envio.supplychain.detector import (
    DetectionResult,
    check_suspicious_patterns,
    check_typosquatting,
)
from envio.supplychain.osv import check_osv
from envio.supplychain.reputation import ReputationResult, score_package
from envio.supplychain.websearch import search_package_security


@dataclass
class PackageRisk:
    package: str
    version: str | None
    risk_score: int
    flags: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanResult:
    packages: list[PackageRisk]
    total_score: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    safe_count: int


def _extract_package_name(pkg_spec: str) -> tuple[str, str | None]:
    """Extract package name and version from a spec like 'requests==2.31.0'."""
    match = re.match(r"^([A-Za-z0-9._-]+)(?:[><=!~]+.+)?$", pkg_spec.strip())
    if match:
        name = match.group(1)
        version = None
        ver_match = re.search(r"==([^\s;]+)", pkg_spec)
        if ver_match:
            version = ver_match.group(1)
        return name, version
    return pkg_spec, None


def _should_search_web(
    package_name: str,
    typo_result: DetectionResult,
    reputation: ReputationResult,
    deep_mode: bool,
) -> bool:
    """Decide whether to run web search for a package.

    ALWAYS search if:
    - Package NOT in top 10k downloads AND flagged by static analysis
    - Flagged by typosquatting detection
    - Very new package (< 30 days)
    - User runs --deep flag

    NEVER search if:
    - Package in top 1000 AND no flags
    """
    if deep_mode:
        return True

    if typo_result.is_typo:
        return True

    if reputation.score >= 30:
        return True

    if reputation.package_age_days < 30:
        return True

    if reputation.download_count < 10000:
        return True

    return False


def scan_package(
    package_spec: str,
    deep_mode: bool = False,
) -> PackageRisk:
    """Run all supply chain checks on a single package."""
    pkg_name, pkg_version = _extract_package_name(package_spec)

    flags = []
    suggestions = []
    risk_score = 0
    details: dict[str, Any] = {}

    typo_result = check_typosquatting(pkg_name)
    details["typo"] = {
        "is_typo": typo_result.is_typo,
        "suggested": typo_result.suggested_package,
        "confidence": typo_result.confidence,
    }

    if typo_result.is_typo:
        risk_score += 60
        flags.append(
            f"Possible typo of '{typo_result.suggested_package}' ({typo_result.confidence:.0%} match)"
        )
        if typo_result.suggested_package:
            suggestions.append(f"Did you mean '{typo_result.suggested_package}'?")

    suspicious = check_suspicious_patterns(pkg_name)
    details["suspicious_patterns"] = suspicious
    for pattern in suspicious:
        risk_score += 30
        flags.append(pattern)

    reputation = score_package(pkg_name)
    details["reputation"] = {
        "score": reputation.score,
        "downloads": reputation.download_count,
        "age_days": reputation.package_age_days,
        "releases": reputation.release_count,
        "maintainers": reputation.maintainer_count,
    }
    risk_score += reputation.score // 3
    if reputation.details != "No risk factors":
        flags.append(reputation.details)

    osv_result = check_osv(pkg_name, pkg_version)
    details["osv"] = {
        "has_vulns": osv_result.has_vulns,
        "vuln_count": osv_result.vuln_count,
    }
    if osv_result.has_vulns:
        risk_score = 100
        vuln_ids = [v.get("id", "unknown") for v in osv_result.vulns[:5]]
        flags.append(f"Known vulnerabilities: {', '.join(vuln_ids)}")
        if pkg_version:
            suggestions.append(
                "Update to a patched version (check OSV.dev for details)"
            )

    if (
        osv_result.has_vulns
        or risk_score >= 50
        or _should_search_web(pkg_name, typo_result, reputation, deep_mode)
    ):
        web_result = search_package_security(pkg_name)
        details["web_search"] = {
            "flagged": web_result.flagged,
            "evidence_count": len(web_result.evidence),
        }
        if web_result.flagged:
            risk_score += 20
            flags.append(
                f"Security concerns found in web sources ({len(web_result.evidence)} mentions)"
            )
            for ev in web_result.evidence[:2]:
                suggestions.append(ev)

    risk_score = min(risk_score, 100)

    return PackageRisk(
        package=pkg_name,
        version=pkg_version,
        risk_score=risk_score,
        flags=flags,
        suggestions=suggestions,
        details=details,
    )


def scan_packages(
    packages: list[str],
    deep_mode: bool = False,
) -> ScanResult:
    """Run supply chain checks on a list of packages."""
    results = []

    for pkg_spec in packages:
        risk = scan_package(pkg_spec, deep_mode=deep_mode)
        results.append(risk)

    critical = sum(1 for r in results if r.risk_score >= 90)
    high = sum(1 for r in results if 70 <= r.risk_score < 90)
    medium = sum(1 for r in results if 40 <= r.risk_score < 70)
    low = sum(1 for r in results if 15 <= r.risk_score < 40)
    safe = sum(1 for r in results if r.risk_score < 15)

    total_score = sum(r.risk_score for r in results)

    return ScanResult(
        packages=results,
        total_score=total_score,
        critical_count=critical,
        high_count=high,
        medium_count=medium,
        low_count=low,
        safe_count=safe,
    )


def fast_scan(package_spec: str) -> PackageRisk:
    """Fast pre-install check: typosquatting + OSV.dev only.

    Skips reputation scoring and web search for speed.
    Used during install/add/prompt/init/sync flows.
    """
    pkg_name, pkg_version = _extract_package_name(package_spec)

    flags = []
    suggestions = []
    risk_score = 0
    details: dict[str, Any] = {}

    typo_result = check_typosquatting(pkg_name)
    details["typo"] = {
        "is_typo": typo_result.is_typo,
        "suggested": typo_result.suggested_package,
        "confidence": typo_result.confidence,
    }

    if typo_result.is_typo:
        risk_score += 60
        flags.append(
            f"Possible typo of '{typo_result.suggested_package}' ({typo_result.confidence:.0%} match)"
        )
        if typo_result.suggested_package:
            suggestions.append(f"Did you mean '{typo_result.suggested_package}'?")

    suspicious = check_suspicious_patterns(pkg_name)
    details["suspicious_patterns"] = suspicious
    for pattern in suspicious:
        risk_score += 30
        flags.append(pattern)

    osv_result = check_osv(pkg_name, pkg_version)
    details["osv"] = {
        "has_vulns": osv_result.has_vulns,
        "vuln_count": osv_result.vuln_count,
    }
    if osv_result.has_vulns:
        risk_score = 100
        vuln_ids = [v.get("id", "unknown") for v in osv_result.vulns[:5]]
        flags.append(f"Known vulnerabilities: {', '.join(vuln_ids)}")
        if pkg_version:
            suggestions.append("Update to a patched version")

    risk_score = min(risk_score, 100)

    return PackageRisk(
        package=pkg_name,
        version=pkg_version,
        risk_score=risk_score,
        flags=flags,
        suggestions=suggestions,
        details=details,
    )
