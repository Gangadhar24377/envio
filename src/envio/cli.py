"""Envio CLI - AI-Native Environment Orchestrator."""

from __future__ import annotations

import signal
import sys

import click

from envio import __version__
from envio.commands.activate import activate
from envio.commands.audit import audit
from envio.commands.config import config
from envio.commands.doctor import doctor
from envio.commands.export import export
from envio.commands.init import init
from envio.commands.install import install
from envio.commands.list_envs import list_envs
from envio.commands.lock import lock
from envio.commands.prompt import prompt
from envio.commands.remove import remove
from envio.commands.resurrect import resurrect_command


def _handle_interrupt(signum, frame) -> None:
    """Handle Ctrl+C gracefully."""
    print("\nAborted.", file=sys.stderr)
    sys.exit(130)


def _get_version_with_llm() -> str:
    """Get version string with LLM provider and model info."""
    try:
        from envio.config import get_model, get_provider

        provider = get_provider()
        model = get_model()
        if provider and model:
            return f"{__version__} ({provider}/{model})"
    except Exception:
        pass
    return __version__


@click.group(
    context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 120},
)
@click.version_option(version=_get_version_with_llm(), prog_name="envio")
def cli() -> None:
    """Envio - AI-Native Environment Orchestrator.

    For detailed documentation and examples, see:
    https://github.com/Gangadhar24377/envio/blob/main/COMMANDS.md
    """
    pass


# Register commands
cli.add_command(config)
cli.add_command(init)
cli.add_command(prompt)
cli.add_command(install)
cli.add_command(doctor)
cli.add_command(lock)
cli.add_command(export)
cli.add_command(audit)
cli.add_command(resurrect_command, "resurrect")
cli.add_command(list_envs, "list")
cli.add_command(activate)
cli.add_command(remove)


def main() -> None:
    signal.signal(signal.SIGINT, _handle_interrupt)

    # Check for first-run setup
    from envio.config import is_first_run, ensure_config

    if is_first_run():
        ensure_config(prompt_first_run=True)

    try:
        cli()
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
