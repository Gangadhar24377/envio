"""Init command - Initialize environment from existing project files."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

import click

from envio.cli_helpers import (
    _get_console,
    _get_profiler,
    _load_dotenv,
    _resolve_and_install,
    _scan_directory,
    _validate_and_normalize_packages,
    _validate_path,
    _ENV_NAME_RE,
    detect_package_managers,
)
from envio.ui.console import ConsoleUI


@click.command()
@click.option(
    "--env-type", "-e", "env_type", default=None, help="Package manager (pip/conda/uv)"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def init(env_type: str | None, verbose: bool) -> None:
    """Initialize environment from directory.

    \b
    Examples:
        envio init .
        envio init /path/to/project
        envio init . -n my-env
        envio init . --manager uv
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Init", "Scan directory and set up environment")

    profiler = _get_profiler()
    profile = profiler.profile()

    try:
        # Detect package managers
        available = detect_package_managers()
        console.print_info("Available package managers:")
        for pm, ok in available.items():
            status = "[green]available[/green]" if ok else "[red]not found[/red]"
            console._safe_print(f"  - {pm} ({status})", markup=True)

        # Scan directory
        directory = Path.cwd()
        console.print_info(f"Scanning {directory}...")

        detected = _scan_directory(directory)

        if not detected:
            console.print_warning("No requirements file found")
            console.print_info("Scanning Python files for imports...")

            # Scan Python files
            py_files = list(directory.glob("*.py")) + list(directory.glob("**/*.py"))
            imports = set()
            for py_file in py_files:
                try:
                    import ast

                    with open(py_file) as f:
                        tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.add(alias.name.split(".")[0])
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports.add(node.module.split(".")[0])
                except Exception:
                    pass

            # Filter out standard library using dynamic detection
            stdlib = sys.stdlib_module_names
            third_party = sorted(imports - stdlib)

            if third_party:
                console.print_info(f"Found {len(third_party)} third-party imports")
                detected = {
                    "source": "detected from imports",
                    "packages": third_party,
                    "env_type": "uv",
                }
            else:
                console.print_error("No packages detected. Use 'envio prompt' instead.")
                return

        # Show detected packages
        console.print_info(f"Detected from: {detected['source']}")
        console.print_packages_table(detected["packages"], "Detected Packages")

        # Ask for environment name
        try:
            env_name = input("\nEnvironment name [default: .venv]: ").strip() or ".venv"
        except (KeyboardInterrupt, EOFError):
            console.print_warning("\nAborted.")
            return

        if not _ENV_NAME_RE.match(env_name):
            console.print_error(
                "Invalid name. Use only letters, numbers, underscore, hyphen, and dot."
            )
            return

        # Ask where to create the environment
        default_envs_dir = str(Path.home() / "Documents" / "envs")
        here_path = str(directory / env_name) if env_name != ".venv" else str(directory)
        default_path = str(Path(default_envs_dir) / env_name)

        console.print_info("Where to create the environment?")
        console._safe_print(f"  [cyan][1][/cyan] Here      ({here_path})")
        console._safe_print(f"  [cyan][2][/cyan] Default   ({default_path})")
        console._safe_print(f"  [cyan][3][/cyan] Custom path")
        try:
            location_choice = input("Choice [1]: ").strip() or "1"
        except (KeyboardInterrupt, EOFError):
            console.print_warning("\nAborted.")
            return

        if location_choice == "2":
            env_path = default_envs_dir
        elif location_choice == "3":
            try:
                env_path = input("Enter path: ").strip()
            except (KeyboardInterrupt, EOFError):
                console.print_warning("\nAborted.")
                return
            if not env_path:
                console.print_error("No path provided.")
                return
            if not _validate_path(env_path):
                console.print_error("Invalid path. Path traversal not allowed.")
                return
        else:
            env_path = str(directory)

        # Use user-specified env_type, detected type, or default to uv
        final_env_type = env_type or detected.get("env_type") or "uv"
        console.print_info(f"Package manager: {final_env_type}")

        # Validate and normalize packages before installation
        validated_packages = _validate_and_normalize_packages(
            detected["packages"], console
        )

        # Setup environment
        _resolve_and_install(
            packages=validated_packages,
            env_path=env_path,
            env_name=env_name,
            package_manager=final_env_type,
            preferences={},
            profile=profile,
            console=console,
            original_command="envio init",
            verbose=verbose,
        )

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())
