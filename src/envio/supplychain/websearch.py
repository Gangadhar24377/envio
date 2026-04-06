"""DuckDuckGo web search for package security intelligence."""

from __future__ import annotations

from dataclasses import dataclass

from envio.supplychain.cache import SupplyChainCache


@dataclass
class WebSearchResult:
    flagged: bool
    evidence: list[str]


def _search_duckduckgo(query: str) -> list[dict]:
    """Search DuckDuckGo and return results.

    Uses the ddgs library (formerly duckduckgo-search) which has no API key requirement.
    """
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        return results
    except Exception:
        return []


def _analyze_results(results: list[dict], package_name: str) -> list[str]:
    """Analyze search results for security warnings about a package."""
    evidence = []
    pkg_lower = package_name.lower()

    warning_keywords = [
        "malicious",
        "compromised",
        "supply chain",
        "backdoor",
        "malware",
        "trojan",
        "exploit",
        "vulnerability",
        "security advisory",
        "removed from pypi",
        "yanked",
        "phishing",
        "data exfiltration",
        "credential theft",
    ]

    for result in results:
        title = (result.get("title", "") or "").lower()
        body = (result.get("body", "") or "").lower()
        href = (result.get("href", "") or "").lower()

        combined = f"{title} {body} {href}"

        if (
            pkg_lower not in combined
            and package_name.lower().replace("-", "") not in combined
        ):
            continue

        for keyword in warning_keywords:
            if keyword in combined:
                snippet = result.get("title", "") or result.get("body", "")
                if snippet and snippet not in evidence:
                    evidence.append(snippet[:200])
                break

    return evidence


def search_package_security(package_name: str) -> WebSearchResult:
    """Search for security concerns about a package using DuckDuckGo.

    Searches for: "<pkg> malicious", "<pkg> compromised", "<pkg> supply chain attack"
    """
    cache = SupplyChainCache.get_instance()
    cached = cache.get(package_name.lower(), "web_search")
    if cached is not None:
        return WebSearchResult(**cached)

    search_queries = [
        f"{package_name} malicious",
        f"{package_name} compromised",
        f"{package_name} supply chain attack",
    ]

    all_evidence = []

    for query in search_queries:
        results = _search_duckduckgo(query)
        evidence = _analyze_results(results, package_name)
        all_evidence.extend(evidence)

    flagged = len(all_evidence) > 0

    result = WebSearchResult(
        flagged=flagged,
        evidence=all_evidence,
    )

    cache.set(
        package_name.lower(),
        "web_search",
        {
            "flagged": result.flagged,
            "evidence": result.evidence,
        },
    )

    return result
