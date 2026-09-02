"""sqlite backend (P1 second backend): same contract as files.py, stdlib
sqlite3 only, no new dependency. Ledger table is INSERT-only from application
code — nothing here ever issues UPDATE/DELETE on the events table. Views are
still rendered to <base_dir>/views/<name> so `store project` output is
diffable the same way regardless of backend.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .base import Backend


class SqliteBackend(Backend):
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.views_dir = self.base_dir / "views"
        self.views_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base_dir / "catalog.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                collection TEXT NOT NULL,
                event_id TEXT NOT NULL,
                data TEXT NOT NULL
            )"""
        )
        self._conn.commit()

    def append(self, collection: str, event: dict) -> None:
        # INSERT only — no UPDATE/DELETE ever issued against this table.
        self._conn.execute(
            "INSERT INTO events (collection, event_id, data) VALUES (?, ?, ?)",
            (collection, event["event_id"], json.dumps(event, ensure_ascii=False, sort_keys=True)),
        )
        self._conn.commit()

    def read_events(self, collection: str) -> list[dict]:
        cur = self._conn.execute(
            "SELECT data FROM events WHERE collection = ? ORDER BY seq ASC", (collection,)
        )
        return [json.loads(row[0]) for row in cur.fetchall()]

    def list_collections(self) -> list[str]:
        cur = self._conn.execute("SELECT DISTINCT collection FROM events ORDER BY collection")
        return [row[0] for row in cur.fetchall()]

    def write_view(self, name: str, content: str) -> None:
        path = self.views_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

    def read_view(self, name: str) -> str | None:
        path = self.views_dir / name
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")
