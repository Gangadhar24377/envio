"""List environments command for Envio."""

from __future__ import annotations

import traceback
from pathlib import Path

import click

from envio.cli_helpers import _load_dotenv, _get_console


@click.command("list", short_help="envio list                  List all environments")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def list_envs(verbose: bool) -> None:
    """List environments created by envio.

    \b
    Examples:
        envio list
        envio list -v
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio List", "Environments created by envio")

    try:
        from rich.table import Table

        from envio.core.registry import EnvironmentRegistry
        from datetime import datetime

        registry = EnvironmentRegistry()
        environments = registry.list_all()

        if not environments:
            console.print_info("No environments created by envio yet.")
            console.print_info("Try: envio prompt 'web app with flask'")
            return

        table = Table(title="Registered Environments", show_lines=True)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Path", style="white")
        table.add_column("Pkgs", justify="right", style="green")
        table.add_column("Manager", style="yellow")
        table.add_column("Created", style="dim")

        for env in environments:
            env_exists = Path(env["path"]).exists()
            name = env["name"] if env_exists else f"{env['name']} (missing)"
            name_style = "cyan" if env_exists else "red"

            created = env.get("created_at", "")
            if created:
                try:
                    created = datetime.fromisoformat(created).strftime("%b %d")
                except Exception:
                    pass

            table.add_row(
                name,
                env.get("path", "unknown"),
                str(len(env.get("packages", []))),
                env.get("manager", "unknown"),
                created,
            )

        console._safe_print(table)

        console.print_info("")
        console.print_info("Recreation commands:")
        for env in environments:
            console.print_info(f"  {env['name']}: {env.get('command', 'unknown')}")

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())
