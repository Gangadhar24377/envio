"""Envio project migrator.

Converts any Python project format to a Envio-managed pyproject.toml.

Architecture
------------
Each source format is a self-contained subclass of ``SourceFormat``.
``Migrator`` holds a registry of all known formats.  To support a new
format, create a subclass and add it to ``Migrator._REGISTRY`` — the
orchestration logic never changes.

Supported source formats
------------------------
* requirements.txt  (+ requirements-dev.txt, requirements-test.txt, …)
* pyproject.toml with [tool.poetry]  (Poetry)
* Pipfile / Pipfile.lock  (Pipenv)
* environment.yml / environment.yaml  (conda)
* setup.py + setup.cfg  (legacy setuptools)
* requirements.in  (pip-tools)
* pixi.toml  (pixi)
"""

from __future__ import annotations

import configparser
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class MigrationData:
    """Normalised representation of a project's dependency information."""

    project_name: str
    python_version: str | None
    dependencies: list[str]
    groups: dict[str, list[str]] = field(default_factory=dict)
    scripts: dict[str, str] = field(default_factory=dict)
    description: str = ""
    source_format: str = "unknown"


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class SourceFormat(ABC):
    """Base class for all migration source formats."""

    #: Human-readable format name — override as a plain class attribute.
    name: str = "unknown"

    @abstractmethod
    def detect(self, cwd: Path) -> bool:
        """Return True if this format is present in *cwd*."""

    @abstractmethod
    def extract(self, cwd: Path) -> MigrationData:
        """Extract all dependency information from *cwd*."""

    # ------------------------------------------------------------------ #
    # Shared utilities available to all subclasses                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _slug(text: str) -> str:
        slug = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
        return slug or "my-project"

    @staticmethod
    def _load_toml(path: Path) -> dict[str, Any]:
        try:
            import tomllib  # type: ignore[import]
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        with open(path, "rb") as fh:
            return tomllib.load(fh)  # type: ignore[return-value]

    @staticmethod
    def _parse_req_lines(lines: list[str]) -> list[str]:
        """Parse requirements lines, stripping comments, blank lines, flags."""
        pkgs: list[str] = []
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # strip inline comment
            line = re.sub(r"\s+#.*$", "", line).strip()
            if line:
                pkgs.append(line)
        return pkgs

    @staticmethod
    def _read_req_file(path: Path) -> list[str]:
        return SourceFormat._parse_req_lines(
            path.read_text(encoding="utf-8").splitlines()
        )

    @staticmethod
    def _poetry_dep_to_pep508(name: str, spec: Any) -> str:
        """Convert a Poetry dependency spec to a PEP 508 string.

        Handles: "*", "^1.2", "~1.2", ">=1.2,<2", plain version strings,
        and table specs {"version": "...", "optional": true, ...}.
        """
        if isinstance(spec, dict):
            if spec.get("optional"):
                return ""  # skip optional poetry deps; caller decides
            spec = spec.get("version", "*")
        if spec in ("*", "latest"):
            return name
        # caret: ^1.2.3 → >=1.2.3,<2.0.0
        caret = re.fullmatch(r"\^(\d+)\.(\d+)(?:\.(\d+))?", spec)
        if caret:
            major, minor, patch = caret.groups()
            lo = f"{major}.{minor}.{patch or 0}"
            hi = str(int(major) + 1) if int(major) > 0 else f"0.{int(minor) + 1}"
            return f"{name}>={lo},<{hi}"
        # tilde: ~1.2 → >=1.2,<1.3
        tilde = re.fullmatch(r"~(\d+)\.(\d+)(?:\.(\d+))?", spec)
        if tilde:
            major, minor, patch = tilde.groups()
            return f"{name}>={major}.{minor}.{patch or 0},<{major}.{int(minor) + 1}"
        # already a PEP 508 specifier
        return f"{name}{spec}" if re.match(r"[><=!~]", spec) else f"{name}=={spec}"


# ---------------------------------------------------------------------------
# Concrete format handlers
# ---------------------------------------------------------------------------


class RequirementsTxtFormat(SourceFormat):
    """requirements.txt (+ optional requirements-*.txt side-files)."""

    name = "requirements.txt"

    # Well-known side-file names mapped to group names
    _SIDE_FILES: list[tuple[str, str]] = [
        ("requirements-dev.txt", "dev"),
        ("requirements-test.txt", "test"),
        ("requirements-docs.txt", "docs"),
        ("requirements-typing.txt", "typing"),
        ("requirements_dev.txt", "dev"),
        ("requirements_test.txt", "test"),
    ]

    def detect(self, cwd: Path) -> bool:
        return (cwd / "requirements.txt").exists() and not (
            cwd / "pyproject.toml"
        ).exists()

    def extract(self, cwd: Path) -> MigrationData:
        deps = self._read_req_file(cwd / "requirements.txt")
        groups: dict[str, list[str]] = {}
        for filename, group in self._SIDE_FILES:
            p = cwd / filename
            if p.exists():
                g_deps = self._read_req_file(p)
                if g_deps:
                    groups[group] = g_deps
        # default dev group if none found
        if not groups:
            groups = {"dev": ["ruff", "pytest"]}
        return MigrationData(
            project_name=self._slug(cwd.name),
            python_version=None,
            dependencies=deps,
            groups=groups,
            source_format=self.name,
        )


class PoetryFormat(SourceFormat):
    """pyproject.toml with [tool.poetry] (Poetry projects)."""

    name = "Poetry"

    def detect(self, cwd: Path) -> bool:
        p = cwd / "pyproject.toml"
        if not p.exists():
            return False
        data = self._load_toml(p)
        return "poetry" in data.get("tool", {})

    def extract(self, cwd: Path) -> MigrationData:
        data = self._load_toml(cwd / "pyproject.toml")
        poetry = data.get("tool", {}).get("poetry", {})

        name = poetry.get("name", self._slug(cwd.name))
        description = poetry.get("description", "")

        # Python version from poetry deps
        raw_python = poetry.get("dependencies", {}).pop("python", None) or poetry.get(
            "dependencies", {}
        ).get("python")
        python_version: str | None = None
        if raw_python and raw_python not in ("*", "latest"):
            python_version = raw_python

        # Main dependencies
        deps: list[str] = []
        for pkg, spec in poetry.get("dependencies", {}).items():
            if pkg.lower() == "python":
                continue
            pep508 = self._poetry_dep_to_pep508(pkg, spec)
            if pep508:
                deps.append(pep508)

        # Dependency groups (Poetry >=1.2 style)
        groups: dict[str, list[str]] = {}
        for grp_name, grp_data in poetry.get("group", {}).items():
            grp_deps: list[str] = []
            for pkg, spec in grp_data.get("dependencies", {}).items():
                pep508 = self._poetry_dep_to_pep508(pkg, spec)
                if pep508:
                    grp_deps.append(pep508)
            if grp_deps:
                groups[grp_name] = grp_deps

        # Legacy dev-dependencies
        for pkg, spec in poetry.get("dev-dependencies", {}).items():
            pep508 = self._poetry_dep_to_pep508(pkg, spec)
            if pep508:
                groups.setdefault("dev", []).append(pep508)

        # Scripts
        scripts = dict(poetry.get("scripts", {}))

        return MigrationData(
            project_name=name,
            python_version=python_version,
            dependencies=deps,
            groups=groups,
            scripts=scripts,
            description=description,
            source_format=self.name,
        )


class PipenvFormat(SourceFormat):
    """Pipfile / Pipfile.lock (Pipenv projects)."""

    name = "Pipenv"

    def detect(self, cwd: Path) -> bool:
        return (cwd / "Pipfile").exists()

    def extract(self, cwd: Path) -> MigrationData:
        # Pipfile is TOML-compatible
        data = self._load_toml(cwd / "Pipfile")

        # Python version
        python_version: str | None = None
        py = data.get("requires", {}).get("python_version")
        if py:
            python_version = f">={py}"

        def _pipenv_spec_to_pep508(name: str, spec: Any) -> str:
            if spec in ("*", {"extras": []}):
                return name
            if isinstance(spec, dict):
                ver = spec.get("version", "*")
                extras = spec.get("extras", [])
                extra_str = f"[{','.join(extras)}]" if extras else ""
                if ver == "*":
                    return f"{name}{extra_str}"
                return f"{name}{extra_str}{ver}"
            if isinstance(spec, str):
                return f"{name}{spec}" if re.match(r"[><=!~]", spec) else name
            return name

        deps: list[str] = []
        for pkg, spec in data.get("packages", {}).items():
            deps.append(_pipenv_spec_to_pep508(pkg, spec))

        dev_deps: list[str] = []
        for pkg, spec in data.get("dev-packages", {}).items():
            dev_deps.append(_pipenv_spec_to_pep508(pkg, spec))

        groups: dict[str, list[str]] = {}
        if dev_deps:
            groups["dev"] = dev_deps
        if not groups:
            groups = {"dev": ["ruff", "pytest"]}

        return MigrationData(
            project_name=self._slug(cwd.name),
            python_version=python_version,
            dependencies=deps,
            groups=groups,
            source_format=self.name,
        )


class CondaFormat(SourceFormat):
    """environment.yml / environment.yaml (conda projects)."""

    name = "conda"

    def detect(self, cwd: Path) -> bool:
        return (cwd / "environment.yml").exists() or (cwd / "environment.yaml").exists()

    def extract(self, cwd: Path) -> MigrationData:
        import yaml  # already in deps

        yml_path = (
            cwd / "environment.yml"
            if (cwd / "environment.yml").exists()
            else cwd / "environment.yaml"
        )
        data = yaml.safe_load(yml_path.read_text(encoding="utf-8"))

        name = data.get("name") or self._slug(cwd.name)
        deps: list[str] = []
        raw_deps: list[Any] = data.get("dependencies", [])
        for item in raw_deps:
            if isinstance(item, str):
                # skip conda-specific entries like "python=3.10"
                if item.startswith("python") or item.startswith("pip"):
                    continue
                # conda uses = for version, convert to ==
                normalized = re.sub(r"=(?!=)", "==", item, count=1)
                deps.append(normalized)
            elif isinstance(item, dict) and "pip" in item:
                # pip sub-list inside environment.yml
                deps.extend(self._parse_req_lines(item["pip"]))

        return MigrationData(
            project_name=self._slug(name),
            python_version=None,
            dependencies=deps,
            groups={"dev": ["ruff", "pytest"]},
            source_format=self.name,
        )


class SetupPyFormat(SourceFormat):
    """setup.py / setup.cfg (legacy setuptools projects)."""

    name = "setuptools (setup.py/setup.cfg)"

    def detect(self, cwd: Path) -> bool:
        return (cwd / "setup.py").exists() or (cwd / "setup.cfg").exists()

    def extract(self, cwd: Path) -> MigrationData:
        deps: list[str] = []
        groups: dict[str, list[str]] = {}
        name = self._slug(cwd.name)
        description = ""

        # --- setup.cfg (preferred, more structured) ---
        cfg_path = cwd / "setup.cfg"
        if cfg_path.exists():
            cfg = configparser.ConfigParser()
            cfg.read(cfg_path, encoding="utf-8")
            name = cfg.get("metadata", "name", fallback=name)
            description = cfg.get("metadata", "description", fallback="")
            raw = cfg.get("options", "install_requires", fallback="")
            deps = self._parse_req_lines(raw.splitlines())
            # extras_require
            for section in cfg.sections():
                if section.startswith("options.extras_require"):
                    grp = section.split(":")[-1].strip() if ":" in section else "extras"
                    g_raw = cfg.get(section, "")
                    g_deps = self._parse_req_lines(g_raw.splitlines())
                    if g_deps:
                        groups[grp] = g_deps

        # --- setup.py (fallback, regex-based) ---
        elif (cwd / "setup.py").exists():
            src = (cwd / "setup.py").read_text(encoding="utf-8")
            # install_requires = [...]
            m = re.search(r"install_requires\s*=\s*\[([^\]]*)\]", src, re.DOTALL)
            if m:
                deps = re.findall(r'["\']([^"\']+)["\']', m.group(1))
            # name = "..."
            mn = re.search(r'name\s*=\s*["\']([^"\']+)["\']', src)
            if mn:
                name = self._slug(mn.group(1))
            # extras_require = {...}
            me = re.search(r"extras_require\s*=\s*\{([^}]*)\}", src, re.DOTALL)
            if me:
                for grp_m in re.finditer(
                    r'["\']([^"\']+)["\']\s*:\s*\[([^\]]*)\]', me.group(1)
                ):
                    grp_name = grp_m.group(1)
                    grp_deps = re.findall(r'["\']([^"\']+)["\']', grp_m.group(2))
                    if grp_deps:
                        groups[grp_name] = grp_deps

        if not groups:
            groups = {"dev": ["ruff", "pytest"]}

        return MigrationData(
            project_name=name,
            python_version=None,
            dependencies=deps,
            groups=groups,
            description=description,
            source_format=self.name,
        )


class PipToolsFormat(SourceFormat):
    """requirements.in (pip-tools projects)."""

    name = "pip-tools (requirements.in)"

    def detect(self, cwd: Path) -> bool:
        return (cwd / "requirements.in").exists()

    def extract(self, cwd: Path) -> MigrationData:
        deps = self._read_req_file(cwd / "requirements.in")
        groups: dict[str, list[str]] = {}
        # optional side-files
        for filename, group in [
            ("requirements-dev.in", "dev"),
            ("requirements-test.in", "test"),
        ]:
            p = cwd / filename
            if p.exists():
                g_deps = self._read_req_file(p)
                if g_deps:
                    groups[group] = g_deps
        if not groups:
            groups = {"dev": ["ruff", "pytest"]}
        return MigrationData(
            project_name=self._slug(cwd.name),
            python_version=None,
            dependencies=deps,
            groups=groups,
            source_format=self.name,
        )


class PixiFormat(SourceFormat):
    """pixi.toml (pixi projects)."""

    name = "pixi"

    def detect(self, cwd: Path) -> bool:
        return (cwd / "pixi.toml").exists()

    def extract(self, cwd: Path) -> MigrationData:
        data = self._load_toml(cwd / "pixi.toml")

        name = data.get("project", {}).get("name", self._slug(cwd.name))
        description = data.get("project", {}).get("description", "")

        deps: list[str] = []
        for pkg, spec in data.get("dependencies", {}).items():
            if isinstance(spec, str):
                # pixi uses ">=1.0,<2" style
                deps.append(f"{pkg}{spec}" if re.match(r"[><=!~]", spec) else pkg)
            elif isinstance(spec, dict):
                ver = spec.get("version", "*")
                deps.append(f"{pkg}{ver}" if ver != "*" else pkg)
            else:
                deps.append(pkg)

        # feature dependencies → groups
        groups: dict[str, list[str]] = {}
        for feat_name, feat_data in data.get("feature", {}).items():
            g_deps: list[str] = []
            for pkg, spec in feat_data.get("dependencies", {}).items():
                if isinstance(spec, str):
                    g_deps.append(f"{pkg}{spec}" if re.match(r"[><=!~]", spec) else pkg)
                else:
                    g_deps.append(pkg)
            if g_deps:
                groups[feat_name] = g_deps

        if not groups:
            groups = {"dev": ["ruff", "pytest"]}

        return MigrationData(
            project_name=self._slug(name),
            python_version=None,
            dependencies=deps,
            groups=groups,
            description=description,
            source_format=self.name,
        )


# ---------------------------------------------------------------------------
# Migrator orchestrator
# ---------------------------------------------------------------------------


class Migrator:
    """Detect source format and convert to pyproject.toml.

    The registry is an ordered list.  The first format whose ``detect()``
    returns True is used.  Order matters: more specific formats (Poetry)
    must appear before generic ones (RequirementsTxt).
    """

    _REGISTRY: list[SourceFormat] = [
        PoetryFormat(),  # before generic pyproject check
        PixiFormat(),
        PipenvFormat(),
        CondaFormat(),
        SetupPyFormat(),
        PipToolsFormat(),  # before RequirementsTxt (has .in files)
        RequirementsTxtFormat(),
    ]

    def detect_format(self, cwd: Path) -> SourceFormat | None:
        """Return the first matching format handler, or None."""
        for fmt in self._REGISTRY:
            if fmt.detect(cwd):
                return fmt
        return None

    def extract(self, cwd: Path, source_format: str | None = None) -> MigrationData:
        """Extract migration data from *cwd*.

        Args:
            cwd:           Project directory to migrate from.
            source_format: Force a specific format name (e.g. "Poetry").
                           If None, auto-detection is used.

        Raises:
            ValueError: If no format is detected and source_format is None.
        """
        if source_format:
            fmt = self._get_by_name(source_format)
            if fmt is None:
                available = [f.name for f in self._REGISTRY]
                raise ValueError(
                    f"Unknown source format {source_format!r}. Available: {available}"
                )
        else:
            fmt = self.detect_format(cwd)
            if fmt is None:
                raise ValueError(
                    f"No recognised project format found in {cwd}. "
                    "Supported: " + ", ".join(f.name for f in self._REGISTRY)
                )
        return fmt.extract(cwd)

    def migrate(
        self,
        cwd: Path,
        source_format: str | None = None,
        dry_run: bool = False,
        keep_original: bool = False,
    ) -> tuple[MigrationData, Path | None]:
        """Migrate *cwd* to pyproject.toml.

        Args:
            cwd:           Project directory to migrate.
            source_format: Force a specific source format name.
            dry_run:       If True, return data without writing any files.
            keep_original: If True, do not delete/rename original files.

        Returns:
            (MigrationData, output_path) where output_path is None for
            dry-run.
        """
        from envio.project.manager import ProjectManager

        data = self.extract(cwd, source_format)

        if dry_run:
            return data, None

        manager = ProjectManager()
        out = manager.create_pyproject(
            cwd=cwd,
            packages=data.dependencies,
            project_name=data.project_name,
            python_version=data.python_version,
            groups=data.groups if data.groups else None,
            description=data.description or "Migrated by Envio",
        )

        return data, out

    def available_formats(self) -> list[str]:
        """Return names of all registered source formats."""
        return [f.name for f in self._REGISTRY]

    def _get_by_name(self, name: str) -> SourceFormat | None:
        name_lower = name.lower()
        for fmt in self._REGISTRY:
            if fmt.name.lower() == name_lower or name_lower in fmt.name.lower():
                return fmt
        return None
