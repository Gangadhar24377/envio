"""Envio CLI - AI-Native Environment Orchestrator."""

from __future__ import annotations

import os
import shutil
import sys
import time
import traceback
from pathlib import Path

import click
import requests

from envio import __version__

VALID_PACKAGE_MANAGERS = ["pip", "conda", "uv"]

# Common import name to PyPI package name mapping
IMPORT_TO_PYPI = {
    "pil": "pillow",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "yaml": "pyyaml",
    "ipython": "ipython",
    "scipy": "scipy",
    "PIL": "pillow",
}


def _normalize_package(pkg: str) -> list[str]:
    """Normalize package name and validate version exists on PyPI.

    Args:
        pkg: Package specification (e.g., "PIL==1.1.6", "requests", "numpy>=1.0")

    Returns:
        List with normalized package name and status [normalized_name, status]
        status: "ok" = valid, "not_found" = version doesn't exist, "unknown" = can't determine
    """
    # Extract package name and version
    version_spec = None
    if "==" in pkg:
        pkg_name, pkg_version = pkg.split("==", 1)
        pkg_name = pkg_name.strip().lower()
        pkg_version = pkg_version.strip()
        version_spec = f"=={pkg_version}"
    elif ">=" in pkg:
        pkg_name, _ = pkg.split(">=", 1)
        pkg_name = pkg_name.strip().lower()
    elif "<=" in pkg:
        pkg_name, _ = pkg.split("<=", 1)
        pkg_name = pkg_name.strip().lower()
    else:
        pkg_name = pkg.strip().lower()

    # Map to PyPI name
    pypi_name = IMPORT_TO_PYPI.get(pkg_name, pkg_name)

    # If version specified, validate it exists on PyPI (using pypi_name)
    if version_spec:
        try:
            url = f"https://pypi.org/pypi/{pypi_name}/{pkg_version}/json"
            response = requests.get(url, timeout=5)
            if response.status_code == 404:
                return [pkg, "not_found"]
        except Exception:
            pass

    # Return normalized name
    if version_spec:
        normalized = f"{pypi_name}{version_spec}"
    else:
        normalized = pypi_name

    return [normalized, "ok"]


def _validate_and_normalize_packages(packages: list[str], console) -> list[str]:
    """Validate packages against PyPI and normalize names.

    Args:
        packages: List of package specifications
        console: Console UI for output

    Returns:
        List of normalized, validated packages
    """
    normalized = []
    issues = []

    console.print_info("Validating packages against PyPI...")

    for pkg in packages:
        result, status = _normalize_package(pkg)

        if status == "not_found":
            issues.append(f"  {pkg} → not found on PyPI")
            # Try to find latest version
            try:
                pkg_name = pkg.split("==")[0].lower()
                pypi_name = IMPORT_TO_PYPI.get(pkg_name, pkg_name)
                url = f"https://pypi.org/pypi/{pypi_name}/json"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    latest = data.get("info", {}).get("version", "unknown")
                    fixed = f"{pypi_name}=={latest}"
                    console.print_info(f"  {pkg} → {fixed}")
                    normalized.append(fixed)
                else:
                    normalized.append(result)
            except Exception:
                normalized.append(result)
        else:
            normalized.append(result)

    if issues:
        console.print_warning("Some packages have issues:" + "\n".join(issues))

    return normalized


def _ensure_envio_config() -> None:
    """Ensure ~/.envio/ directory exists with sample .env on first run."""
    from pathlib import Path

    config_dir = Path.home() / ".envio"
    sample_env = config_dir / ".env.example"
    user_env = config_dir / ".env"

    config_dir.mkdir(parents=True, exist_ok=True)

    if not user_env.exists() and not sample_env.exists():
        sample_content = """# Envio Configuration
# Add your API keys here - this file works from any directory!

# OpenAI API Key (required for AI features)
OPENAI_API_KEY=sk-your-openai-key-here

# Optional: Serper API Key (for web search)
# SERPER_API_KEY=your-serper-key

# Optional: Ollama settings (for local models)
# ENVIO_LLM_MODEL=llama3
# ENVIO_OLLAMA_HOST=http://localhost:11434
"""
        sample_env.write_text(sample_content)


def _load_dotenv() -> None:
    """Load environment variables from .env file.

    Looks in multiple locations (priority order):
    1. Current working directory (for project-specific .env)
    2. Envio project directory (where envio is installed)
    3. ~/.envio/ (global config - works from any directory)
    """
    _ensure_envio_config()

    from dotenv import load_dotenv
    from pathlib import Path

    locations = [
        Path.cwd() / ".env",
        Path(__file__).parent.parent / ".env",
        Path.home() / ".envio" / ".env",
    ]

    for env_path in locations:
        if env_path.exists():
            load_dotenv(env_path, override=False)
            return


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
    original_command: str = "envio install",
    dry_run: bool = False,
    skip_confirm: bool = False,
) -> bool:
    """Resolve dependencies and install environment with self-healing."""
    resolver = _get_dependency_resolver()
    executor = _get_executor()
    script_gen = _get_script_generator()

    venv_path = Path(env_path) / env_name
    max_retries = 3

    for attempt in range(max_retries):
        # Display plan (only on first attempt)
        if attempt == 0:
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

        # Check for any failure status and attempt healing
        if resolved.get("status") in ("conflict", "error", "not_found", "failed"):
            console.print_resolution_status(
                resolved.get("status", "error"),
                resolved.get("resolution_method", "unknown"),
                resolved.get("error"),
            )

            # Trigger self-healing for failed resolutions
            console.print_info("Attempting to fix resolution issues...")
            healed = resolver.heal_and_resolve(
                packages,
                resolved.get("error", ""),
                package_manager,
            )

            if healed.get("status") in ("healed", "resolved"):
                final_packages = healed.get("packages", packages)
                console.print_success(f"Resolved! Using packages: {final_packages}")
                console.print_resolution_status(
                    "success",
                    healed.get("resolution_method", "healed"),
                )
            elif healed.get("status") == "partial":
                console.print_warning(
                    "Partial resolution - some packages may need manual intervention"
                )
                final_packages = healed.get("packages", packages)
            # If healing also failed, continue with original packages

        # Also handle cases where resolution succeeded but had to fix issues (e.g., not_found -> resolved)
        elif resolved.get("resolution_method") in ("ai_search", "ai_healed_validated"):
            # AI had to fix issues during initial resolution
            final_packages = resolved.get("packages", packages)
            console.print_success(f"Resolved via AI! Using packages: {final_packages}")

        console.print_packages_table(final_packages, "Resolved Packages")

        # Get CUDA URL for PyTorch if GPU is available
        cuda_url = None
        if profile.gpu.available and package_manager in ("pip", "uv"):
            cuda_version = profile.gpu.cuda_version
            if cuda_version:
                if "12.4" in cuda_version:
                    cuda_url = "https://download.pytorch.org/whl/cu124"
                elif "12.1" in cuda_version:
                    cuda_url = "https://download.pytorch.org/whl/cu121"
                elif "11.8" in cuda_version:
                    cuda_url = "https://download.pytorch.org/whl/cu118"

        # Generate script
        console.print_info("Generating installation script...")
        script_content = script_gen.generate_setup_script(
            venv_path=str(venv_path),
            packages=final_packages,
            package_manager=package_manager,
            cuda_url=cuda_url,
        )

        script_path = executor.write_script(
            script_content,
            Path(env_path) / f"envio_setup_{env_name}",
        )

        # Dry run: show what would happen without executing
        if dry_run:
            console.print_info("[DRY RUN] Would execute the following script:")
            console.print_code_block(script_content, "bash")
            console.print_info(f"[DRY RUN] Script saved to: {script_path}")
            console.print_info("[DRY RUN] No changes were made to your system.")
            return True

        # Interactive confirmation
        if not skip_confirm:
            if not console.confirm("Proceed with installation?", default=True):
                console.print_warning("Installation cancelled by user.")
                console.print_info(f"Generated script saved to: {script_path}")
                return False

        # Execute script
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

        # Self-healing: try to fix the error
        if attempt < max_retries - 1:
            error_output = stderr or stdout
            console.print_warning(
                f"Installation failed (attempt {attempt + 1}/{max_retries})"
            )
            console.print_info("Analyzing error with AI...")

            console.print_healing_status(attempt + 1, max_retries, error_output)

            healing_result = resolver.heal_and_resolve(
                final_packages, error_output, package_manager
            )

            if healing_result.get("status") == "healed":
                console.print_healing_solution(
                    f"Fixed packages: {healing_result['packages']}"
                )
                packages = healing_result["packages"]
                continue
            else:
                console.print_warning(
                    "Could not find fix, retrying with original packages..."
                )
        else:
            console.print_error("Installation failed after all attempts!")
            console.print_code_block(stderr or stdout, "bash")
            return False

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
        "env_type": None,
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


@cli.group()
def config() -> None:
    """Manage envio configuration."""
    pass


@config.command("show")
def config_show() -> None:
    """Show current configuration."""
    from envio.config import show_config

    show_config()


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value."""
    from envio.config import set_default_envs_dir, set_preferred_package_manager

    if key == "default_envs_dir":
        set_default_envs_dir(value)
        print(f"✓ Default envs directory set to: {value}")
    elif key == "preferred_package_manager":
        set_preferred_package_manager(value)
        print(f"✓ Preferred package manager set to: {value}")
    else:
        print(f"Unknown setting: {key}")
        print("Available: default_envs_dir, preferred_package_manager")


@config.command("unset")
@click.argument("key")
def config_unset(key: str) -> None:
    """Unset a configuration value."""
    from envio import config as config_module

    cfg = config_module.load_config()
    if key in cfg:
        del cfg[key]
        config_module.save_config(cfg)
        print(f"✓ {key} has been unset")
    else:
        print(f"{key} is not set")


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

            # Filter out standard library using dynamic detection
            stdlib = sys.stdlib_module_names
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

        # Use user-specified env_type, detected type, or default to uv
        final_env_type = env_type or detected.get("env_type") or "uv"
        console.print_info(f"Package manager: {final_env_type}")

        # Validate and normalize packages before installation
        validated_packages = _validate_and_normalize_packages(
            detected["packages"], console
        )

        # Setup environment
        _resolve_and_install(
            packages=validated_packages,
            env_path=env_path,
            env_name=env_name,
            package_manager=final_env_type,
            preferences={},
            profile=profile,
            console=console,
            original_command="envio init",
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
@click.option(
    "--optimize-for",
    "optimize_for",
    default=None,
    type=click.Choice(["training", "inference", "development"]),
    help="Optimize packages for specific use case",
)
@click.option("--dry-run", is_flag=True, help="Preview without making changes")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def prompt(
    prompt_text: tuple[str, ...],
    name: str | None,
    path: str | None,
    env_type: str,
    cpu_only: bool,
    optimize_for: str | None,
    dry_run: bool,
    yes: bool,
    verbose: bool,
) -> None:
    """Set up environment from natural language prompt."""
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Prompt", "Natural language environment setup")

    # Check for API key
    api_key = os.getenv("ENVIO_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print_warning("No API key found. Falling back to PyPI-only resolution.")
        console.print_info(
            "Set ENVIO_LLM_API_KEY or OPENAI_API_KEY for AI-powered features."
        )

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
        if optimize_for:
            preferences["optimize_for"] = optimize_for
            console.print_info(f"Optimizing for: {optimize_for}")

        console.print_packages_table(packages, "Suggested Packages")

        # Validate and normalize packages before installation
        validated_packages = _validate_and_normalize_packages(packages, console)

        # Ask for environment name and path
        default_path = str(Path.home() / "Documents" / "envs")
        env_path = (
            path or input(f"\nPath [default: {default_path}]: ").strip() or default_path
        )
        env_name = name or input("Name: ").strip() or f"env_{int(time.time())}"

        # Resolve and install
        _resolve_and_install(
            packages=validated_packages,
            env_path=env_path,
            env_name=env_name,
            package_manager=env_type,
            preferences=preferences,
            profile=profile,
            console=console,
            original_command=f"envio prompt '{user_input}'",
            dry_run=dry_run,
            skip_confirm=yes,
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
@click.option(
    "--optimize-for",
    "optimize_for",
    default=None,
    type=click.Choice(["training", "inference", "development"]),
    help="Optimize packages for specific use case",
)
@click.option("--dry-run", is_flag=True, help="Preview without making changes")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def install(
    packages: tuple[str, ...],
    env_type: str,
    name: str | None,
    path: str | None,
    cpu_only: bool,
    optimize_for: str | None,
    dry_run: bool,
    yes: bool,
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

        # Validate and normalize packages
        validated_packages = _validate_and_normalize_packages(pkg_list, console)

        preferences = {}
        if cpu_only:
            preferences["cpu_only"] = True
        if optimize_for:
            preferences["optimize_for"] = optimize_for
            console.print_info(f"Optimizing for: {optimize_for}")

        env_name = name or f"env_{int(time.time())}"
        env_path = path or str(Path.home() / "Documents" / "envs")

        # Build the command string for registry
        cmd_parts = ["envio install"] + list(pkg_list)
        if env_type != "uv":
            cmd_parts.append(f"--env-type {env_type}")
        if cpu_only:
            cmd_parts.append("--cpu-only")
        if optimize_for:
            cmd_parts.append(f"--optimize-for {optimize_for}")

        _resolve_and_install(
            packages=validated_packages,
            env_path=env_path,
            env_name=env_name,
            package_manager=env_type,
            preferences=preferences,
            profile=profile,
            console=console,
            original_command=" ".join(cmd_parts),
            dry_run=dry_run,
            skip_confirm=yes,
        )

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())


@cli.command()
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option(
    "--output", "-o", default=None, help="Output file path (default: envio.lock)"
)
@click.option(
    "--format",
    "fmt",
    default="json",
    type=click.Choice(["json", "text"]),
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def lock(
    name: str | None,
    path: str | None,
    output: str | None,
    fmt: str,
    verbose: bool,
) -> None:
    """Generate a lockfile for reproducible environments."""
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Lock", "Generate reproducible lockfile")

    try:
        import json
        import platform
        from datetime import datetime

        from envio.core.virtualenv_manager import VirtualEnvManager

        manager = VirtualEnvManager()

        # Find the environment
        env_path = Path(path) if path else None
        if not env_path:
            # Search in default location
            default_base = Path.home() / "Documents" / "envs"
            if name:
                env_path = default_base / name
            else:
                # Search current directory
                env_path = Path.cwd() / ".venv"

        if not manager.exists(env_path):
            console.print_error(f"Virtual environment not found at: {env_path}")
            return

        console.print_info(f"Locking environment: {env_path}")

        # Get installed packages with versions
        success, packages = manager.get_installed_packages_with_versions(env_path)

        if not success:
            console.print_error("Failed to get installed packages")
            return

        if not packages:
            console.print_warning("No packages installed in this environment")
            return

        console.print_info(f"Found {len(packages)} packages")

        # Get hardware profile
        profiler = _get_profiler()
        profile = profiler.profile()

        # Generate lockfile content
        lock_data = {
            "version": "1.0",
            "generated_by": f"envio {__version__}",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "package_manager": "pip",
            "python_version": platform.python_version(),
            "environment_name": name or env_path.name,
            "environment_path": str(env_path),
            "hardware": {
                "gpu": profile.gpu.name if profile.gpu.available else None,
                "cuda": profile.gpu.cuda_version if profile.gpu.available else None,
            },
            "packages": packages,
        }

        # Determine output file
        output_path = Path(output) if output else Path("envio.lock")

        if fmt == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(lock_data, f, indent=2, ensure_ascii=False)
                f.write("\n")
        else:
            # Text format (requirements.txt style)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# Generated by envio {__version__}\n")
                f.write(f"# Date: {lock_data['generated_at']}\n")
                f.write(f"# Python: {platform.python_version()}\n")
                if profile.gpu.available:
                    f.write(f"# GPU: {profile.gpu.name}\n")
                f.write("\n")
                for pkg in sorted(packages, key=lambda x: x["name"].lower()):
                    f.write(f"{pkg['name']}=={pkg['version']}\n")

        console.print_success(f"Lockfile saved to: {output_path}")
        console.print_info(f"Locked {len(packages)} packages")

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())


@cli.command()
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option("--output", "-o", default=None, help="Output file path")
@click.option(
    "--format",
    "fmt",
    default="requirements",
    type=click.Choice(["requirements", "dockerfile", "devcontainer"]),
    help="Export format",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def export(
    name: str | None,
    path: str | None,
    output: str | None,
    fmt: str,
    verbose: bool,
) -> None:
    """Export environment configuration to various formats."""
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Export", f"Export to {fmt} format")

    try:
        import platform

        from envio.core.virtualenv_manager import VirtualEnvManager

        manager = VirtualEnvManager()

        # Find the environment
        env_path = Path(path) if path else None
        if not env_path:
            # Search in default location
            default_base = Path.home() / "Documents" / "envs"
            if name:
                env_path = default_base / name
            else:
                # Search current directory
                env_path = Path.cwd() / ".venv"

        if not manager.exists(env_path):
            console.print_error(f"Virtual environment not found at: {env_path}")
            return

        console.print_info(f"Exporting environment: {env_path}")

        # Get installed packages with versions
        success, packages = manager.get_installed_packages_with_versions(env_path)

        if not success:
            console.print_error("Failed to get installed packages")
            return

        if not packages:
            console.print_warning("No packages installed in this environment")
            return

        python_version = platform.python_version()
        env_name = name or env_path.name

        # Generate content based on format
        if fmt == "requirements":
            content = _generate_requirements_export(packages, __version__)
            default_output = "requirements.txt"
        elif fmt == "dockerfile":
            content = _generate_dockerfile_export(packages, python_version, __version__)
            default_output = "Dockerfile"
        elif fmt == "devcontainer":
            content = _generate_devcontainer_export(
                packages, python_version, env_name, __version__
            )
            default_output = "devcontainer.json"
        else:
            console.print_error(f"Unknown format: {fmt}")
            return

        # Determine output file
        output_path = Path(output) if output else Path(default_output)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        console.print_success(f"Exported to: {output_path}")
        console.print_info(f"Format: {fmt}")
        console.print_info(f"Packages: {len(packages)}")

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())


def _generate_requirements_export(packages: list[dict], version: str) -> str:
    """Generate requirements.txt content."""
    lines = [f"# Generated by envio {version}\n"]
    for pkg in sorted(packages, key=lambda x: x["name"].lower()):
        lines.append(f"{pkg['name']}=={pkg['version']}\n")
    return "".join(lines)


def _generate_dockerfile_export(
    packages: list[dict], python_version: str, version: str
) -> str:
    """Generate Dockerfile content."""
    major_minor = ".".join(python_version.split(".")[:2])
    pkg_list = " ".join(
        f"{pkg['name']}=={pkg['version']}"
        for pkg in sorted(packages, key=lambda x: x["name"].lower())
    )

    return f"""# Generated by envio {version}
FROM python:{major_minor}-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir {pkg_list}

# Copy application code
COPY . .

CMD ["python"]
"""


def _generate_devcontainer_export(
    packages: list[dict],
    python_version: str,
    env_name: str,
    version: str,
) -> str:
    """Generate devcontainer.json content."""
    import json

    pkg_list = " ".join(
        f"{pkg['name']}=={pkg['version']}"
        for pkg in sorted(packages, key=lambda x: x["name"].lower())
    )

    devcontainer = {
        "name": env_name,
        "image": f"mcr.microsoft.com/devcontainers/python:{'.'.join(python_version.split('.')[:2])}",
        "postCreateCommand": f"pip install {pkg_list}",
        "customizations": {
            "vscode": {
                "extensions": [
                    "ms-python.python",
                    "ms-python.vscode-pylance",
                ],
                "settings": {
                    "python.defaultInterpreterPath": "/usr/local/bin/python",
                },
            }
        },
    }

    return json.dumps(devcontainer, indent=2) + "\n"


@cli.command()
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option(
    "--severity",
    default=None,
    type=click.Choice(["low", "medium", "high", "critical"]),
    help="Minimum severity to report",
)
@click.option("--fix", is_flag=True, help="Auto-fix vulnerabilities by upgrading")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def audit(
    name: str | None,
    path: str | None,
    severity: str | None,
    fix: bool,
    verbose: bool,
) -> None:
    """Scan environment for known vulnerabilities."""
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Audit", "Security vulnerability scan")

    try:
        import shutil
        import subprocess
        import sys

        from envio.core.virtualenv_manager import VirtualEnvManager

        # Check if pip-audit is available globally first
        pip_audit_cmd = shutil.which("pip-audit")

        if not pip_audit_cmd:
            # Try to install pip-audit globally
            console.print_info("pip-audit not found. Installing globally...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "pip-audit"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                console.print_error("Failed to install pip-audit")
                if verbose:
                    console.print_code_block(result.stderr, "text")
                return
            pip_audit_cmd = shutil.which("pip-audit")
            console.print_success("pip-audit installed successfully")

        manager = VirtualEnvManager()

        # Find the environment
        env_path = Path(path) if path else None
        if not env_path:
            # Search in default location
            default_base = Path.home() / "Documents" / "envs"
            if name:
                env_path = default_base / name
            else:
                # Search current directory
                env_path = Path.cwd() / ".venv"

        if not manager.exists(env_path):
            console.print_error(f"Virtual environment not found at: {env_path}")
            return

        python_path = manager.get_python_path(env_path)
        console.print_info(f"Auditing environment: {env_path}")

        # Run pip-audit using GLOBAL pip-audit (not from target venv)
        if not pip_audit_cmd:
            console.print_error("pip-audit not available")
            return

        console.print_info("Scanning for vulnerabilities...")
        with console.spinner("Running pip-audit..."):
            result = subprocess.run(
                [
                    pip_audit_cmd,
                    "--format",
                    "json",
                    "--desc",
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(env_path),
            )

        if result.returncode == 0:
            console.print_success("No vulnerabilities found!")
            return

        # Parse and display vulnerabilities
        import json

        try:
            audit_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            # pip-audit might return non-zero even on success
            if "No known vulnerabilities found" in result.stdout:
                console.print_success("No vulnerabilities found!")
                return
            console.print_error("Failed to run pip-audit")
            console.print_info(f"Error: {result.stderr.strip()}")
            if verbose:
                console.print_code_block(result.stdout, "text")
                console.print_code_block(result.stderr, "text")
            return

        vulnerabilities = audit_data.get("dependencies", [])
        vuln_list = []
        severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_severity = severity_levels.get(severity, 0) if severity else 0

        for dep in vulnerabilities:
            dep_vulns = dep.get("vulns", [])
            for vuln in dep_vulns:
                vuln_severity = vuln.get("severity", "unknown").lower()
                vuln_level = severity_levels.get(vuln_severity, 0)

                if vuln_level >= min_severity:
                    vuln_list.append(
                        {
                            "package": dep.get("name", "unknown"),
                            "version": dep.get("version", "unknown"),
                            "vuln_id": vuln.get("id", "unknown"),
                            "description": vuln.get("description", "No description"),
                            "severity": vuln_severity,
                            "fix_version": vuln.get("fix_versions", ["unknown"])[0]
                            if vuln.get("fix_versions")
                            else "unknown",
                        }
                    )

        if not vuln_list:
            console.print_success("No vulnerabilities above threshold!")
            return

        # Display vulnerabilities
        console.print_error(f"Found {len(vuln_list)} vulnerabilities:")
        console._safe_print("")

        from rich.table import Table

        table = Table(title="Vulnerabilities Found")
        table.add_column("Package", style="cyan")
        table.add_column("Version", style="white")
        table.add_column("CVE ID", style="yellow")
        table.add_column("Severity", style="red")
        table.add_column("Fix Version", style="green")

        for vuln in vuln_list:
            severity_style = {
                "critical": "[bold red]CRITICAL[/]",
                "high": "[red]HIGH[/]",
                "medium": "[yellow]MEDIUM[/]",
                "low": "[dim]LOW[/]",
            }.get(vuln["severity"], vuln["severity"])

            table.add_row(
                vuln["package"],
                vuln["version"],
                vuln["vuln_id"],
                severity_style,
                vuln["fix_version"],
            )

        console._safe_print(table)

        # Offer to fix
        if fix and vuln_list:
            console._safe_print("")
            fixable = [v for v in vuln_list if v["fix_version"] != "unknown"]
            if fixable:
                console.print_info(f"Fixing {len(fixable)} packages...")
                for vuln in fixable:
                    pkg = vuln["package"]
                    fix_ver = vuln["fix_version"]
                    console.print_info(f"  Upgrading {pkg} to {fix_ver}")

                # Run pip install with upgrades
                upgrade_cmd = [
                    str(python_path),
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                ] + [f"{v['package']}>={v['fix_version']}" for v in fixable]
                upgrade_result = subprocess.run(
                    upgrade_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if upgrade_result.returncode == 0:
                    console.print_success("Vulnerabilities fixed!")
                else:
                    console.print_error("Some fixes failed")
                    if verbose:
                        console.print_code_block(upgrade_result.stderr, "text")
            else:
                console.print_warning("No automatic fixes available")

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())


@cli.command("resurrect")
@click.argument("source")
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Installation path")
@click.option("--env-type", "-e", "env_type", default="uv", help="Package manager")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def resurrect(
    source: str,
    name: str | None,
    path: str | None,
    env_type: str,
    verbose: bool,
) -> None:
    """Resurrect dead repositories by analyzing imports and generating requirements."""
    _load_dotenv()
    from envio.commands.resurrect import resurrect_command

    resurrect_command(source, name, path, env_type, verbose)


@cli.command("list")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def list_envs(verbose: bool) -> None:
    """List environments created by envio."""
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio List", "Environments created by envio")

    try:
        from rich.table import Table

        from envio.core.registry import EnvironmentRegistry

        registry = EnvironmentRegistry()
        environments = registry.list_all()

        if not environments:
            console.print_info("No environments created by envio yet.")
            console.print_info("Try: envio prompt 'web app with flask'")
            return

        table = Table(title="Registered Environments", show_lines=True)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Path", style="white")
        table.add_column("Pkgs", justify="right", style="green")
        table.add_column("Manager", style="yellow")
        table.add_column("Created", style="dim")

        for env in environments:
            env_exists = Path(env["path"]).exists()
            name = env["name"] if env_exists else f"{env['name']} (missing)"
            name_style = "cyan" if env_exists else "red"

            created = env.get("created_at", "")
            if created:
                try:
                    created = datetime.fromisoformat(created).strftime("%b %d")
                except Exception:
                    pass

            table.add_row(
                name,
                env.get("path", "unknown"),
                str(len(env.get("packages", []))),
                env.get("manager", "unknown"),
                created,
            )

        console._safe_print(table)

        console.print_info("")
        console.print_info("Recreation commands:")
        for env in environments:
            console.print_info(f"  {env['name']}: {env.get('command', 'unknown')}")

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())


@cli.command()
@click.option("--env", "-e", "env_name", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def activate(env_name: str | None, path: str | None, verbose: bool) -> None:
    """Show activation command for a virtual environment."""
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Activate", "Show activation command")

    try:
        from envio.core.virtualenv_manager import VirtualEnvManager

        manager = VirtualEnvManager()

        env_path = Path(path) if path else None
        if not env_path and env_name:
            default_base = Path.home() / "Documents" / "envs"
            env_path = default_base / env_name

        if not env_path:
            console.print_error("Please specify --env or --path")
            return

        if not manager.exists(env_path):
            console.print_error(f"Environment not found at: {env_path}")
            return

        console.print_info(f"Environment: {env_path}")
        console.print_info("")

        from envio.core.system_profiler import OSType, SystemProfiler

        os_type = SystemProfiler().detect_os()

        if os_type == OSType.WINDOWS:
            console.print_info("PowerShell:")
            console._safe_print(f'  & "{env_path}\\Scripts\\Activate.ps1"')
            console.print_info("")
            console.print_info("CMD:")
            console._safe_print(f'  "{env_path}\\Scripts\\activate.bat"')
            console.print_info("")
            console.print_info("Git Bash:")
            console._safe_print(f'  source "{env_path}/Scripts/activate"')
        else:
            console.print_info("Bash/Zsh:")
            console._safe_print(f"  source {env_path}/bin/activate")

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())


@cli.command()
@click.argument("packages", nargs=-1, required=True)
@click.option("--env", "-e", "env_name", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def remove(
    packages: tuple[str, ...],
    env_name: str | None,
    path: str | None,
    yes: bool,
    verbose: bool,
) -> None:
    """Remove packages from a virtual environment."""
    _load_dotenv()
    console = _get_console(verbose)
    console.print_header("Envio Remove", "Remove packages from environment")

    try:
        from envio.core.virtualenv_manager import VirtualEnvManager

        manager = VirtualEnvManager()

        env_path = Path(path) if path else None
        if not env_path and env_name:
            default_base = Path.home() / "Documents" / "envs"
            env_path = default_base / env_name

        if not env_path:
            console.print_error("Please specify --env or --path")
            return

        if not manager.exists(env_path):
            console.print_error(f"Environment not found at: {env_path}")
            return

        package_list = list(packages)
        console.print_info(f"Removing packages: {', '.join(package_list)}")
        console.print_info(f"Environment: {env_path}")

        if not yes:
            console.print_warning("This will permanently uninstall these packages.")
            response = input("Continue? [y/N]: ").strip().lower()
            if response != "y":
                console.print_info("Cancelled.")
                return

        console.print_info("Uninstalling...")

        success, stdout, stderr = manager.uninstall_packages(env_path, package_list)

        if success:
            console.print_success(
                f"Successfully removed {len(package_list)} package(s)"
            )
        else:
            console.print_error("Failed to remove packages")
            if stderr:
                console.print_code_block(stderr, "text")

    except Exception as e:
        console.print_error(f"Error: {e}")
        if verbose:
            console._safe_print(traceback.format_exc())


from datetime import datetime


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
