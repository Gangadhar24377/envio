"""Cross-platform script generator factory."""

from __future__ import annotations

import re
import shlex
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from envio.core.system_profiler import OSType, SystemProfiler
from envio.utils.sanitize import sanitize_package_name

if TYPE_CHECKING:
    from envio.core.system_profiler import ShellType


class ScriptGenerator(ABC):
    """Abstract base class for script generators."""

    @abstractmethod
    def generate_venv_create_script(
        self,
        venv_path: Path,
        python_version: str | None = None,
    ) -> str:
        """Generate script to create virtual environment."""
        pass

    @abstractmethod
    def generate_venv_activation_instructions(self, venv_path: Path) -> str:
        """Generate instructions for activating the virtual environment."""
        pass

    @abstractmethod
    def generate_package_install_script(
        self,
        packages: list[str],
        package_manager: str,
    ) -> str:
        """Generate script to install packages."""
        pass

    @abstractmethod
    def generate_setup_script(
        self,
        venv_path: str,
        packages: list[str],
        package_manager: str,
        python_version: str | None = None,
        cuda_url: str | None = None,
    ) -> str:
        """Generate complete environment setup script.

        Args:
            venv_path: Full path to the virtual environment
            packages: List of packages to install
            package_manager: pip, conda, or uv
            cuda_url: PyTorch CUDA index URL for GPU installations
        """
        pass


class PowerShellGenerator(ScriptGenerator):
    """PowerShell script generator for Windows."""

    def generate_venv_create_script(
        self,
        venv_path: Path,
        python_version: str | None = None,
    ) -> str:
        """Generate PowerShell script to create virtual environment."""
        venv_name = venv_path.name
        parent_dir = venv_path.parent

        script = f"""
# Create virtual environment: {venv_name}
$ErrorActionPreference = 'Stop'
$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogFile = Join-Path '{parent_dir}' "log_${{Timestamp}}.txt"

try {{
    Set-Location '{parent_dir}'
    Write-Host "Creating virtual environment: {venv_name}..."

    # Create the virtual environment
    python -m venv "{venv_name}"

    if (-not (Test-Path "{venv_path}")) {{
        throw "Failed to create virtual environment"
    }}

    Write-Host "Virtual environment created successfully at: {venv_path}"
}} catch {{
    Write-Error "Error creating virtual environment: $_"
    exit 1
}}
"""
        return script

    def generate_venv_activation_instructions(self, venv_path: Path) -> str:
        """Generate activation instructions for different shells."""
        # Convert path to string with proper separators for each shell
        path_str = str(venv_path)
        # For Git Bash, convert backslashes to forward slashes
        git_bash_path = path_str.replace("\\", "/")

        return f"""
# To activate the virtual environment, run:
# PowerShell: & "{path_str}\\Scripts\\Activate.ps1"
# CMD: "{path_str}\\Scripts\\activate.bat"
# Git Bash: source "{git_bash_path}/Scripts/activate"
"""

    def generate_package_install_script(
        self,
        packages: list[str],
        package_manager: str,
    ) -> str:
        """Generate PowerShell script to install packages."""
        if not packages:
            return ""

        if package_manager == "conda":
            return f"""
# Install packages using conda
conda install -y {" ".join(packages)}
"""
        else:
            packages_str = " ".join(packages)
            return f"""
# Upgrade pip and install packages
pip install --upgrade pip
pip install {packages_str}
"""

    def generate_setup_script(
        self,
        venv_path: str,
        packages: list[str],
        package_manager: str,
        python_version: str | None = None,
        cuda_url: str | None = None,
    ) -> str:
        """Generate complete PowerShell setup script.

        Args:
            venv_path: Full path to the virtual environment
            packages: List of packages to install
            package_manager: pip, conda, or uv
            cuda_url: PyTorch CUDA index URL for GPU installations
        """
        env_name = Path(venv_path).name
        safe_venv_path = venv_path  # Use original path - don't sanitize drive letters

        # Sanitize package names
        safe_packages = []
        for pkg in packages:
            try:
                safe_packages.append(sanitize_package_name(pkg))
            except ValueError:
                # Skip invalid package names
                continue

        # Build package string with CUDA URL if provided
        packages_str = " ".join(safe_packages)
        extra_index_arg = f" --extra-index-url {cuda_url}" if cuda_url else ""

        if package_manager == "conda":
            activation = f"""
# To activate the conda environment, run:
# conda activate {env_name}
"""
            install_block = "\n".join(
                f"    conda run -n {env_name} pip install {pkg}"
                for pkg in safe_packages
            )
            env_setup = f"""
    # Create conda environment
    Write-Host "Creating conda environment: {env_name}..."
    conda create -y -n {env_name} python=3.11
"""
            install_note = "# Using conda for installation"
        else:
            activation = self.generate_venv_activation_instructions(Path(venv_path))
            env_setup = f"""
    # Create virtual environment
    Write-Host "Creating virtual environment..."
    python -m venv "{safe_venv_path}"

    # Activate virtual environment
    Write-Host "Activating virtual environment..."
    & "{safe_venv_path}\\Scripts\\Activate.ps1"
"""
            if package_manager == "uv":
                install_block = "\n".join(
                    f'    uv pip install --python "{safe_venv_path}\\Scripts\\python.exe"{extra_index_arg} {pkg}'
                    for pkg in safe_packages
                )
                install_note = "# Using uv for fast installation"
            else:
                install_block = "\n".join(
                    f"    pip install{extra_index_arg} {pkg}" for pkg in safe_packages
                )
                install_note = "# Using pip for installation"

        return f"""# Envio Environment Setup Script (PowerShell)
# Generated on: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
# Platform: Windows
# Package Manager: {package_manager}

$ErrorActionPreference = 'Stop'
$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogFile = "setup_${{Timestamp}}.log"

# Start logging
Start-Transcript -Path $LogFile

Write-Host "Starting environment setup..." -ForegroundColor Cyan

try {{
{env_setup}
{install_note}
    Write-Host "Installing packages..."
{install_block}

    Write-Host "Environment setup completed successfully!" -ForegroundColor Green
    Write-Host "Log file: $LogFile" -ForegroundColor Yellow
}} catch {{
    Write-Error "Error during setup: $_"
    exit 1
}} finally {{
    Stop-Transcript
}}

# Activation instructions
{activation}

# Cleanup
Remove-Item $LogFile -ErrorAction SilentlyContinue
"""


class BashGenerator(ScriptGenerator):
    """Bash script generator for Linux and macOS."""

    def generate_venv_create_script(
        self,
        venv_path: Path,
        python_version: str | None = None,
    ) -> str:
        """Generate Bash script to create virtual environment."""
        venv_name = venv_path.name
        parent_dir = venv_path.parent

        script = f"""#!/bin/bash
# Create virtual environment: {venv_name}

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="{parent_dir}/log_${{TIMESTAMP}}.txt"

exec > >(tee -a "$LOG_FILE") 2>&1

cd "{parent_dir}"

echo "Creating virtual environment: {venv_name}..."

python3 -m venv "{venv_name}"

if [ ! -d "{venv_path}" ]; then
    echo "Failed to create virtual environment at {venv_path}"
    exit 1
fi

echo "Virtual environment created successfully at: {venv_path}"
"""
        return script

    def generate_venv_activation_instructions(self, venv_path: Path) -> str:
        """Generate Bash instructions for activating virtual environment."""
        path_str = str(venv_path).replace("\\", "/")
        return f"""
# To activate the virtual environment, run:
source {path_str}/bin/activate
"""

    def generate_package_install_script(
        self,
        packages: list[str],
        package_manager: str,
    ) -> str:
        """Generate Bash script to install packages."""
        if not packages:
            return ""

        # Sanitize package names
        from envio.utils.sanitize import sanitize_packages

        try:
            safe_packages = sanitize_packages(packages)
        except ValueError:
            # If any package name is invalid, fall back to original behavior
            # but this should be validated upstream
            safe_packages = [shlex.quote(pkg) for pkg in packages]

        if package_manager == "conda":
            return f"""# Install packages using conda
conda install -y {" ".join(safe_packages)}
"""
        else:
            packages_str = " ".join(safe_packages)
            return f"""# Upgrade pip and install packages
pip install --upgrade pip
pip install {packages_str}
"""

    def generate_setup_script(
        self,
        venv_path: str,
        packages: list[str],
        package_manager: str,
        python_version: str | None = None,
        cuda_url: str | None = None,
    ) -> str:
        """Generate complete Bash setup script.

        Args:
            venv_path: Full path to the virtual environment
            packages: List of packages to install
            package_manager: pip, conda, or uv
            cuda_url: PyTorch CUDA index URL for GPU installations
        """
        env_name = Path(venv_path).name

        # Build extra index arg for CUDA
        extra_index_arg = f" --extra-index-url {cuda_url}" if cuda_url else ""

        if package_manager == "conda":
            activation = f"""
# To activate the conda environment, run:
# conda activate {env_name}
"""
            env_setup = f"""
# Create conda environment
echo "Creating conda environment: {env_name}..."
conda create -y -n {env_name} python=3.11
"""
            install_lines = "\n".join(
                f"conda run -n {env_name} pip install {pkg}" for pkg in packages
            )
            install_note = "# Using conda for installation"
        else:
            activation = self.generate_venv_activation_instructions(Path(venv_path))
            path_str = venv_path.replace("\\", "/")
            env_setup = f"""
# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv "{path_str}"

# Activate virtual environment
echo "Activating virtual environment..."
source "{path_str}/bin/activate"
"""
            if package_manager == "uv":
                # Sanitize package names
                from envio.utils.sanitize import sanitize_packages

                try:
                    safe_packages = sanitize_packages(packages)
                except ValueError:
                    # If any package name is invalid, fall back to quoting each package
                    safe_packages = [shlex.quote(pkg) for pkg in packages]

                install_lines = "\n".join(
                    f"uv pip install --python {venv_path}/bin/python{extra_index_arg} {pkg}"
                    for pkg in safe_packages
                )
                install_note = "# Using uv for fast installation"
            else:
                # Sanitize package names
                from envio.utils.sanitize import sanitize_packages

                try:
                    safe_packages = sanitize_packages(packages)
                except ValueError:
                    # If any package name is invalid, fall back to quoting each package
                    safe_packages = [shlex.quote(pkg) for pkg in packages]

                install_lines = "\n".join(
                    f"pip install{extra_index_arg} {pkg}" for pkg in safe_packages
                )
                install_note = "# Using pip for installation"

        return f"""#!/bin/bash
# Envio Environment Setup Script (Bash)
# Generated on: $(date +'%Y-%m-%d %H:%M:%S')
# Platform: {"Linux" if SystemProfiler().detect_os() == OSType.LINUX else "macOS"}
# Package Manager: {package_manager}

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="setup_${{TIMESTAMP}}.log"

# Start logging
exec > >(tee -a "$LOG_FILE") 2>&1

echo "Starting environment setup..."
{env_setup}
{install_note}
echo "Installing packages..."
{install_lines}

echo "Environment setup completed successfully!"
echo "Log file: $LOG_FILE"

# Activation instructions
{activation}

# Cleanup
rm -f "$LOG_FILE"
"""


class ScriptGeneratorFactory:
    """Factory for creating platform-appropriate script generators."""

    def __init__(self) -> None:
        self._profiler = SystemProfiler()

    def create(self) -> ScriptGenerator:
        """Create a script generator based on the current OS."""
        os_type = self._profiler.detect_os()

        if os_type == OSType.WINDOWS:
            return PowerShellGenerator()
        else:
            return BashGenerator()

    def create_for_shell(self, shell_type: ShellType) -> ScriptGenerator:
        """Create a script generator for a specific shell type."""
        if shell_type == ShellType.POWERSHELL or shell_type == ShellType.CMD:
            return PowerShellGenerator()
        else:
            return BashGenerator()
