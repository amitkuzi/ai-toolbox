"""Smoke test for remind_outcome.py's open-decision detection and once-only
reminding. Plain asserts, runnable as:

    python hooks/test_remind_outcome.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from store import Store  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import remind_outcome  # noqa: E402


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="toolbox-hook-test-"))
    state = tmp / "state.json"
    os.environ["TOOLBOX_BASE_DIR"] = str(tmp)
    remind_outcome.STATE_FILE = state
    try:
        store = Store(backend_name="files", base_dir=tmp)
        store.append(kind="decision", subject_id="d-test-001", actor="agent:orchestrator", via="route",
                     reason="test", payload={"task": "t"})

        assert remind_outcome.open_decisions() == ["d-test-001"], "unclosed decision should show up"

        store.append(kind="score.outcome", subject_id="d-test-001", actor="auto:validator", via="outcome",
                     reason="ok", payload={"tool_id": "python3", "result": "success", "score": 9})
        assert remind_outcome.open_decisions() == [], "outcome should close the decision"
        print("ok  open_decisions detects and clears open decisions")

        # once-only reminding
        store.append(kind="decision", subject_id="d-test-002", actor="agent:orchestrator", via="route",
                     reason="test", payload={"task": "t2"})
        remind_outcome.main()
        first = state.read_text()
        remind_outcome.main()
        second = state.read_text()
        assert first == second, "state file should not grow on a repeat reminder for the same decision"
        assert "d-test-002" in first
        print("ok  reminder state is idempotent per decision")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        os.environ.pop("TOOLBOX_BASE_DIR", None)


if __name__ == "__main__":
    main()
