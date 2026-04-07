"""Package diff engine — download, extract, and compare package versions."""

from __future__ import annotations

import hashlib
import tarfile
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import requests

from envio.utils.http_utils import get_with_retry


@dataclass
class FileDiff:
    """A single file change."""

    path: str
    status: str  # "added", "deleted", "modified"
    old_hash: str | None = None
    new_hash: str | None = None
    size_change: int = 0


@dataclass
class PackageDiff:
    """Diff between two versions of a package."""

    package: str
    old_version: str
    new_version: str
    added_files: list[FileDiff] = field(default_factory=list)
    deleted_files: list[FileDiff] = field(default_factory=list)
    modified_files: list[FileDiff] = field(default_factory=list)
    report: str = ""
    error: str | None = None


def _file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_extract(archive: tarfile.TarFile | zipfile.ZipFile, dest: Path) -> None:
    """Extract archive with path-traversal protection."""
    if isinstance(archive, tarfile.TarFile):
        members = archive.getmembers()
        for member in members:
            member_path = (dest / member.name).resolve()
            if not str(member_path).startswith(str(dest.resolve())):
                raise ValueError(f"Path traversal detected: {member.name}")
        archive.extractall(dest, filter="data")
    elif isinstance(archive, zipfile.ZipFile):
        for zip_member in archive.namelist():
            member_path = (dest / zip_member).resolve()
            if not str(member_path).startswith(str(dest.resolve())):
                raise ValueError(f"Path traversal detected: {zip_member}")
        archive.extractall(dest)


def _download_and_extract(package: str, version: str, dest: Path) -> Path | None:
    """Download a package version from PyPI and extract it.

    Returns the extracted directory path, or None on failure.
    """
    try:
        dest.mkdir(parents=True, exist_ok=True)
        url = f"https://pypi.org/pypi/{package}/{version}/json"
        response = get_with_retry(url, timeout=15)
        if response.status_code != 200:
            return None

        data = response.json()
        urls = data.get("urls", [])
        if not urls:
            return None

        # Prefer sdist (source distribution) for diffing
        sdist = None
        wheel = None
        for url_info in urls:
            if url_info.get("packagetype") == "sdist":
                sdist = url_info
            elif url_info.get("packagetype") == "bdist_wheel":
                wheel = url_info

        chosen = sdist or wheel
        if chosen is None:
            return None

        archive_url = chosen["url"]
        archive_response = requests.get(archive_url, timeout=30)
        if archive_response.status_code != 200:
            return None

        archive_path = dest / chosen["filename"]
        archive_path.write_bytes(archive_response.content)

        extract_dir = dest / "extracted"
        extract_dir.mkdir(exist_ok=True)

        if archive_path.suffix == ".gz" or archive_path.name.endswith(".tar.gz"):
            with tarfile.open(archive_path, "r:gz") as tar:
                _safe_extract(tar, extract_dir)
        elif archive_path.suffix == ".zip" or archive_path.name.endswith(".whl"):
            with zipfile.ZipFile(archive_path) as zf:
                _safe_extract(zf, extract_dir)
        elif archive_path.suffix == ".bz2" or archive_path.name.endswith(".tar.bz2"):
            with tarfile.open(archive_path, "r:bz2") as tar:
                _safe_extract(tar, extract_dir)
        elif archive_path.suffix == ".xz" or archive_path.name.endswith(".tar.xz"):
            with tarfile.open(archive_path, "r:xz") as tar:
                _safe_extract(tar, extract_dir)
        else:
            return None

        # Find the actual source directory (sdist archives have a top-level dir)
        contents = list(extract_dir.iterdir())
        if len(contents) == 1 and contents[0].is_dir():
            return contents[0]
        return extract_dir

    except Exception:
        return None


def _collect_files(directory: Path) -> dict[str, bytes]:
    """Collect all files in a directory with their contents."""
    files = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(directory)).replace("\\", "/")
            # Skip binary files and very large files
            try:
                content = file_path.read_bytes()
                if len(content) > 500_000:
                    continue
                # Skip common binary extensions
                skip_extensions = {
                    ".pyc",
                    ".pyo",
                    ".so",
                    ".dll",
                    ".dylib",
                    ".egg-info",
                    ".dist-info",
                    ".egg",
                    ".whl",
                }
                if any(rel_path.endswith(ext) for ext in skip_extensions):
                    continue
                files[rel_path] = content
            except (OSError, PermissionError):
                pass
    return files


def _compute_diff(
    old_files: dict[str, bytes], new_files: dict[str, bytes]
) -> list[FileDiff]:
    """Compute file-level diff between two versions."""
    diffs = []
    all_paths = set(old_files.keys()) | set(new_files.keys())

    for path in sorted(all_paths):
        old_content = old_files.get(path)
        new_content = new_files.get(path)

        if old_content is None:
            diffs.append(
                FileDiff(
                    path=path,
                    status="added",
                    new_hash=_file_hash(new_content) if new_content else None,
                    size_change=len(new_content) if new_content else 0,
                )
            )
        elif new_content is None:
            diffs.append(
                FileDiff(
                    path=path,
                    status="deleted",
                    old_hash=_file_hash(old_content),
                    size_change=-len(old_content),
                )
            )
        elif old_content != new_content:
            old_hash = _file_hash(old_content)
            new_hash = _file_hash(new_content)
            size_change = len(new_content) - len(old_content)
            diffs.append(
                FileDiff(
                    path=path,
                    status="modified",
                    old_hash=old_hash,
                    new_hash=new_hash,
                    size_change=size_change,
                )
            )

    return diffs


def _generate_report(
    package: str,
    old_version: str,
    new_version: str,
    diffs: list[FileDiff],
) -> str:
    """Generate a human-readable diff report for LLM analysis."""
    added = [d for d in diffs if d.status == "added"]
    deleted = [d for d in diffs if d.status == "deleted"]
    modified = [d for d in diffs if d.status == "modified"]

    lines = [
        f"Package: {package}",
        f"Old version: {old_version}",
        f"New version: {new_version}",
        "",
        f"Summary: {len(added)} files added, {len(deleted)} deleted, {len(modified)} modified",
        "",
    ]

    if added:
        lines.append("=== ADDED FILES ===")
        for d in added:
            lines.append(f"  + {d.path} ({d.size_change} bytes)")
        lines.append("")

    if deleted:
        lines.append("=== DELETED FILES ===")
        for d in deleted:
            lines.append(f"  - {d.path} ({abs(d.size_change)} bytes)")
        lines.append("")

    if modified:
        lines.append("=== MODIFIED FILES ===")
        for d in modified:
            lines.append(f"  ~ {d.path} (size change: {d.size_change:+d} bytes)")
        lines.append("")

    # Include content of suspicious files for LLM analysis
    suspicious_extensions = {".py", ".sh", ".bat", ".cmd", ".ps1", ".js", ".html"}
    for d in added + modified:
        if any(d.path.endswith(ext) for ext in suspicious_extensions):
            lines.append(f"--- Content of {d.path} ---")
            try:
                lines.append(f"[File: {d.path}, {d.size_change} bytes]")
            except Exception:
                pass
            lines.append("")

    return "\n".join(lines)


def get_package_versions(package: str) -> list[dict[str, str]]:
    """Get all versions of a package from PyPI.

    Returns list of dicts with version and upload_time.
    """
    try:
        url = f"https://pypi.org/pypi/{package}/json"
        response = get_with_retry(url, timeout=15)
        if response.status_code != 200:
            return []

        data = response.json()
        releases = data.get("releases", {})
        versions = []

        for version, files in releases.items():
            if not files:
                continue
            upload_time = ""
            for f in files:
                if f.get("upload_time_iso_8601"):
                    upload_time = f["upload_time_iso_8601"]
                    break
            versions.append(
                {
                    "version": version,
                    "upload_time": upload_time,
                }
            )

        return versions
    except Exception:
        return []


def diff_package(
    package: str,
    old_version: str,
    new_version: str,
) -> PackageDiff:
    """Download two versions of a package and generate a diff report.

    Uses a temporary directory that is automatically cleaned up.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Download old and new versions concurrently — they are fully independent.
        with ThreadPoolExecutor(max_workers=2) as executor:
            old_future = executor.submit(
                _download_and_extract, package, old_version, tmp_path / "old"
            )
            new_future = executor.submit(
                _download_and_extract, package, new_version, tmp_path / "new"
            )

        old_dir = old_future.result()
        if old_dir is None:
            return PackageDiff(
                package=package,
                old_version=old_version,
                new_version=new_version,
                error=f"Failed to download version {old_version}",
            )

        new_dir = new_future.result()
        if new_dir is None:
            return PackageDiff(
                package=package,
                old_version=old_version,
                new_version=new_version,
                error=f"Failed to download version {new_version}",
            )

        old_files = _collect_files(old_dir)
        new_files = _collect_files(new_dir)

        diffs = _compute_diff(old_files, new_files)
        report = _generate_report(package, old_version, new_version, diffs)

        added = [d for d in diffs if d.status == "added"]
        deleted = [d for d in diffs if d.status == "deleted"]
        modified = [d for d in diffs if d.status == "modified"]

        return PackageDiff(
            package=package,
            old_version=old_version,
            new_version=new_version,
            added_files=added,
            deleted_files=deleted,
            modified_files=modified,
            report=report,
        )
