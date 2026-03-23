"""Bash Executor Utility."""

import subprocess


def execute_bash(command: str, timeout: int | None = None) -> tuple[int, str, str]:
    """Execute a bash command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)
