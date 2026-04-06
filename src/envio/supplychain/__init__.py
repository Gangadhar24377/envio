"""Supply chain security module for Envio."""

from envio.supplychain.analyzer import DiffAnalysis, analyze_diff
from envio.supplychain.diff import PackageDiff, diff_package
from envio.supplychain.remediation import suggest_alternative
from envio.supplychain.scanner import (
    fast_scan,
    scan_package,
    scan_package_with_diff,
    scan_packages,
)

__all__ = [
    "DiffAnalysis",
    "PackageDiff",
    "analyze_diff",
    "diff_package",
    "fast_scan",
    "scan_package",
    "scan_package_with_diff",
    "scan_packages",
    "suggest_alternative",
]
