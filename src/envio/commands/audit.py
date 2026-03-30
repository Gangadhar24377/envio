"""Audit command."""

from __future__ import annotations

import traceback
from pathlib import Path

import click

from envio.cli_helpers import (
    _find_environment,
    _get_console,
    _load_dotenv,
)
from envio.ui.console import ConsoleUI


@click.command()
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option(
    "--severity",
    default=None,
    type=click.Choice(["low", "medium", "high", "critical"]),
    help="Minimum severity to report",
)
@click.option("--fix", is_flag=True, help="Auto-fix vulnerabilities by upgrading")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def audit(
    name: str | None,
    path: str | None,
    severity: str | None,
    fix: bool,
    verbose: bool,
) -> None:
    """Scan environment for known vulnerabilities.

    \b
    Examples:
        envio audit
        envio audit -n my-env
        envio audit -n my-env --severity high
        envio audit -n my-env --fix
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Audit", "Security vulnerability scan")

    try:
        import shutil
        import subprocess
        import sys

        from envio.core.virtualenv_manager import VirtualEnvManager

        # Check if pip-audit is available globally first
        pip_audit_cmd = shutil.which("pip-audit")

        if not pip_audit_cmd:
            # Try to install pip-audit globally
            console.print_info("pip-audit not found. Installing globally...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "pip-audit"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                console.print_error("Failed to install pip-audit")
                if verbose:
                    console.print_code_block(result.stderr, "text")
                return
            pip_audit_cmd = shutil.which("pip-audit")
            console.print_success("pip-audit installed successfully")

        # Find environment using shared helper
        env_path = _find_environment(name, path, console)
        if not env_path:
            return

            # Print choices to stderr to not interfere with stdin
            for i, (p, label) in enumerate(choices, 1):
                print(f"  [{i}] {label}", file=sys.stderr)

            try:
                choice = click.prompt(
                    "Select environment number", type=int, default=1, err=True
                )
                idx = choice - 1
                if 0 <= idx < len(choices):
                    env_path = Path(choices[idx][0])
                else:
                    console.print_error("Invalid selection.")
                    return
            except click.Abort:
                print("\nAborted.", file=sys.stderr)
                return

        if not manager.exists(env_path):
            console.print_error(f"Virtual environment not found at: {env_path}")
            return

            print("")  # Print newline before choices
            for i, (p, label) in enumerate(choices, 1):
                print(f"  [{i}] {label}")
            print("")

            try:
                choice = click.prompt("Select environment number", type=int, default=1)
                idx = choice - 1
                if 0 <= idx < len(choices):
                    env_path = Path(choices[idx][0])
                else:
                    console.print_error("Invalid selection.")
                    return
            except click.Abort:
                print("\nAborted.")
                return

        if not manager.exists(env_path):
            console.print_error(f"Virtual environment not found at: {env_path}")
            return

            console.print_info("Select an environment to audit:")
            console.print_info("")
            for i, (p, label) in enumerate(choices, 1):
                console._safe_print(f"  [{i}] {label}", style="cyan")
            console.print_info("")

            try:
                choice = input("Enter number [1]: ").strip() or "1"
                idx = int(choice) - 1
                if 0 <= idx < len(choices):
                    env_path = Path(choices[idx][0])
                else:
                    console.print_error("Invalid selection.")
                    return
            except (KeyboardInterrupt, EOFError, ValueError):
                console.print_warning("\nAborted.")
                return

        if not manager.exists(env_path):
            console.print_error(f"Virtual environment not found at: {env_path}")
            return

        if not manager.exists(env_path):
            console.print_error(f"Virtual environment not found at: {env_path}")
            return

        python_path = manager.get_python_path(env_path)
        console.print_info(f"Auditing environment: {env_path}")

        # Run pip-audit using GLOBAL pip-audit (not from target venv)
        if not pip_audit_cmd:
            console.print_error("pip-audit not available")
            return

        console.print_info("Scanning for vulnerabilities...")
        with console.spinner("Running pip-audit..."):
            result = subprocess.run(
                [
                    pip_audit_cmd,
                    "--format",
                    "json",
                    "--desc",
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(env_path),
            )

        if result.returncode == 0:
            console.print_success("No vulnerabilities found!")
            return

        # Parse and display vulnerabilities
        import json

        try:
            audit_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            # pip-audit might return non-zero even on success
            if "No known vulnerabilities found" in result.stdout:
                console.print_success("No vulnerabilities found!")
                return
            console.print_error("Failed to run pip-audit")
            console.print_info(f"Error: {result.stderr.strip()}")
            if verbose:
                console.print_code_block(result.stdout, "text")
                console.print_code_block(result.stderr, "text")
            return

        vulnerabilities = audit_data.get("dependencies", [])
        vuln_list = []
        severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_severity = severity_levels.get(severity, 0) if severity else 0

        for dep in vulnerabilities:
            dep_vulns = dep.get("vulns", [])
            for vuln in dep_vulns:
                vuln_severity = vuln.get("severity", "unknown").lower()
                vuln_level = severity_levels.get(vuln_severity, 0)

                if vuln_level >= min_severity:
                    vuln_list.append(
                        {
                            "package": dep.get("name", "unknown"),
                            "version": dep.get("version", "unknown"),
                            "vuln_id": vuln.get("id", "unknown"),
                            "description": vuln.get("description", "No description"),
                            "severity": vuln_severity,
                            "fix_version": vuln.get("fix_versions", ["unknown"])[0]
                            if vuln.get("fix_versions")
                            else "unknown",
                        }
                    )

        if not vuln_list:
            console.print_success("No vulnerabilities above threshold!")
            return

        # Display vulnerabilities
        console.print_error(f"Found {len(vuln_list)} vulnerabilities:")
        console._safe_print("")

        from rich.table import Table

        table = Table(title="Vulnerabilities Found")
        table.add_column("Package", style="cyan")
        table.add_column("Version", style="white")
        table.add_column("CVE ID", style="yellow")
        table.add_column("Severity", style="red")
        table.add_column("Fix Version", style="green")

        for vuln in vuln_list:
            severity_style = {
                "critical": "[bold red]CRITICAL[/]",
                "high": "[red]HIGH[/]",
                "medium": "[yellow]MEDIUM[/]",
                "low": "[dim]LOW[/]",
            }.get(vuln["severity"], vuln["severity"])

            table.add_row(
                vuln["package"],
                vuln["version"],
                vuln["vuln_id"],
                severity_style,
                vuln["fix_version"],
            )

        console._safe_print(table)

        # Offer to fix
        if fix and vuln_list:
            console._safe_print("")
            fixable = [v for v in vuln_list if v["fix_version"] != "unknown"]
            if fixable:
                console.print_info(f"Fixing {len(fixable)} packages...")
                for vuln in fixable:
                    pkg = vuln["package"]
                    fix_ver = vuln["fix_version"]
                    console.print_info(f"  Upgrading {pkg} to {fix_ver}")

                # Run pip install with upgrades
                upgrade_cmd = [
                    str(python_path),
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                ] + [f"{v['package']}>={v['fix_version']}" for v in fixable]
                upgrade_result = subprocess.run(
                    upgrade_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if upgrade_result.returncode == 0:
                    console.print_success("Vulnerabilities fixed!")
                else:
                    console.print_error("Some fixes failed")
                    if verbose:
                        console.print_code_block(upgrade_result.stderr, "text")
            else:
                console.print_warning("No automatic fixes available")

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())
