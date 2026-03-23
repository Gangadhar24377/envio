"""Cross-platform script executor."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from envio.core.script_generator import ScriptGeneratorFactory
from envio.core.system_profiler import OSType, SystemProfiler


class ScriptExecutor:
    """Executor for running setup scripts on any platform."""

    def __init__(self) -> None:
        self._profiler = SystemProfiler()
        self._factory = ScriptGeneratorFactory()

    def write_script(
        self,
        content: str,
        output_path: Path,
        make_executable: bool = True,
    ) -> Path:
        """Write script content to a file."""
        os_type = self._profiler.detect_os()

        if os_type == OSType.WINDOWS:
            script_path = output_path.with_suffix(".ps1")
        else:
            script_path = output_path.with_suffix(".sh")

        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(content, encoding="utf-8")

        if make_executable and os_type != OSType.WINDOWS:
            script_path.chmod(0o755)

        return script_path

    def execute_script(
        self,
        script_path: Path,
        capture_output: bool = False,
        timeout: int | None = None,
    ) -> tuple[int, str, str]:
        """Execute a script and return (returncode, stdout, stderr)."""
        os_type = self._profiler.detect_os()

        try:
            if os_type == OSType.WINDOWS:
                result = subprocess.run(
                    [
                        "powershell",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(script_path),
                    ],
                    capture_output=capture_output,
                    text=True,
                    timeout=timeout,
                )
            else:
                result = subprocess.run(
                    ["bash", str(script_path)],
                    capture_output=capture_output,
                    text=True,
                    timeout=timeout,
                )

            return result.returncode, result.stdout or "", result.stderr or ""

        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except FileNotFoundError as e:
            return -1, "", f"Script interpreter not found: {e}"
        except Exception as e:
            return -1, "", str(e)

    def execute_command(
        self,
        command: str,
        capture_output: bool = True,
        timeout: int | None = None,
        check: bool = False,
    ) -> tuple[int, str, str]:
        """Execute a single command using the system shell."""
        os_type = self._profiler.detect_os()

        try:
            if os_type == OSType.WINDOWS:
                shell = ["powershell", "-Command"]
            else:
                shell = ["bash", "-c"]

            result = subprocess.run(
                shell + [command],
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=check,
            )

            return result.returncode, result.stdout or "", result.stderr or ""

        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    def execute_interactive(
        self,
        script_path: Path,
    ) -> None:
        """Execute a script interactively (user will see output)."""
        os_type = self._profiler.detect_os()

        try:
            if os_type == OSType.WINDOWS:
                subprocess.run(
                    [
                        "powershell",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(script_path),
                    ],
                    check=True,
                )
            else:
                subprocess.run(
                    ["bash", str(script_path)],
                    check=True,
                )
        except subprocess.CalledProcessError as e:
            print(f"Script execution failed with exit code: {e.returncode}")
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            print("Make sure PowerShell (Windows) or Bash (Linux/macOS) is installed.")
            sys.exit(1)
