"""Cross-platform script generator factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from envio.core.system_profiler import OSType, SystemProfiler

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
    ) -> str:
        """Generate complete environment setup script.

        Args:
            venv_path: Full path to the virtual environment
            packages: List of packages to install
            package_manager: pip, conda, or uv
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
    ) -> str:
        """Generate complete PowerShell setup script.

        Args:
            venv_path: Full path to the virtual environment (e.g., "envs/forecasting")
            packages: List of packages to install
            package_manager: pip, conda, or uv
        """
        activation = self.generate_venv_activation_instructions(Path(venv_path))

        if package_manager == "uv":
            install_block = "\n".join(
                f'    uv pip install --python "{venv_path}\\Scripts\\python.exe" {pkg}'
                for pkg in packages
            )
            install_note = "# Using uv for fast installation"
        elif package_manager == "conda":
            install_block = "\n".join(f"    conda install -y {pkg}" for pkg in packages)
            install_note = "# Using conda for installation"
        else:
            install_block = "\n".join(f"    pip install {pkg}" for pkg in packages)
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
Write-Host "Virtual environment: {venv_path}" -ForegroundColor Cyan

try {{
    # Create virtual environment
    Write-Host "Creating virtual environment..."
    python -m venv "{venv_path}"

    # Activate virtual environment
    Write-Host "Activating virtual environment..."
    & "{venv_path}\\Scripts\\Activate.ps1"

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

        if package_manager == "conda":
            return f"""# Install packages using conda
conda install -y {" ".join(packages)}
"""
        else:
            packages_str = " ".join(packages)
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
    ) -> str:
        """Generate complete Bash setup script.

        Args:
            venv_path: Full path to the virtual environment
            packages: List of packages to install
            package_manager: pip, conda, or uv
        """
        if package_manager == "uv":
            install_lines = "\n".join(
                f"uv pip install --python {venv_path}/bin/python {pkg}"
                for pkg in packages
            )
            install_note = "# Using uv for fast installation"
        elif package_manager == "conda":
            install_lines = "\n".join(f"conda install -y {pkg}" for pkg in packages)
            install_note = "# Using conda for installation"
        else:
            install_lines = "\n".join(f"pip install {pkg}" for pkg in packages)
            install_note = "# Using pip for installation"

        activation = self.generate_venv_activation_instructions(Path(venv_path))

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
echo "Virtual environment: {venv_path}"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv "{venv_path}"

# Activate virtual environment
echo "Activating virtual environment..."
source "{venv_path}/bin/activate"

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
