"""files backend (P1 default): ledger = JSONL under <base_dir>/ledger/<collection>.jsonl,
one JSON object per line, append-only. Views = text files under <base_dir>/views/<name>.
"""
from __future__ import annotations

import json
from pathlib import Path

from .base import Backend


class FilesBackend(Backend):
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.ledger_dir = self.base_dir / "ledger"
        self.views_dir = self.base_dir / "views"
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        self.views_dir.mkdir(parents=True, exist_ok=True)

    def _ledger_path(self, collection: str) -> Path:
        return self.ledger_dir / f"{collection}.jsonl"

    def append(self, collection: str, event: dict) -> None:
        path = self._ledger_path(collection)
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    def read_events(self, collection: str) -> list[dict]:
        path = self._ledger_path(collection)
        if not path.exists():
            return []
        events = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events

    def list_collections(self) -> list[str]:
        return sorted(p.stem for p in self.ledger_dir.glob("*.jsonl"))

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
