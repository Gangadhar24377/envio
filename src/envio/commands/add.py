"""envio add — add packages to the current project.

Decision tree
-------------
1. pyproject.toml present  → edit [project.dependencies] (or optional group)
2. requirements.txt present → edit requirements.txt
3. Neither                 → create a minimal pyproject.toml, then install

Natural-language input is supported: if the argument looks like a sentence
(single token containing spaces, or explicitly quoted) it is routed through
the NLP agent first.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from envio.project.manager import ProjectManager
    from envio.ui.console import ConsoleUI

from envio.cli_helpers import (
    _get_console,
    _get_profiler,
    _load_dotenv,
    _resolve_and_install,
    _validate_and_normalize_packages,
)


def _is_nlp_input(packages: tuple[str, ...]) -> bool:
    """Heuristic: treat a single multi-word token as a natural-language prompt."""
    return len(packages) == 1 and " " in packages[0]


@click.command()
@click.argument("packages", nargs=-1, required=True)
@click.option(
    "--group",
    "-g",
    default=None,
    help="Optional-dependency group (e.g. dev, test, docs)",
)
@click.option(
    "--legacy",
    is_flag=True,
    help="Force requirements.txt mode even if pyproject.toml exists",
)
@click.option(
    "--name",
    "-n",
    default=None,
    help="Project name (used only when creating a new pyproject.toml)",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would happen without making changes"
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def add(
    packages: tuple[str, ...],
    group: str | None,
    legacy: bool,
    name: str | None,
    dry_run: bool,
    yes: bool,
    verbose: bool,
) -> None:
    """Add packages to the current project.

    Examples:
        envio add requests flask
        envio add "fastapi with postgres and redis"
        envio add pytest --group dev
        envio add requests --legacy
        envio add flask --dry-run
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Add", "Add packages to project")

    cwd = Path.cwd()

    try:
        from envio.project.detector import ProjectDetector, ProjectMode
        from envio.project.manager import ProjectManager

        detector = ProjectDetector()
        manager = ProjectManager()

        # ------------------------------------------------------------------ #
        # 1. Resolve packages (NLP or direct)                                  #
        # ------------------------------------------------------------------ #
        resolved_packages: list[str]

        if _is_nlp_input(packages):
            console.print_info(f"[NLP] Interpreting: {packages[0]!r}")
            try:
                from envio.cli_helpers import _get_nlp_processor, get_hardware_context

                profiler = _get_profiler()
                profile = profiler.profile()
                hw_ctx = get_hardware_context(profile)
                nlp = _get_nlp_processor()
                result = nlp.extract(packages[0], hw_ctx)
                from envio.cli_helpers import _parse_nlp_result

                resolved_packages, _, _ = _parse_nlp_result(result)
                console.print_info(f"Resolved packages: {', '.join(resolved_packages)}")
            except Exception as exc:
                console.print_warning(
                    f"NLP resolution failed ({exc}), treating as package name."
                )
                resolved_packages = list(packages)
        else:
            resolved_packages = list(packages)

        # ------------------------------------------------------------------ #
        # 2. Validate / normalise against PyPI                                 #
        # ------------------------------------------------------------------ #
        validated = _validate_and_normalize_packages(resolved_packages, console)
        if not validated:
            console.print_error("No valid packages found.")
            return

        # ------------------------------------------------------------------ #
        # 3. Determine project mode                                            #
        # ------------------------------------------------------------------ #
        if legacy:
            mode = ProjectMode.REQUIREMENTS
        else:
            mode = detector.detect(cwd)

        console.print_info(f"Project mode: {mode.value}")

        # ------------------------------------------------------------------ #
        # 4. Update the project file                                           #
        # ------------------------------------------------------------------ #
        if dry_run:
            _show_dry_run(console, validated, mode, group, cwd, name)
            return

        if mode == ProjectMode.NEW:
            _handle_new_project(console, manager, cwd, validated, group, name, yes)
        elif mode == ProjectMode.PYPROJECT:
            manager.add_to_pyproject(validated, cwd, group=group)
            loc = (
                f"[project.optional-dependencies.{group}]"
                if group
                else "[project.dependencies]"
            )
            console.print_success(f"Updated pyproject.toml → {loc}")
        else:  # REQUIREMENTS
            manager.add_to_requirements(validated, cwd)
            console.print_success("Updated requirements.txt")

        # ------------------------------------------------------------------ #
        # 5. Install into .venv                                                #
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

    except Exception as exc:
        console.print_error(f"Error: {exc}")
        if verbose:
            console._safe_print(traceback.format_exc())
        sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _handle_new_project(
    console: ConsoleUI,
    manager: ProjectManager,
    cwd: Path,
    packages: list[str],
    group: str | None,
    name: str | None,
    yes: bool,
) -> None:
    """Handle the brand-new project case: create pyproject.toml first."""
    from envio.project.manager import ProjectManager

    manager = ProjectManager()  # type: ignore[assignment]

    import re

    slug = re.sub(r"[^A-Za-z0-9]+", "-", cwd.name).strip("-").lower() or "my-project"
    project_name = name or slug
    py_ver = f">={sys.version_info.major}.{sys.version_info.minor}"

    console.print_info(
        f"No project file found. Creating pyproject.toml for {project_name!r}."
    )
    if not yes:
        response = input(f"Create pyproject.toml in {cwd}? [Y/n]: ").strip().lower()
        if response == "n":
            console.print_warning("Aborted.")
            return

    main_packages = packages if group is None else []
    grp_packages = {group: packages} if group else None

    manager.create_pyproject(
        cwd=cwd,
        packages=main_packages,
        project_name=project_name,
        python_version=py_ver,
        groups=grp_packages,
    )
    console.print_success(f"Created pyproject.toml ({project_name})")


def _show_dry_run(
    console: ConsoleUI,
    packages: list[str],
    mode: object,
    group: str | None,
    cwd: Path,
    name: str | None,
) -> None:
    """Print a dry-run summary without touching any files."""
    from envio.project.detector import ProjectMode

    console.print_info("--- Dry run ---")
    console.print_info(f"Packages : {', '.join(packages)}")  # type: ignore[arg-type]

    if mode == ProjectMode.NEW:
        import re

        slug = re.sub(r"[^A-Za-z0-9]+", "-", cwd.name).strip("-").lower()
        console.print_info(f"Would create pyproject.toml for {name or slug!r}")
    elif mode == ProjectMode.PYPROJECT:
        loc = (
            f"[project.optional-dependencies.{group}]"
            if group
            else "[project.dependencies]"
        )
        console.print_info(f"Would update pyproject.toml → {loc}")
    else:
        console.print_info("Would update requirements.txt")

    console.print_info("Would install into ./.venv")
