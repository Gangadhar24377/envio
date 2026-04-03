"""Project dependency file read/write engine for Envio.

Single source of truth for all mutations to pyproject.toml and
requirements.txt.  Commands never touch these files directly — they
always go through ProjectManager.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from envio.project.detector import ProjectDetector, ProjectMode


def _load_toml() -> Any:
    """Return a tomllib-compatible reader (stdlib on 3.11+, tomli on 3.10)."""
    try:
        import tomllib  # type: ignore[import]

        return tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

        return tomllib


def _load_toml_w() -> Any:
    """Return tomli_w for writing TOML."""
    import tomli_w  # type: ignore[import]

    return tomli_w


# Regex that matches a bare package name (no version specifier) from a
# PEP 508 dependency string, e.g. "flask>=2.0" → "flask"
_PKG_NAME_RE = re.compile(r"^([A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?)", re.ASCII)


def _pkg_name(dep: str) -> str:
    """Extract the normalised package name from a PEP 508 string."""
    m = _PKG_NAME_RE.match(dep.strip())
    return m.group(1).lower().replace("_", "-") if m else dep.strip().lower()


def _slugify(text: str) -> str:
    """Convert an arbitrary string to a valid project name slug."""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return slug or "my-project"


class ProjectManager:
    """Read and write project dependency files.

    All public methods accept a *cwd* parameter so they are stateless and
    easy to test — pass any temporary directory in tests.
    """

    def __init__(self) -> None:
        self._detector = ProjectDetector()

    # ------------------------------------------------------------------ #
    # Reading                                                              #
    # ------------------------------------------------------------------ #

    def read_dependencies(self, cwd: Path) -> list[str]:
        """Return the main (non-group) dependencies for the project in *cwd*.

        Returns an empty list for NEW projects.
        """
        mode = self._detector.detect(cwd)
        if mode == ProjectMode.PYPROJECT:
            return self._read_pyproject_deps(cwd, group=None)
        if mode == ProjectMode.REQUIREMENTS:
            return self._read_requirements(cwd)
        return []

    def read_group(self, group: str, cwd: Path) -> list[str]:
        """Return dependencies for a named optional-dependency group.

        Only meaningful for PYPROJECT mode; returns [] otherwise.
        """
        mode = self._detector.detect(cwd)
        if mode == ProjectMode.PYPROJECT:
            return self._read_pyproject_deps(cwd, group=group)
        return []

    def read_all_groups(self, cwd: Path) -> dict[str, list[str]]:
        """Return all optional-dependency groups as {group_name: [packages]}.

        Only meaningful for PYPROJECT mode; returns {} otherwise.
        """
        mode = self._detector.detect(cwd)
        if mode != ProjectMode.PYPROJECT:
            return {}
        data = self._read_pyproject_raw(cwd)
        groups: dict[str, list[str]] = {}
        for name, deps in (
            data.get("project", {}).get("optional-dependencies", {}).items()
        ):
            groups[name] = list(deps)
        return groups

    # ------------------------------------------------------------------ #
    # Writing — pyproject.toml                                             #
    # ------------------------------------------------------------------ #

    def add_to_pyproject(
        self, packages: list[str], cwd: Path, group: str | None = None
    ) -> None:
        """Add *packages* to pyproject.toml.

        Args:
            packages: PEP 508 dependency strings.
            cwd:      Project directory.
            group:    Optional-dependency group name.  None → [project.dependencies].
        """
        data = self._read_pyproject_raw(cwd)

        if group is None:
            existing: list[str] = data.setdefault("project", {}).setdefault(
                "dependencies", []
            )
            data["project"]["dependencies"] = _merge_deps(existing, packages)
        else:
            opt = data.setdefault("project", {}).setdefault("optional-dependencies", {})
            existing = opt.setdefault(group, [])
            opt[group] = _merge_deps(existing, packages)

        self._write_pyproject(data, cwd)

    def remove_from_pyproject(
        self, packages: list[str], cwd: Path, group: str | None = None
    ) -> None:
        """Remove *packages* from pyproject.toml.

        Matches by normalised package name (case-insensitive, - == _).
        Leaves packages that are not found rather than raising.
        """
        data = self._read_pyproject_raw(cwd)
        remove_names = {_pkg_name(p) for p in packages}

        if group is None:
            deps: list[str] = data.get("project", {}).get("dependencies", [])
            data["project"]["dependencies"] = [
                d for d in deps if _pkg_name(d) not in remove_names
            ]
        else:
            opt = data.get("project", {}).get("optional-dependencies", {})
            if group in opt:
                opt[group] = [d for d in opt[group] if _pkg_name(d) not in remove_names]

        self._write_pyproject(data, cwd)

    # ------------------------------------------------------------------ #
    # Writing — requirements.txt                                           #
    # ------------------------------------------------------------------ #

    def add_to_requirements(self, packages: list[str], cwd: Path) -> None:
        """Add *packages* to requirements.txt, deduplicating by name."""
        req_path = cwd / "requirements.txt"
        existing = self._read_requirements(cwd)
        merged = _merge_deps(existing, packages)
        req_path.write_text("\n".join(merged) + "\n", encoding="utf-8")

    def remove_from_requirements(self, packages: list[str], cwd: Path) -> None:
        """Remove *packages* from requirements.txt by normalised name."""
        req_path = cwd / "requirements.txt"
        if not req_path.exists():
            return
        remove_names = {_pkg_name(p) for p in packages}
        lines = req_path.read_text(encoding="utf-8").splitlines()
        kept: list[str] = []
        for line in lines:
            stripped = line.strip()
            if (
                stripped
                and not stripped.startswith("#")
                and not stripped.startswith("-")
            ):
                if _pkg_name(stripped) in remove_names:
                    continue
            kept.append(line)
        req_path.write_text("\n".join(kept) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------ #
    # Creating from scratch                                                #
    # ------------------------------------------------------------------ #

    def create_pyproject(
        self,
        cwd: Path,
        packages: list[str],
        *,
        project_name: str | None = None,
        python_version: str | None = None,
        groups: dict[str, list[str]] | None = None,
        description: str = "Auto-generated by Envio",
    ) -> Path:
        """Create a minimal, PEP 621-compliant pyproject.toml in *cwd*.

        Args:
            cwd:            Target directory.
            packages:       Main dependency list.
            project_name:   Defaults to slugified directory name.
            python_version: Defaults to current interpreter minor version.
            groups:         Optional-dependency groups {name: [packages]}.
                            If None a sensible default dev group is added.
            description:    Value for the description field.

        Returns:
            Path to the created file.
        """
        name = project_name or _slugify(cwd.name)
        py_ver = python_version or (
            f">={sys.version_info.major}.{sys.version_info.minor}"
        )

        # Default groups when caller doesn't specify any
        if groups is None:
            groups = {"dev": ["ruff", "pytest"]}

        data: dict[str, Any] = {
            "project": {
                "name": name,
                "version": "0.1.0",
                "description": description,
                "requires-python": py_ver,
                "dependencies": packages,
            },
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }

        if groups:
            data["project"]["optional-dependencies"] = {
                grp: list(pkgs) for grp, pkgs in groups.items()
            }

        out = cwd / "pyproject.toml"
        self._write_pyproject(data, cwd)
        return out

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _read_pyproject_raw(self, cwd: Path) -> dict[str, Any]:
        """Load pyproject.toml as a raw dict.  Returns {} if file absent."""
        path = cwd / "pyproject.toml"
        if not path.exists():
            return {}
        tomllib = _load_toml()
        with open(path, "rb") as fh:
            return tomllib.load(fh)  # type: ignore[return-value]

    def _write_pyproject(self, data: dict[str, Any], cwd: Path) -> None:
        """Atomically write *data* to pyproject.toml in *cwd*."""
        tomli_w = _load_toml_w()
        out = cwd / "pyproject.toml"
        tmp = out.with_suffix(".toml.tmp")
        tmp.write_bytes(tomli_w.dumps(data).encode("utf-8"))
        tmp.replace(out)  # atomic on POSIX; best-effort on Windows

    def _read_pyproject_deps(self, cwd: Path, group: str | None) -> list[str]:
        """Read dependencies from pyproject.toml for *group* (None = main)."""
        data = self._read_pyproject_raw(cwd)
        project = data.get("project", {})
        if group is None:
            return list(project.get("dependencies", []))
        return list(project.get("optional-dependencies", {}).get(group, []))

    def _read_requirements(self, cwd: Path) -> list[str]:
        """Read non-comment, non-flag lines from requirements.txt."""
        path = cwd / "requirements.txt"
        if not path.exists():
            return []
        pkgs: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if (
                stripped
                and not stripped.startswith("#")
                and not stripped.startswith("-")
            ):
                pkgs.append(stripped)
        return pkgs


# ------------------------------------------------------------------ #
# Module-level helpers                                                 #
# ------------------------------------------------------------------ #


def _merge_deps(existing: list[str], incoming: list[str]) -> list[str]:
    """Merge *incoming* into *existing*, deduplicating by package name.

    Incoming entries win over existing entries with the same name
    (allows version upgrades via ``envio add flask>=3.0``).
    """
    existing_map: dict[str, str] = {_pkg_name(d): d for d in existing}
    for dep in incoming:
        existing_map[_pkg_name(dep)] = dep  # overwrite if same name
    return list(existing_map.values())
