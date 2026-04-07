"""Supply chain scanner - orchestrates all security checks.

Optimized with ThreadPoolExecutor for parallel I/O and batch OSV.dev queries.
Session-level LRU cache avoids redundant checks within a single scan run.
Web searches are capped at MAX_WEB_SEARCHES_PER_SCAN to prevent rate limiting.
"""

from __future__ import annotations

import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from envio.supplychain.detector import (
    DetectionResult,
    check_suspicious_patterns,
    check_typosquatting,
)
from envio.supplychain.osv import OSVResult, check_osv, check_osv_batch
from envio.supplychain.reputation import ReputationResult, score_package
from envio.supplychain.websearch import search_package_security

# Maximum number of web searches per scan session to avoid rate limiting.
MAX_WEB_SEARCHES_PER_SCAN = 5


class _SessionCache:
    """In-memory LRU cache for a single scan session.

    Prevents redundant checks when the same package appears multiple times
    (e.g., direct + transitive dependency listed separately).
    Thread-safe via a lock used around the web-search counter.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._web_search_count = 0
        # Per-package result cache: pkg_name -> PackageRisk
        self._results: dict[str, PackageRisk] = {}

    def get(self, key: str) -> PackageRisk | None:
        return self._results.get(key)

    def set(self, key: str, value: PackageRisk) -> None:
        self._results[key] = value

    def can_web_search(self) -> bool:
        with self._lock:
            return self._web_search_count < MAX_WEB_SEARCHES_PER_SCAN

    def record_web_search(self) -> None:
        with self._lock:
            self._web_search_count += 1

    @property
    def web_search_count(self) -> int:
        with self._lock:
            return self._web_search_count


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
    typo_result: DetectionResult,
    reputation: ReputationResult,
    deep_mode: bool,
) -> bool:
    """Decide whether to run web search for a package."""
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


def _build_risk(
    pkg_name: str,
    pkg_version: str | None,
    typo_result: DetectionResult,
    suspicious: list[str],
    reputation: ReputationResult,
    osv_result: OSVResult,
    web_result: dict[str, Any] | None,
    deep_mode: bool = False,
) -> PackageRisk:
    """Build a PackageRisk from individual check results."""
    flags = []
    suggestions = []
    risk_score = 0
    details: dict[str, Any] = {}

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

    details["suspicious_patterns"] = suspicious
    for pattern in suspicious:
        risk_score += 30
        flags.append(pattern)

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

    if web_result is not None:
        details["web_search"] = {
            "flagged": web_result["flagged"],
            "evidence_count": web_result["evidence_count"],
        }
        if web_result["flagged"]:
            risk_score += 20
            evidence = web_result.get("evidence", [])
            flags.append(
                f"Security concerns found in web sources ({len(evidence)} mentions)"
            )
            for ev in evidence[:2]:
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
    max_workers: int = 10,
) -> ScanResult:
    """Run supply chain checks on a list of packages in parallel.

    Uses ThreadPoolExecutor for parallel HTTP calls and batch OSV.dev queries.
    Web searches are capped at MAX_WEB_SEARCHES_PER_SCAN per session.
    Duplicate packages are resolved from a session-level in-memory cache.
    """
    session = _SessionCache()

    parsed = [_extract_package_name(pkg) for pkg in packages]
    pkg_names = [name for name, _ in parsed]
    pkg_versions = [ver for _, ver in parsed]

    osv_queries = list(zip(pkg_names, pkg_versions, strict=True))
    osv_results_map = check_osv_batch(osv_queries)

    results: list[PackageRisk] = [None] * len(packages)  # type: ignore[list-item]

    def _scan_single(idx: int) -> tuple[int, PackageRisk]:
        pkg_name = pkg_names[idx]
        pkg_version = pkg_versions[idx]

        # Return cached result for duplicate packages in the same scan run.
        cache_key = f"{pkg_name}:{pkg_version or ''}"
        cached = session.get(cache_key)
        if cached is not None:
            return (idx, cached)

        typo_result = check_typosquatting(pkg_name)
        suspicious = check_suspicious_patterns(pkg_name)
        reputation = score_package(pkg_name)

        osv_key = f"{pkg_name}:{pkg_version}" if pkg_version else pkg_name
        osv_result = osv_results_map.get(
            osv_key, OSVResult(has_vulns=False, vuln_count=0, vulns=[])
        )

        web_result = None
        wants_web = osv_result.has_vulns or _should_search_web(
            typo_result, reputation, deep_mode
        )
        if wants_web and session.can_web_search():
            session.record_web_search()
            ws = search_package_security(pkg_name)
            web_result = {
                "flagged": ws.flagged,
                "evidence_count": len(ws.evidence),
                "evidence": ws.evidence,
            }

        risk = _build_risk(
            pkg_name,
            pkg_version,
            typo_result,
            suspicious,
            reputation,
            osv_result,
            web_result,
            deep_mode,
        )
        session.set(cache_key, risk)
        return (idx, risk)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_scan_single, i): i for i in range(len(packages))}
        for future in as_completed(futures):
            idx, risk = future.result()
            results[idx] = risk

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


def _is_recently_updated(package_name: str, days: int = 30) -> bool:
    """Check if a package has been updated in the last N days."""
    try:
        from envio.supplychain.diff import get_package_versions

        versions = get_package_versions(package_name)
        if not versions:
            return False

        latest = versions[-1]
        upload_time = latest.get("upload_time", "")
        if not upload_time:
            return False

        try:
            upload_dt = datetime.fromisoformat(upload_time.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return (now - upload_dt).days <= days
        except (ValueError, TypeError):
            return False
    except Exception:
        return False


def _run_diff_analysis(
    package_name: str,
    current_version: str | None,
) -> dict[str, Any]:
    """Run diff analysis between current and latest version."""
    from envio.supplychain.analyzer import analyze_diff
    from envio.supplychain.diff import diff_package, get_package_versions

    versions = get_package_versions(package_name)
    if not versions:
        return {"error": "Could not fetch versions"}

    latest_version = versions[-1]["version"]

    if current_version is None or current_version == latest_version:
        return {"skipped": True, "reason": "Already on latest version"}

    diff_result = diff_package(package_name, current_version, latest_version)
    if diff_result.error:
        return {"error": diff_result.error}

    analysis = analyze_diff(
        package_name,
        current_version,
        latest_version,
        diff_result.report,
    )

    if analysis.error:
        return {"error": analysis.error}

    return {
        "skipped": False,
        "verdict": analysis.verdict,
        "risk_score": analysis.risk_score,
        "categories": analysis.categories_found,
        "findings": [
            {
                "category": f.category,
                "file": f.file,
                "description": f.description,
                "severity": f.severity,
            }
            for f in analysis.findings
        ],
        "summary": analysis.summary,
    }


def scan_package_with_diff(
    package_spec: str,
    deep_mode: bool = False,
) -> PackageRisk:
    """Run full supply chain check including LLM diff analysis.

    Diff analysis runs when:
    - deep_mode is True (all packages)
    - Package was updated in last 30 days
    - Package is already flagged by static checks
    """
    pkg_name, pkg_version = _extract_package_name(package_spec)

    risk = scan_package(package_spec, deep_mode=deep_mode)

    should_diff = deep_mode or _is_recently_updated(pkg_name) or risk.risk_score >= 30

    if should_diff:
        diff_result = _run_diff_analysis(pkg_name, pkg_version)

        if not diff_result.get("skipped") and not diff_result.get("error"):
            risk.details["diff_analysis"] = diff_result
            verdict = diff_result.get("verdict", "unknown")

            if verdict == "malicious":
                risk.risk_score = 100
                risk.flags.append("LLM analysis: package appears malicious")
            elif verdict == "suspicious":
                risk.risk_score = min(risk.risk_score + 40, 100)
                risk.flags.append(
                    f"LLM analysis: suspicious changes detected ({diff_result.get('summary', '')})"
                )
            elif verdict == "safe":
                risk.flags.append("LLM analysis: changes appear safe")

            categories = diff_result.get("categories", [])
            if categories:
                risk.flags.append(f"Categories: {', '.join(categories)}")

    return risk


def scan_package(
    package_spec: str,
    deep_mode: bool = False,
) -> PackageRisk:
    """Run all supply chain checks on a single package."""
    pkg_name, pkg_version = _extract_package_name(package_spec)

    typo_result = check_typosquatting(pkg_name)
    suspicious = check_suspicious_patterns(pkg_name)
    reputation = score_package(pkg_name)
    osv_result = check_osv(pkg_name, pkg_version)

    web_result = None
    if osv_result.has_vulns or _should_search_web(typo_result, reputation, deep_mode):
        ws = search_package_security(pkg_name)
        web_result = {
            "flagged": ws.flagged,
            "evidence_count": len(ws.evidence),
            "evidence": ws.evidence,
        }

    return _build_risk(
        pkg_name,
        pkg_version,
        typo_result,
        suspicious,
        reputation,
        osv_result,
        web_result,
        deep_mode,
    )
