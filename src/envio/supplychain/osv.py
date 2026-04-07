"""OSV.dev vulnerability check with batch query support."""

from __future__ import annotations

from dataclasses import dataclass

from envio.supplychain.cache import SupplyChainCache
from envio.utils.http_utils import get_with_retry


@dataclass
class OSVResult:
    has_vulns: bool
    vuln_count: int
    vulns: list[dict]


def check_osv(package_name: str, version: str | None = None) -> OSVResult:
    """Check for known vulnerabilities via OSV.dev API.

    OSV.dev is free, requires no authentication.
    """
    cache = SupplyChainCache.get_instance()
    cache_key = f"{package_name}:{version}" if version else package_name
    cached = cache.get(cache_key, "osv")
    if cached is not None:
        return OSVResult(**cached)

    vulns = []

    try:
        if version:
            query = {
                "package": {"name": package_name, "ecosystem": "PyPI"},
                "version": version,
            }
        else:
            query = {
                "package": {"name": package_name, "ecosystem": "PyPI"},
            }

        response = get_with_retry(
            "https://api.osv.dev/v1/query",
            timeout=10,
            json=query,
        )

        if response.status_code == 200:
            data = response.json()
            vulns = data.get("vulns", [])
    except Exception:
        pass

    result = OSVResult(
        has_vulns=len(vulns) > 0,
        vuln_count=len(vulns),
        vulns=vulns,
    )

    cache.set(
        cache_key,
        "osv",
        {
            "has_vulns": result.has_vulns,
            "vuln_count": result.vuln_count,
            "vulns": result.vulns,
        },
    )

    return result


def check_osv_batch(
    packages: list[tuple[str, str | None]],
) -> dict[str, OSVResult]:
    """Check multiple packages for vulnerabilities in a single batch request.

    OSV.dev supports batch queries which is much faster than individual calls.

    Args:
        packages: List of (package_name, version) tuples

    Returns:
        Dict mapping "name:version" keys to OSVResult
    """
    cache = SupplyChainCache.get_instance()
    results: dict[str, OSVResult] = {}
    uncached: list[tuple[str, str, str | None]] = []

    for pkg_name, pkg_version in packages:
        cache_key = f"{pkg_name}:{pkg_version}" if pkg_version else pkg_name
        cached = cache.get(cache_key, "osv")
        if cached is not None:
            results[cache_key] = OSVResult(**cached)
        else:
            uncached.append((cache_key, pkg_name, pkg_version))

    if not uncached:
        return results

    batch_query = {
        "queries": [
            {
                "package": {"name": pkg_name, "ecosystem": "PyPI"},
                **({"version": pkg_version} if pkg_version else {}),
            }
            for _, pkg_name, pkg_version in uncached
        ]
    }

    try:
        response = get_with_retry(
            "https://api.osv.dev/v1/querybatch",
            timeout=30,
            json=batch_query,
        )

        if response.status_code == 200:
            data = response.json()
            vuln_results = data.get("results", [])

            for i, (_, pkg_name, pkg_version) in enumerate(uncached):
                cache_key = f"{pkg_name}:{pkg_version}" if pkg_version else pkg_name
                vulns = []
                if i < len(vuln_results):
                    vulns = vuln_results[i].get("vulns", [])

                result = OSVResult(
                    has_vulns=len(vulns) > 0,
                    vuln_count=len(vulns),
                    vulns=vulns,
                )

                results[cache_key] = result
                cache.set(
                    cache_key,
                    "osv",
                    {
                        "has_vulns": result.has_vulns,
                        "vuln_count": result.vuln_count,
                        "vulns": result.vulns,
                    },
                )
    except Exception:
        for cache_key, _pkg_name, _pkg_version in uncached:
            results[cache_key] = OSVResult(has_vulns=False, vuln_count=0, vulns=[])

    return results
