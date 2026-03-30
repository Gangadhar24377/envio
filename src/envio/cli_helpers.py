"""Shared helper functions for Envio CLI."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from envio.ui.console import ConsoleUI

VALID_PACKAGE_MANAGERS = ["pip", "conda", "uv"]

# Pattern for valid environment names (alphanumeric, underscore, hyphen, dot)
_ENV_NAME_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")

# Path traversal pattern - blocks ".." components
_PATH_TRAVERSAL_RE = re.compile(r"(^|[/\\])\.\.([/\\]|$)")


def _validate_path(path: str) -> bool:
    """Validate path doesn't contain traversal attempts.

    Args:
        path: Path to validate

    Returns:
        True if safe, False if potentially malicious
    """
    if not path:
        return False
    # Check for path traversal attempts
    if _PATH_TRAVERSAL_RE.search(path.replace("\\", "/")):
        return False
    # Check for null bytes
    if "\0" in path:
        return False
    return True


def _is_writable(path: Path) -> bool:
    """Check if path is writable without attempting to create/modify.

    Args:
        path: Path to check

    Returns:
        True if writable, False otherwise
    """
    try:
        if path.exists():
            return os.access(path, os.W_OK)
        # Check parent directory for new files
        parent = path.parent
        return parent.exists() and os.access(parent, os.W_OK)
    except Exception:
        return False


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

# Cache for AI-discovered package mappings
_ai_package_cache: dict[str, str] = {}


def _get_pypi_name_for_import(import_name: str) -> str | None:
    """Use AI to find the pip package name for an import.

    Args:
        import_name: The Python import name (e.g., 'PIL', 'cv2', 'yaml')

    Returns:
        The PyPI package name or None if couldn't determine
    """
    if import_name in _ai_package_cache:
        return _ai_package_cache[import_name]

    try:
        from envio.config import get_api_key, get_model
        from envio.llm.client import LLMClient

        api_key = get_api_key()
        if not api_key:
            return None

        model = get_model()
        client = LLMClient(api_key=api_key, model=model)

        prompt = f"""For the Python import "{import_name}", what is the exact pip package name I should install?

Examples:
- import PIL → pillow
- import cv2 → opencv-python
- import yaml → pyyaml
- import sklearn → scikit-learn

Respond with ONLY the package name, nothing else. If you don't know, respond with "UNKNOWN"."""

        response = client.chat(
            system_prompt="You are a Python package expert.", user_prompt=prompt
        )
        content = (
            response.choices[0].message.content.strip() if response.choices else ""
        )

        if content and content != "UNKNOWN":
            pypi_name = content.lower().strip()
            _ai_package_cache[import_name] = pypi_name
            return pypi_name
    except Exception:
        pass

    return None


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

    # Map to PyPI name - try static first, then AI for unknown imports
    if pkg_name in IMPORT_TO_PYPI:
        pypi_name = IMPORT_TO_PYPI[pkg_name]
    else:
        # Use AI to find the correct PyPI package name
        ai_name = _get_pypi_name_for_import(pkg_name)
        pypi_name = ai_name if ai_name else pkg_name

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
            # Try to find latest version using static dict first, then AI
            try:
                pkg_name = pkg.split("==")[0].lower()
                if pkg_name in IMPORT_TO_PYPI:
                    pypi_name = IMPORT_TO_PYPI[pkg_name]
                else:
                    ai_name = _get_pypi_name_for_import(pkg_name)
                    pypi_name = ai_name if ai_name else pkg_name
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


def _load_dotenv() -> None:
    """Load environment variables from envio config file.

    Reads from ~/.envio/config.json (or ~/.config/envio/config.json on Linux).
    This is the central config location for the PyPI package.
    """
    from envio.config import load_config

    config = load_config()

    # Set API keys and other config as environment variables
    if config.get("api_key"):
        os.environ["API_KEY"] = config["api_key"]
    if config.get("serper_api_key"):
        os.environ["SERPER_API_KEY"] = config["serper_api_key"]


def detect_package_managers() -> dict[str, bool]:
    """Detect which package managers are available."""
    return {
        "pip": shutil.which("pip") is not None,
        "conda": shutil.which("conda") is not None or _is_conda_active(),
        "uv": shutil.which("uv") is not None,
    }


def _find_environment(
    name: str | None,
    path: str | None,
    console: ConsoleUI | None = None,
) -> Path | None:
    """Find environment path by name or path, or show available environments.

    Args:
        name: Environment name (from registry or default location)
        path: Explicit environment path
        console: ConsoleUI instance for output (optional)

    Returns:
        Path to environment if found, None if not found/cancelled
    """
    from envio.core.registry import EnvironmentRegistry
    from envio.core.virtualenv_manager import VirtualEnvManager

    manager = VirtualEnvManager()
    env_path = Path(path) if path else None

    # If path provided directly, validate it exists
    if env_path:
        if manager.exists(env_path):
            return env_path
        if console:
            console.print_error(f"Virtual environment not found at: {env_path}")
        return None

    # If name provided, search in registry and default location
    if name:
        # Check registry first
        try:
            registry = EnvironmentRegistry()
            reg_entry = registry.get(name)
            if reg_entry:
                env_path = Path(reg_entry["path"])
                if manager.exists(env_path):
                    return env_path
        except Exception:
            pass

        # Check default location
        from envio.config import get_default_envs_dir

        default_base = get_default_envs_dir(prompt=False)[0]
        if default_base:
            env_path = Path(default_base) / name
            if manager.exists(env_path):
                return env_path

        if console:
            console.print_error(f"Environment '{name}' not found.")
        return None

    # No name or path - show available environments
    if console:
        console.print_error("No environment specified.")
        console.print_info("")

        # Check current directory for venv
        for venv_name in [".venv", "venv", "env"]:
            v = Path.cwd() / venv_name
            if manager.exists(v):
                console.print_info("Found in current directory:")
                console._safe_print(f"  {v}", style="cyan")
                console.print_info("")
                break

        # Show registered environments
        try:
            registry = EnvironmentRegistry()
            environments = registry.list_all()
        except Exception:
            environments = []

        if environments:
            console.print_info("Registered environments:")
            for env in environments:
                exists = " " if Path(env["path"]).exists() else "✗ "
                console._safe_print(
                    f"  {exists}{env['name']}: {env['path']}", style="cyan"
                )
            console.print_info("")
            console.print_info("Specify an environment with:")
            console._safe_print("  -n <name>  (from registry)", style="yellow")
            console._safe_print("  -p <path>  (explicit path)", style="yellow")
        else:
            console.print_info("No registered environments.")
            console.print_info("Create one with: envio prompt '...' or envio init .")

    return None


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
    verbose: bool = False,
) -> bool:
    """Resolve dependencies and install environment with self-healing."""
    resolver = _get_dependency_resolver()
    executor = _get_executor()
    script_gen = _get_script_generator()

    venv_path = Path(env_path) / env_name
    max_retries = 3
    error_output = ""

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

        # Get full dependency tree from uv output
        full_deps = []
        if resolved.get("stdout"):
            # Parse uv output to extract all dependencies
            lines = resolved["stdout"].split("\n")
            for line in lines:
                line = line.strip()
                if line and not line.startswith("=") and not line.startswith("-"):
                    # Extract package info from uv output
                    if " " in line or "==" in line:
                        # Clean up the line to get package name
                        pkg = line.split()[0].split("==")[0]
                        if pkg and pkg not in full_deps:
                            full_deps.append(pkg)

        # If we got dependencies from uv, use them; otherwise use final_packages
        display_packages = full_deps if full_deps else final_packages

        if full_deps and len(full_deps) > len(final_packages):
            console.print_packages_table(
                final_packages, f"Core Packages ({len(final_packages)})"
            )
            console.print_package_tree(
                full_deps, f"Full Dependency Tree ({len(full_deps)} packages)"
            )
        else:
            console.print_package_tree(display_packages, "Resolved Packages")

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

        # Generate script content in memory (not written to disk yet)
        console.print_info("Generating installation script...")
        script_content = script_gen.generate_setup_script(
            venv_path=str(venv_path),
            packages=final_packages,
            package_manager=package_manager,
            cuda_url=cuda_url,
        )

        # Dry run: show what would happen without executing
        if dry_run:
            console.print_info("[DRY RUN] Would execute the following script:")
            console.print_code_block(script_content, "bash")
            console.print_info("[DRY RUN] No changes were made to your system.")
            return True

        # Interactive confirmation
        if not skip_confirm:
            if not console.confirm("Proceed with installation?", default=True):
                console.print_warning("Aborted. No environment was created.")
                return False

        # Write script to disk only after confirmation
        script_path = executor.write_script(
            script_content,
            Path(env_path) / f"envio_setup_{env_name}",
        )

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

            # Register environment in the registry so `envio list` can track it
            try:
                from envio.core.registry import EnvironmentRegistry

                registry = EnvironmentRegistry()
                registry.register(
                    name=env_name,
                    path=str(venv_path),
                    packages=final_packages,
                    manager=package_manager,
                    command=original_command,
                )
            except Exception:
                console.print_warning(
                    "Could not register environment. It won't appear in 'envio list'."
                )

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

            # Show full error details in verbose mode
            if verbose:
                console.print_info("=== ERROR DETAILS ===")
                console.print_code_block(f"Return code: {returncode}", "bash")
                console.print_code_block(f"STDOUT:\n{stdout}", "bash")
                console.print_code_block(f"STDERR:\n{stderr}", "bash")
                console.print_code_block(f"Full error:\n{error_output}", "bash")

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
                # Show healing failure details in verbose mode
                if verbose and healing_result.get("error"):
                    console.print_info(f"Healing error: {healing_result.get('error')}")
                console.print_warning(
                    "Could not find fix, retrying with original packages..."
                )
        else:
            console.print_error("Installation failed after all attempts!")
            # Show full error details
            console.print_code_block(f"STDOUT:\n{stdout}", "bash") if stdout else None
            console.print_code_block(f"STDERR:\n{stderr}", "bash") if stderr else None
            if verbose:
                console.print_info("=== FINAL ERROR SUMMARY ===")
                console.print_code_block(f"Return code: {returncode}", "bash")
                console.print_code_block(f"Error output: {error_output}", "bash")
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
