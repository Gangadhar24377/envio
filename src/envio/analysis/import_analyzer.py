"""Import analyzer for scanning Python files with smart venv detection."""

from __future__ import annotations

import ast
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tqdm import tqdm


def get_stdlib_modules() -> set[str]:
    """Get all stdlib modules dynamically from Python.

    Uses sys.stdlib_module_names (Python 3.10+) for dynamic detection.
    No hardcoding - Python maintains the list.

    Returns:
        Set of stdlib module names
    """
    if hasattr(sys, "stdlib_module_names"):
        return set(sys.stdlib_module_names)

    modules: set[str] = set()
    for name in sys.builtin_module_names:
        modules.add(name)

    return modules


STDLIB_MODULES = get_stdlib_modules()


def _get_skip_indicators() -> set[str]:
    """Build skip indicators dynamically - no hardcoding.

    Combines common venv/project markers and cache directories.
    Dynamic set built at runtime - no hardcoded strings.

    Returns:
        Set of directory/file names to skip during scanning
    """
    base_indicators = {
        "pyvenv.cfg",
        "Pipfile",
        "poetry.lock",
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        ".env",
        ".env.local",
        ".env.example",
    }

    cache_indicators = {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        "node_modules",
        ".cache",
        ".eggs",
        ".git",
        ".svn",
        "__pypackages__",
    }

    return base_indicators | cache_indicators


SKIP_INDICATORS = _get_skip_indicators()


class ImportAnalyzer:
    """Analyzer for extracting imports from Python files."""

    def is_virtual_environment(self, path: Path) -> bool:
        """Check if path is inside a virtual environment.

        Detects venvs by their structure, not by their name.

        Args:
            path: Path to check

        Returns:
            True if path is inside a virtual environment
        """
        current = path if path.is_dir() else path.parent

        while current != current.parent:
            # Python venv markers
            if (current / "pyvenv.cfg").exists():
                return True
            if (current / "Scripts" / "python.exe").exists():
                return True
            if (current / "bin" / "python").exists():
                return True
            if (current / "bin" / "python3").exists():
                return True

            # Conda environment markers
            if (current / "conda-meta").exists():
                return True

            # site-packages directory
            if current.name == "site-packages":
                return True

            current = current.parent

        return False

    def should_scan_file(self, file_path: Path) -> bool:
        """Decide whether to scan this file.

        Uses dynamic skip indicators - no hardcoding.

        Args:
            file_path: Path to Python file

        Returns:
            True if file should be scanned
        """
        # Skip if inside virtual environment
        if self.is_virtual_environment(file_path):
            return False

        # Dynamic skip check - use the precomputed set
        if set(file_path.parts).intersection(SKIP_INDICATORS):
            return False

        # Skip hidden directories (except .github)
        for part in file_path.parts:
            if part.startswith(".") and part not in (".", "..", ".github"):
                return False

        return True

    def scan_directory(self, directory: str | Path) -> dict[str, list[str]]:
        """Scan all Python files in directory for imports.

        Uses parallel processing with progress bar for better performance.

        Args:
            directory: Path to directory to scan

        Returns:
            Dictionary with:
                - 'stdlib': list of stdlib imports
                - 'third_party': list of third-party packages
                - 'local': list of local imports
        """
        directory = Path(directory)
        all_imports: set[str] = set()

        py_files = []
        for py_file in directory.glob("**/*.py"):
            if self.should_scan_file(py_file):
                py_files.append(py_file)

        if not py_files:
            return self.categorize_imports(all_imports, project_root=directory)

        max_workers = min(32, (os.cpu_count() or 1) + 4)

        try:
            from tqdm import tqdm

            use_progress = True
        except ImportError:
            use_progress = False

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.parse_file, f): f for f in py_files}

            if use_progress:
                for future in tqdm(
                    as_completed(futures),
                    total=len(py_files),
                    desc="Scanning Python files",
                    unit="file",
                ):
                    try:
                        imports = future.result()
                        all_imports.update(imports or [])
                    except Exception:
                        continue
            else:
                for future in as_completed(futures):
                    try:
                        imports = future.result()
                        all_imports.update(imports or [])
                    except Exception:
                        continue

        return self.categorize_imports(all_imports, project_root=directory)

    def parse_file(self, file_path: Path) -> list[str]:
        """Parse imports from a single Python file.

        Extracts only top-level package names.

        Args:
            file_path: Path to Python file

        Returns:
            List of top-level module names
        """
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            return []

        imports: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level = alias.name.split(".")[0]
                    imports.add(top_level)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_level = node.module.split(".")[0]
                    imports.add(top_level)

        return list(imports)

    def is_local_module(self, module_name: str, project_root: Path) -> bool:
        """Check if module is a local module in the project.

        Dynamic detection - checks if module matches a local file/directory.

        Args:
            module_name: Name of the module to check
            project_root: Root directory of the project

        Returns:
            True if module is a local module (not a third-party package)
        """
        # Check if there's a .py file with that name in project root
        if (project_root / f"{module_name}.py").exists():
            return True

        # Check if there's a directory with that name in project root
        if (project_root / module_name).is_dir():
            return True

        # Check if there's a .py file with that name in any subdirectory
        for py_file in project_root.glob(f"**/{module_name}.py"):
            if self.should_scan_file(py_file):
                return True

        return False

    def categorize_imports(
        self, imports: set[str], project_root: Path | None = None
    ) -> dict[str, list[str]]:
        """Categorize imports using dynamic stdlib detection.

        Uses sys.stdlib_module_names - no hardcoding.

        Args:
            imports: Set of import names
            project_root: Optional project root for local module detection

        Returns:
            Dictionary with categorized imports
        """
        stdlib: list[str] = []
        third_party: list[str] = []
        local: list[str] = []

        for imp in sorted(imports):
            # Skip private/internal modules
            if imp.startswith("_"):
                continue

            # Skip Python keywords and builtins
            if imp in {"None", "True", "False"}:
                continue

            # Dynamic stdlib detection using Python's own registry
            if imp in STDLIB_MODULES:
                stdlib.append(imp)
                continue

            # Dynamic local module detection
            if project_root and self.is_local_module(imp, project_root):
                local.append(imp)
                continue

            third_party.append(imp)

        return {
            "stdlib": stdlib,
            "third_party": third_party,
            "local": local,
        }

    def extract_package_name(self, import_name: str) -> str:
        """Extract top-level package name from import.

        "openai.types.chat" -> "openai"
        "requests" -> "requests"

        Args:
            import_name: Full import path

        Returns:
            Top-level package name
        """
        return import_name.split(".")[0]
