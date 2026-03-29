"""Path utilities for envio."""

from __future__ import annotations

import os
from pathlib import Path


def get_default_envs_dir() -> Path:
    """Get the default environments directory using platform-appropriate conventions.

    Priority:
    1. ENVIO_ENVS_DIR environment variable (user override)
    2. $XDG_DATA_HOME/envio/envs on Linux/macOS (if XDG_DATA_HOME set)
    3. ~/.local/share/envio/envs on Linux/macOS (XDG default)
    4. ~/Documents/envio/envs on Windows (legacy compatibility)
    """
    # 1. Explicit override
    if env_override := os.getenv("ENVIO_ENVS_DIR"):
        return Path(env_override)

    # 2. XDG on Unix-like systems
    if os.name != "nt":
        xdg_data = os.getenv("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        return Path(xdg_data) / "envio" / "envs"

    # 3. Windows legacy path
    return Path.home() / "Documents" / "envio" / "envs"


def get_envio_config_dir() -> Path:
    """Get the configuration directory for envio.

    Priority:
    1. ENVIO_CONFIG_DIR environment variable (user override)
    2. $XDG_CONFIG_HOME/envio on Linux/macOS
    3. ~/.config/envio on Linux/macOS
    4. ~/.envio on Windows
    """
    if env_override := os.getenv("ENVIO_CONFIG_DIR"):
        return Path(env_override)

    if os.name != "nt":
        xdg_config = os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(xdg_config) / "envio"

    return Path.home() / ".envio"


def get_envio_cache_dir() -> Path:
    """Get the cache directory for envio.

    Priority:
    1. ENVIO_CACHE_DIR environment variable (user override)
    2. $XDG_CACHE_HOME/envio on Linux/macOS
    3. ~/.cache/envio on Linux/macOS
    4. ~/.envio/cache on Windows
    """
    if env_override := os.getenv("ENVIO_CACHE_DIR"):
        return Path(env_override)

    if os.name != "nt":
        xdg_cache = os.getenv("XDG_CACHE_HOME", str(Path.home() / ".cache"))
        return Path(xdg_cache) / "envio"

    return Path.home() / ".envio" / "cache"
