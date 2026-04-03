"""Tests for the sync command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from envio.commands.sync import sync


class TestSyncCommand:
    """Tests for envio sync command."""

    def test_sync_help(self):
        """Test that sync --help works."""
        runner = CliRunner()
        result = runner.invoke(sync, ["--help"])
        assert result.exit_code == 0

    def test_sync_no_project_file(self, tmp_path):
        """Test error when no project file exists."""
        runner = CliRunner()
        with (
            patch("envio.commands.sync._load_dotenv"),
            patch("envio.commands.sync._get_console") as mock_console,
        ):
            console = MagicMock()
            mock_console.return_value = console

            with runner.isolated_filesystem(temp_dir=tmp_path):
                result = runner.invoke(sync, [])

        # Should exit with non-zero because NEW mode calls sys.exit(1)
        assert result.exit_code != 0

    def test_sync_pyproject_mode(self, tmp_path):
        """Test sync with a pyproject.toml present."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\nversion = "0.1.0"\n'
            'dependencies = ["requests"]\n',
            encoding="utf-8",
        )
        runner = CliRunner()
        with (
            patch("envio.commands.sync._load_dotenv"),
            patch("envio.commands.sync._get_console") as mock_console,
            patch(
                "envio.commands.sync._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.sync._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_validate.return_value = ["requests"]
            mock_install.return_value = True

            with runner.isolated_filesystem(temp_dir=tmp_path):
                import shutil

                shutil.copy(tmp_path / "pyproject.toml", "pyproject.toml")
                result = runner.invoke(sync, ["--yes"])

        assert result.exit_code == 0
        mock_install.assert_called_once()

    def test_sync_dry_run(self, tmp_path):
        """Test --dry-run shows packages without installing."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\nversion = "0.1.0"\ndependencies = ["flask"]\n',
            encoding="utf-8",
        )
        runner = CliRunner()
        with (
            patch("envio.commands.sync._load_dotenv"),
            patch("envio.commands.sync._get_console") as mock_console,
            patch(
                "envio.commands.sync._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.sync._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_validate.return_value = ["flask"]
            mock_install.return_value = True

            with runner.isolated_filesystem(temp_dir=tmp_path):
                import shutil

                shutil.copy(tmp_path / "pyproject.toml", "pyproject.toml")
                result = runner.invoke(sync, ["--dry-run"])

        assert result.exit_code == 0
        mock_install.assert_not_called()

    def test_sync_requirements_mode(self, tmp_path):
        """Test sync with a requirements.txt present."""
        (tmp_path / "requirements.txt").write_text("numpy\n", encoding="utf-8")
        runner = CliRunner()
        with (
            patch("envio.commands.sync._load_dotenv"),
            patch("envio.commands.sync._get_console") as mock_console,
            patch(
                "envio.commands.sync._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.sync._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_validate.return_value = ["numpy"]
            mock_install.return_value = True

            with runner.isolated_filesystem(temp_dir=tmp_path):
                import shutil

                shutil.copy(tmp_path / "requirements.txt", "requirements.txt")
                result = runner.invoke(sync, ["--yes"])

        assert result.exit_code == 0
        mock_install.assert_called_once()

    def test_sync_no_packages_in_file(self, tmp_path):
        """Test warning when project file has no packages."""
        (tmp_path / "requirements.txt").write_text("# empty\n", encoding="utf-8")
        runner = CliRunner()
        with (
            patch("envio.commands.sync._load_dotenv"),
            patch("envio.commands.sync._get_console") as mock_console,
        ):
            console = MagicMock()
            mock_console.return_value = console

            with runner.isolated_filesystem(temp_dir=tmp_path):
                import shutil

                shutil.copy(tmp_path / "requirements.txt", "requirements.txt")
                result = runner.invoke(sync, [])

        assert result.exit_code == 0
        console.print_warning.assert_called()

    def test_sync_all_groups(self, tmp_path):
        """Test --all-groups flag includes optional dependency groups."""
        toml = (
            '[project]\nname = "test"\nversion = "0.1.0"\n'
            'dependencies = ["requests"]\n\n'
            '[project.optional-dependencies]\ndev = ["pytest", "ruff"]\n'
        )
        (tmp_path / "pyproject.toml").write_text(toml, encoding="utf-8")
        runner = CliRunner()
        with (
            patch("envio.commands.sync._load_dotenv"),
            patch("envio.commands.sync._get_console") as mock_console,
            patch(
                "envio.commands.sync._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.sync._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_validate.return_value = ["requests", "pytest", "ruff"]
            mock_install.return_value = True

            with runner.isolated_filesystem(temp_dir=tmp_path):
                import shutil

                shutil.copy(tmp_path / "pyproject.toml", "pyproject.toml")
                result = runner.invoke(sync, ["--all-groups", "--yes"])

        assert result.exit_code == 0
        mock_install.assert_called_once()
        # Validate was called with 3 packages (main + dev group)
        call_args = mock_validate.call_args[0][0]
        assert len(call_args) == 3
