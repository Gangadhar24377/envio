"""Virtual environment manager for cross-platform venv operations."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from envio.core.system_profiler import OSType, ShellType, SystemProfiler

if TYPE_CHECKING:
    pass


class VirtualEnvManager:
    """Manager for creating and managing virtual environments."""

    def __init__(self) -> None:
        self._profiler = SystemProfiler()

    def create(
        self,
        path: Path,
        python_version: str | None = None,
    ) -> bool:
        """Create a virtual environment at the specified path."""
        import shutil

        os_type = self._profiler.detect_os()

        try:
            if python_version:
                if os_type == OSType.WINDOWS:
                    # On Windows, use py launcher if available
                    if shutil.which("py"):
                        cmd = ["py", f"-{python_version}", "-m", "venv", str(path)]
                    else:
                        # Fall back to current Python but warn
                        import sys

                        cmd = [sys.executable, "-m", "venv", str(path)]
                else:
                    # On Unix, use pythonX.Y
                    cmd = [f"python{python_version}", "-m", "venv", str(path)]
            else:
                cmd = [sys.executable, "-m", "venv", str(path)]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return True

            print(f"Failed to create venv: {result.stderr}", file=sys.stderr)
            return False

        except Exception as e:
            print(f"Error creating virtual environment: {e}", file=sys.stderr)
            return False

    def exists(self, path: Path) -> bool:
        """Check if a virtual environment exists at the path."""
        os_type = self._profiler.detect_os()

        if os_type == OSType.WINDOWS:
            return path.exists() and (path / "Scripts" / "python.exe").exists()
        else:
            return path.exists() and (path / "bin" / "python").exists()

    def get_activation_command(self, venv_path: Path) -> str:
        """Get the correct activation command for the current shell."""
        os_type = self._profiler.detect_os()
        shell_type = self._profiler.detect_shell()

        if os_type == OSType.WINDOWS:
            if shell_type == ShellType.POWERSHELL:
                return f'& "{venv_path}\\Scripts\\Activate.ps1"'
            elif shell_type == ShellType.CMD:
                return f'"{venv_path}\\Scripts\\activate.bat"'
            else:
                return f'"{venv_path}\\Scripts\\activate.bat"'
        else:
            return f"source {venv_path}/bin/activate"

    def get_python_path(self, venv_path: Path) -> Path:
        """Get the path to the Python executable in the venv."""
        os_type = self._profiler.detect_os()

        if os_type == OSType.WINDOWS:
            return venv_path / "Scripts" / "python.exe"
        else:
            return venv_path / "bin" / "python"

    def install_packages(
        self,
        venv_path: Path,
        packages: list[str],
        package_manager: str = "pip",
    ) -> tuple[bool, str, str]:
        """Install packages into the virtual environment."""
        python_path = self.get_python_path(venv_path)

        if not python_path.exists():
            return False, "", f"Python not found at {python_path}"

        try:
            cmd = self._build_install_command(
                package_manager=package_manager,
                python_path=python_path,
                venv_path=venv_path,
                packages=packages,
            )

            if cmd is None:
                return False, "", f"Unsupported package manager: {package_manager}"

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            return (
                result.returncode == 0,
                result.stdout,
                result.stderr,
            )

        except subprocess.TimeoutExpired:
            return False, "", "Installation timed out"
        except Exception as e:
            return False, "", str(e)

    def _build_install_command(
        self,
        package_manager: str,
        python_path: Path,
        venv_path: Path,
        packages: list[str],
    ) -> list[str] | None:
        """Build the correct install command for the package manager.

        Args:
            package_manager: Package manager name (pip, uv, conda)
            python_path: Path to Python executable in venv
            venv_path: Path to virtual environment
            packages: List of packages to install

        Returns:
            Command list or None if unsupported
        """
        commands = {
            "pip": [str(python_path), "-m", "pip", "install"] + packages,
            "uv": ["uv", "pip", "install", "--python", str(python_path)] + packages,
            "conda": ["conda", "install", "-y", "--prefix", str(venv_path)] + packages,
        }
        return commands.get(package_manager)

    def upgrade_pip(self, venv_path: Path) -> tuple[bool, str, str]:
        """Upgrade pip in the virtual environment."""
        python_path = self.get_python_path(venv_path)

        try:
            result = subprocess.run(
                [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            return (
                result.returncode == 0,
                result.stdout,
                result.stderr,
            )

        except Exception as e:
            return False, "", str(e)

    def get_installed_packages(
        self,
        venv_path: Path,
    ) -> tuple[bool, list[str]]:
        """Get list of installed packages in the venv."""
        python_path = self.get_python_path(venv_path)

        try:
            result = subprocess.run(
                [str(python_path), "-m", "pip", "list", "--format=freeze"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                packages = [
                    line.split("==")[0]
                    for line in result.stdout.strip().split("\n")
                    if "==" in line
                ]
                return True, packages

            return False, []

        except Exception:
            return False, []

    def get_installed_packages_with_versions(
        self,
        venv_path: Path,
    ) -> tuple[bool, list[dict[str, str]]]:
        """Get list of installed packages with versions in the venv.

        Returns:
            Tuple of (success, list of dicts with 'name' and 'version' keys)
        """
        python_path = self.get_python_path(venv_path)

        try:
            result = subprocess.run(
                [str(python_path), "-m", "pip", "list", "--format=freeze"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                packages = []
                for line in result.stdout.strip().split("\n"):
                    if "==" in line:
                        parts = line.split("==")
                        if len(parts) == 2:
                            packages.append(
                                {
                                    "name": parts[0],
                                    "version": parts[1],
                                }
                            )
                return True, packages

            return False, []

        except Exception:
            return False, []

    def list_envs(self, base_path: Path | None = None) -> list[dict[str, str]]:
        """List all virtual environments in a directory.

        Args:
            base_path: Directory to search for environments. Defaults to ~/Documents/envs/

        Returns:
            List of dicts with 'name', 'path', and 'python_version' keys
        """
        if base_path is None:
            base_path = Path.home() / "Documents" / "envs"

        if not base_path.exists():
            return []

        environments = []
        for item in base_path.iterdir():
            if item.is_dir() and self.exists(item):
                # Try to get Python version
                python_path = self.get_python_path(item)
                try:
                    result = subprocess.run(
                        [str(python_path), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    python_version = (
                        result.stdout.strip() if result.returncode == 0 else "unknown"
                    )
                except Exception:
                    python_version = "unknown"

                environments.append(
                    {
                        "name": item.name,
                        "path": str(item),
                        "python_version": python_version,
                    }
                )

        return environments

    def uninstall_packages(
        self,
        venv_path: Path,
        packages: list[str],
    ) -> tuple[bool, str, str]:
        """Uninstall packages from a virtual environment.

        Args:
            venv_path: Path to the virtual environment
            packages: List of package names to uninstall

        Returns:
            Tuple of (success, stdout, stderr)
        """
        python_path = self.get_python_path(venv_path)

        if not python_path.exists():
            return False, "", f"Python not found at {python_path}"

        try:
            cmd = [str(python_path), "-m", "pip", "uninstall", "-y"] + packages
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            return result.returncode == 0, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return False, "", "Uninstallation timed out"
        except Exception as e:
            return False, "", str(e)
