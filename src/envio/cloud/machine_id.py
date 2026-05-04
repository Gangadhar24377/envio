"""Anonymous machine fingerprint for rate limiting.

Generates a SHA-256 hash of non-PII system attributes so the
cloud proxy can rate-limit per installation without user accounts.
The hash is NOT reversible to identify the user.
"""

from __future__ import annotations

import hashlib
import os
import platform
import sys


def get_machine_id() -> str:
    """Generate an anonymous, non-PII machine fingerprint.

    Components used (all hashed together):
    - hostname
    - OS username
    - OS type (Windows/Linux/Darwin)
    - Python executable path
    - CPU architecture

    Returns:
        32-character hex string (truncated SHA-256)
    """
    components = [
        platform.node(),
        _safe_login(),
        platform.system(),
        sys.executable,
        platform.machine(),
    ]
    raw = "|".join(components)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _safe_login() -> str:
    """Get username without raising on headless systems."""
    try:
        return os.getlogin()
    except OSError:
        return os.environ.get("USER", os.environ.get("USERNAME", "unknown"))
