"""Resurrect command for analyzing and reviving old repositories."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from envio.analysis.import_analyzer import ImportAnalyzer
from envio.analysis.syntax_detector import SyntaxDetector
from envio.analysis.version_inference import VersionInference
from envio.ui.console import ConsoleUI


def _is_url(source: str) -> bool:
    """Check if source is a URL."""
    return source.startswith("http://") or source.startswith("https://")


def _is_valid_git_url(url: str) -> bool:
    """Validate git URL format."""
    if not url:
        return False
    url = url.replace(".git", "")
    parts = url.split("/")
    if len(parts) < 2:
        return False
    return True


def _clone_repo(url: str, target_dir: Path) -> Path:
    """Clone a git repository.

    Args:
        url: Git repository URL
        target_dir: Directory to clone into

    Returns:
        Path to cloned repository

    Raises:
        ValueError: If URL format is invalid
        RuntimeError: If git clone fails
    """
    if not _is_valid_git_url(url):
        raise ValueError(f"Invalid git URL format: {url}")

    repo_name = url.split("/")[-1].replace(".git", "")

    # Security: Validate and sanitize repo name to prevent path traversal
    # Remove any path components that could escape target_dir
    repo_name = repo_name.replace("..", "").replace("\\", "").replace("/", "")

    if not repo_name or repo_name.startswith("."):
        raise ValueError(f"Invalid repository name: {repo_name}")

    # Validate it's a safe filename
    import re

    if not re.match(r"^[a-zA-Z0-9_.-]+$", repo_name):
        raise ValueError(f"Repository name contains invalid characters: {repo_name}")

    clone_path = target_dir / repo_name

    if clone_path.exists():
        shutil.rmtree(clone_path)

    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(clone_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        if clone_path.exists():
            shutil.rmtree(clone_path)
        raise RuntimeError(f"Git clone failed: {result.stderr.strip()}")

    if not clone_path.exists():
        raise RuntimeError("Git clone completed but directory not found")

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
        # Check if git is installed
        if shutil.which("git") is None:
            console.print_error(
                "Git is not installed. Please install git to clone repositories."
            )
            return

        console.print_info(f"Cloning repository: {source}")

        # Ask for path if not specified
        if not path:
            from envio import config as config_module

            default_path = (
                config_module.get_default_envs_dir(prompt=False)[0] or "~/.envs"
            )
            path = input(f"Environment path [default: {default_path}]: ").strip()
            if not path:
                path = default_path

        # Create a temporary directory for cloning
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                repo_path = _clone_repo(source, Path(tmp_dir))
            except (ValueError, RuntimeError) as e:
                console.print_error(f"Failed to clone repository: {e}")
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

    # Show dependency tree if packages have dependencies
    if len(third_party) > 1:
        console.print_package_tree(third_party, "Package Dependencies")

    # Detect deprecated patterns
    console.print_info("Analyzing code patterns...")
    with console.spinner("Detecting deprecated syntax..."):
        pattern_results = detector.detect_from_directory(directory)

    all_patterns = []
    for file_patterns in pattern_results.values():
        all_patterns.extend(file_patterns)

    llm_client = None
    try:
        from envio.llm.client import LLMClient

        llm_client = LLMClient()
        detector = SyntaxDetector(llm_client=llm_client)
    except Exception:
        detector = SyntaxDetector()

    from envio.utils.version_utils import detect_system_python_version

    system_python = detect_system_python_version()

    if all_patterns:
        timeline = detector.infer_timeline(all_patterns)
        python_version, warning = detector.infer_python_version(
            all_patterns, system_python
        )
        console.print_info(f"Inferred timeline: {timeline}")
        console.print_info(f"Recommended Python: {python_version}")
        if warning:
            console.print_warning(warning)
    else:
        timeline = "modern (2020+)"
        python_version = system_python if system_python else "3.11"
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

    # Validate and normalize packages against PyPI (dynamic - handles any deprecated/wrong names)
    from envio.cli import _validate_and_normalize_packages

    pkgs_with_versions = [f"{pkg}=={ver}" for pkg, ver in versions.items()]
    validated_packages = _validate_and_normalize_packages(pkgs_with_versions, console)

    # Rebuild versions dict from validated packages
    validated_versions = {}
    for pkg_spec in validated_packages:
        if "==" in pkg_spec:
            pkg_name, pkg_version = pkg_spec.split("==", 1)
            validated_versions[pkg_name] = pkg_version
        else:
            validated_versions[pkg_spec] = "latest"

    # Generate requirements.txt
    requirements_content = inference.generate_requirements(validated_versions)

    console.print_info("Generated requirements.txt:")
    console.print_code_block(requirements_content, "txt")

    # Save requirements.txt to the analyzed directory
    req_path = directory / "requirements.txt"
    if req_path.exists():
        if not console.confirm(
            f"\n{req_path} already exists. Overwrite?", default=True
        ):
            # Save with timestamp suffix instead
            req_path = directory / f"requirements_envio_{int(time.time())}.txt"
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
            packages=[f"{pkg}=={ver}" for pkg, ver in validated_versions.items()],
            env_path=env_path,
            env_name=env_name,
            package_manager=env_type,
            preferences={},
            profile=profile,
            console=console,
            original_command=f"envio resurrect {directory}",
        )
    else:
        console.print_warning("Aborted. No environment was resurrected.")
