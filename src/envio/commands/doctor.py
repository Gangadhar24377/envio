"""Doctor command."""

from __future__ import annotations

import traceback

import click

from envio.cli_helpers import (
    _get_console,
    _get_profiler,
    _load_dotenv,
    detect_package_managers,
)


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def doctor(verbose: bool) -> None:
    """Show system hardware profile.

    \b
    Examples:
        envio doctor
        envio doctor -v
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Doctor", "System hardware profile")

    profiler = _get_profiler()

    try:
        console.print_info("Profiling system...")
        with console.spinner("Detecting hardware..."):
            profile = profiler.profile()

        console.print_hardware_profile(profile)

        # Check package managers
        console.print_info("Package managers:")
        managers = detect_package_managers()
        for pm, ok in managers.items():
            if ok:
                console._console.print(f"  - {pm}: ", end="", markup=True)
                console._console.print("available", style="green")
            else:
                console._console.print(f"  - {pm}: ", end="", markup=True)
                console._console.print("not found", style="red")

        # Check LLM configuration
        from envio.config import get_api_key, get_model

        console.print_info("LLM configuration:")
        api_key = get_api_key()
        if api_key:
            console._safe_print("  - API Key: [green]configured[/green]")
        else:
            console._safe_print("  - API Key: [red]not set[/red]")

        model = get_model()
        console._safe_print(f"  - Model: {model}")

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())
