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
