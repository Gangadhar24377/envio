"""Tests for ScriptGenerator."""

from pathlib import Path

from envio.core.script_generator import (
    BashGenerator,
    PowerShellGenerator,
    ScriptGeneratorFactory,
)
from envio.core.system_profiler import OSType


class TestBashGenerator:
    """Tests for BashGenerator."""

    def test_generate_venv_create_script(self):
        """Test generating venv creation script."""
        generator = BashGenerator()
        venv_path = Path("/home/user/.venvs/test")
        script = generator.generate_venv_create_script(venv_path)
        assert "python3 -m venv" in script
        assert "test" in script

    def test_generate_package_install_script(self):
        """Test generating package install script."""
        generator = BashGenerator()
        packages = ["numpy", "pandas", "scikit-learn"]
        script = generator.generate_package_install_script(packages, "pip")
        assert "pip install" in script
        assert "numpy" in script

    def test_generate_package_install_script_empty(self):
        """Test generating empty package install script."""
        generator = BashGenerator()
        script = generator.generate_package_install_script([], "pip")
        assert script == ""

    def test_generate_venv_activation_instructions(self):
        """Test generating activation instructions."""
        generator = BashGenerator()
        venv_path = Path("/home/user/.venvs/test")
        instructions = generator.generate_venv_activation_instructions(venv_path)
        assert "source" in instructions
        assert "activate" in instructions


class TestPowerShellGenerator:
    """Tests for PowerShellGenerator."""

    def test_generate_venv_create_script(self):
        """Test generating venv creation script."""
        generator = PowerShellGenerator()
        venv_path = Path("C:\\Users\\test\\.venvs\\test")
        script = generator.generate_venv_create_script(venv_path)
        assert "python -m venv" in script

    def test_generate_package_install_script(self):
        """Test generating package install script."""
        generator = PowerShellGenerator()
        packages = ["numpy", "pandas"]
        script = generator.generate_package_install_script(packages, "pip")
        assert "pip install" in script
        assert "numpy" in script


class TestScriptGeneratorFactory:
    """Tests for ScriptGeneratorFactory."""

    def test_create_for_windows(self):
        """Test creating generator for Windows."""
        factory = ScriptGeneratorFactory()
        with patch.object(factory._profiler, "detect_os", return_value=OSType.WINDOWS):
            generator = factory.create()
            assert isinstance(generator, PowerShellGenerator)

    def test_create_for_linux(self):
        """Test creating generator for Linux."""
        factory = ScriptGeneratorFactory()
        with patch.object(factory._profiler, "detect_os", return_value=OSType.LINUX):
            generator = factory.create()
            assert isinstance(generator, BashGenerator)


# Patch import for the test
from unittest.mock import patch
