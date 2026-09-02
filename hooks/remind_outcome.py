#!/usr/bin/env python3
"""SubagentStop/Stop hook: remind to close a `decision` event with no outcome.

ponytail: "once per decision" is tracked with a small local state file next
to this script, not a full notification queue — good enough for a single
reminder per open decision, upgrade to per-session dedup if that's not
enough.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = Path(__file__).resolve().parent / ".reminded.json"


def store_query(collection: str, **filters) -> list:
    args = [sys.executable, str(ROOT / "scripts" / "store.py")]
    base_dir = os.environ.get("TOOLBOX_BASE_DIR")  # test hook only, unset in normal use
    if base_dir:
        args += ["--base-dir", base_dir]
    args += ["query", collection]
    for k, v in filters.items():
        args += ["--filter", f"{k}={v}"]
    out = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def open_decisions() -> list[str]:
    decisions = store_query("scores", kind="decision")
    outcomes = store_query("scores", kind="score.outcome") + store_query("scores", kind="score.human")
    closed = {ev["subject_id"] for ev in outcomes}
    return [d["subject_id"] for d in decisions if d["subject_id"] not in closed]


def main() -> None:
    try:
        already = set(json.loads(STATE_FILE.read_text())) if STATE_FILE.exists() else set()
    except (json.JSONDecodeError, OSError):
        already = set()

    try:
        open_ids = open_decisions()
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return  # no catalog yet / store not runnable — nothing to remind about

    new = [d for d in open_ids if d not in already]
    if new:
        print(
            f"toolbox: {len(new)} decision(s) with no recorded outcome — "
            f"{', '.join(new)}. Run /toolbox:outcome <decision_id> before this task closes.",
            file=sys.stderr,
        )
        STATE_FILE.write_text(json.dumps(sorted(already | set(new))))


if __name__ == "__main__":
    main()
