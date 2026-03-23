"""System Profiler for detecting OS, hardware, and Python version."""

from __future__ import annotations

import os
import platform
import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum


class OSType(Enum):
    """Supported operating system types."""

    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"  # macOS


class ShellType(Enum):
    """Supported shell types."""

    POWERSHELL = "powershell"
    CMD = "cmd"
    BASH = "bash"
    ZSH = "zsh"


@dataclass
class GPUInfo:
    """GPU information."""

    available: bool
    name: str | None = None
    vram_mb: int | None = None
    cuda_version: str | None = None
    memory_efficient: bool = False


@dataclass
class MLConfig:
    """Machine Learning specific configuration."""

    pytorch_index_url: str | None = None
    xformers_package: str | None = None
    recommended_batch_size: int | None = None
    flash_attention: bool = False
    cpu_only: bool = True


@dataclass
class SystemProfile:
    """Complete system profile."""

    os_type: OSType
    os_release: str
    architecture: str
    python_version: str
    shell_type: ShellType
    gpu: GPUInfo
    ml_config: MLConfig = field(default_factory=MLConfig)
    ram_gb: int | None = None


class SystemProfiler:
    """Profiler for detecting system information."""

    def __init__(self) -> None:
        self._profile: SystemProfile | None = None

    def detect_os(self) -> OSType:
        """Detect the operating system type."""
        system = platform.system().lower()
        if system == "windows":
            return OSType.WINDOWS
        elif system == "linux":
            return OSType.LINUX
        elif system == "darwin":
            return OSType.DARWIN
        return OSType.LINUX  # Default fallback

    def detect_shell(self) -> ShellType:
        """Detect the current shell type."""
        if self.detect_os() == OSType.WINDOWS:
            # Check if running in PowerShell or CMD
            psmodulepath = os.environ.get("PSModulePath")
            if psmodulepath:
                return ShellType.POWERSHELL
            return ShellType.CMD

        # Unix-like systems
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell:
            return ShellType.ZSH
        return ShellType.BASH

    def detect_architecture(self) -> str:
        """Detect system architecture."""
        return platform.machine()

    def detect_python_version(self) -> str:
        """Detect the current Python version."""
        return platform.python_version()

    def detect_gpu(self) -> GPUInfo:
        """Detect NVIDIA GPU information using nvidia-smi."""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,driver_version",
                    "--format=csv,noheader",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                if lines:
                    parts = lines[0].split(",")
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        vram_str = (
                            parts[1]
                            .strip()
                            .replace(" MiB", "")
                            .replace("MiB", "")
                            .strip()
                        )
                        vram_mb = int(vram_str) if vram_str.isdigit() else None

                        cuda_version = self._detect_cuda_version()

                        return GPUInfo(
                            available=True,
                            name=name,
                            vram_mb=vram_mb,
                            cuda_version=cuda_version,
                        )
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, OSError):
            pass

        return GPUInfo(available=False)

    def _detect_ram(self) -> int | None:
        """Detect total RAM in GB using nvidia-smi as fallback."""
        # Skip ctypes detection due to segfault issues on Windows
        # Try nvidia-smi for GPU memory as indicator
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                vram_mb = int(result.stdout.strip().split()[0])
                # Estimate system RAM as at least 2x VRAM for ML setups
                return max(vram_mb // 1024 * 2, 8)
        except Exception:
            pass
        return None

    def _detect_cuda_version(self) -> str | None:
        """Detect CUDA toolkit version."""
        try:
            result = subprocess.run(
                ["nvcc", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                match = re.search(r"release (\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

        # Fallback: try to read from nvidia-smi
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return f"driver-{result.stdout.strip()}"
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

        return None

    def profile(self) -> SystemProfile:
        """Get complete system profile."""
        if self._profile is None:
            gpu = self.detect_gpu()
            ml_config = self._get_ml_config(gpu)

            self._profile = SystemProfile(
                os_type=self.detect_os(),
                os_release=platform.release(),
                architecture=self.detect_architecture(),
                python_version=self.detect_python_version(),
                shell_type=self.detect_shell(),
                gpu=gpu,
                ml_config=ml_config,
                ram_gb=self._detect_ram(),
            )
        return self._profile

    def _get_ml_config(self, gpu: GPUInfo) -> MLConfig:
        """Get ML-specific configuration based on hardware."""
        config = MLConfig()

        if gpu.available and gpu.cuda_version:
            config.cpu_only = False
            config.pytorch_index_url = self.get_pytorch_index_url()

            cuda_short = ""
            if "12.4" in gpu.cuda_version:
                cuda_short = "124"
            elif "12.1" in gpu.cuda_version:
                cuda_short = "121"
            elif "11.8" in gpu.cuda_version:
                cuda_short = "118"

            if cuda_short:
                config.xformers_package = f"xformers cu{cuda_short}xx"

            if gpu.vram_mb and gpu.vram_mb >= 8000:
                config.recommended_batch_size = 32
                config.flash_attention = True
            elif gpu.vram_mb and gpu.vram_mb >= 4000:
                config.recommended_batch_size = 16
            else:
                config.recommended_batch_size = 8

        return config

    def get_pytorch_index_url(self) -> str | None:
        """Get the appropriate PyTorch index URL based on CUDA version."""
        gpu = self.detect_gpu()
        if not gpu.available or not gpu.cuda_version:
            return None

        cuda_ver = gpu.cuda_version
        if cuda_ver.startswith("12.4"):
            return "https://download.pytorch.org/whl/cu124"
        elif cuda_ver.startswith("12.1"):
            return "https://download.pytorch.org/whl/cu121"
        elif cuda_ver.startswith("11.8"):
            return "https://download.pytorch.org/whl/cu118"
        elif cuda_ver.startswith("11.7"):
            return "https://download.pytorch.org/whl/cu117"
        elif "driver" in cuda_ver:
            return (
                "https://download.pytorch.org/whl/cu121"  # Default for driver versions
            )

        return None
