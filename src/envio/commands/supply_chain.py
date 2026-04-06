"""envio supply-chain — supply chain security scanning."""

from __future__ import annotations

import traceback
from pathlib import Path

import click

from envio.cli_helpers import _find_environment, _get_console, _load_dotenv


@click.group()
def supply_chain() -> None:
    """Supply chain security tools."""
    pass


@supply_chain.command("scan")
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option("--deep", is_flag=True, help="Full scan with web search on all packages")
@click.option(
    "--all", "scan_all", is_flag=True, help="Scan all registered environments"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def scan(
    name: str | None,
    path: str | None,
    deep: bool,
    scan_all: bool,
    verbose: bool,
) -> None:
    """Scan environment for supply chain risks.

    Checks for typosquatting, known vulnerabilities, suspicious patterns,
    and web-sourced security intelligence.

    Examples:
        envio supply-chain scan
        envio supply-chain scan -n my-env
        envio supply-chain scan --deep
        envio supply-chain scan --all
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Supply Chain Scan", "Security intelligence scan")

    try:
        from envio.core.virtualenv_manager import VirtualEnvManager
        from envio.supplychain.scanner import scan_packages

        if scan_all:
            _scan_all_environments(console, deep, verbose)
            return

        env_path = _find_environment(name, path, console)
        if not env_path:
            return

        manager = VirtualEnvManager()
        if not manager.exists(env_path):
            console.print_error(f"Virtual environment not found at: {env_path}")
            return

        console.print_info(f"Scanning environment: {env_path}")
        console.print_info("Mode: deep scan" if deep else "Mode: standard scan")

        packages = _get_installed_packages(env_path, manager)
        if not packages:
            console.print_warning("No packages found in environment")
            return

        console.print_info(f"Analyzing {len(packages)} package(s)...")

        with console.spinner("Running supply chain checks..."):
            result = scan_packages(packages, deep_mode=deep)

        _display_results(console, result, verbose)

    except Exception as exc:
        console.print_error(f"Error: {exc}")
        if verbose:
            console._safe_print(traceback.format_exc())


def _scan_all_environments(console, deep: bool, verbose: bool) -> None:
    """Scan all registered environments."""
    try:
        from envio.core.registry import EnvironmentRegistry
        from envio.core.virtualenv_manager import VirtualEnvManager
        from envio.supplychain.scanner import scan_packages

        registry = EnvironmentRegistry()
        manager = VirtualEnvManager()
        environments = registry.list_all()

        if not environments:
            console.print_warning("No registered environments found")
            return

        console.print_info(f"Scanning {len(environments)} environment(s)...")

        for env in environments:
            env_path = Path(env["path"])
            if not manager.exists(env_path):
                console.print_warning(f"Skipping {env['name']}: environment not found")
                continue

            console.print_info(f"\n--- {env['name']} ({env_path}) ---")
            packages = _get_installed_packages(env_path, manager)
            if not packages:
                console.print_warning("  No packages found")
                continue

            with console.spinner(f"  Scanning {env['name']}..."):
                result = scan_packages(packages, deep_mode=deep)

            _display_results(console, result, verbose, indent="  ")

    except Exception as exc:
        console.print_error(f"Error scanning environments: {exc}")
        if verbose:
            console._safe_print(traceback.format_exc())


def _get_installed_packages(env_path: Path, manager) -> list[str]:
    """Get list of installed packages in an environment."""
    try:
        import subprocess

        python_path = manager.get_python_path(env_path)
        result = subprocess.run(
            [str(python_path), "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            import json

            data = json.loads(result.stdout)
            return [f"{pkg['name']}=={pkg['version']}" for pkg in data]
    except Exception:
        pass
    return []


def _display_results(console, result, verbose: bool, indent: str = "") -> None:
    """Display scan results in a Rich table."""
    from rich.table import Table

    if not result.packages:
        console.print_info(f"{indent}No packages to analyze")
        return

    flagged = [p for p in result.packages if p.risk_score >= 15]

    table = Table(
        title=f"Supply Chain Scan Results ({len(result.packages)} packages)",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
    )
    table.add_column("Package", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Risk", style="yellow", justify="right")
    table.add_column("Level", style="yellow")
    table.add_column("Flags", style="red")

    for pkg in result.packages:
        if pkg.risk_score < 15 and not verbose:
            continue

        if pkg.risk_score >= 90:
            level = "[bold red]CRITICAL[/]"
        elif pkg.risk_score >= 70:
            level = "[red]HIGH[/]"
        elif pkg.risk_score >= 40:
            level = "[yellow]MEDIUM[/]"
        elif pkg.risk_score >= 15:
            level = "[dim]LOW[/]"
        else:
            level = "[green]SAFE[/]"

        flags_text = "; ".join(pkg.flags[:2]) if pkg.flags else ""
        if len(pkg.flags) > 2:
            flags_text += f" (+{len(pkg.flags) - 2} more)"

        table.add_row(
            f"{indent}{pkg.package}",
            pkg.version or "latest",
            str(pkg.risk_score),
            level,
            flags_text,
        )

    console._safe_print(table)

    console.print_info("")
    console.print_info(
        f"Summary: {result.safe_count} safe, {result.low_count} low, "
        f"{result.medium_count} medium, {result.high_count} high, "
        f"{result.critical_count} critical"
    )

    if flagged:
        console.print_warning(f"{len(flagged)} package(s) flagged for review")

        for pkg in flagged:
            from envio.supplychain.remediation import suggest_alternative

            alternative = suggest_alternative(pkg)
            if alternative:
                console.print_info(
                    f"  {pkg.package} -> consider using '{alternative}' instead"
                )
    else:
        console.print_success("No supply chain risks detected")


@supply_chain.command("cache")
@click.option("--clear", is_flag=True, help="Clear all cached scan results")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def cache_clear(clear: bool, verbose: bool) -> None:
    """Manage supply chain scan cache."""
    console = _get_console(verbose)

    if clear:
        from envio.supplychain.cache import SupplyChainCache

        cache = SupplyChainCache.get_instance()
        cache.clear()
        console.print_success("Supply chain cache cleared")
    else:
        console.print_info("Usage: envio supply-chain cache --clear")


supply_chain.add_command(scan)
supply_chain.add_command(cache_clear)
