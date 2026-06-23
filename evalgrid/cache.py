"""SQLite response cache for EvalGrid."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from evalgrid.schemas import ModelRequest, ModelResponse


class SQLiteResponseCache:
    """Tiny SQLite cache keyed by stable request hashes."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def get(self, cache_key: str) -> ModelResponse | None:
        """Return cached response when present."""

        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT response_json FROM responses WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        if row is None:
            return None
        return ModelResponse.model_validate(json.loads(row[0]))

    def set(self, cache_key: str, response: ModelResponse) -> None:
        """Store one response."""

        payload = response.model_dump_json()
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO responses(cache_key, response_json)
                VALUES (?, ?)
                """,
                (cache_key, payload),
            )
            connection.commit()

    def has(self, cache_key: str) -> bool:
        """Return whether key is present."""

        return self.get(cache_key) is not None

    def _init_db(self) -> None:
        """Create cache table."""

        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS responses (
                    cache_key TEXT PRIMARY KEY,
                    response_json TEXT NOT NULL
                )
                """
            )
            connection.commit()


def make_cache_key(request: ModelRequest) -> str:
    """Create a stable hash for request identity and prompt content."""

    payload: dict[str, Any] = {
        "provider": request.model_provider,
        "model_name": request.model_name,
        "system_prompt": request.system_prompt,
        "user_prompt": request.user_prompt,
        "temperature": request.temperature,
        "response_format": request.response_format,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
