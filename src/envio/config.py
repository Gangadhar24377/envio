"""Envio configuration management."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def get_config_dir() -> Path:
    """Get the configuration directory for envio."""
    if os.name != "nt":
        xdg_config = os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(xdg_config) / "envio"
    return Path.home() / ".envio"


def get_config_path() -> Path:
    """Get the path to the config file."""
    return get_config_dir() / "config.json"


def load_config() -> dict[str, Any]:
    """Load the configuration from disk."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to disk."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_default_envs_dir(prompt: bool = True) -> tuple[str | None, str | None]:
    """Get the default environments directory.

    Args:
        prompt: If True and no config exists, prompt user to set one.

    Returns:
        Tuple of (default_dir, package_manager).
        If not configured, returns (None, None).
    """
    config = load_config()

    default_dir = config.get("default_envs_dir")
    package_manager = config.get("preferred_package_manager", "pip")

    if default_dir:
        return default_dir, package_manager

    if not prompt:
        return None, package_manager

    # First run - prompt user
    print("\n" + "=" * 50)
    print("First run setup - Welcome to Envio!")
    print("=" * 50)
    print("\nI need to set up some defaults for you.")
    print()

    # Ask for default directory
    default_path_input = input(
        "Where should I create your environments? [default: ~/.envs]: "
    ).strip()
    if not default_path_input:
        default_path_input = "~/.envs"

    # Expand user home
    default_dir = str(Path(default_path_input).expanduser())

    # Ask for preferred package manager
    print("\nWhich package manager do you prefer?")
    print("  1. pip (default)")
    print("  2. uv (faster, modern)")
    print("  3. conda")
    pm_choice = input("Choice [1]: ").strip() or "1"

    pm_map = {"1": "pip", "2": "uv", "3": "conda"}
    package_manager = pm_map.get(pm_choice, "pip")

    # Save config
    config["default_envs_dir"] = default_dir
    config["preferred_package_manager"] = package_manager
    save_config(config)

    print(f"\n✓ Default directory set to: {default_dir}")
    print(f"✓ Preferred package manager: {package_manager}")
    print("\nYou can change these anytime with: envio config")
    print("=" * 50 + "\n")

    return default_dir, package_manager


def get_preferred_package_manager() -> str:
    """Get the preferred package manager."""
    config = load_config()
    return config.get("preferred_package_manager", "pip")


def set_default_envs_dir(path: str) -> None:
    """Set the default environments directory."""
    config = load_config()
    config["default_envs_dir"] = str(Path(path).expanduser())
    save_config(config)


def set_preferred_package_manager(manager: str) -> None:
    """Set the preferred package manager."""
    valid = {"pip", "uv", "conda"}
    if manager not in valid:
        raise ValueError(f"Invalid package manager. Choose from: {', '.join(valid)}")
    config = load_config()
    config["preferred_package_manager"] = manager
    save_config(config)


def show_config() -> None:
    """Display current configuration."""
    config = load_config()

    print("\n╭─ Envio Configuration ─")
    print("│")

    default_dir = config.get("default_envs_dir", "~/.envs (not set)")
    print(f"│  Default envs directory: {default_dir}")

    pm = config.get("preferred_package_manager", "pip")
    print(f"│  Preferred package manager: {pm}")

    config_path = get_config_path()
    print("│")
    print(f"│  Config file: {config_path}")
    print("│")
    print("╰─ Change with: envio config set <key> <value>")
    print()


def is_first_run() -> bool:
    """Check if this is the first time running envio."""
    config_path = get_config_path()
    return not config_path.exists()


def ensure_config(prompt_first_run: bool = True) -> dict[str, Any]:
    """Ensure config exists, prompting user on first run if needed."""
    config = load_config()

    if not config and prompt_first_run:
        # First run - get defaults from user
        default_dir, package_manager = get_default_envs_dir(prompt=True)
        config = {
            "default_envs_dir": default_dir,
            "preferred_package_manager": package_manager,
        }

    return config
