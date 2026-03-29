"""Envio configuration management."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Provider detection from API key prefix
_PROVIDER_PREFIXES = {
    "sk-": "openai",
    "sk-ant-": "anthropic",
}

# Available providers
AVAILABLE_PROVIDERS = [
    "openai",
    "anthropic",
    "together",
    "cohere",
    "replicate",
    "ollama",
]

# Default models per provider
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-sonnet-20240229",
    "together": "together-ai-7b",
    "cohere": "command",
    "replicate": "replicate-7b",
    "ollama": "llama3",
}


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
    """Save configuration to disk with secure permissions."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = get_config_path()

    # Set directory permissions (Unix only)
    if os.name != "nt":
        config_dir.chmod(0o700)

    # Write to temp file first for atomic operation
    temp_path = config_path.with_suffix(".tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        # Set file permissions (Unix only)
        if os.name != "nt":
            temp_path.chmod(0o600)

        # Atomic rename
        if config_path.exists():
            config_path.unlink()
        temp_path.rename(config_path)
    except Exception as e:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise e


def detect_provider_from_key(api_key: str) -> str | None:
    """Auto-detect provider from API key prefix.

    Returns:
        Provider name or None if unknown
    """
    if not api_key:
        return "ollama"

    # Sort prefixes by length (longest first) to match specific prefixes before general ones
    sorted_prefixes = sorted(
        _PROVIDER_PREFIXES.items(), key=lambda x: len(x[0]), reverse=True
    )

    for prefix, provider in sorted_prefixes:
        if api_key.startswith(prefix):
            return provider

    return None


def set_api_key(api_key: str, provider: str | None = None) -> str:
    """Set API key with auto-detection.

    Args:
        api_key: The API key
        provider: Explicit provider (optional, auto-detected if not provided)

    Returns:
        The provider that was set
    """
    config = load_config()

    if not api_key:
        # Empty API key = Ollama (no key needed)
        config["api_key"] = ""
        config["provider"] = "ollama"
        save_config(config)
        return "ollama"

    # Auto-detect provider if not specified
    if not provider:
        provider = detect_provider_from_key(api_key)

    if not provider:
        # Unknown key format - need user input
        return ""  # Signal to caller to ask user

    config["api_key"] = api_key
    config["provider"] = provider
    save_config(config)
    return provider


def set_serper_api_key(api_key: str) -> None:
    """Set Serper API key.

    Args:
        api_key: The Serper API key
    """
    config = load_config()
    config["serper_api_key"] = api_key
    save_config(config)
    return provider


def set_provider(provider: str) -> None:
    """Set the LLM provider explicitly."""
    if provider not in AVAILABLE_PROVIDERS:
        raise ValueError(
            f"Unknown provider: {provider}. Available: {', '.join(AVAILABLE_PROVIDERS)}"
        )

    config = load_config()
    config["provider"] = provider
    save_config(config)


def set_model(model: str) -> None:
    """Set the LLM model."""
    config = load_config()
    config["model"] = model
    save_config(config)


def get_api_key() -> str | None:
    """Get API key from config file."""
    config = load_config()
    return config.get("api_key") or None


def get_serper_api_key() -> str | None:
    """Get Serper API key from config file."""
    config = load_config()
    return config.get("serper_api_key") or None


def get_provider() -> str:
    """Get provider from config or auto-detection."""
    config = load_config()

    provider = config.get("provider")
    if provider:
        return provider

    # Auto-detect from API key
    api_key = get_api_key()
    if api_key:
        detected = detect_provider_from_key(api_key)
        if detected:
            return detected

    # Check if Ollama is available
    try:
        from envio.llm.client import is_ollama_available

        if is_ollama_available():
            return "ollama"
    except Exception:
        pass

    return "openai"  # Default


def get_model() -> str:
    """Get model from config."""
    config = load_config()

    model = config.get("model")
    if model:
        return model

    # Get default for provider
    provider = get_provider()
    return DEFAULT_MODELS.get(provider, "gpt-4o-mini")


def show_config() -> None:
    """Display current configuration."""
    config = load_config()

    # Try to import Rich, fall back to plain text if not available
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        use_rich = True
    except ImportError:
        use_rich = False

    if use_rich:
        console = Console()
        # Create Rich table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        # Default directory
        default_dir = config.get("default_envs_dir", "~/.envs (not set)")
        table.add_row("Default envs directory:", default_dir)

        # Package manager
        pm = config.get("preferred_package_manager", "pip")
        table.add_row("Preferred package manager:", pm)

        # Provider and model
        provider = config.get("provider", "not set")
        model = config.get("model", "not set")

        # Color provider and model based on whether they're set
        provider_style = "green" if provider != "not set" else "red"
        model_style = "green" if model != "not set" else "red"
        table.add_row("LLM provider:", Text(provider, style=provider_style))
        table.add_row("LLM model:", Text(model, style=model_style))

        # API key (masked)
        api_key = config.get("api_key", "")
        if api_key:
            if len(api_key) > 12:
                masked = api_key[:8] + "..." + api_key[-4:]
            else:
                masked = api_key[:4] + "..."
            api_key_style = "green"
        else:
            masked = "not set (Ollama or no provider)"
            api_key_style = "red"
        table.add_row("API key:", Text(masked, style=api_key_style))

        # Config file
        config_path = get_config_path()
        table.add_row("Config file:", str(config_path))

        # Create panel with table
        panel = Panel(
            table,
            title="[bold cyan]Envio Configuration[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )

        console.print(panel)
        console.print(
            "[dim]Commands: envio config api <key>, envio config model <name>[/dim]"
        )
        console.print()
    else:
        # Fallback to original plain text implementation - ASCII only
        print("\n+ Envio Configuration +")
        print("|")

        # Default directory
        default_dir = config.get("default_envs_dir", "~/.envs (not set)")
        print(f"|  Default envs directory: {default_dir}")

        # Package manager
        pm = config.get("preferred_package_manager", "pip")
        print(f"|  Preferred package manager: {pm}")

        # Provider and model
        provider = config.get("provider", "not set")
        model = config.get("model", "not set")
        print(f"|  LLM provider: {provider}")
        print(f"|  LLM model: {model}")

        # API key (masked)
        api_key = config.get("api_key", "")
        if api_key:
            if len(api_key) > 12:
                masked = api_key[:8] + "..." + api_key[-4:]
            else:
                masked = api_key[:4] + "..."
            print(f"|  API key: {masked}")
        else:
            print("|  API key: not set (Ollama or no provider)")

        config_path = get_config_path()
        print("|")
        print(f"|  Config file: {config_path}")
        print("|")
        print("+ Commands: envio config api <key>, envio config model <name> +")
        print()


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


def setup_llm_first_run() -> None:
    """Interactive first-run setup for LLM configuration."""
    # Check if Ollama is available
    ollama_available = False
    ollama_models = []
    try:
        from envio.llm.client import is_ollama_available, list_ollama_models

        ollama_available = is_ollama_available()
        if ollama_available:
            ollama_models = list_ollama_models()
    except Exception:
        pass

    print("\nWhich LLM would you like to use?")
    options = [
        "  1. OpenAI (requires API key)",
        "  2. Anthropic (requires API key)",
        "  3. Other provider (requires API key)",
    ]
    if ollama_available:
        options.insert(
            0,
            f"  0. Ollama (free, local, no API key) - Models: {', '.join(ollama_models)}",
        )
    options.append("  4. Skip for now")

    for opt in options:
        print(opt)

    choice = (
        input("Choice [0]: ").strip()
        if ollama_available
        else input("Choice [1]: ").strip()
    )

    if ollama_available and choice == "0":
        # Ollama selected
        provider = "ollama"
        print("\nSelect your model:")
        for i, m in enumerate(ollama_models, 1):
            print(f"  {i}. {m}")
        model_choice = input(f"Choice [1]: ").strip() or "1"
        try:
            model = ollama_models[int(model_choice) - 1]
        except (ValueError, IndexError):
            model = ollama_models[0] if ollama_models else "llama3"

        config = load_config()
        config["api_key"] = ""
        config["provider"] = provider
        config["model"] = model
        save_config(config)

        print(f"\n✓ Provider: Ollama")
        print(f"✓ Model: {model}")

    elif choice == "1":
        # OpenAI
        api_key = input("\nEnter your OpenAI API key: ").strip()
        if api_key:
            config = load_config()
            config["api_key"] = api_key
            config["provider"] = "openai"

            # Ask for model
            print("\nSelect your model:")
            print("  1. gpt-4o-mini (default, cheaper)")
            print("  2. gpt-4o (better, more expensive)")
            print("  3. gpt-3.5-turbo (legacy)")
            print("  4. Enter custom model")
            model_choice = input("Choice [1]: ").strip() or "1"

            model_map = {"1": "gpt-4o-mini", "2": "gpt-4o", "3": "gpt-3.5-turbo"}
            if model_choice in model_map:
                model = model_map[model_choice]
            elif model_choice == "4":
                model = input("Enter model name: ").strip()
            else:
                model = "gpt-4o-mini"

            config["model"] = model
            save_config(config)

            print(f"\n✓ Provider: OpenAI")
            print(f"✓ Model: {model}")

    elif choice == "2":
        # Anthropic
        api_key = input("\nEnter your Anthropic API key: ").strip()
        if api_key:
            config = load_config()
            config["api_key"] = api_key
            config["provider"] = "anthropic"

            print("\nSelect your model:")
            print("  1. claude-3-sonnet-20240229 (default)")
            print("  2. claude-3-opus-20240229 (best)")
            print("  3. claude-3-haiku-20240307 (fastest)")
            model_choice = input("Choice [1]: ").strip() or "1"

            model_map = {
                "1": "claude-3-sonnet-20240229",
                "2": "claude-3-opus-20240229",
                "3": "claude-3-haiku-20240307",
            }
            model = model_map.get(model_choice, "claude-3-sonnet-20240229")

            config["model"] = model
            save_config(config)

            print(f"\n✓ Provider: Anthropic")
            print(f"✓ Model: {model}")

    elif choice == "3":
        # Other provider
        print("\nAvailable providers:")
        providers = [
            p for p in AVAILABLE_PROVIDERS if p not in ("openai", "anthropic", "ollama")
        ]
        for i, p in enumerate(providers, 1):
            print(f"  {i}. {p}")

        prov_choice = input(f"Choice [1]: ").strip() or "1"
        try:
            provider = providers[int(prov_choice) - 1]
        except (ValueError, IndexError):
            provider = providers[0]

        api_key = input(f"\nEnter your {provider} API key: ").strip()
        if api_key:
            config = load_config()
            config["api_key"] = api_key
            config["provider"] = provider

            model = input(
                f"Enter model name [default: {DEFAULT_MODELS.get(provider, 'default')}]: "
            ).strip()
            if not model:
                model = DEFAULT_MODELS.get(provider, "default")

            config["model"] = model
            save_config(config)

            print(f"\n✓ Provider: {provider}")
            print(f"✓ Model: {model}")

    else:
        print(
            "\n✓ Skipped LLM setup. You can configure later with: envio config api <key>"
        )


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


def is_first_run() -> bool:
    """Check if this is the first time running envio."""
    config_path = get_config_path()
    return not config_path.exists()


def ensure_config(prompt_first_run: bool = True) -> dict[str, Any]:
    """Ensure config exists, prompting user on first run if needed."""
    config = load_config()

    if not config and prompt_first_run:
        # First run - run full setup
        print("\n" + "=" * 50)
        print("First run setup - Welcome to Envio!")
        print("=" * 50)

        # Ask for default directory
        default_path_input = input(
            "\nWhere should I create your environments? [default: ~/.envs]: "
        ).strip()
        if not default_path_input:
            default_path_input = "~/.envs"
        default_dir = str(Path(default_path_input).expanduser())

        # Ask for preferred package manager
        print("\nWhich package manager do you prefer?")
        print("  1. pip (default)")
        print("  2. uv (faster, modern)")
        print("  3. conda")
        pm_choice = input("Choice [1]: ").strip() or "1"
        pm_map = {"1": "pip", "2": "uv", "3": "conda"}
        package_manager = pm_map.get(pm_choice, "pip")

        # Ask for LLM configuration
        setup_llm_first_run()

        # Save all config
        config = load_config()  # Reload after LLM setup
        config["default_envs_dir"] = default_dir
        config["preferred_package_manager"] = package_manager
        save_config(config)

        print(f"\n✓ Default envs directory: {default_dir}")
        print(f"✓ Preferred package manager: {package_manager}")
        print("\nConfiguration saved! You can change these anytime with: envio config")
        print("=" * 50 + "\n")

    return config
