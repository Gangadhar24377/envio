"""Remove command for Envio."""

from __future__ import annotations

import traceback
from pathlib import Path

import click

from envio.cli_helpers import _get_console, _load_dotenv


@click.command(short_help="envio remove numpy -n my-env    Remove packages from env")
@click.argument("packages", nargs=-1, required=True)
@click.option("--env", "-e", "env_name", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option(
    "--group",
    "-g",
    default=None,
    help="Optional-dependency group to remove from (pyproject.toml only)",
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def remove(
    packages: tuple[str, ...],
    env_name: str | None,
    path: str | None,
    group: str | None,
    yes: bool,
    verbose: bool,
) -> None:
    """Remove packages from a virtual environment and the project file.

    \b
    Examples:
        envio remove numpy -n my-env
        envio remove package1 package2 -n my-env
        envio remove numpy pandas -n my-env -y
        envio remove pytest --group dev
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Remove", "Remove packages from environment")

    cwd = Path.cwd()

    try:
        from envio.core.virtualenv_manager import VirtualEnvManager

        manager = VirtualEnvManager()

        # ------------------------------------------------------------------ #
        # Resolve the venv path                                                #
        # ------------------------------------------------------------------ #
        env_path: Path | None = None

        if path:
            env_path = Path(path)
        elif env_name:
            default_base = Path.home() / "Documents" / "envs"
            env_path = default_base / env_name
        else:
            # Auto-detect .venv in cwd (in-project mode)
            candidate = cwd / ".venv"
            if manager.exists(candidate):
                env_path = candidate
                console.print_info(f"Auto-detected environment: {env_path}")

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

        # ------------------------------------------------------------------ #
        # Update the project file first                                        #
        # ------------------------------------------------------------------ #
        _remove_from_project_file(package_list, group, cwd, console, verbose)

        # ------------------------------------------------------------------ #
        # Uninstall from the venv                                              #
        # ------------------------------------------------------------------ #
        console.print_info("Uninstalling from environment...")

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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _remove_from_project_file(
    packages: list[str],
    group: str | None,
    cwd: Path,
    console,
    verbose: bool,
) -> None:
    """Edit the project file (pyproject.toml or requirements.txt) if present."""
    try:
        from envio.project.detector import ProjectDetector, ProjectMode
        from envio.project.manager import ProjectManager

        mode = ProjectDetector().detect(cwd)
        pm = ProjectManager()

        if mode == ProjectMode.PYPROJECT:
            pm.remove_from_pyproject(packages, cwd, group=group)
            loc = (
                f"[project.optional-dependencies.{group}]"
                if group
                else "[project.dependencies]"
            )
            console.print_info(f"Updated pyproject.toml → removed from {loc}")
        elif mode == ProjectMode.REQUIREMENTS:
            pm.remove_from_requirements(packages, cwd)
            console.print_info("Updated requirements.txt")
        else:
            # NEW mode — no project file to edit, that's fine
            if verbose:
                console.print_info(
                    "No project file found; skipping project-file update."
                )
    except Exception as exc:
        # Non-fatal: log and continue so the venv uninstall still runs
        console.print_warning(f"Could not update project file: {exc}")
        if verbose:
            import traceback as tb

            console._safe_print(tb.format_exc())
