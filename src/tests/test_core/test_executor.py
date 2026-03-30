"""Tests for core/executor.py - Cross-platform script executor."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envio.core.executor import ScriptExecutor
from envio.core.system_profiler import OSType


class TestScriptExecutor:
    """Tests for ScriptExecutor class."""

    @pytest.fixture
    def executor(self):
        """Create a ScriptExecutor instance."""
        return ScriptExecutor()

    @patch("envio.core.executor.SystemProfiler")
    @patch("envio.core.executor.ScriptGeneratorFactory")
    def test_init(self, mock_factory, mock_profiler):
        """Test executor initialization."""
        executor = ScriptExecutor()
        assert executor._profiler is not None
        assert executor._factory is not None

    @patch("envio.core.executor.SystemProfiler")
    @patch("envio.core.executor.ScriptGeneratorFactory")
    def test_write_script_windows(self, mock_factory, mock_profiler):
        """Test writing script on Windows."""
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.detect_os.return_value = OSType.WINDOWS
        mock_profiler.return_value = mock_profiler_instance

        executor = ScriptExecutor()
        content = "Write-Host 'Hello'"

        with patch("pathlib.Path.mkdir"):
            with patch("pathlib.Path.write_text"):
                with patch("pathlib.Path.chmod"):
                    result = executor.write_script(content, Path("test"))
                    assert result.suffix == ".ps1"

    @patch("envio.core.executor.SystemProfiler")
    @patch("envio.core.executor.ScriptGeneratorFactory")
    def test_write_script_unix(self, mock_factory, mock_profiler):
        """Test writing script on Unix."""
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.detect_os.return_value = OSType.LINUX
        mock_profiler.return_value = mock_profiler_instance

        executor = ScriptExecutor()
        content = "echo 'Hello'"

        with patch("pathlib.Path.mkdir"):
            with patch("pathlib.Path.write_text"):
                with patch("pathlib.Path.chmod") as mock_chmod:
                    result = executor.write_script(content, Path("test"))
                    assert result.suffix == ".sh"
                    mock_chmod.assert_called_once_with(0o755)

    @patch("envio.core.executor.SystemProfiler")
    @patch("envio.core.executor.ScriptGeneratorFactory")
    def test_write_script_creates_parent_dirs(self, mock_factory, mock_profiler):
        """Test that write_script creates parent directories."""
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.detect_os.return_value = OSType.LINUX
        mock_profiler.return_value = mock_profiler_instance

        executor = ScriptExecutor()

        with patch("pathlib.Path.mkdir") as mock_mkdir:
            with patch("pathlib.Path.write_text"):
                with patch("pathlib.Path.chmod"):
                    executor.write_script("echo test", Path("/nested/dir/script"))
                    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("envio.core.executor.SystemProfiler")
    @patch("subprocess.run")
    def test_execute_script_windows(self, mock_run, mock_profiler):
        """Test executing script on Windows."""
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.detect_os.return_value = OSType.WINDOWS
        mock_profiler.return_value = mock_profiler_instance

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        executor = ScriptExecutor()
        returncode, stdout, stderr = executor.execute_script(Path("test.ps1"))

        assert returncode == 0
        assert stdout == "Success"
        mock_run.assert_called_once()

    @patch("envio.core.executor.SystemProfiler")
    @patch("subprocess.run")
    def test_execute_script_unix(self, mock_run, mock_profiler):
        """Test executing script on Unix."""
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.detect_os.return_value = OSType.LINUX
        mock_profiler.return_value = mock_profiler_instance

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        executor = ScriptExecutor()
        returncode, stdout, stderr = executor.execute_script(Path("test.sh"))

        assert returncode == 0
        assert "bash" in mock_run.call_args[0][0]

    @patch("envio.core.executor.SystemProfiler")
    @patch("subprocess.run")
    def test_execute_script_timeout(self, mock_run, mock_profiler):
        """Test script execution timeout handling."""
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.detect_os.return_value = OSType.LINUX
        mock_profiler.return_value = mock_profiler_instance

        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 60)

        executor = ScriptExecutor()
        returncode, stdout, stderr = executor.execute_script(Path("test.sh"))

        assert returncode == -1
        assert "timed out" in stderr

    @patch("envio.core.executor.SystemProfiler")
    @patch("subprocess.run")
    def test_execute_script_not_found(self, mock_run, mock_profiler):
        """Test script interpreter not found handling."""
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.detect_os.return_value = OSType.LINUX
        mock_profiler.return_value = mock_profiler_instance

        mock_run.side_effect = FileNotFoundError("bash not found")

        executor = ScriptExecutor()
        returncode, stdout, stderr = executor.execute_script(Path("test.sh"))

        assert returncode == -1
        assert "not found" in stderr

    @patch("envio.core.executor.SystemProfiler")
    @patch("subprocess.run")
    def test_execute_command(self, mock_run, mock_profiler):
        """Test executing a single command."""
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.detect_os.return_value = OSType.LINUX
        mock_profiler.return_value = mock_profiler_instance

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        executor = ScriptExecutor()
        returncode, stdout, stderr = executor.execute_command("echo hello")

        assert returncode == 0
        assert stdout == "output"

    @patch("envio.core.executor.SystemProfiler")
    @patch("subprocess.run")
    def test_execute_command_timeout(self, mock_run, mock_profiler):
        """Test command timeout handling."""
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.detect_os.return_value = OSType.LINUX
        mock_profiler.return_value = mock_profiler_instance

        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)

        executor = ScriptExecutor()
        returncode, stdout, stderr = executor.execute_command("sleep 100", timeout=1)

        assert returncode == -1

    @patch("envio.core.executor.SystemProfiler")
    @patch("subprocess.run")
    def test_execute_interactive(self, mock_run, mock_profiler):
        """Test interactive script execution."""
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.detect_os.return_value = OSType.LINUX
        mock_profiler.return_value = mock_profiler_instance

        mock_run.return_value = MagicMock()

        executor = ScriptExecutor()
        # Should not raise
        executor.execute_interactive(Path("test.sh"))
        mock_run.assert_called_once()

    @patch("envio.core.executor.SystemProfiler")
    @patch("subprocess.run")
    def test_execute_interactive_failure(self, mock_run, mock_profiler):
        """Test interactive script execution failure."""
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.detect_os.return_value = OSType.LINUX
        mock_profiler.return_value = mock_profiler_instance

        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")

        executor = ScriptExecutor()
        with pytest.raises(SystemExit) as exc_info:
            executor.execute_interactive(Path("test.sh"))
        assert exc_info.value.code == 1
