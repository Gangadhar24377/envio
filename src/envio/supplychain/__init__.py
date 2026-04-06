"""Supply chain security module for Envio."""

from envio.supplychain.remediation import suggest_alternative
from envio.supplychain.scanner import fast_scan, scan_packages

__all__ = [
    "fast_scan",
    "scan_packages",
    "suggest_alternative",
]
