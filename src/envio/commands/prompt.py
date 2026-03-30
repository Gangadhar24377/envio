"""Prompt command."""

from __future__ import annotations

import time
import traceback
from pathlib import Path

import click

from envio.cli_helpers import (
    _ENV_NAME_RE,
    _get_console,
    _get_nlp_processor,
    _get_profiler,
    _load_dotenv,
    _parse_nlp_result,
    _resolve_and_install,
    _validate_and_normalize_packages,
    _validate_path,
    get_hardware_context,
)


@click.command()
@click.argument("prompt_text", nargs=-1, required=True)
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option("--env-type", "-e", "env_type", default="uv", help="Package manager")
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
def prompt(
    prompt_text: tuple[str, ...],
    name: str | None,
    path: str | None,
    env_type: str,
    cpu_only: bool,
    optimize_for: str | None,
    dry_run: bool,
    yes: bool,
    verbose: bool,
) -> None:
    """Set up environment from natural language prompt.

    \b
    Examples:
        envio prompt "web app with flask and react"
        envio prompt "machine learning with pytorch" --optimize-for gpu
        envio prompt "data analysis with pandas" --cpu-only
        envio prompt "flask api" --dry-run
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Prompt", "Natural language environment setup")

    # Check for API key from config
    from envio.config import get_api_key

    api_key = get_api_key()
    if not api_key:
        console.print_warning("No API key found. Falling back to PyPI-only resolution.")
        console.print_info("Run: envio config api <your-key> to enable AI features.")

    profiler = _get_profiler()
    profile = profiler.profile()

    try:
        user_input = " ".join(prompt_text)
        console.print_info(f"Request: {user_input}")

        # NLP processing
        console.print_info("Analyzing request...")
        nlp = _get_nlp_processor()
        hw_context = get_hardware_context(profile)

        def callback(msg: str) -> None:
            console.print_agent_thought("NLP", msg)

        result = nlp.extract(user_input, hw_context, callback)
        packages, _, preferences = _parse_nlp_result(result)

        if cpu_only:
            preferences["cpu_only"] = True
        if optimize_for:
            preferences["optimize_for"] = optimize_for
            console.print_info(f"Optimizing for: {optimize_for}")
        if cpu_only and optimize_for == "training":
            console.print_warning(
                "--cpu-only and --optimize-for training may conflict. "
                "GPU packages will not be installed."
            )

        console.print_packages_table(packages, "Suggested Packages")

        # Validate and normalize packages before installation
        validated_packages = _validate_and_normalize_packages(packages, console)

        # Ask for environment name and path
        default_path = str(Path.home() / "Documents" / "envs")
        try:
            env_path = (
                path
                or input(f"\nPath [default: {default_path}]: ").strip()
                or default_path
            )
            env_name = name or input("Name: ").strip() or f"env_{int(time.time())}"
        except (KeyboardInterrupt, EOFError):
            console.print_warning("\nAborted.")
            return

        if not _validate_path(env_path):
            console.print_error("Invalid path. Path traversal not allowed.")
            return

        if not _ENV_NAME_RE.match(env_name):
            console.print_error(
                "Invalid name. Use only letters, numbers, underscore, hyphen, and dot."
            )
            return

        # Resolve and install
        _resolve_and_install(
            packages=validated_packages,
            env_path=env_path,
            env_name=env_name,
            package_manager=env_type,
            preferences=preferences,
            profile=profile,
            console=console,
            original_command=f"envio prompt '{user_input}'",
            dry_run=dry_run,
            skip_confirm=yes,
            verbose=verbose,
        )

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())
