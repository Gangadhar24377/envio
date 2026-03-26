"""Environment registry for tracking envio-created environments."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class EnvironmentRegistry:
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
