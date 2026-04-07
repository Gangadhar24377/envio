"""Package reputation scoring."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone

from envio.supplychain.cache import SupplyChainCache
from envio.utils.http_utils import get_with_retry


@dataclass
class ReputationResult:
    score: int
    download_count: int
    package_age_days: int
    release_count: int
    maintainer_count: int
    details: str


def _get_pypi_info(package_name: str) -> dict | None:
    """Fetch package info from PyPI JSON API."""
    cache = SupplyChainCache.get_instance()
    cached = cache.get(package_name.lower(), "reputation")
    if cached is not None:
        return cached

    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = get_with_retry(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            cache.set(package_name.lower(), "reputation", data)
            return data
    except Exception:
        pass

    return None


def _parse_download_count(package_name: str) -> int:
    """Get approximate download count from PyPI stats."""
    try:
        url = f"https://pypistats.org/api/packages/{package_name}/recent"
        response = get_with_retry(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("last_month", 0)
    except Exception:
        pass
    return 0


def score_package(package_name: str) -> ReputationResult:
    """Score a package's reputation on a 0-100 scale (higher = riskier).

    Fetches PyPI metadata and download statistics concurrently.
    """
    with ThreadPoolExecutor(max_workers=2) as executor:
        info_future = executor.submit(_get_pypi_info, package_name)
        downloads_future = executor.submit(_parse_download_count, package_name)

    info = info_future.result()
    prefetched_downloads = downloads_future.result()

    if info is None:
        return ReputationResult(
            score=80,
            download_count=0,
            package_age_days=0,
            release_count=0,
            maintainer_count=0,
            details="Package not found on PyPI",
        )

    info_data = info.get("info", {})
    releases = info.get("releases", {})

    download_count = prefetched_downloads
    release_count = len([v for v in releases.values() if v])

    first_release = None
    last_release = None
    for _version, files in releases.items():
        if not files:
            continue
        for f in files:
            upload_time = f.get("upload_time_iso_8601", "")
            if upload_time:
                try:
                    dt = datetime.fromisoformat(upload_time.replace("Z", "+00:00"))
                    if first_release is None or dt < first_release:
                        first_release = dt
                    if last_release is None or dt > last_release:
                        last_release = dt
                except (ValueError, TypeError):
                    pass

    package_age_days = 0
    if first_release:
        now = datetime.now(timezone.utc)
        package_age_days = (now - first_release).days

    maintainer_count = len(info_data.get("maintainers", []))

    score = 0
    details_parts = []

    if download_count < 1000:
        score += 25
        details_parts.append(f"Low downloads ({download_count}/month)")
    elif download_count < 10000:
        score += 15
        details_parts.append(f"Moderate downloads ({download_count}/month)")
    elif download_count < 100000:
        score += 5
    else:
        details_parts.append(f"High downloads ({download_count}/month)")

    if package_age_days < 30:
        score += 20
        details_parts.append(f"Very new package ({package_age_days} days old)")
    elif package_age_days < 90:
        score += 10
        details_parts.append(f"Relatively new ({package_age_days} days old)")
    elif package_age_days < 365:
        score += 5
    else:
        details_parts.append(f"Established package ({package_age_days} days old)")

    if release_count < 3:
        score += 10
        details_parts.append(f"Few releases ({release_count})")

    if maintainer_count <= 1:
        score += 5
        details_parts.append("Single maintainer")

    score = min(score, 100)

    return ReputationResult(
        score=score,
        download_count=download_count,
        package_age_days=package_age_days,
        release_count=release_count,
        maintainer_count=maintainer_count,
        details="; ".join(details_parts) if details_parts else "No risk factors",
    )
