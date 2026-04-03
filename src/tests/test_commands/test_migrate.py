"""Tests for the migrate command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from envio.commands.migrate import migrate


class TestMigrateCommand:
    """Tests for envio migrate command."""

    def test_migrate_help(self):
        """Test that migrate --help works."""
        runner = CliRunner()
        result = runner.invoke(migrate, ["--help"])
        assert result.exit_code == 0

    def test_migrate_no_format_detected(self, tmp_path):
        """Test error when no recognisable format is found."""
        runner = CliRunner()
        with (
            patch("envio.commands.migrate._load_dotenv"),
            patch("envio.commands.migrate._get_console") as mock_console,
        ):
            console = MagicMock()
            mock_console.return_value = console
            result = runner.invoke(migrate, [str(tmp_path)])

        assert result.exit_code == 0
        console.print_error.assert_called()

    def test_migrate_invalid_directory(self, tmp_path):
        """Test error when directory does not exist."""
        runner = CliRunner()
        nonexistent = str(tmp_path / "does_not_exist")
        with (
            patch("envio.commands.migrate._load_dotenv"),
            patch("envio.commands.migrate._get_console") as mock_console,
        ):
            console = MagicMock()
            mock_console.return_value = console
            result = runner.invoke(migrate, [nonexistent])

        assert result.exit_code == 0
        console.print_error.assert_called()

    def test_migrate_requirements_txt(self, tmp_path):
        """Test successful migration from requirements.txt."""
        (tmp_path / "requirements.txt").write_text(
            "requests\nflask\n", encoding="utf-8"
        )
        runner = CliRunner()
        with (
            patch("envio.commands.migrate._load_dotenv"),
            patch("envio.commands.migrate._get_console") as mock_console,
            patch("envio.project.migrator.Migrator") as mock_migrator,
        ):
            console = MagicMock()
            mock_console.return_value = console

            mock_data = MagicMock()
            mock_data.project_name = "test-project"
            mock_data.python_version = None
            mock_data.dependencies = ["requests", "flask"]
            mock_data.groups = {"dev": ["pytest"]}

            migrator_instance = MagicMock()
            migrator_instance.detect_format.return_value = MagicMock(
                name="requirements.txt"
            )
            migrator_instance.migrate.return_value = (
                mock_data,
                tmp_path / "pyproject.toml",
            )
            mock_migrator.return_value = migrator_instance

            result = runner.invoke(migrate, [str(tmp_path)])

        assert result.exit_code == 0
        console.print_success.assert_called()

    def test_migrate_dry_run(self, tmp_path):
        """Test --dry-run does not write files."""
        (tmp_path / "requirements.txt").write_text("requests\n", encoding="utf-8")
        runner = CliRunner()
        with (
            patch("envio.commands.migrate._load_dotenv"),
            patch("envio.commands.migrate._get_console") as mock_console,
            patch("envio.project.migrator.Migrator") as mock_migrator,
        ):
            console = MagicMock()
            mock_console.return_value = console

            mock_data = MagicMock()
            mock_data.project_name = "test-project"
            mock_data.python_version = None
            mock_data.dependencies = ["requests"]
            mock_data.groups = {}

            migrator_instance = MagicMock()
            migrator_instance.detect_format.return_value = MagicMock(
                name="requirements.txt"
            )
            # dry_run returns None as out_path
            migrator_instance.migrate.return_value = (mock_data, None)
            mock_migrator.return_value = migrator_instance

            result = runner.invoke(migrate, [str(tmp_path), "--dry-run"])

        assert result.exit_code == 0
        # print_success should NOT be called (no file written)
        console.print_success.assert_not_called()
        # dry run message should appear
        console.print_info.assert_called()

    def test_migrate_unknown_format_raises(self, tmp_path):
        """Test error when --from specifies an unknown format."""
        runner = CliRunner()
        with (
            patch("envio.commands.migrate._load_dotenv"),
            patch("envio.commands.migrate._get_console") as mock_console,
            patch("envio.project.migrator.Migrator") as mock_migrator,
        ):
            console = MagicMock()
            mock_console.return_value = console

            migrator_instance = MagicMock()
            migrator_instance.migrate.side_effect = ValueError("Unknown source format")
            mock_migrator.return_value = migrator_instance

            result = runner.invoke(migrate, [str(tmp_path), "--from", "NotAFormat"])

        assert result.exit_code == 0
        console.print_error.assert_called()

    def test_migrate_default_directory(self, tmp_path):
        """Test that migrate defaults to current directory."""
        runner = CliRunner()
        with (
            patch("envio.commands.migrate._load_dotenv"),
            patch("envio.commands.migrate._get_console") as mock_console,
            patch("envio.project.migrator.Migrator") as mock_migrator,
        ):
            console = MagicMock()
            mock_console.return_value = console

            migrator_instance = MagicMock()
            migrator_instance.detect_format.return_value = None
            mock_migrator.return_value = migrator_instance

            with runner.isolated_filesystem(temp_dir=tmp_path):
                result = runner.invoke(migrate, [])

        assert result.exit_code == 0
        # No format → error
        console.print_error.assert_called()
