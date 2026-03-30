"""Activate command for Envio."""

from __future__ import annotations

import traceback
from pathlib import Path

import click

from envio.cli_helpers import _load_dotenv, _get_console


@click.command(short_help="envio activate -n my-env       Show activation command")
@click.option("--env", "-e", "env_name", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def activate(env_name: str | None, path: str | None, verbose: bool) -> None:
    """Show activation command for a virtual environment.

    \b
    Examples:
        envio activate -n my-env
        envio activate -p /path/to/env
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Activate", "Show activation command")

    try:
        from envio.core.virtualenv_manager import VirtualEnvManager

        manager = VirtualEnvManager()

        env_path = Path(path) if path else None
        if not env_path and env_name:
            default_base = Path.home() / "Documents" / "envs"
            env_path = default_base / env_name

        if not env_path:
            console.print_error("Please specify --env or --path")
            return

        if not manager.exists(env_path):
            console.print_error(f"Environment not found at: {env_path}")
            return

        console.print_info(f"Environment: {env_path}")
        console.print_info("")

        from envio.core.system_profiler import OSType, SystemProfiler

        os_type = SystemProfiler().detect_os()

        if os_type == OSType.WINDOWS:
            console.print_info("PowerShell:")
            console._safe_print(f'& "{env_path}\\Scripts\\Activate.ps1"')
            console.print_info("")
            console.print_info("CMD:")
            console._safe_print(f'"{env_path}\\Scripts\\activate.bat"')
            console.print_info("")
            console.print_info("Git Bash:")
            console._safe_print(f'source "{env_path}/Scripts/activate"')
        else:
            console.print_info("Bash/Zsh:")
            console._safe_print(f"source {env_path}/bin/activate")

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())
