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
@click.option(
    "--pin-versions",
    "pin_versions",
    is_flag=True,
    help="Write a security lockfile (envio-security.lock) after scanning",
)
@click.option(
    "--pin-json",
    is_flag=True,
    help="Also emit envio-security.lock.json with full scan metadata (requires --pin-versions)",
)
@click.option(
    "--output-dir",
    default=None,
    help="Directory for the lockfile (default: current directory)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def scan(
    name: str | None,
    path: str | None,
    deep: bool,
    scan_all: bool,
    pin_versions: bool,
    pin_json: bool,
    output_dir: str | None,
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
        envio supply-chain scan --pin-versions
        envio supply-chain scan --pin-versions --pin-json
        envio supply-chain scan --pin-versions --output-dir ./security
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

        if pin_versions:
            from envio.supplychain.pinning import pin_versions as do_pin

            pin_result = do_pin(
                result,
                env_path=env_path,
                output_dir=output_dir,
                json_output=pin_json,
            )
            console.print_success(
                f"Security lockfile written: {pin_result.lockfile_path}"
            )
            if pin_result.json_path:
                console.print_success(
                    f"JSON metadata written:     {pin_result.json_path}"
                )
            console.print_info(
                f"Pinned {pin_result.total_packages} packages "
                f"({pin_result.flagged_packages} flagged, "
                f"{pin_result.safe_packages} safe)"
            )
            if pin_result.flagged_packages:
                console.print_warning(
                    "Flagged packages are annotated in the lockfile. "
                    "Review before deploying."
                )

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


@supply_chain.command("fix")
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be fixed without making changes"
)
@click.option(
    "--update-project", is_flag=True, help="Update pyproject.toml or requirements.txt"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def fix_command(
    name: str | None,
    path: str | None,
    dry_run: bool,
    update_project: bool,
    verbose: bool,
) -> None:
    """Fix supply chain issues by replacing flagged packages.

    Analyzes flagged packages and suggests safe alternatives.
    Can update project files (pyproject.toml / requirements.txt) on confirmation.

    Examples:
        envio supply-chain fix -n my-env
        envio supply-chain fix -n my-env --dry-run
        envio supply-chain fix -n my-env --update-project
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Supply Chain Fix", "Auto-remediation")

    try:
        from envio.core.virtualenv_manager import VirtualEnvManager
        from envio.supplychain.remediation import suggest_alternative
        from envio.supplychain.scanner import scan_package_with_diff

        env_path = _find_environment(name, path, console)
        if not env_path:
            return

        manager = VirtualEnvManager()
        if not manager.exists(env_path):
            console.print_error(f"Virtual environment not found at: {env_path}")
            return

        console.print_info(f"Scanning environment: {env_path}")

        packages = _get_installed_packages(env_path, manager)
        if not packages:
            console.print_warning("No packages found in environment")
            return

        console.print_info(f"Analyzing {len(packages)} package(s) for issues...")

        flagged = []
        with console.spinner("Running supply chain checks..."):
            for pkg_spec in packages:
                risk = scan_package_with_diff(pkg_spec, deep_mode=False)
                if risk.risk_score >= 20:
                    flagged.append(risk)

        if not flagged:
            console.print_success("No supply chain issues found")
            return

        console.print_warning(f"Found {len(flagged)} package(s) with issues:")
        console.print_info("")

        fixes = []
        for risk in flagged:
            alternative = suggest_alternative(risk)
            if alternative:
                fixes.append(
                    {
                        "package": risk.package,
                        "version": risk.version,
                        "alternative": alternative,
                        "risk_score": risk.risk_score,
                        "flags": risk.flags,
                        "reason": "typo or suspicious name",
                    }
                )
            elif risk.risk_score >= 90:
                fixes.append(
                    {
                        "package": risk.package,
                        "version": risk.version,
                        "alternative": None,
                        "risk_score": risk.risk_score,
                        "flags": risk.flags,
                        "reason": "high risk (consider removing)",
                    }
                )
            else:
                fixes.append(
                    {
                        "package": risk.package,
                        "version": risk.version,
                        "alternative": None,
                        "risk_score": risk.risk_score,
                        "flags": risk.flags,
                        "reason": "; ".join(risk.flags[:2]),
                    }
                )

        if dry_run:
            console.print_info("[DRY RUN] The following changes would be made:")
            console.print_info("")

        from rich.table import Table

        table = Table(
            title="Suggested Fixes",
            show_header=True,
            header_style="bold cyan",
            border_style="dim",
        )
        table.add_column("Current", style="red")
        table.add_column("Suggested", style="green")
        table.add_column("Risk", style="yellow", justify="right")
        table.add_column("Reason", style="white")

        for fix in fixes:
            current = str(fix["package"])
            fix_version = fix.get("version")
            if fix_version:
                current += f"=={fix_version}"

            suggested = fix["alternative"] or "[remove]"
            if fix["alternative"] and not dry_run:
                suggested = fix["alternative"]

            reason = fix["reason"]
            if isinstance(reason, list):
                reason = "; ".join(reason[:2])

            table.add_row(
                current,
                str(suggested),
                str(fix["risk_score"]),
                str(reason),
            )

        console._safe_print(table)
        console.print_info("")

        if dry_run:
            console.print_info("[DRY RUN] No changes were made.")
            return

        swappable = [f for f in fixes if f["alternative"]]
        if not swappable:
            console.print_warning("No automatic fixes available")
            console.print_info("Review the flagged packages above and decide manually.")
            return

        console.print_info(f"{len(swappable)} package(s) can be auto-fixed.")

        if not console.confirm("Apply these fixes?", default=True):
            console.print_warning("Aborted. No changes were made.")
            return

        console.print_info("Applying fixes...")

        for fix in swappable:
            console.print_info(
                f"  Replacing '{fix['package']}' with '{fix['alternative']}'..."
            )

        import subprocess

        python_path = manager.get_python_path(env_path)

        for fix in swappable:
            pkg = str(fix["package"])
            alt = str(fix["alternative"])
            result = subprocess.run(
                [str(python_path), "-m", "pip", "install", alt],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                console.print_success(f"  Installed '{alt}'")
                uninstall_result = subprocess.run(
                    [str(python_path), "-m", "pip", "uninstall", "-y", pkg],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if uninstall_result.returncode == 0:
                    console.print_success(f"  Removed '{pkg}'")
                else:
                    console.print_warning(
                        f"  Could not remove '{pkg}' (may not be installed)"
                    )
            else:
                console.print_error(f"  Failed to install '{alt}'")
                if verbose:
                    console.print_code_block(result.stderr, "text")

        if update_project:
            _update_project_file(fixes, console)

        console.print_success("Supply chain fixes applied!")

    except Exception as exc:
        console.print_error(f"Error: {exc}")
        if verbose:
            console._safe_print(traceback.format_exc())


def _update_project_file(fixes: list[dict], console) -> None:
    """Update pyproject.toml or requirements.txt with fixed packages."""
    from pathlib import Path

    pyproject = Path("pyproject.toml")
    requirements = Path("requirements.txt")

    if pyproject.exists():
        _update_pyproject_toml(fixes, pyproject, console)
    elif requirements.exists():
        _update_requirements_txt(fixes, requirements, console)
    else:
        console.print_warning("No pyproject.toml or requirements.txt found to update")


def _update_pyproject_toml(fixes: list[dict], filepath: Path, console) -> None:
    """Update dependencies in pyproject.toml."""
    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        import tomli_w

        with open(filepath, "rb") as f:
            data = tomllib.load(f)

        deps = data.get("project", {}).get("dependencies", [])
        updated = False

        for i, dep in enumerate(deps):
            dep_name = dep.split("==")[0].split(">=")[0].split("<=")[0].strip().lower()
            for fix in fixes:
                if fix["alternative"] and fix["package"].lower() == dep_name:
                    deps[i] = fix["alternative"]
                    updated = True
                    console.print_info(
                        f"  Updated pyproject.toml: {fix['package']} -> {fix['alternative']}"
                    )

        if updated:
            data["project"]["dependencies"] = deps
            with open(filepath, "wb") as f:
                tomli_w.dump(data, f)
            console.print_success("pyproject.toml updated")
        else:
            console.print_info("No dependencies to update in pyproject.toml")

    except Exception as exc:
        console.print_error(f"Failed to update pyproject.toml: {exc}")


def _update_requirements_txt(fixes: list[dict], filepath: Path, console) -> None:
    """Update requirements.txt with fixed packages."""
    try:
        with open(filepath) as f:
            lines = f.readlines()

        updated = False
        new_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("-"):
                new_lines.append(line)
                continue

            dep_name = (
                stripped.split("==")[0].split(">=")[0].split("<=")[0].strip().lower()
            )
            replaced = False

            for fix in fixes:
                if fix["alternative"] and fix["package"].lower() == dep_name:
                    new_lines.append(fix["alternative"] + "\n")
                    updated = True
                    replaced = True
                    console.print_info(
                        f"  Updated requirements.txt: {fix['package']} -> {fix['alternative']}"
                    )
                    break

            if not replaced:
                new_lines.append(line)

        if updated:
            with open(filepath, "w") as f:
                f.writelines(new_lines)
            console.print_success("requirements.txt updated")
        else:
            console.print_info("No dependencies to update in requirements.txt")

    except Exception as exc:
        console.print_error(f"Failed to update requirements.txt: {exc}")


supply_chain.add_command(scan)
supply_chain.add_command(cache_clear)
supply_chain.add_command(fix_command)


@supply_chain.command("hook")
@click.argument("action", type=click.Choice(["install", "remove", "ci"]))
@click.option(
    "--platform",
    type=click.Choice(["github", "gitlab"]),
    default="github",
    help="CI platform (only used with 'ci' action)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def hook_command(action: str, platform: str, verbose: bool) -> None:
    """Manage pre-commit hooks and CI/CD templates.

    \b
    Actions:
      install  Add supply chain check to pre-commit hooks
      remove   Remove supply chain check from pre-commit hooks
      ci       Generate CI/CD pipeline template

    \b
    Examples:
        envio supply-chain hook install
        envio supply-chain hook remove
        envio supply-chain hook ci --platform github
        envio supply-chain hook ci --platform gitlab
    """
    console = _get_console(verbose)

    if action == "install":
        from envio.supplychain.hooks import install_pre_commit_hook

        install_pre_commit_hook(console)
    elif action == "remove":
        from envio.supplychain.hooks import remove_pre_commit_hook

        remove_pre_commit_hook(console)
    elif action == "ci":
        from envio.supplychain.hooks import generate_ci_template

        generate_ci_template(platform, console)


supply_chain.add_command(hook_command)


@supply_chain.command("verify")
@click.option(
    "--lockfile",
    default="envio-security.lock",
    show_default=True,
    help="Path to the security lockfile to verify against",
)
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def verify_command(
    lockfile: str,
    name: str | None,
    path: str | None,
    verbose: bool,
) -> None:
    """Verify installed packages match the security lockfile.

    Compares every package currently installed in the environment against the
    pinned versions in ``envio-security.lock`` (or a custom lockfile).
    Exits with a non-zero status code if any mismatch or missing package is
    found, making it suitable for CI gates.

    \b
    Examples:
        envio supply-chain verify
        envio supply-chain verify --lockfile ./security/envio-security.lock
        envio supply-chain verify -n my-env
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Supply Chain Verify", "Lockfile integrity check")

    try:
        from envio.core.virtualenv_manager import VirtualEnvManager
        from envio.supplychain.pinning import verify_lockfile

        env_path = _find_environment(name, path, console)
        if not env_path:
            return

        manager = VirtualEnvManager()
        if not manager.exists(env_path):
            console.print_error(f"Virtual environment not found at: {env_path}")
            return

        lockfile_path = Path(lockfile)
        if not lockfile_path.exists():
            console.print_error(f"Lockfile not found: {lockfile_path}")
            console.print_info(
                "Run `envio supply-chain scan --pin-versions` to generate one."
            )
            raise SystemExit(1)

        console.print_info(f"Verifying against: {lockfile_path}")

        packages = _get_installed_packages(env_path, manager)
        if not packages:
            console.print_warning("No packages found in environment")
            return

        matched, mismatched, missing = verify_lockfile(lockfile_path, packages)

        if verbose:
            for m in matched:
                console.print_info(f"  ok  {m}")

        if mismatched:
            console.print_warning(f"{len(mismatched)} version mismatch(es):")
            for m in mismatched:
                console.print_warning(f"  MISMATCH  {m}")

        if missing:
            console.print_warning(
                f"{len(missing)} package(s) missing from environment:"
            )
            for m in missing:
                console.print_warning(f"  MISSING   {m}")

        if not mismatched and not missing:
            console.print_success(
                f"All {len(matched)} pinned packages match the lockfile."
            )
        else:
            console.print_error(
                "Lockfile verification FAILED. "
                "Re-run `envio supply-chain scan --pin-versions` to update the lockfile, "
                "or investigate the mismatched packages."
            )
            raise SystemExit(1)

    except SystemExit:
        raise
    except Exception as exc:
        console.print_error(f"Error: {exc}")
        if verbose:
            console._safe_print(traceback.format_exc())
        raise SystemExit(1) from exc


supply_chain.add_command(verify_command)
