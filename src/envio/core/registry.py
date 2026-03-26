"""Environment registry for tracking envio-created environments."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class EnvironmentRegistry:
    """Registry for storing environment metadata.

    Stores data in ~/.envio/environments.json
    """

    def __init__(self) -> None:
        self._registry_path = Path.home() / ".envio" / "environments.json"
        self._ensure_registry_exists()

    def _ensure_registry_exists(self) -> None:
        """Create registry directory and file if they don't exist."""
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._registry_path.exists():
            self._write_registry({})

    def _read_registry(self) -> dict[str, Any]:
        """Read the registry from disk."""
        try:
            with open(self._registry_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_registry(self, data: dict[str, Any]) -> None:
        """Write the registry to disk."""
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add(
    """Registry that tracks environments created by envio.

    Stores metadata in ~/.envio/environments.json.
    O(1) lookup - no filesystem scanning.
    """

    def __init__(self) -> None:
        self._dir = Path.home() / ".envio"
        self._path = self._dir / "environments.json"

    def register(
        self,
        name: str,
        path: str,
        packages: list[str],
        manager: str,
        command: str,
    ) -> None:
        """Register a new environment.

        Args:
            name: Environment name
            path: Absolute path to environment
            packages: List of package names installed
            manager: Package manager used (pip/uv/conda)
            command: Original command used to create
        """
        data = self._read_registry()
        data[name] = {
            "path": path,
            "packages": packages,
            "manager": manager,
            "command": command,
            "created_at": datetime.now().isoformat(),
        }
        self._write_registry(data)

    def remove(self, name: str) -> bool:
        """Remove an environment from the registry.

        Args:
            name: Environment name

        Returns:
            True if removed, False if not found
        """
        data = self._read_registry()
        if name in data:
            del data[name]
            self._write_registry(data)
        command: str,
        package_manager: str,
        python_version: str,
    ) -> None:
        """Add or update an environment entry.

        If an entry with the same name and path exists, updates its
        packages and command. Preserves the original created_at timestamp.
        If no match, appends a new entry.
        """
        data = self._load()
        path_key = str(Path(path).resolve())

        # Find existing entry by name + resolved path
        existing = None
        for env in data["environments"]:
            if env["name"] == name and str(Path(env["path"]).resolve()) == path_key:
                existing = env
                break

        if existing:
            # Update existing entry
            existing["packages"] = packages
            existing["command"] = command
            existing["package_manager"] = package_manager
            existing["python_version"] = python_version
        else:
            # Append new entry
            data["environments"].append(
                {
                    "name": name,
                    "path": path,
                    "packages": packages,
                    "package_manager": package_manager,
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "command": command,
                    "python_version": python_version,
                }
            )

        self._save(data)

    def list_all(self) -> list[dict[str, Any]]:
        """Read all registered environments."""
        return self._load()["environments"]

    def remove(self, name: str) -> bool:
        """Remove entry by name. Returns True if found and removed."""
        data = self._load()
        original_len = len(data["environments"])
        data["environments"] = [e for e in data["environments"] if e["name"] != name]
        if len(data["environments"]) < original_len:
            self._save(data)
            return True
        return False

    def get(self, name: str) -> dict[str, Any] | None:
        """Get environment details by name.

        Args:
            name: Environment name

        Returns:
            Environment details or None if not found
        """
        data = self._read_registry()
        return data.get(name)

    def list_all(self) -> list[dict[str, Any]]:
        """List all registered environments.

        Returns:
            List of environment details
        """
        data = self._read_registry()
        return [{"name": name, **details} for name, details in data.items()]

    def exists(self, name: str) -> bool:
        """Check if an environment is registered.

        Args:
            name: Environment name

        Returns:
            True if exists
        """
        data = self._read_registry()
        return name in data

    def update(
        self,
        name: str,
        packages: list[str] | None = None,
        manager: str | None = None,
    ) -> bool:
        """Update environment details.

        Args:
            name: Environment name
            packages: Updated package list
            manager: Updated package manager

        Returns:
            True if updated, False if not found
        """
        data = self._read_registry()
        if name not in data:
            return False

        if packages is not None:
            data[name]["packages"] = packages
        if manager is not None:
            data[name]["manager"] = manager

        self._write_registry(data)
        return True
        """Lookup environment by name."""
        for env in self._load()["environments"]:
            if env["name"] == name:
                return env
        return None

    def _load(self) -> dict[str, Any]:
        """Read JSON file. Returns empty structure if missing or corrupt."""
        if not self._path.exists():
            return {"environments": []}
        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "environments" not in data:
                return {"environments": []}
            return data
        except (json.JSONDecodeError, OSError):
            return {"environments": []}

    def _save(self, data: dict[str, Any]) -> None:
        """Write JSON file, creating ~/.envio/ directory if needed."""
        self._dir.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
