"""OSV.dev vulnerability check."""

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
