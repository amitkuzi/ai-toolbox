"""Backend interface (P1). A backend persists raw ledger events and rendered
view text. All folding/computation logic lives in store.py, not here — a
backend is dumb storage so a second implementation (sqlite, later postgres)
can satisfy the same contract with no change to store.py or any rule/skill.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class Backend(ABC):
    """Append-only ledger + generated views, scoped to one base_dir."""

    @abstractmethod
    def append(self, collection: str, event: dict) -> None:
        """Append one event to collection. Never update/delete existing events."""

    @abstractmethod
    def read_events(self, collection: str) -> list[dict]:
        """Return every event ever appended to collection, in append order."""

    @abstractmethod
    def list_collections(self) -> list[str]:
        """Return the names of collections that have at least one event."""

    @abstractmethod
    def write_view(self, name: str, content: str) -> None:
        """Overwrite the rendered view file `name` (e.g. 'tools.yaml') with content."""

    @abstractmethod
    def read_view(self, name: str) -> str | None:
        """Return the current rendered view text, or None if it doesn't exist."""
