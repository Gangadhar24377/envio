"""Envio CLI - AI-Native Environment Orchestrator."""

from __future__ import annotations

import os
import shutil
import time
import traceback
from pathlib import Path

import click

VALID_PACKAGE_MANAGERS = ["pip", "conda", "uv"]


def _load_dotenv() -> None:
    """Load environment variables from .env file."""
    from dotenv import load_dotenv

    load_dotenv()


def detect_package_managers() -> dict[str, bool]:
    """Detect which package managers are available."""
    return {
        "pip": shutil.which("pip") is not None,
        "conda": shutil.which("conda") is not None or _is_conda_active(),
        "uv": shutil.which("uv") is not None,
    }


def _is_conda_active() -> bool:
    """Check if conda is currently active."""
    return (
        os.environ.get("CONDA_PREFIX") is not None
        or os.environ.get("CONDA_DEFAULT_ENV") is not None
    )


def get_hardware_context(profile) -> str:
    """Build hardware context string for LLM."""
    lines = []
    if profile.gpu.available:
        lines.append(f"Hardware: {profile.gpu.name} GPU detected")
        lines.append(f"VRAM: {profile.gpu.vram_mb} MB")
        lines.append(f"CUDA: {profile.gpu.cuda_version}")
    else:
        lines.append("Hardware: CPU-only (no GPU detected)")
    return "\n".join(lines)


def _get_console(verbose: bool):
    """Lazy load ConsoleUI."""
    from envio.ui.console import ConsoleUI

    return ConsoleUI(verbose=verbose)


def _get_profiler():
    """Lazy load SystemProfiler."""
    from envio.core.system_profiler import SystemProfiler

    return SystemProfiler()


def _get_nlp_processor():
    """Lazy load NLPProcessor."""
    from envio.agents.nlp_agent import NLPProcessor

    return NLPProcessor()


def _get_dependency_resolver():
    """Lazy load DependencyResolver."""
    from envio.agents.dependency_resolution_agent import DependencyResolver

    return DependencyResolver()


def _get_executor():
    """Lazy load ScriptExecutor."""
    from envio.core.executor import ScriptExecutor

    return ScriptExecutor()


def _get_script_generator():
    """Lazy load ScriptGeneratorFactory."""
    from envio.core.script_generator import ScriptGeneratorFactory

    return ScriptGeneratorFactory().create()


def _get_response_parser():
    """Lazy load ResponseParser."""
    from envio.llm.parser import ResponseParser

    return ResponseParser()


def _resolve_and_install(
    packages: list[str],
    env_path: str,
    env_name: str,
    package_manager: str,
    preferences: dict | None,
    profile,
    console,
) -> bool:
    """Resolve dependencies and install environment."""
    resolver = _get_dependency_resolver()
    executor = _get_executor()
    script_gen = _get_script_generator()

    # Display plan
    venv_path = Path(env_path) / env_name
    console.print_installation_plan(
        env_name=env_name,
        env_path=str(venv_path),
        package_manager=package_manager,
        packages=packages,
        preferences=preferences,
        profile=profile,
    )

    # Resolve dependencies
    console.print_info("Resolving dependencies...")
    resolved = resolver.resolve(packages, package_manager, profile, preferences)
    final_packages = resolved.get("packages", packages)

    if resolved.get("status") in ("conflict", "error"):
        console.print_resolution_status(
            resolved["status"],
            resolved.get("resolution_method", "unknown"),
        )

    console.print_packages_table(final_packages, "Resolved Packages")

    # Generate commands
    console.print_info("Generating installation script...")

    # Create and execute script
    script_content = script_gen.generate_setup_script(
        venv_path=str(venv_path),
        packages=final_packages,
        package_manager=package_manager,
    )

    script_path = executor.write_script(
        script_content,
        Path(env_path) / f"envio_setup_{env_name}",
    )

    console.print_info("Executing installation...")
    with console.spinner("Installing packages..."):
        returncode, stdout, stderr = executor.execute_script(
            script_path,
            capture_output=True,
            timeout=300,
        )

    if returncode == 0:
        console.print_success("Environment setup completed!")
        activation_cmd = script_gen.generate_venv_activation_instructions(venv_path)
        console.print_info("To activate the environment:")
        console.print_code_block(activation_cmd.strip(), "bash")
        return True
    else:
        console.print_error("Installation failed!")
        console.print_code_block(stderr or stdout, "bash")
        return False


def _parse_nlp_result(result: dict) -> tuple[list[str], str, dict]:
    """Parse NLP result into packages, env_type, preferences."""
    parser = _get_response_parser()
    packages = parser.parse_packages(result)
    env_type = result.get("environment_type", "uv").lower()
    if env_type not in VALID_PACKAGE_MANAGERS:
        env_type = "uv"
    preferences = result.get("preferences", {})
    return packages, env_type, preferences


def _scan_directory(directory: Path) -> dict | None:
    """Scan directory for requirements files."""
    files_to_check = [
        ("requirements.txt", _parse_requirements_txt),
        ("pyproject.toml", _parse_pyproject_toml),
        ("setup.py", _parse_setup_py),
        ("environment.yml", _parse_environment_yml),
        ("conda.yml", _parse_environment_yml),
    ]

    for filename, parser in files_to_check:
        filepath = directory / filename
        if filepath.exists():
            return parser(filepath, filename)

    return None


def _parse_requirements_txt(filepath: Path, filename: str) -> dict:
    """Parse requirements.txt file."""
    packages = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                packages.append(line)
    return {
        "source": filename,
        "packages": packages,
        "env_type": "pip",
    }


def _parse_pyproject_toml(filepath: Path, filename: str) -> dict:
    """Parse pyproject.toml file."""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    with open(filepath, "rb") as f:
        data = tomllib.load(f)

    packages = data.get("project", {}).get("dependencies", [])
    return {
        "source": filename,
        "packages": packages,
        "env_type": "pip",
    }


def _parse_setup_py(filepath: Path, filename: str) -> dict:
    """Parse setup.py file."""
    import re

    with open(filepath) as f:
        content = f.read()

    install_requires = re.findall(
        r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL
    )
    if install_requires:
        packages = re.findall(r'["\']([^"\']+)["\']', install_requires[0])
        return {
            "source": filename,
            "packages": packages,
            "env_type": "pip",
        }
    return {
        "source": filename,
        "packages": [],
        "env_type": "pip",
    }


def _parse_environment_yml(filepath: Path, filename: str) -> dict:
    """Parse environment.yml file."""
    try:
        import yaml

        with open(filepath) as f:
            data = yaml.safe_load(f)

        packages = data.get("dependencies", [])
        return {
            "source": filename,
            "packages": packages,
            "env_type": "conda",
        }
    except Exception:
        return {
            "source": filename,
            "packages": [],
            "env_type": "conda",
        }


# =============================================================================
# CLI COMMANDS
# =============================================================================


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Envio - AI-Native Environment Orchestrator."""
    pass


@cli.command()
@click.option(
    "--env-type", "-e", "env_type", default=None, help="Package manager (pip/conda/uv)"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def init(env_type: str | None, verbose: bool) -> None:
    """Initialize environment from directory."""
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Init", "Scan directory and set up environment")

    profiler = _get_profiler()
    profile = profiler.profile()

    try:
        # Detect package managers
        available = detect_package_managers()
        console.print_info("Available package managers:")
        for pm, ok in available.items():
            status = "available" if ok else "not found"
            console._safe_print(f"  - {pm} ({status})")

        # Scan directory
        directory = Path.cwd()
        console.print_info(f"Scanning {directory}...")

        detected = _scan_directory(directory)

        if not detected:
            console.print_warning("No requirements file found")
            console.print_info("Scanning Python files for imports...")

            # Scan Python files
            py_files = list(directory.glob("*.py")) + list(directory.glob("**/*.py"))
            imports = set()
            for py_file in py_files:
                try:
                    import ast

                    with open(py_file) as f:
                        tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.add(alias.name.split(".")[0])
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports.add(node.module.split(".")[0])
                except Exception:
                    pass

            # Filter out standard library
            stdlib = {
                "os",
                "sys",
                "re",
                "json",
                "time",
                "datetime",
                "pathlib",
                "collections",
                "itertools",
                "functools",
                "typing",
                "abc",
                "io",
                "logging",
                "unittest",
                "argparse",
                "shutil",
                "glob",
                "pickle",
                "copy",
                "math",
                "random",
                "string",
                "textwrap",
            }
            third_party = sorted(imports - stdlib)

            if third_party:
                console.print_info(f"Found {len(third_party)} third-party imports")
                detected = {
                    "source": "detected from imports",
                    "packages": third_party,
                    "env_type": "uv",
                }
            else:
                console.print_error("No packages detected. Use 'envio prompt' instead.")
                return

        # Show detected packages
        console.print_info(f"Detected from: {detected['source']}")
        console.print_packages_table(detected["packages"], "Detected Packages")

        # Ask for environment name
        env_name = input("\nEnvironment name [default: .venv]: ").strip() or ".venv"
        env_path = str(directory)

        # Use user-specified env_type or detected type
        final_env_type = env_type if env_type else detected["env_type"]
        console.print_info(f"Package manager: {final_env_type}")

        # Setup environment
        _resolve_and_install(
            packages=detected["packages"],
            env_path=env_path,
            env_name=env_name,
            package_manager=final_env_type,
            preferences={},
            profile=profile,
            console=console,
        )

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())


@cli.command()
@click.argument("prompt_text", nargs=-1, required=True)
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option("--env-type", "-e", "env_type", default="uv", help="Package manager")
@click.option("--cpu-only", is_flag=True, help="Force CPU-only mode")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def prompt(
    prompt_text: tuple[str, ...],
    name: str | None,
    path: str | None,
    env_type: str,
    cpu_only: bool,
    verbose: bool,
) -> None:
    """Set up environment from natural language prompt."""
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Prompt", "Natural language environment setup")

    profiler = _get_profiler()
    profile = profiler.profile()

    try:
        user_input = " ".join(prompt_text)
        console.print_info(f"Request: {user_input}")

        # NLP processing
        console.print_info("Analyzing request...")
        nlp = _get_nlp_processor()
        hw_context = get_hardware_context(profile)

        def callback(msg: str) -> None:
            console.print_agent_thought("NLP", msg)

        result = nlp.extract(user_input, hw_context, callback)
        packages, _, preferences = _parse_nlp_result(result)

        if cpu_only:
            preferences["cpu_only"] = True

        console.print_packages_table(packages, "Suggested Packages")

        # Ask for environment name and path
        default_path = str(Path.home() / "Documents" / "envs")
        env_path = (
            path or input(f"\nPath [default: {default_path}]: ").strip() or default_path
        )
        env_name = name or input("Name: ").strip() or f"env_{int(time.time())}"

        # Resolve and install
        _resolve_and_install(
            packages=packages,
            env_path=env_path,
            env_name=env_name,
            package_manager=env_type,
            preferences=preferences,
            profile=profile,
            console=console,
        )

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())


@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def doctor(verbose: bool) -> None:
    """Show system hardware profile."""
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Doctor", "System hardware profile")

    profiler = _get_profiler()

    try:
        console.print_info("Profiling system...")
        with console.spinner("Detecting hardware..."):
            profile = profiler.profile()

        console.print_hardware_profile(profile)

        # Check package managers
        console.print_info("Package managers:")
        managers = detect_package_managers()
        for pm, ok in managers.items():
            status = "[green]available[/green]" if ok else "[red]not found[/red]"
            console._safe_print(f"  - {pm}: {status}")

        # Check LLM configuration
        console.print_info("LLM configuration:")
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            console._safe_print("  - API Key: [green]configured[/green]")
        else:
            console._safe_print("  - API Key: [red]not set[/red]")

        model = os.getenv("ENVIO_LLM_MODEL", "gpt-4o-mini")
        console._safe_print(f"  - Model: {model}")

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())


@cli.command()
@click.argument("packages", nargs=-1, required=True)
@click.option("--env-type", "-e", "env_type", default="uv", help="Package manager")
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option("--cpu-only", is_flag=True, help="Force CPU-only mode")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def install(
    packages: tuple[str, ...],
    env_type: str,
    name: str | None,
    path: str | None,
    cpu_only: bool,
    verbose: bool,
) -> None:
    """Install packages directly."""
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Install", "Direct package installation")

    profiler = _get_profiler()
    profile = profiler.profile()

    try:
        if env_type not in VALID_PACKAGE_MANAGERS:
            console.print_warning(f"Invalid: {env_type}. Using uv.")
            env_type = "uv"

        pkg_list = list(packages)
        preferences = {"cpu_only": cpu_only} if cpu_only else {}

        env_name = name or f"env_{int(time.time())}"
        env_path = path or str(Path.home() / "Documents" / "envs")

        _resolve_and_install(
            packages=pkg_list,
            env_path=env_path,
            env_name=env_name,
            package_manager=env_type,
            preferences=preferences,
            profile=profile,
            console=console,
        )

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
