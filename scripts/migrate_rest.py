#!/usr/bin/env python3
"""One-time migration (PRD Phase 1.6): sources.yaml, changelog.jsonl,
docs/decisions-draft.md and gaps.md into the ledger. Read-only against the
sources; only writes through Store.append (P1). Safe to re-run into a fresh
--base-dir for a dry run; running twice against the real catalog duplicates
events.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from store import Store  # noqa: E402

SOURCES_PATH = Path(r"D:\Development\AiAgent\ai-toolbox\sources.yaml")
CHANGELOG_PATH = Path(r"D:\Development\AiAgent\ai-toolbox\changelog.jsonl")
GAPS_PATH = Path(r"D:\Development\Luctures\TaskTriagOrcetrator\ai-toolbox\gaps.md")
DECISIONS_DRAFT_PATH = Path(__file__).resolve().parent.parent / "docs" / "decisions-draft.md"

ACTOR_MAP = {
    "amitkuzi@gmail.com": "human:amit",
    "weekly-run": "agent:toolbox-curator",
    "daily-run": "agent:toolbox-curator",
    "system": "system:migration",
}
VIA_MAP = {"bootstrap": "migration"}
KIND_ACTION_TO_EVENT = {
    # A changelog "added" on a *tool* almost always duplicates an id that
    # migrate_tools.py already gave a proper tool.added (with full type +
    # category) from the current tools.yaml snapshot. Replaying it as a
    # second tool.added would either fail validate.py's payload check (this
    # changelog line only ever carries a name) or silently clobber the real
    # record. tool.status keeps the historical note (P2) without re-declaring
    # the tool; for the handful of ids that are pure changelog noise and were
    # never in the clean snapshot, it's a harmless no-op in the fold.
    ("tool", "added"): "tool.status",
    ("tool", "changed"): "tool.revised",
    ("tool", "promoted"): "tool.revised",
    ("tool", "removed"): "tool.retired",
    ("source", "added"): "source.added",
    ("source", "changed"): "source.revised",
    ("source", "promoted"): "source.revised",
    ("source", "removed"): "source.retired",
    ("catalog", "bootstrap"): "tool.status",
    ("catalog", "changed"): "tool.status",
}


def stringify_dates(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [stringify_dates(v) for v in value]
    if isinstance(value, dict):
        return {k: stringify_dates(v) for k, v in value.items()}
    return value


def migrate_sources(store: Store) -> int:
    data = yaml.safe_load(SOURCES_PATH.read_text(encoding="utf-8"))
    last_reviewed = data["meta"]["last_reviewed"]
    n = 0
    for src in data["sources"]:
        sid = src["id"]
        payload = stringify_dates({k: v for k, v in src.items() if k != "id"})
        store.append(
            kind="source.added",
            subject_id=sid,
            actor="system:migration",
            via="migration",
            reason=f"imported from AiAgent/ai-toolbox/sources.yaml (last_reviewed {last_reviewed})",
            payload=payload,
        )
        n += 1
    return n


def migrate_changelog(store: Store) -> int:
    n = 0
    for line in CHANGELOG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        kind_field = rec.get("kind", "tool")
        action = rec.get("action", "changed")
        event_kind = KIND_ACTION_TO_EVENT.get((kind_field, action))
        if event_kind is None:
            event_kind = "tool.status"  # unknown combo — keep the history, park it as a status note
        actor = ACTOR_MAP.get(rec.get("actor"), f"human:{rec.get('actor', 'unknown')}")
        via = VIA_MAP.get(rec.get("via"), rec.get("via", "migration"))
        note = rec.get("note") or f"replayed changelog entry ({action} {kind_field})"
        store.append(
            kind=event_kind,
            subject_id=rec.get("id", "catalog"),
            actor=actor,
            via=via,
            reason=f"[changelog {rec['ts']}] {note}",
            payload={"name": rec.get("name"), "changelog_action": action},
            ts=rec["ts"],
        )
        n += 1
    return n


def migrate_decisions(store: Store) -> int:
    text = DECISIONS_DRAFT_PATH.read_text(encoding="utf-8")
    # sections start with "### D-0NN — Title"
    sections = re.split(r"\n(?=### D-\d+ )", text)
    n = 0
    for section in sections:
        m = re.match(r"### (D-\d+) — (.+)", section)
        if not m:
            continue
        adr_id, title = m.group(1), m.group(2).strip()
        body = section[m.end():].strip()
        store.append(
            kind="adr.added",
            subject_id=adr_id,
            actor="agent:architect",
            via="migration",
            reason="promoted from docs/decisions-draft.md (Task 0.3 PRD contradiction review)",
            payload={"title": title, "body": body},
        )
        n += 1
    return n


def migrate_gaps(store: Store) -> int:
    text = GAPS_PATH.read_text(encoding="utf-8")
    n = 0
    for m in re.finditer(
        r"\|\s*(G-\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|\s*([\d-]+)\s*\|\s*(\w+)\s*\|",
        text,
    ):
        gid, gap, blocked, type_needed, hits, first_seen, status = m.groups()
        store.append(
            kind="gap.opened",
            subject_id=gid,
            actor="system:migration",
            via="migration",
            reason=f"imported from TaskTriagOrcetrator/ai-toolbox/gaps.md (first_seen {first_seen})",
            payload={
                "gap": gap,
                "blocked_subtask": blocked,
                "type_needed": type_needed,
                "first_seen": first_seen,
            },
        )
        n += 1
    return n


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=None)
    args = parser.parse_args()
    store = Store(backend_name="files", base_dir=args.base_dir)

    n_sources = migrate_sources(store)
    n_changelog = migrate_changelog(store)
    n_decisions = migrate_decisions(store)
    n_gaps = migrate_gaps(store)
    print(f"migrated {n_sources} sources, {n_changelog} changelog events, {n_decisions} ADRs, {n_gaps} gaps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
