"""Tests for the add command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from envio.commands.add import add


class TestAddCommand:
    """Tests for envio add command."""

    def test_add_help(self):
        """Test that add --help works."""
        runner = CliRunner()
        result = runner.invoke(add, ["--help"])
        assert result.exit_code == 0

    def test_add_requires_packages(self):
        """Test that add without packages fails."""
        runner = CliRunner()
        result = runner.invoke(add, [])
        assert result.exit_code != 0

    def test_add_pyproject_mode(self, tmp_path):
        """Test adding packages when pyproject.toml exists."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\nversion = "0.1.0"\ndependencies = []\n',
            encoding="utf-8",
        )
        runner = CliRunner()
        with (
            patch("envio.commands.add._load_dotenv"),
            patch("envio.commands.add._get_console") as mock_console,
            patch(
                "envio.commands.add._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.add._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_validate.return_value = ["requests"]
            mock_install.return_value = True

            with runner.isolated_filesystem(temp_dir=tmp_path):
                import shutil

                shutil.copy(tmp_path / "pyproject.toml", "pyproject.toml")
                result = runner.invoke(add, ["requests", "--yes"])

        assert result.exit_code == 0

    def test_add_dry_run(self, tmp_path):
        """Test --dry-run shows plan without writing."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\nversion = "0.1.0"\ndependencies = []\n',
            encoding="utf-8",
        )
        runner = CliRunner()
        with (
            patch("envio.commands.add._load_dotenv"),
            patch("envio.commands.add._get_console") as mock_console,
            patch(
                "envio.commands.add._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.add._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_validate.return_value = ["flask"]
            mock_install.return_value = True

            with runner.isolated_filesystem(temp_dir=tmp_path):
                import shutil

                shutil.copy(tmp_path / "pyproject.toml", "pyproject.toml")
                result = runner.invoke(add, ["flask", "--dry-run"])

        assert result.exit_code == 0
        # dry-run should NOT call install
        mock_install.assert_not_called()

    def test_add_requirements_mode(self, tmp_path):
        """Test adding packages when only requirements.txt exists."""
        (tmp_path / "requirements.txt").write_text("requests\n", encoding="utf-8")
        runner = CliRunner()
        with (
            patch("envio.commands.add._load_dotenv"),
            patch("envio.commands.add._get_console") as mock_console,
            patch(
                "envio.commands.add._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.add._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_validate.return_value = ["flask"]
            mock_install.return_value = True

            with runner.isolated_filesystem(temp_dir=tmp_path):
                import shutil

                shutil.copy(tmp_path / "requirements.txt", "requirements.txt")
                result = runner.invoke(add, ["flask", "--yes"])

        assert result.exit_code == 0

    def test_add_with_group(self, tmp_path):
        """Test adding packages to an optional-dependency group."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\nversion = "0.1.0"\ndependencies = []\n',
            encoding="utf-8",
        )
        runner = CliRunner()
        with (
            patch("envio.commands.add._load_dotenv"),
            patch("envio.commands.add._get_console") as mock_console,
            patch(
                "envio.commands.add._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.add._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_validate.return_value = ["pytest"]
            mock_install.return_value = True

            with runner.isolated_filesystem(temp_dir=tmp_path):
                import shutil

                shutil.copy(tmp_path / "pyproject.toml", "pyproject.toml")
                result = runner.invoke(add, ["pytest", "--group", "dev", "--yes"])

        assert result.exit_code == 0

    def test_add_no_valid_packages(self, tmp_path):
        """Test error when validation returns no valid packages."""
        runner = CliRunner()
        with (
            patch("envio.commands.add._load_dotenv"),
            patch("envio.commands.add._get_console") as mock_console,
            patch(
                "envio.commands.add._validate_and_normalize_packages"
            ) as mock_validate,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_validate.return_value = []

            with runner.isolated_filesystem(temp_dir=tmp_path):
                result = runner.invoke(add, ["totally-not-real-pkg-xyzzy"])

        assert result.exit_code == 0
        console.print_error.assert_called_with("No valid packages found.")
