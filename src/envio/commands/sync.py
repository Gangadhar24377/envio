"""envio sync — install exactly what the project file declares.

Behaviour
---------
* PYPROJECT mode : installs [project.dependencies] + any requested groups
* REQUIREMENTS mode : installs everything in requirements.txt
* NEW mode : error — nothing to sync

Group flags
-----------
  envio sync                   # default deps only
  envio sync --group dev       # default deps + dev group
  envio sync --all-groups      # default deps + every optional group
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

import click

from envio.cli_helpers import (
    _get_console,
    _load_dotenv,
    _resolve_and_install,
    _validate_and_normalize_packages,
)


@click.command()
@click.option(
    "--group",
    "-g",
    "groups",
    multiple=True,
    help="Include this optional-dependency group (repeatable)",
)
@click.option(
    "--all-groups",
    "all_groups",
    is_flag=True,
    help="Include all optional-dependency groups",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be installed without doing it"
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def sync(
    groups: tuple[str, ...],
    all_groups: bool,
    dry_run: bool,
    yes: bool,
    verbose: bool,
) -> None:
    """Sync the environment with the current project file.

    Installs exactly the packages declared in pyproject.toml or
    requirements.txt.  Use --group / --all-groups to include optional
    dependency groups.

    Examples:
        envio sync
        envio sync --group dev
        envio sync --group dev --group test
        envio sync --all-groups
        envio sync --dry-run
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Sync", "Sync environment with project file")

    cwd = Path.cwd()

    try:
        from envio.project.detector import ProjectDetector, ProjectMode
        from envio.project.manager import ProjectManager

        detector = ProjectDetector()
        manager = ProjectManager()
        mode = detector.detect(cwd)

        # ------------------------------------------------------------------ #
        # Guard: no project file → nothing to sync                            #
        # ------------------------------------------------------------------ #
        if mode == ProjectMode.NEW:
            console.print_error(
                "No project file found in the current directory.\n"
                "Run 'envio add <packages>' to create one first."
            )
            sys.exit(1)

        # ------------------------------------------------------------------ #
        # Collect packages                                                     #
        # ------------------------------------------------------------------ #
        packages = manager.read_dependencies(cwd)

        if mode == ProjectMode.PYPROJECT:
            if all_groups:
                for grp_pkgs in manager.read_all_groups(cwd).values():
                    packages.extend(grp_pkgs)
            else:
                for grp in groups:
                    packages.extend(manager.read_group(grp, cwd))

        if not packages:
            console.print_warning(
                "No packages declared in project file. Nothing to sync."
            )
            return

        # ------------------------------------------------------------------ #
        # Validate                                                             #
        # ------------------------------------------------------------------ #
        validated = _validate_and_normalize_packages(packages, console)
        if not validated:
            console.print_error("No valid packages after validation.")
            sys.exit(1)

        # ------------------------------------------------------------------ #
        # Report                                                               #
        # ------------------------------------------------------------------ #
        group_label = ""
        if all_groups:
            group_label = " (all groups)"
        elif groups:
            group_label = f" (+ groups: {', '.join(groups)})"

        console.print_info(
            f"Syncing {len(validated)} package(s) from "
            f"{mode.value}{group_label} into ./.venv"
        )

        if dry_run:
            console.print_info("--- Dry run ---")
            for pkg in validated:
                console.print_info(f"  {pkg}")
            return

        # ------------------------------------------------------------------ #
        # Install                                                              #
        # ------------------------------------------------------------------ #
        _resolve_and_install(
            packages=validated,
            env_name=".venv",
            env_path=str(cwd),
            package_manager="uv",
            profile=None,
            preferences={},
            dry_run=False,
            skip_confirm=yes,
            console=console,
            verbose=verbose,
        )

    except SystemExit:
        raise
    except Exception as exc:
        console.print_error(f"Error: {exc}")
        if verbose:
            console._safe_print(traceback.format_exc())
        sys.exit(1)
