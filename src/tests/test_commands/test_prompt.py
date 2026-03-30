"""Tests for the prompt command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from envio.commands.prompt import prompt


class TestPromptCommand:
    """Tests for envio prompt command."""

    def test_prompt_help(self):
        """Test that prompt --help works."""
        runner = CliRunner()
        result = runner.invoke(prompt, ["--help"])
        assert result.exit_code == 0
        assert (
            "natural language" in result.output.lower()
            or "prompt" in result.output.lower()
        )

    def test_prompt_requires_text(self):
        """Test that prompt without text fails."""
        runner = CliRunner()
        result = runner.invoke(prompt, [])
        assert result.exit_code != 0

    def test_prompt_no_api_key_warns(self):
        """Test that prompt warns when no API key is configured."""
        runner = CliRunner()
        with (
            patch("envio.commands.prompt._load_dotenv"),
            patch("envio.commands.prompt._get_console") as mock_console,
            patch("envio.config.get_api_key") as mock_api_key,
            patch("envio.commands.prompt._get_profiler") as mock_profiler,
            patch("envio.commands.prompt._get_nlp_processor") as mock_nlp,
            patch(
                "envio.commands.prompt._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.prompt._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_api_key.return_value = None
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            nlp = MagicMock()
            nlp.extract.return_value = {
                "packages": ["flask"],
                "environment_type": "uv",
                "preferences": {},
            }
            mock_nlp.return_value = nlp
            mock_validate.return_value = ["flask"]
            mock_install.return_value = True

            result = runner.invoke(
                prompt,
                ["web app with flask", "-p", "/tmp/envs", "-n", "myenv"],
            )
        assert result.exit_code == 0
        console.print_warning.assert_any_call(
            "No API key found. Falling back to PyPI-only resolution."
        )

    def test_prompt_resolves_packages(self):
        """Test that prompt calls NLP and resolver."""
        runner = CliRunner()
        with (
            patch("envio.commands.prompt._load_dotenv"),
            patch("envio.commands.prompt._get_console") as mock_console,
            patch("envio.config.get_api_key") as mock_api_key,
            patch("envio.commands.prompt._get_profiler") as mock_profiler,
            patch("envio.commands.prompt._get_nlp_processor") as mock_nlp_cls,
            patch(
                "envio.commands.prompt._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.prompt._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_api_key.return_value = "sk-test"
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            nlp = MagicMock()
            nlp.extract.return_value = {
                "packages": ["flask", "sqlalchemy"],
                "environment_type": "uv",
                "preferences": {},
            }
            mock_nlp_cls.return_value = nlp
            mock_validate.return_value = ["flask", "sqlalchemy"]
            mock_install.return_value = True

            result = runner.invoke(
                prompt,
                ["flask web app", "-p", "/tmp/envs", "-n", "flask-app"],
            )
        assert result.exit_code == 0
        nlp.extract.assert_called_once()
        mock_install.assert_called_once()

    def test_prompt_dry_run(self):
        """Test prompt with --dry-run flag."""
        runner = CliRunner()
        with (
            patch("envio.commands.prompt._load_dotenv"),
            patch("envio.commands.prompt._get_console") as mock_console,
            patch("envio.config.get_api_key") as mock_api_key,
            patch("envio.commands.prompt._get_profiler") as mock_profiler,
            patch("envio.commands.prompt._get_nlp_processor") as mock_nlp_cls,
            patch(
                "envio.commands.prompt._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.prompt._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_api_key.return_value = "sk-test"
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            nlp = MagicMock()
            nlp.extract.return_value = {
                "packages": ["flask"],
                "environment_type": "uv",
                "preferences": {},
            }
            mock_nlp_cls.return_value = nlp
            mock_validate.return_value = ["flask"]
            mock_install.return_value = True

            result = runner.invoke(
                prompt,
                ["flask app", "--dry-run", "-p", "/tmp/envs", "-n", "myenv"],
            )
        assert result.exit_code == 0
        call_kwargs = mock_install.call_args[1]
        assert call_kwargs.get("dry_run") is True

    def test_prompt_invalid_path_rejected(self):
        """Test that prompt rejects path traversal."""
        runner = CliRunner()
        with (
            patch("envio.commands.prompt._load_dotenv"),
            patch("envio.commands.prompt._get_console") as mock_console,
            patch("envio.config.get_api_key") as mock_api_key,
            patch("envio.commands.prompt._get_profiler") as mock_profiler,
            patch("envio.commands.prompt._get_nlp_processor") as mock_nlp_cls,
            patch(
                "envio.commands.prompt._validate_and_normalize_packages"
            ) as mock_validate,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_api_key.return_value = "sk-test"
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            nlp = MagicMock()
            nlp.extract.return_value = {
                "packages": ["flask"],
                "environment_type": "uv",
                "preferences": {},
            }
            mock_nlp_cls.return_value = nlp
            mock_validate.return_value = ["flask"]

            result = runner.invoke(
                prompt,
                ["flask app", "-p", "/tmp/../etc/shadow", "-n", "myenv"],
            )
        assert result.exit_code == 0
        console.print_error.assert_called()

    def test_prompt_cpu_only_and_optimize_for(self):
        """Test prompt with --cpu-only and --optimize-for flags."""
        runner = CliRunner()
        with (
            patch("envio.commands.prompt._load_dotenv"),
            patch("envio.commands.prompt._get_console") as mock_console,
            patch("envio.config.get_api_key") as mock_api_key,
            patch("envio.commands.prompt._get_profiler") as mock_profiler,
            patch("envio.commands.prompt._get_nlp_processor") as mock_nlp_cls,
            patch(
                "envio.commands.prompt._validate_and_normalize_packages"
            ) as mock_validate,
            patch("envio.commands.prompt._resolve_and_install") as mock_install,
        ):
            console = MagicMock()
            mock_console.return_value = console
            mock_api_key.return_value = "sk-test"
            profiler = MagicMock()
            profiler.profile.return_value = MagicMock()
            mock_profiler.return_value = profiler
            nlp = MagicMock()
            nlp.extract.return_value = {
                "packages": ["torch"],
                "environment_type": "uv",
                "preferences": {},
            }
            mock_nlp_cls.return_value = nlp
            mock_validate.return_value = ["torch"]
            mock_install.return_value = True

            result = runner.invoke(
                prompt,
                [
                    "pytorch training",
                    "--cpu-only",
                    "--optimize-for",
                    "training",
                    "-p",
                    "/tmp/envs",
                    "-n",
                    "myenv",
                ],
            )
        assert result.exit_code == 0
        # Conflict warning should have been printed
        console.print_warning.assert_called()
