"""Unit tests for Catalog Store API (scripts/store.py)"""
import pytest
from pathlib import Path
import tempfile
import json
from datetime import datetime, timedelta

# Add scripts to path for import
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from store import Store, Event, collection_for_kind


@pytest.fixture
def temp_catalog():
    """Temporary catalog directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        catalog_dir = Path(tmpdir) / "catalog"
        catalog_dir.mkdir()
        (catalog_dir / "ledger").mkdir()
        (catalog_dir / "views").mkdir()
        yield catalog_dir


@pytest.fixture
def store(temp_catalog):
    """Store instance with temp catalog"""
    return Store(backend_name="files", base_dir=temp_catalog)


class TestAppendAPI:
    """Test Store.append() operation"""

    def test_append_creates_event_id(self, store):
        """Event IDs are ULIDs (time-sortable, unique)"""
        event_id_1 = store.append(
            kind="tool.added",
            subject_id="python3",
            actor="human:test",
            via="test",
            reason="test event",
            payload={"type": "script", "category": "runtime"}
        )

        event_id_2 = store.append(
            kind="tool.added",
            subject_id="bash",
            actor="human:test",
            via="test",
            reason="test event 2",
            payload={"type": "script", "category": "runtime"}
        )

        assert event_id_1 is not None
        assert event_id_2 is not None
        assert event_id_1 != event_id_2
        # ULID is time-sortable; second one should be >= first
        assert event_id_2 >= event_id_1

    def test_append_generates_timestamp(self, store):
        """Event gets ts (ISO-8601 UTC)"""
        before = datetime.utcnow()

        store.append(
            kind="tool.added",
            subject_id="test",
            actor="human:test",
            via="test",
            reason="test",
            payload={"type": "script", "category": "runtime"}
        )

        after = datetime.utcnow()

        # Read back the event
        events = list(store.read_events("tools"))
        assert len(events) == 1

        event_ts = datetime.fromisoformat(events[0]["ts"].replace("Z", "+00:00"))
        assert before <= event_ts <= after

    def test_append_requires_reason(self, store):
        """Every event must have reason (D-011)"""
        with pytest.raises(ValueError):
            store.append(
                kind="tool.added",
                subject_id="test",
                actor="human:test",
                via="test",
                reason="",  # Empty reason
                payload={"type": "script", "category": "runtime"}
            )

    def test_append_validates_required_fields(self, store):
        """Missing required payload fields → error"""
        # tool.added requires type and category in payload
        with pytest.raises((KeyError, ValueError)):
            store.append(
                kind="tool.added",
                subject_id="test",
                actor="human:test",
                via="test",
                reason="test",
                payload={"name": "test"}  # Missing type, category
            )

    def test_append_only_creates_new_line(self, store):
        """Appending doesn't modify existing lines"""
        # Append first event
        id1 = store.append(
            kind="tool.added",
            subject_id="tool1",
            actor="human:test",
            via="test",
            reason="first",
            payload={"type": "script", "category": "runtime"}
        )

        # Read line hash
        ledger_path = store.catalog_dir / "ledger" / "tools.jsonl"
        with open(ledger_path, "r") as f:
            lines_before = f.readlines()
        line1_hash = hash(lines_before[0])

        # Append second event
        id2 = store.append(
            kind="tool.added",
            subject_id="tool2",
            actor="human:test",
            via="test",
            reason="second",
            payload={"type": "script", "category": "runtime"}
        )

        # First line should be unchanged
        with open(ledger_path, "r") as f:
            lines_after = f.readlines()

        assert lines_after[0] == lines_before[0]
        assert len(lines_after) == len(lines_before) + 1


class TestQueryAPI:
    """Test Store.query() operation"""

    def test_query_returns_events_in_order(self, store):
        """Events returned in ts order (oldest first)"""
        ids = []
        for i in range(5):
            id = store.append(
                kind="tool.added",
                subject_id=f"tool{i}",
                actor="human:test",
                via="test",
                reason=f"event {i}",
                payload={"type": "script", "category": "runtime"}
            )
            ids.append(id)

        events = list(store.query("tools"))
        assert len(events) == 5

        # Check order (ts should increase)
        for i in range(len(events) - 1):
            ts_curr = datetime.fromisoformat(events[i]["ts"].replace("Z", "+00:00"))
            ts_next = datetime.fromisoformat(events[i+1]["ts"].replace("Z", "+00:00"))
            assert ts_curr <= ts_next

    def test_query_filters_by_field(self, store):
        """Query with filter parameter"""
        store.append(
            kind="tool.added",
            subject_id="python3",
            actor="human:test",
            via="test",
            reason="test",
            payload={"type": "script", "category": "runtime", "cost": "free"}
        )

        store.append(
            kind="tool.added",
            subject_id="claude",
            actor="human:test",
            via="test",
            reason="test",
            payload={"type": "model", "category": "model", "cost": "paid"}
        )

        # Query for free tools only
        free_tools = [e for e in store.query("tools") if e.get("payload", {}).get("cost") == "free"]
        assert len(free_tools) == 1
        assert free_tools[0]["subject_id"] == "python3"


class TestProjectAPI:
    """Test Store.project() operation"""

    def test_project_is_idempotent(self, store):
        """Same ledger → same views, always"""
        # Add some events
        for i in range(5):
            store.append(
                kind="tool.added",
                subject_id=f"tool{i}",
                actor="human:test",
                via="test",
                reason=f"event {i}",
                payload={"type": "script", "category": "runtime", "cost": "free"}
            )

        # Project twice
        views1 = store.project(collections=["tools"])
        views2 = store.project(collections=["tools"])

        # Should be identical
        assert views1["tools.yaml"] == views2["tools.yaml"]

    def test_project_computes_verified_date(self, store):
        """verified field from latest score.outcome"""
        # Add a tool
        store.append(
            kind="tool.added",
            subject_id="test-tool",
            actor="human:test",
            via="test",
            reason="test",
            payload={"type": "script", "category": "runtime"}
        )

        # Add a score.outcome
        outcome_date = "2026-09-01T10:00:00Z"
        store.append(
            kind="score.outcome",
            subject_id="test-tool",
            actor="auto:validator",
            via="outcome",
            reason="test outcome",
            payload={"score": 9, "result": "success"},
            ts_override=outcome_date
        )

        # Project and check
        views = store.project(collections=["tools"])
        # verified should be in the projection (check YAML contains date)
        assert "verified" in views["tools.yaml"] or "2026-09-01" in views["tools.yaml"]


class TestValidation:
    """Test schema and P1-P4 validation"""

    def test_event_envelope_required_fields(self, store):
        """All required fields present in stored event"""
        store.append(
            kind="tool.added",
            subject_id="test",
            actor="human:test",
            via="test",
            reason="test",
            payload={"type": "script", "category": "runtime"}
        )

        events = list(store.query("tools"))
        event = events[0]

        # Check all required envelope fields
        required = ["event_id", "ts", "kind", "subject_id", "actor", "via", "reason", "payload"]
        for field in required:
            assert field in event, f"Missing required field: {field}"

    def test_kind_determines_collection(self, store):
        """Different kinds go to different collections"""
        store.append(kind="tool.added", subject_id="t1", actor="h:t", via="t", reason="r",
                    payload={"type": "script", "category": "runtime"})
        store.append(kind="score.outcome", subject_id="s1", actor="h:t", via="t", reason="r",
                    payload={"score": 9})

        tools = list(store.query("tools"))
        scores = list(store.query("scores"))

        assert len(tools) == 1
        assert len(scores) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
