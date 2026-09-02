"""Contract test for the Catalog Store (P1). Runs the same scenarios against
every backend so a new backend only needs to pass this file. Plain asserts,
no framework — runnable as:

    python scripts/backends/test_contract.py
    python -m pytest scripts/backends/test_contract.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from store import Store  # noqa: E402


def _fresh_store(backend_name: str) -> tuple[Store, Path]:
    tmp = Path(tempfile.mkdtemp(prefix=f"store-contract-{backend_name}-"))
    return Store(backend_name=backend_name, base_dir=tmp), tmp


def test_append_then_query_returns_it(backend_name: str):
    store, tmp = _fresh_store(backend_name)
    try:
        store.append(kind="tool.added", subject_id="t1", actor="human:amit", via="ui-manual",
                     payload={"name": "Tool One", "type": "script", "category": "tool"})
        results = store.query("tools", kind="tool.added", subject_id="t1")
        assert len(results) == 1
        assert results[0]["payload"]["name"] == "Tool One"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_append_then_project_folds(backend_name: str):
    store, tmp = _fresh_store(backend_name)
    try:
        store.append(kind="tool.added", subject_id="t1", actor="human:amit", via="ui-manual",
                     payload={"name": "Tool One", "type": "script", "category": "tool", "my_score": 7})
        written = store.project(collection="tools")
        assert "tools.yaml" in written
        assert "Tool One" in written["tools.yaml"]
        # views really landed on disk
        assert (tmp / "views" / "tools.yaml").exists()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_added_plus_revised_folds_to_current_state(backend_name: str):
    store, tmp = _fresh_store(backend_name)
    try:
        store.append(kind="tool.added", subject_id="t1", actor="human:amit", via="ui-manual",
                     payload={"name": "Tool One", "type": "script", "category": "tool", "purpose": "old"})
        store.append(kind="tool.added", subject_id="t2", actor="human:amit", via="ui-manual",
                     payload={"name": "Tool Two", "type": "script", "category": "tool", "purpose": "unrelated"})
        store.append(kind="tool.revised", subject_id="t1", actor="human:amit", via="ui-manual",
                     reason="fix purpose", payload={"purpose": "new"})
        written = store.project(collection="tools")
        import yaml
        data = yaml.safe_load(written["tools.yaml"])
        by_id = {t["id"]: t for t in data["tools"]}
        assert by_id["t1"]["purpose"] == "new"
        assert by_id["t2"]["purpose"] == "unrelated"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_trace_returns_full_chain(backend_name: str):
    store, tmp = _fresh_store(backend_name)
    try:
        store.append(kind="tool.added", subject_id="t1", actor="human:amit", via="ui-manual",
                     payload={"name": "Tool One", "type": "script", "category": "tool"})
        store.append(kind="decision", subject_id="d-1", actor="agent:orchestrator", via="route",
                     reason="chose t1", payload={"chosen": "t1"})
        store.append(kind="score.outcome", subject_id="d-1", actor="auto:validator", via="outcome",
                     reason="worked", payload={"tool_id": "t1", "score": 9})
        chain = store.trace("d-1")
        assert [e["kind"] for e in chain] == ["decision", "score.outcome"]
        tool_chain = store.trace("t1")
        kinds = {e["kind"] for e in tool_chain}
        assert "tool.added" in kinds and "score.outcome" in kinds
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_missing_reason_on_non_initial_event_raises(backend_name: str):
    store, tmp = _fresh_store(backend_name)
    try:
        store.append(kind="tool.added", subject_id="t1", actor="human:amit", via="ui-manual", payload={})
        raised = False
        try:
            store.append(kind="tool.revised", subject_id="t1", actor="human:amit", via="ui-manual", payload={})
        except ValueError:
            raised = True
        assert raised, "tool.revised without reason must raise"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_views_never_read_as_input(backend_name: str):
    store, tmp = _fresh_store(backend_name)
    try:
        store.append(kind="tool.added", subject_id="t1", actor="human:amit", via="ui-manual",
                     payload={"name": "Tool One", "type": "script", "category": "tool"})
        store.project(collection="tools")
        # corrupt the view — if append/query ever read views as input this would break them
        (tmp / "views" / "tools.yaml").write_text("not even yaml: [[[", encoding="utf-8")
        results = store.query("tools", subject_id="t1")
        assert len(results) == 1 and results[0]["payload"]["name"] == "Tool One"
        store.append(kind="tool.revised", subject_id="t1", actor="human:amit", via="ui-manual",
                     reason="still works", payload={"purpose": "x"})
        assert len(store.query("tools", kind="tool.revised")) == 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_score_fold_estimate_below_five_samples(backend_name: str):
    store, tmp = _fresh_store(backend_name)
    try:
        store.append(kind="tool.added", subject_id="t1", actor="human:amit", via="ui-manual",
                     payload={"name": "Tool One", "type": "script", "category": "tool"})
        store.append(kind="score.seed", subject_id="d-seed", actor="system:migration", via="migration",
                     reason="seed", payload={"tool_id": "t1", "score": 6})
        store.append(kind="score.outcome", subject_id="d-1", actor="auto:validator", via="outcome",
                     reason="ok", payload={"tool_id": "t1", "score": 8})
        import yaml
        summary = yaml.safe_load(store.project(collection="tools")["scores-summary.yaml"])
        assert summary["t1"]["estimate"] is True
        assert summary["t1"]["score_samples"] == 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_retract_removes_a_sample(backend_name: str):
    store, tmp = _fresh_store(backend_name)
    try:
        store.append(kind="tool.added", subject_id="t1", actor="human:amit", via="ui-manual", payload={})
        e1 = store.append(kind="score.seed", subject_id="d-seed", actor="system:migration", via="migration",
                          reason="seed", payload={"tool_id": "t1", "score": 6})
        store.append(kind="score.outcome", subject_id="d-1", actor="auto:validator", via="outcome",
                     reason="ok", payload={"tool_id": "t1", "score": 8})
        import yaml
        before = yaml.safe_load(store.project(collection="tools")["scores-summary.yaml"])["t1"]["score_samples"]
        store.append(kind="score.retract", subject_id="d-seed", actor="human:amit", via="ui-manual",
                     supersedes=e1["event_id"], reason="wrong tool", payload={})
        after = yaml.safe_load(store.project(collection="tools")["scores-summary.yaml"])["t1"]["score_samples"]
        assert after == before - 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_append_only_ledger_file_grows_monotonically(backend_name: str):
    if backend_name != "files":
        return  # this scenario is about the JSONL file specifically
    store, tmp = _fresh_store(backend_name)
    try:
        store.append(kind="tool.added", subject_id="t1", actor="human:amit", via="ui-manual", payload={})
        path = tmp / "ledger" / "tools.jsonl"
        before = path.read_text(encoding="utf-8")
        store.append(kind="tool.revised", subject_id="t1", actor="human:amit", via="ui-manual",
                     reason="x", payload={"purpose": "y"})
        after = path.read_text(encoding="utf-8")
        assert after.startswith(before)  # pure addition, nothing before it changed
        assert after != before
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


ALL_TESTS = [
    test_append_then_query_returns_it,
    test_append_then_project_folds,
    test_added_plus_revised_folds_to_current_state,
    test_trace_returns_full_chain,
    test_missing_reason_on_non_initial_event_raises,
    test_views_never_read_as_input,
    test_score_fold_estimate_below_five_samples,
    test_retract_removes_a_sample,
    test_append_only_ledger_file_grows_monotonically,
]


def run_all():
    for backend_name in ("files", "sqlite"):
        for test in ALL_TESTS:
            test(backend_name)
            print(f"ok  {backend_name:<8} {test.__name__}")


# pytest entry points (auto-parametrized without a plugin dependency)
def test_contract_files():
    for test in ALL_TESTS:
        test("files")


def test_contract_sqlite():
    for test in ALL_TESTS:
        test("sqlite")


if __name__ == "__main__":
    run_all()
    print("all contract tests passed")
