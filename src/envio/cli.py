"""CLI entry point for Envio with user-centric flow."""

from __future__ import annotations

import os
import shutil
import time
import traceback
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import click

from envio.agents.command_construction_agent import CommandGenerator
from envio.agents.dependency_resolution_agent import DependencyResolver
from envio.agents.nlp_agent import NLPProcessor
from envio.core.executor import ScriptExecutor
from envio.core.script_generator import ScriptGeneratorFactory
from envio.core.system_profiler import SystemProfiler
from envio.llm.parser import ResponseParser
from envio.ui.console import ConsoleUI

VALID_PACKAGE_MANAGERS = ["pip", "conda", "uv"]


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


def select_package_manager(available: dict[str, bool], console: ConsoleUI) -> str:
    """Let user select a package manager."""
    console.print_info("Available package managers:")
    for pm, is_available in available.items():
        status = "available" if is_available else "not found"
        console._print(f"  - {pm} ({status})")

    while True:
        choice = (
            input("\nSelect package manager (pip/conda/uv) [default: uv]: ")
            .strip()
            .lower()
        )
        if not choice:
            return "uv"
        if choice in VALID_PACKAGE_MANAGERS:
            if not available.get(choice, False):
                console.print_warning(
                    f"{choice} is not available. Please choose another."
                )
                continue
            return choice
        console.print_warning(
            f"Invalid choice. Please choose from: {', '.join(VALID_PACKAGE_MANAGERS)}"
        )


def display_installation_plan(
    console: ConsoleUI,
    packages: list[str],
    env_type: str,
    install_path: Path,
    preferences: dict | None,
    profile,
) -> None:
    """Display the installation plan for user confirmation."""
    console.print_header("Installation Plan")

    print(f"\nEnvironment: {install_path.name}")
    print(f"Location: {install_path}")
    print(f"Package Manager: {env_type}")

    # Show preferences
    pref_display = []
    if preferences:
        if preferences.get("cpu_only"):
            pref_display.append("CPU-only mode")
        elif preferences.get("gpu_optimized"):
            pref_display.append("GPU-optimized mode")
    if pref_display:
        print(f"Mode: {', '.join(pref_display)}")

    # Show hardware info
    if profile.gpu.available:
        print(f"\nHardware: {profile.gpu.name}")
        if profile.gpu.vram_mb:
            print(f"VRAM: {profile.gpu.vram_mb} MB")
        if profile.gpu.cuda_version:
            print(f"CUDA: {profile.gpu.cuda_version}")
        if preferences and preferences.get("cpu_only"):
            print("Note: GPU detected but CPU-only mode requested")
    else:
        print("\nHardware: CPU-only (no GPU detected)")

    # Show packages
    print(f"\nPackages to install ({len(packages)}):")
    for pkg in packages:
        print(f"  - {pkg}")

    print("")


def confirm_installation(console: ConsoleUI) -> bool | str:
    """Ask user to confirm installation. Returns True, False, or 'modify'."""
    while True:
        choice = input("Proceed with installation? (Y/n/modify): ").strip().lower()
        if choice in ("", "y", "yes"):
            return True
        elif choice in ("n", "no"):
            return False
        elif choice == "modify":
            print("\nModify options:")
            print("  - Type a package name to add it (e.g., 'add torch')")
            print("  - Type 'remove <package>' to remove it")
            print("  - Type 'CPU only' to switch to CPU-only mode")
            print("  - Type 'done' when finished\n")
            return "modify"
        else:
            console.print_warning("Please enter Y, n, or 'modify'")


def setup_environment(
    packages: list[str],
    env_path: str,
    env_name: str,
    package_manager: str = "uv",
    preferences: dict | None = None,
    verbose: bool = True,
) -> bool:
    """Set up a virtual environment with the specified packages."""
    console = ConsoleUI(verbose=verbose)
    profiler = SystemProfiler()
    executor = ScriptExecutor()
    generator_factory = ScriptGeneratorFactory()
    generator = generator_factory.create()

    profile = profiler.profile()

    # Display installation plan
    venv_path = Path(env_path) / env_name
    display_installation_plan(
        console, packages, package_manager, venv_path, preferences, profile
    )

    # Confirm installation
    confirmed = confirm_installation(console)
    if confirmed == "modify":
        # Handle modification
        while True:
            mod_input = input("Modification: ").strip()
            if mod_input.lower() == "done":
                break
            elif mod_input.lower().startswith("add "):
                pkg = mod_input[4:].strip()
                if pkg and pkg not in packages:
                    packages.append(pkg)
                    console.print_success(f"Added: {pkg}")
            elif mod_input.lower().startswith("remove "):
                pkg = mod_input[7:].strip()
                if pkg in packages:
                    packages.remove(pkg)
                    console.print_success(f"Removed: {pkg}")
            elif "cpu only" in mod_input.lower():
                if preferences is None:
                    preferences = {}
                preferences["cpu_only"] = True
                console.print_success("Switched to CPU-only mode")
            else:
                console.print_warning(f"Unknown command: {mod_input}")

        # Re-display plan
        display_installation_plan(
            console, packages, package_manager, venv_path, preferences, profile
        )
        confirmed = confirm_installation(console)

    if not confirmed:
        console.print_warning("Installation cancelled")
        return False

    # Create and execute setup script
    script_content = generator.generate_setup_script(
        venv_path=str(venv_path),
        packages=packages,
        package_manager=package_manager,
    )

    script_path = executor.write_script(
        script_content,
        Path(env_path) / f"envio_setup_{env_name}",
    )

    console.print_info("Executing setup script...")
    with console.status("Installing packages..."):
        returncode, stdout, stderr = executor.execute_script(
            script_path,
            capture_output=True,
            timeout=300,
        )

    if returncode == 0:
        console.print_success("Environment setup completed successfully!")
        activation_cmd = generator.generate_venv_activation_instructions(venv_path)
        console.print_info("To activate the environment, run:")
        console.print_code_block(activation_cmd.strip(), "bash")
        return True
    else:
        console.print_error("Environment setup failed!")
        console.print_info("Output:")
        console.print_code_block(stderr or stdout, "bash")
        return False


def parse_extracted_info(
    result: dict, console: ConsoleUI
) -> tuple[list[str], str, dict]:
    """Parse extracted info and return packages, env type, and preferences."""
    parser = ResponseParser()

    packages = parser.parse_packages(result)

    env_type = result.get("environment_type", "uv").lower()
    if env_type not in VALID_PACKAGE_MANAGERS:
        env_type = "uv"

    preferences = result.get("preferences", {})

    return packages, env_type, preferences


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Envio - AI-Native Environment Orchestrator."""
    pass


@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def interactive(verbose: bool) -> None:
    """Run Envio in interactive mode."""
    console = ConsoleUI(verbose=verbose)
    console.print_header("Envio - Interactive Mode")

    try:
        available_managers = detect_package_managers()

        console.print_info("Detected package managers:")
        for pm, available in available_managers.items():
            status = "[+]" if available else "[-]"
            console._print(f"  {status} {pm}")

        package_manager = select_package_manager(available_managers, console)

        nlp_processor = NLPProcessor()
        dependency_resolver = DependencyResolver()
        command_generator = CommandGenerator()
        profiler = SystemProfiler()
        profile = profiler.profile()

        # Build hardware context for LLM
        hw_context_lines = []
        if profile.gpu.available:
            hw_context_lines.append(f"Hardware: {profile.gpu.name} GPU detected")
            hw_context_lines.append(f"VRAM: {profile.gpu.vram_mb} MB")
            hw_context_lines.append(f"CUDA: {profile.gpu.cuda_version}")
        else:
            hw_context_lines.append("Hardware: CPU-only (no GPU detected)")
        hardware_context = "\n".join(hw_context_lines)

        print("")
        print(
            "Enter your package request (e.g., 'set up a Python environment for ML with pytorch')"
        )
        print("(You can say 'CPU only', 'use GPU', 'Python 3.11', etc.)")
        print("")
        user_input = input("> ")

        if not user_input.strip():
            console.print_warning(
                "No input provided. Using default: basic Python environment"
            )
            user_input = "set up a basic Python environment"

        console.print_info("User request received")
        console.print_agent_thought("User", user_input)

        print("")
        print("=== Analyzing Your Request ===")
        print("")

        def callback(msg: str) -> None:
            print(msg)

        extracted_info = nlp_processor.extract(
            user_input,
            hardware_context=hardware_context,
            callback=callback,
        )

        packages, _, preferences = parse_extracted_info(extracted_info, console)

        console.print_packages(packages, "\nSuggested Packages")

        console.print_info(f"Using package manager: {package_manager}")

        print("")
        print("[Resolution] Checking compatibility...")
        resolved = dependency_resolver.resolve(
            packages, package_manager, profile, preferences
        )
        console.print_agent_thought("Dependency Agent", "Resolution complete")
        console.print_packages(resolved.get("packages", packages), "Resolved Packages")

        console.print_info("Generating commands...")
        command_result = command_generator.generate(
            resolved.get("packages", packages),
            package_manager,
            profile,
            preferences,
        )

        if not command_result.get("commands"):
            command_result["commands"] = [
                f"{package_manager} install " + " ".join(packages)
            ]

        # Prompt for environment path and name
        default_path = str(Path.home() / "Documents" / "envs")
        env_path = (
            input(f"\nEnvironment path [default: {default_path}]: ").strip()
            or default_path
        )
        env_name = input("Environment name: ").strip()
        if not env_name:
            env_name = f"env_setup_{int(time.time())}"

        setup_environment(
            resolved.get("packages", packages),
            env_path,
            env_name,
            package_manager,
            preferences,
            verbose,
        )

    except Exception as e:
        console.print_error(f"An error occurred: {e}")
        console.print_info("\nFull traceback:")
        console._print(traceback.format_exc())
        console.print_info("Please check your API keys and network connection.")


@cli.command()
@click.argument("packages", nargs=-1, required=True)
@click.option(
    "--env-type", "-e", "env_type", default="uv", help="Package manager (pip/conda/uv)"
)
@click.option("--name", "-n", default=None, help="Environment name")
@click.option("--path", "-p", default=None, help="Environment path")
@click.option("--cpu-only", is_flag=True, help="Force CPU-only mode (ignore GPU)")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def install(
    packages: tuple[str, ...],
    env_type: str,
    name: str | None,
    path: str | None,
    cpu_only: bool,
    verbose: bool,
) -> None:
    """Install packages directly (non-interactive mode)."""
    console = ConsoleUI(verbose=verbose)
    console.print_header("Envio - Direct Install")

    if env_type not in VALID_PACKAGE_MANAGERS:
        console.print_warning(f"Invalid package manager: {env_type}. Using uv.")
        env_type = "uv"

    pkg_list = list(packages)
    preferences = {"cpu_only": cpu_only} if cpu_only else {}

    env_name = name or f"env_setup_{int(time.time())}"
    env_path = path or str(Path.home() / "Documents" / "envs")

    setup_environment(pkg_list, env_path, env_name, env_type, preferences, verbose)


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
