"""Resurrect command for analyzing and reviving old repositories."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from envio.analysis.import_analyzer import ImportAnalyzer
from envio.analysis.syntax_detector import SyntaxDetector
from envio.analysis.version_inference import VersionInference
from envio.ui.console import ConsoleUI


def _is_url(source: str) -> bool:
    """Check if source is a URL."""
    return source.startswith("http://") or source.startswith("https://")


def _clone_repo(url: str, target_dir: Path) -> Path:
    """Clone a git repository.

    Args:
        url: Git repository URL
        target_dir: Directory to clone into

    Returns:
        Path to cloned repository
    """
    repo_name = url.split("/")[-1].replace(".git", "")
    clone_path = target_dir / repo_name

    subprocess.run(
        ["git", "clone", "--depth", "1", url, str(clone_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )

    return clone_path


def resurrect_command(
    source: str,
    name: str | None,
    path: str | None,
    env_type: str,
    verbose: bool,
) -> None:
    """Execute the resurrect command.

    Args:
        source: URL or local path to analyze
        name: Environment name
        path: Installation path
        env_type: Package manager
        verbose: Enable verbose output
    """
    console = ConsoleUI(verbose=verbose)
    console.print_header("Envio Resurrect", "Analyze and revive old repositories")

    if _is_url(source):
        console.print_info(f"Cloning repository: {source}")

        # Ask for path if not specified
        if not path:
            default_path = str(Path.home() / "Documents" / "envs")
            path = input(f"Environment path [default: {default_path}]: ").strip()
            if not path:
                path = default_path

        # Create a temporary directory for cloning
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = _clone_repo(source, Path(tmp_dir))
            if not repo_path.exists():
                console.print_error("Failed to clone repository")
                return

            # Derive name from repo URL if not specified
            if not name:
                name = source.split("/")[-1].replace(".git", "")

            _analyze_directory(repo_path, name, path, env_type, console)
    else:
        repo_path = Path(source)
        if not repo_path.exists():
            console.print_error(f"Path not found: {source}")
            return

        # Ask for path if not specified (for local directories)
        if not path:
            path = str(repo_path.parent / "envs")

        _analyze_directory(repo_path, name, path, env_type, console)


def _analyze_directory(
    directory: Path,
    name: str | None,
    path: str | None,
    env_type: str,
    console: ConsoleUI,
) -> None:
    """Analyze a directory and generate environment.

    Args:
        directory: Path to directory to analyze
        name: Environment name
        path: Installation path
        env_type: Package manager
        console: Console UI for output
    """
    analyzer = ImportAnalyzer()
    detector = SyntaxDetector()
    inference = VersionInference()

    # Scan for imports
    console.print_info(f"Scanning {directory} for Python files...")
    with console.spinner("Analyzing imports..."):
        categorized = analyzer.scan_directory(directory)

    third_party = categorized.get("third_party", [])

    if not third_party:
        console.print_warning("No third-party packages detected")
        return

    # Map import names to PyPI package names dynamically
    from envio.analysis.package_mapping import find_package_for_import

    mapped_packages = []
    for imp in third_party:
        pkg_name = find_package_for_import(imp)
        mapped_packages.append(pkg_name)
        if pkg_name != imp:
            console.print_info(f"  {imp} → {pkg_name}")

    third_party = mapped_packages
    console.print_packages_table(third_party, "Detected Third-Party Packages")

    # Detect deprecated patterns
    console.print_info("Analyzing code patterns...")
    with console.spinner("Detecting deprecated syntax..."):
        pattern_results = detector.detect_from_directory(directory)

    all_patterns = []
    for file_patterns in pattern_results.values():
        all_patterns.extend(file_patterns)

    if all_patterns:
        timeline = detector.infer_timeline(all_patterns)
        python_version = detector.infer_python_version(all_patterns)
        console.print_info(f"Inferred timeline: {timeline}")
        console.print_info(f"Recommended Python: {python_version}")
    else:
        timeline = "modern (2020+)"
        python_version = "3.11"
        console.print_info("Code appears to be modern (no deprecated patterns found)")

    # Find compatible versions
    console.print_info("Querying PyPI for compatible versions...")
    with console.spinner("Finding compatible versions..."):
        versions = inference.find_compatible_versions(
            third_party, timeline, python_version
        )

    if not versions:
        console.print_warning("Could not find compatible versions")
        return

    # Generate requirements.txt
    requirements_content = inference.generate_requirements(versions)

    console.print_info("Generated requirements.txt:")
    console.print_code_block(requirements_content, "txt")

    # Save requirements.txt
    req_path = directory / "requirements.txt"
    with open(req_path, "w") as f:
        f.write(requirements_content)
    console.print_success(f"Saved to: {req_path}")

    # Ask user if they want to create environment
    if console.confirm("\nCreate environment with these packages?", default=True):
        from envio.cli import _resolve_and_install
        from envio.core.system_profiler import SystemProfiler

        env_name = name or directory.name
        env_path = path or str(directory)

        profiler = SystemProfiler()
        profile = profiler.profile()

        _resolve_and_install(
            packages=[f"{pkg}=={ver}" for pkg, ver in versions.items()],
            env_path=env_path,
            env_name=env_name,
            package_manager=env_type,
            preferences={},
            profile=profile,
            console=console,
        )
