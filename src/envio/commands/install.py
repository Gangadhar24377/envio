"""Install command."""

from __future__ import annotations

import time
import traceback
from pathlib import Path

import click

from envio.cli_helpers import (
    _get_console,
    _get_profiler,
    _load_dotenv,
    _resolve_and_install,
    _validate_and_normalize_packages,
    _validate_path,
    _ENV_NAME_RE,
    VALID_PACKAGE_MANAGERS,
)
from envio.ui.console import ConsoleUI


@click.command()
@click.argument("packages", nargs=-1, required=True)
@click.option("--env-type", "-e", "env_type", default="uv", help="Package manager")
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option("--cpu-only", is_flag=True, help="Force CPU-only mode")
@click.option(
    "--optimize-for",
    "optimize_for",
    default=None,
    type=click.Choice(["training", "inference", "development"]),
    help="Optimize packages for specific use case",
)
@click.option("--dry-run", is_flag=True, help="Preview without making changes")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def install(
    packages: tuple[str, ...],
    env_type: str,
    name: str | None,
    path: str | None,
    cpu_only: bool,
    optimize_for: str | None,
    dry_run: bool,
    yes: bool,
    verbose: bool,
) -> None:
    """Install packages directly.

    \b
    Examples:
        envio install requests
        envio install numpy pandas scikit-learn
        envio install "numpy>=1.24" "pandas>=2.0"
        envio install flask --manager pip
        envio install flask --dry-run
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Install", "Direct package installation")

    profiler = _get_profiler()
    profile = profiler.profile()

    try:
        if env_type not in VALID_PACKAGE_MANAGERS:
            console.print_warning(f"Invalid: {env_type}. Using uv.")
            env_type = "uv"

        pkg_list = list(packages)

        # Validate and normalize packages
        validated_packages = _validate_and_normalize_packages(pkg_list, console)

        preferences = {}
        if cpu_only:
            preferences["cpu_only"] = True
        if optimize_for:
            preferences["optimize_for"] = optimize_for
            console.print_info(f"Optimizing for: {optimize_for}")

        # Ask for environment name and path if not provided
        default_path = str(Path.home() / "Documents" / "envs")

        if not path:
            print("")  # Newline for spacing
            path_input = input(f"Path [default: {default_path}]: ").strip()
            path = path_input if path_input else default_path

        env_path = path.replace("\n", "").replace("\r", "")

        if not name:
            print("")  # Newline for spacing
            name = input("Name: ").strip() or f"env_{int(time.time())}"

        env_name = name

        from envio.cli_helpers import _ENV_NAME_RE, _validate_path

        if not _validate_path(env_path):
            console.print_error("Invalid path. Path traversal not allowed.")
            return

        if not _ENV_NAME_RE.match(env_name):
            console.print_error(
                "Invalid name. Use only letters, numbers, underscore, hyphen, and dot."
            )
            return

        # Build the command string for registry
        cmd_parts = ["envio install"] + list(pkg_list)
        if env_type != "uv":
            cmd_parts.append(f"--env-type {env_type}")
        if cpu_only:
            cmd_parts.append("--cpu-only")
        if optimize_for:
            cmd_parts.append(f"--optimize-for {optimize_for}")

        _resolve_and_install(
            packages=validated_packages,
            env_path=env_path,
            env_name=env_name,
            package_manager=env_type,
            preferences=preferences,
            profile=profile,
            console=console,
            original_command=" ".join(cmd_parts),
            dry_run=dry_run,
            skip_confirm=yes,
            verbose=verbose,
        )

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())
