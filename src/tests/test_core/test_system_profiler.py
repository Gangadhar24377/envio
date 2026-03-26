"""Tests for SystemProfiler."""

import pytest
from unittest.mock import patch, MagicMock

from envio.core.system_profiler import SystemProfiler, OSType, ShellType, GPUInfo


class TestSystemProfiler:
    """Tests for SystemProfiler."""

    def test_detect_os(self):
        """Test OS detection."""
        profiler = SystemProfiler()
        with patch("platform.system", return_value="Windows"):
            assert profiler.detect_os() == OSType.WINDOWS
        with patch("platform.system", return_value="Linux"):
            assert profiler.detect_os() == OSType.LINUX
        with patch("platform.system", return_value="Darwin"):
            assert profiler.detect_os() == OSType.DARWIN

    def test_detect_architecture(self):
        """Test architecture detection."""
        profiler = SystemProfiler()
        with patch("platform.machine", return_value="AMD64"):
            assert profiler.detect_architecture() == "AMD64"

    def test_detect_python_version(self):
        """Test Python version detection."""
        profiler = SystemProfiler()
        with patch("platform.python_version", return_value="3.11.5"):
            assert profiler.detect_python_version() == "3.11.5"

    def test_detect_gpu_available(self):
        """Test GPU detection when GPU is available."""
        profiler = SystemProfiler()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="NVIDIA GeForce RTX 4060, 8192 MiB, 535.129.03"
            )
            gpu = profiler.detect_gpu()
            assert gpu.available is True
            assert "RTX 4060" in gpu.name
            assert gpu.vram_mb == 8192

    def test_detect_gpu_not_available(self):
        """Test GPU detection when GPU is not available."""
        profiler = SystemProfiler()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            gpu = profiler.detect_gpu()
            assert gpu.available is False

    def test_detect_shell(self):
        """Test shell detection."""
        profiler = SystemProfiler()
        with patch.object(profiler, "detect_os", return_value=OSType.WINDOWS):
            with patch.dict(
                "os.environ",
                {
                    "PSModulePath": "C:\\Windows\\system32\\WindowsPowerShell\\v1.0\\Modules"
                },
            ):
                assert profiler.detect_shell() == ShellType.POWERSHELL

    def test_singleton(self):
        """Test that SystemProfiler is a singleton."""
        profiler1 = SystemProfiler()
        profiler2 = SystemProfiler()
        assert profiler1 is profiler2

    def test_profile_caching(self):
        """Test that profile is cached."""
        profiler = SystemProfiler()
        with patch.object(profiler, "detect_gpu") as mock_detect_gpu:
            mock_detect_gpu.return_value = GPUInfo(available=False)

            # First call
            profile1 = profiler.profile()
            # Second call
            profile2 = profiler.profile()

            # detect_gpu should only be called once due to caching
            assert mock_detect_gpu.call_count == 1
            assert profile1 is profile2
