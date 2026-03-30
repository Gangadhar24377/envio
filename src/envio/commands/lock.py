"""Lock command."""

from __future__ import annotations

import traceback
from pathlib import Path

import click

from envio import __version__
from envio.cli_helpers import (
    _get_console,
    _get_profiler,
    _is_writable,
    _load_dotenv,
)
from envio.config import get_default_envs_dir
from envio.core.registry import EnvironmentRegistry


@click.command()
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option(
    "--output", "-o", default=None, help="Output file path (default: envio.lock)"
)
@click.option(
    "--format",
    "fmt",
    default="json",
    type=click.Choice(["json", "text"]),
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def lock(
    name: str | None,
    path: str | None,
    output: str | None,
    fmt: str,
    verbose: bool,
) -> None:
    """Generate a lockfile for reproducible environments.

    \b
    Examples:
        envio lock -n my-env
        envio lock -n my-env -o requirements.lock
        envio lock -n my-env --format text
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Lock", "Generate reproducible lockfile")

    try:
        import json
        import platform
        from datetime import datetime

        from envio.core.virtualenv_manager import VirtualEnvManager

        manager = VirtualEnvManager()

        # Find the environment
        env_path = Path(path) if path else None

        if not env_path and name:
            # Check registry first
            registry = EnvironmentRegistry()
            reg_entry = registry.get(name)
            if reg_entry:
                env_path = Path(reg_entry["path"])
            else:
                # Not in registry, try default location from config
                default_base = get_default_envs_dir(prompt=False)[0]
                if default_base:
                    env_path = Path(default_base) / name
                else:
                    env_path = None

                if not env_path or not manager.exists(env_path):
                    # Not at default location, ask user
                    console.print_warning(
                        f"Environment '{name}' not found in registry or at default location."
                    )
                    try:
                        user_path = input("Enter path to the environment: ").strip()
                    except (KeyboardInterrupt, EOFError):
                        console.print_warning("\nAborted.")
                        return
                    if user_path:
                        env_path = Path(user_path)
                    else:
                        console.print_error("No path provided.")
                        return

        if not env_path:
            # No name provided, use current directory
            env_path = Path.cwd() / ".venv"

        if not manager.exists(env_path):
            console.print_error(f"Virtual environment not found at: {env_path}")
            return

        console.print_info(f"Locking environment: {env_path}")

        # Get installed packages with versions
        success, packages = manager.get_installed_packages_with_versions(env_path)

        if not success:
            console.print_error("Failed to get installed packages")
            return

        if not packages:
            console.print_warning("No packages installed in this environment")
            return

        console.print_info(f"Found {len(packages)} packages")

        # Get hardware profile
        profiler = _get_profiler()
        profile = profiler.profile()

        # Generate lockfile content
        lock_data = {
            "version": "1.0",
            "generated_by": f"envio {__version__}",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "package_manager": "pip",
            "python_version": platform.python_version(),
            "environment_name": name or env_path.name,
            "environment_path": str(env_path),
            "hardware": {
                "gpu": profile.gpu.name if profile.gpu.available else None,
                "cuda": profile.gpu.cuda_version if profile.gpu.available else None,
            },
            "packages": packages,
        }

        # Determine output file
        output_path = Path(output) if output else Path("envio.lock")

        if output_path.exists():
            console.print_warning(f"{output_path} already exists.")
            if not console.confirm("Overwrite?", default=False):
                console.print_warning("Aborted. No lockfile was created.")
                return

        if not _is_writable(output_path):
            console.print_error(f"Cannot write to {output_path}. Check permissions.")
            return

        if fmt == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(lock_data, f, indent=2, ensure_ascii=False)
                f.write("\n")
        else:
            # Text format (requirements.txt style)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# Generated by envio {__version__}\n")
                f.write(f"# Date: {lock_data['generated_at']}\n")
                f.write(f"# Python: {platform.python_version()}\n")
                if profile.gpu.available:
                    f.write(f"# GPU: {profile.gpu.name}\n")
                f.write("\n")
                for pkg in sorted(packages, key=lambda x: x["name"].lower()):
                    f.write(f"{pkg['name']}=={pkg['version']}\n")

        console.print_success(f"Lockfile saved to: {output_path}")
        console.print_info(f"Locked {len(packages)} packages")

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())
