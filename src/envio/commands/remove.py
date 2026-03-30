"""Remove command for Envio."""

from __future__ import annotations

import traceback
from pathlib import Path

import click

from envio.cli_helpers import _load_dotenv, _get_console


@click.command(short_help="envio remove numpy -n my-env    Remove packages from env")
@click.argument("packages", nargs=-1, required=True)
@click.option("--env", "-e", "env_name", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def remove(
    packages: tuple[str, ...],
    env_name: str | None,
    path: str | None,
    yes: bool,
    verbose: bool,
) -> None:
    """Remove packages from a virtual environment.

    \b
    Examples:
        envio remove numpy -n my-env
        envio remove package1 package2 -n my-env
        envio remove numpy pandas -n my-env -y
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Remove", "Remove packages from environment")

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

        package_list = list(packages)
        console.print_info(f"Removing packages: {', '.join(package_list)}")
        console.print_info(f"Environment: {env_path}")

        if not yes:
            console.print_warning("This will permanently uninstall these packages.")
            response = input("Continue? [y/N]: ").strip().lower()
            if response != "y":
                console.print_warning("Aborted. No packages were removed.")
                return

        console.print_info("Uninstalling...")

        success, stdout, stderr = manager.uninstall_packages(env_path, package_list)

        if success:
            console.print_success(
                f"Successfully removed {len(package_list)} package(s)"
            )
        else:
            console.print_error("Failed to remove packages")
            if stderr:
                console.print_code_block(stderr, "text")

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())
