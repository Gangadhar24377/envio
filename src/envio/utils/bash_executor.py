"""Bash Executor Utility."""

import shlex
import subprocess


def execute_bash(command: str, timeout: int | None = None) -> tuple[int, str, str]:
    """Execute a bash command and return (returncode, stdout, stderr)."""
    try:
        # Split the command string into a list for safe execution without shell
        args = shlex.split(command)
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)
