"""SQLite-based cache for supply chain scan results."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from envio.utils.paths import get_envio_cache_dir


class SupplyChainCache:
    """SQLite cache for supply chain scan results.

    TTLs:
    - web_search: 24 hours
    - osv: 1 hour
    - reputation: 1 hour
    - detector: 24 hours
    """

    _instance: SupplyChainCache | None = None

    WEB_SEARCH_TTL = 24 * 3600
    OSV_TTL = 3600
    REPUTATION_TTL = 3600
    DETECTOR_TTL = 24 * 3600

    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            cache_dir = get_envio_cache_dir()
            db_path = cache_dir / "supplychain.db"
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    @classmethod
    def get_instance(cls) -> SupplyChainCache:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
        return self._conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scan_cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_category ON scan_cache(category)"
        )
        conn.commit()

    def _get_ttl(self, category: str) -> int:
        ttls = {
            "web_search": self.WEB_SEARCH_TTL,
            "osv": self.OSV_TTL,
            "reputation": self.REPUTATION_TTL,
            "detector": self.DETECTOR_TTL,
        }
        return ttls.get(category, self.OSV_TTL)

    def get(self, key: str, category: str) -> Any | None:
        cache_key = f"{category}:{key}"
        ttl = self._get_ttl(category)
        now = time.time()

        conn = self._get_conn()
        row = conn.execute(
            "SELECT value, created_at FROM scan_cache WHERE key = ?",
            (cache_key,),
        ).fetchone()

        if row is None:
            return None

        value, created_at = row
        if now - created_at > ttl:
            self.delete(cache_key)
            return None

        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    def set(self, key: str, category: str, value: Any) -> None:
        cache_key = f"{category}:{key}"
        now = time.time()
        serialized = json.dumps(value)

        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO scan_cache (key, value, category, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (cache_key, serialized, category, now),
        )
        conn.commit()

    def delete(self, key: str) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM scan_cache WHERE key = ?", (key,))
        conn.commit()

    def clear(self, category: str | None = None) -> None:
        conn = self._get_conn()
        if category:
            conn.execute("DELETE FROM scan_cache WHERE category = ?", (category,))
        else:
            conn.execute("DELETE FROM scan_cache")
        conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
