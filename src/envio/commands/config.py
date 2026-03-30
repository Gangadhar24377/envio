"""Config command group for Envio."""

from __future__ import annotations

import click


@click.group()
def config() -> None:
    """Manage envio configuration.

    \b
    envio config api <key>         Set API key (auto-detects provider)
    envio config model <name>      Set model name
    envio config show              Show configuration
    envio config unset api         Clear API key
    envio config unset model       Clear model
    envio config set <key> <value> Set arbitrary config value
    """
    pass


@config.command("show")
def config_show() -> None:
    """Show current configuration."""
    from envio.config import show_config

    show_config()


@config.command("api")
@click.argument("api_key")
@click.option(
    "--provider", "-p", default=None, help="Explicit provider (openai, anthropic, etc.)"
)
def config_api(api_key: str, provider: str | None = None) -> None:
    """Set API key (auto-detects provider).

    Examples:
        envio config api sk-your-openai-key
        envio config api sk-ant-your-key
        envio config api some-key --provider together
    """
    from envio.config import (
        AVAILABLE_PROVIDERS,
        detect_provider_from_key,
        set_api_key,
        set_provider,
    )

    # Auto-detect provider
    if not provider:
        provider = detect_provider_from_key(api_key)

    if not provider:
        # Unknown key format - ask user
        print("Unknown API key format. Please select provider:")
        for i, p in enumerate(AVAILABLE_PROVIDERS, 1):
            if p != "ollama":  # Ollama doesn't need API key
                print(f"  {i}. {p}")
        choice = input("Choice [1]: ").strip() or "1"
        try:
            provider = AVAILABLE_PROVIDERS[int(choice) - 1]
        except (ValueError, IndexError):
            provider = "openai"

    set_api_key(api_key, provider)

    # Mask the key for display
    if len(api_key) > 12:
        masked = api_key[:8] + "..." + api_key[-4:]
    else:
        masked = api_key[:4] + "..."

    # Try to import Rich
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
        # Create table for API key info
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        table.add_row("API key:", Text(masked, style="green"))
        table.add_row("Provider:", Text(provider, style="green"))

        # Create panel
        panel = Panel(
            table,
            title="[bold green]API Key Configured[/bold green]",
            border_style="green",
            padding=(1, 2),
        )

        console.print(panel)
        console.print("[dim]Set your model with: envio config model <name>[/dim]")
        console.print()
    else:
        # Fallback to original plain text
        print(f"[+] API key set: {masked}")
        print(f"[+] Provider: {provider}")
        print("\nSet your model with: envio config model <name>")


@config.command("serper-api")
@click.argument("api_key")
def config_serper_api(api_key: str) -> None:
    """Set Serper API key for web search.

    Examples:
        envio config serper-api your-serper-key
    """
    from envio.config import set_serper_api_key

    set_serper_api_key(api_key)

    # Mask the key for display
    if len(api_key) > 12:
        masked = api_key[:8] + "..." + api_key[-4:]
    else:
        masked = api_key[:4] + "..."

    # Try to import Rich
    try:
        from rich.console import Console
        from rich.panel import Panel

        console = Console()
        console.print(f"[green]Serper API key set:[/green] {masked}")
        console.print()
    except ImportError:
        print(f"[+] Serper API key set: {masked}")


@config.command("model")
@click.argument("model")
def config_model(model: str) -> None:
    """Set the LLM model.

    Examples:
        envio config model gpt-4o
        envio config model llama3
        envio config model claude-3-opus-20240229
    """
    from envio.config import get_provider, set_model

    # Try to import Rich
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        use_rich = True
    except ImportError:
        use_rich = False

    provider = get_provider()
    set_model(model)

    if use_rich:
        console = Console()
        # Create table for model info
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        table.add_row("Model:", Text(model, style="green"))
        table.add_row("Provider:", Text(provider, style="green"))

        # Create panel
        panel = Panel(
            table,
            title="[bold green]Model Configured[/bold green]",
            border_style="green",
            padding=(1, 2),
        )

        console.print(panel)
        console.print()
    else:
        # Fallback to original plain text
        print(f"[+] Model set: {model}")
        print(f"[+] Provider: {provider}")


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value.

    Supported keys:
        default_envs_dir - Default directory for environments
        preferred_package_manager - Preferred package manager (pip, uv, conda)
    """
    from envio.config import set_default_envs_dir, set_preferred_package_manager

    # Try to import Rich
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        use_rich = True
    except ImportError:
        use_rich = False

    if key == "default_envs_dir":
        set_default_envs_dir(value)
        if use_rich:
            console = Console()
            # Create table for directory info
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Setting", style="cyan", no_wrap=True)
            table.add_column("Value", style="green")

            table.add_row("Default envs directory:", Text(value, style="green"))

            # Create panel
            panel = Panel(
                table,
                title="[bold green]Configuration Updated[/bold green]",
                border_style="green",
                padding=(1, 2),
            )

            console.print(panel)
            console.print()
        else:
            print(f"[+] Default envs directory set to: {value}")
    elif key == "preferred_package_manager":
        set_preferred_package_manager(value)
        if use_rich:
            console = Console()
            # Create table for package manager info
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Setting", style="cyan", no_wrap=True)
            table.add_column("Value", style="green")

            table.add_row("Preferred package manager:", Text(value, style="green"))

            # Create panel
            panel = Panel(
                table,
                title="[bold green]Configuration Updated[/bold green]",
                border_style="green",
                padding=(1, 2),
            )

            console.print(panel)
            console.print()
        else:
            print(f"[+] Preferred package manager set to: {value}")
    else:
        if use_rich:
            console = Console()
            # Create error table
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Message", style="red")

            table.add_row(Text(f"Unknown setting: {key}", style="red"))
            table.add_row(
                Text(
                    "Available: default_envs_dir, preferred_package_manager",
                    style="yellow",
                )
            )

            # Create panel
            panel = Panel(
                table,
                title="[bold red]Configuration Error[/bold red]",
                border_style="red",
                padding=(1, 2),
            )

            console.print(panel)
            console.print()
        else:
            print(f"Unknown setting: {key}")
            print("Available: default_envs_dir, preferred_package_manager")


@config.command("unset")
@click.argument("key")
def config_unset(key: str) -> None:
    """Unset a configuration value.

    Supported keys:
        api - Clear API key
        model - Clear model
        provider - Clear provider
    """
    from envio import config as config_module

    # Try to import Rich
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        use_rich = True
    except ImportError:
        use_rich = False

    cfg = config_module.load_config()
    if key == "api":
        cfg.pop("api_key", None)
        cfg.pop("provider", None)
        config_module.save_config(cfg)
        if use_rich:
            console = Console()
            # Create table for unset info
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Message", style="green")

            table.add_row(Text("API key cleared", style="green"))

            # Create panel
            panel = Panel(
                table,
                title="[bold green]Configuration Cleared[/bold green]",
                border_style="green",
                padding=(1, 2),
            )

            console.print(panel)
            console.print()
        else:
            print("[+] API key cleared")
    elif key == "model":
        cfg.pop("model", None)
        config_module.save_config(cfg)
        if use_rich:
            console = Console()
            # Create table for unset info
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Message", style="green")

            table.add_row(Text("Model cleared", style="green"))

            # Create panel
            panel = Panel(
                table,
                title="[bold green]Configuration Cleared[/bold green]",
                border_style="green",
                padding=(1, 2),
            )

            console.print(panel)
            console.print()
        else:
            print("[+] Model cleared")
    elif key in cfg:
        del cfg[key]
        config_module.save_config(cfg)
        if use_rich:
            console = Console()
            # Create table for unset info
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Message", style="green")

            table.add_row(Text(f"{key} has been unset", style="green"))

            # Create panel
            panel = Panel(
                table,
                title="[bold green]Configuration Cleared[/bold green]",
                border_style="green",
                padding=(1, 2),
            )

            console.print(panel)
            console.print()
        else:
            print(f"[+] {key} has been unset")
    else:
        if use_rich:
            console = Console()
            # Create table for warning
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Message", style="yellow")

            table.add_row(Text(f"{key} is not set", style="yellow"))

            # Create panel
            panel = Panel(
                table,
                title="[bold yellow]Configuration Info[/bold yellow]",
                border_style="yellow",
                padding=(1, 2),
            )

            console.print(panel)
            console.print()
        else:
            print(f"{key} is not set")
