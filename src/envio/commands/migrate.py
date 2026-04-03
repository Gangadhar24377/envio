"""envio migrate — convert any Python project format to pyproject.toml.

Supported source formats
------------------------
* requirements.txt  (+ requirements-dev.txt, requirements-test.txt, …)
* pyproject.toml with [tool.poetry]  (Poetry)
* Pipfile / Pipfile.lock  (Pipenv)
* environment.yml / environment.yaml  (conda)
* setup.py + setup.cfg  (legacy setuptools)
* requirements.in  (pip-tools)
* pixi.toml  (pixi)
"""

from __future__ import annotations

import traceback
from pathlib import Path

import click

from envio.cli_helpers import _get_console, _load_dotenv


@click.command()
@click.argument("directory", default=".", required=False)
@click.option(
    "--from",
    "source_format",
    default=None,
    metavar="FORMAT",
    help="Force a specific source format (e.g. Poetry, Pipenv, conda).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be written without touching any files.",
)
@click.option(
    "--keep",
    "keep_original",
    is_flag=True,
    help="Keep original project files after migration.",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
def migrate(
    directory: str,
    source_format: str | None,
    dry_run: bool,
    keep_original: bool,
    verbose: bool,
) -> None:
    """Migrate a project to a pyproject.toml managed by Envio.

    Automatically detects the source format (requirements.txt, Poetry,
    Pipenv, conda, setuptools, pip-tools, or pixi) and creates a
    standards-compliant PEP 621 pyproject.toml.

    \b
    Examples:
        envio migrate
        envio migrate /path/to/project
        envio migrate --from Poetry
        envio migrate --dry-run
        envio migrate --keep
    """
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Migrate", "Convert project to pyproject.toml")

    cwd = Path(directory).resolve()
    if not cwd.is_dir():
        console.print_error(f"Directory not found: {cwd}")
        return

    try:
        from envio.project.migrator import Migrator

        migrator = Migrator()

        # ------------------------------------------------------------------ #
        # Show available formats when no source detected                       #
        # ------------------------------------------------------------------ #
        if source_format is None:
            fmt = migrator.detect_format(cwd)
            if fmt is None:
                console.print_error(
                    f"No recognised project format found in: {cwd}\n"
                    f"Supported formats: {', '.join(migrator.available_formats())}"
                )
                return
            console.print_info(f"Detected format: {fmt.name}")
        else:
            console.print_info(f"Using format: {source_format}")

        # ------------------------------------------------------------------ #
        # Extract migration data                                               #
        # ------------------------------------------------------------------ #
        data, out_path = migrator.migrate(
            cwd,
            source_format=source_format,
            dry_run=dry_run,
            keep_original=keep_original,
        )

        # ------------------------------------------------------------------ #
        # Report results                                                        #
        # ------------------------------------------------------------------ #
        console.print_info(f"Project name : {data.project_name}")
        console.print_info(f"Python       : {data.python_version or '(not specified)'}")
        console.print_info(f"Dependencies : {len(data.dependencies)} package(s)")

        if data.dependencies:
            for dep in data.dependencies:
                console.print_info(f"  {dep}")

        if data.groups:
            for grp, pkgs in data.groups.items():
                console.print_info(f"Group [{grp}]   : {len(pkgs)} package(s)")
                for pkg in pkgs:
                    console.print_info(f"  {pkg}")

        if dry_run:
            console.print_info(
                "[DRY RUN] No files were written. "
                "Run without --dry-run to apply the migration."
            )
        else:
            console.print_success(f"Created: {out_path}")
            console.print_info(
                "Next steps:\n"
                "  envio sync           # install all dependencies\n"
                "  envio sync --all-groups  # include dev/test groups"
            )

    except ValueError as exc:
        console.print_error(str(exc))
    except Exception as exc:
        console.print_error(f"Error: {exc}")
        if verbose:
            console._safe_print(traceback.format_exc())
