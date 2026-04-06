"""Audit command."""

from __future__ import annotations

import traceback

import click

from envio.cli_helpers import (
    _find_environment,
    _get_console,
    _load_dotenv,
)


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
@click.option(
    "--supply-chain", is_flag=True, help="Include supply chain security checks"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def audit(
    name: str | None,
    path: str | None,
    severity: str | None,
    fix: bool,
    supply_chain: bool,
    verbose: bool,
) -> None:
    """Scan environment for known vulnerabilities.

    \b
    Examples:
        envio audit
        envio audit -n my-env
        envio audit -n my-env --severity high
        envio audit -n my-env --fix
        envio audit -n my-env --supply-chain
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Audit", "Security vulnerability scan")

    try:
        import shutil
        import subprocess
        import sys

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

        from envio.core.virtualenv_manager import VirtualEnvManager

        manager = VirtualEnvManager()
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

        if supply_chain:
            console.print_info("")
            console.print_info("Running supply chain security checks...")
            _run_supply_chain_scan(env_path, manager, console, verbose)

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())


def _run_supply_chain_scan(env_path, manager, console, verbose: bool) -> None:
    """Run supply chain scan as part of audit."""
    try:
        from envio.supplychain.scanner import scan_packages

        packages = _get_installed_packages_for_audit(env_path, manager)
        if not packages:
            console.print_warning("No packages found for supply chain scan")
            return

        console.print_info(f"Analyzing {len(packages)} package(s)...")

        with console.spinner("Running supply chain checks..."):
            result = scan_packages(packages, deep_mode=False)

        from rich.table import Table

        flagged = [p for p in result.packages if p.risk_score >= 15]

        if flagged:
            console.print_warning(f"Supply chain: {len(flagged)} package(s) flagged")
            console.print_info("")

            table = Table(title="Supply Chain Risks")
            table.add_column("Package", style="cyan")
            table.add_column("Version", style="white")
            table.add_column("Risk", style="yellow", justify="right")
            table.add_column("Level", style="yellow")
            table.add_column("Flags", style="red")

            for pkg in result.packages:
                if pkg.risk_score < 15:
                    continue

                if pkg.risk_score >= 90:
                    level = "[bold red]CRITICAL[/]"
                elif pkg.risk_score >= 70:
                    level = "[red]HIGH[/]"
                elif pkg.risk_score >= 40:
                    level = "[yellow]MEDIUM[/]"
                else:
                    level = "[dim]LOW[/]"

                flags_text = "; ".join(pkg.flags[:2]) if pkg.flags else ""
                if len(pkg.flags) > 2:
                    flags_text += f" (+{len(pkg.flags) - 2} more)"

                table.add_row(
                    pkg.package,
                    pkg.version or "latest",
                    str(pkg.risk_score),
                    level,
                    flags_text,
                )

            console._safe_print(table)
        else:
            console.print_success("Supply chain: No risks detected")

    except Exception as exc:
        console.print_error(f"Supply chain scan failed: {exc}")
        if verbose:
            console._safe_print(traceback.format_exc())


def _get_installed_packages_for_audit(env_path, manager) -> list[str]:
    """Get installed packages for audit supply chain scan."""
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
