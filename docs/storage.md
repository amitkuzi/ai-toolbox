# Storage — The Catalog Store contract

**Version:** 0.5 · **Date:** 2026-09-02

How the Catalog Store works (P1 principle: storage abstraction) and how to write a new backend.

---

## Overview

The **Catalog Store** (`scripts/store.py`) is an abstraction layer between skills/agents and the data. It provides four operations — append, query, project, trace — and supports multiple backends (files, SQLite, Postgres, enterprise).

Changing backends = changing one flag. Skills don't change.

```
Skill/Agent
    ↓
Store API (append/query/project/trace)
    ↓
Backend (files.py | sqlite.py | postgres.py | custom)
    ↓
Data (JSONL | SQLite DB | Postgres | S3/Blob)
```

---

## Store API (four operations)

### 1. `append(kind, subject_id, actor, via, reason, payload)`

Immutably add an event to the ledger.

```python
store.append(
    kind="tool.added",
    subject_id="python3",
    actor="agent:curator",
    via="daily-run",
    reason="discovered on PyPI; high confidence",
    payload={
        "type": "script",
        "category": "runtime",
        "name": "Python 3",
        "cost": "free",
        "local_capable": True,
        ...
    }
)
```

Returns: `event_id` (ULID, unique + time-sortable)

**Contract:**
- Appends only; never edits existing events
- Auto-generates `event_id`, `ts` (ISO-8601 UTC)
- Validates `kind`, envelope (required fields)
- Validates `rules_version` (for `decision` events)
- Fails if validation error

### 2. `query(collection, filter=None, limit=None)`

Read events matching criteria.

```python
events = store.query(
    collection="tools",
    filter={"review_status": "verified", "cost": "free"},
    limit=10
)
```

Returns: list of events (full envelope + payload)

**Contract:**
- Read-only
- Supports filtering by any top-level payload field
- Returns ledger events in time order
- No pagination (for V1); V2 can add cursors

### 3. `project(collections=None)`

Generate views from the ledger. Computes computed fields (my_score_current, verified date, review_status, etc.).

```python
views = store.project(collections=["tools", "scores"])
# Returns:
# {
#   "tools.yaml": "...",
#   "scores-summary.yaml": "...",
#   ...
# }
```

Returns: dict of {filename: content} (written as YAML files)

**Contract:**
- Idempotent (always produces same views from same ledger)
- Folds all events per subject by timestamp
- Computes derived fields (never overwrites user input)
- All logic in `_fold_*()` methods (auditable, testable)

### 4. `trace(subject_id)`

Show the full decision chain: decision → candidates → outcomes → score impact.

```python
chain = store.trace(subject_id="d-20260902-001")
```

Returns: structured trace (decision, all outcomes, score history, rules in force)

**Contract:**
- Read-only
- Follows decision → score events → tool history
- Shows rules_version (what rules were in force)
- Human-readable formatted output

---

## Backend interface (what to implement)

A backend is a Python class implementing `Backend` ABC:

```python
from abc import ABC, abstractmethod

class Backend(ABC):
    def __init__(self, base_dir: Path):
        pass
    
    @abstractmethod
    def append_event(self, collection: str, event: dict) -> None:
        """Store an event immutably."""
        pass
    
    @abstractmethod
    def read_events(self, collection: str) -> Iterator[dict]:
        """Yield all events in a collection, in order."""
        pass
    
    @abstractmethod
    def write_views(self, views: dict[str, str]) -> None:
        """Write computed view files atomically."""
        pass
```

### Example: stub backend

```python
class StubBackend(Backend):
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.ledgers = {}
    
    def append_event(self, collection: str, event: dict) -> None:
        if collection not in self.ledgers:
            self.ledgers[collection] = []
        self.ledgers[collection].append(event)
    
    def read_events(self, collection: str) -> Iterator[dict]:
        return iter(self.ledgers.get(collection, []))
    
    def write_views(self, views: dict[str, str]) -> None:
        for name, content in views.items():
            (self.base_dir / "views" / name).write_text(content)
```

### Existing backends

| Backend | What | Strengths |
|---|---|---|
| **files** | `catalog/ledger/*.jsonl` + YAML views | Simple, git-friendly, auditable diffs |
| **sqlite** | SQLite database file | Portable, queryable, no server |
| **postgres** | PostgreSQL (future) | Scalable, multi-tenant, powerful queries |

---

## Contract test (ensure all backends are equivalent)

Every backend must pass the same contract test (`scripts/backends/test_contract.py`):

```bash
python scripts/backends/test_contract.py --backend files
python scripts/backends/test_contract.py --backend sqlite
# (and any new backend)
```

The test:
1. Appends 20 events (tools, scores, decisions)
2. Queries them back
3. Projects views
4. Traces a decision chain
5. Verifies output is identical across backends

**Why:** Guarantees that the abstraction holds. A view computed from files.py is byte-identical to one from sqlite.py.

---

## Writing a new backend

### Step 1: Create the backend class

File: `scripts/backends/mydb.py`

```python
from pathlib import Path
from backends import Backend
from store import Event

class MyDbBackend(Backend):
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.db = ...  # initialize your DB
    
    def append_event(self, collection: str, event: dict) -> None:
        # Validate event schema
        Event(**event)  # raises if invalid
        # Insert into your DB
        self.db.insert(collection, event)
    
    def read_events(self, collection: str) -> Iterator[dict]:
        # Read from your DB, in time order
        for row in self.db.query(collection, order_by="ts"):
            yield row
    
    def write_views(self, views: dict[str, str]) -> None:
        # Write YAML files to catalog/views/
        for name, content in views.items():
            path = self.base_dir / "views" / name
            path.write_text(content, encoding="utf-8")
```

### Step 2: Register the backend

File: `scripts/store.py`, function `Store()`:

```python
BACKENDS = {
    "files": FilesBackend,
    "sqlite": SqliteBackend,
    "mydb": MyDbBackend,  # ← add this
}
```

### Step 3: Pass the contract test

Run:
```bash
python scripts/backends/test_contract.py --backend mydb
```

Fix any failures. The test is the contract; passing = production-ready.

### Step 4: Document

Add to this file (storage.md):

```markdown
| **mydb** | Custom DB | specific strengths |
```

---

## Backend selection

Users choose at runtime:

```bash
# Use files backend (default)
python scripts/store.py append ... --backend files

# Use SQLite
python scripts/store.py append ... --backend sqlite --base-dir /path/to/db

# Use custom
python scripts/store.py append ... --backend mydb
```

Or set `TOOLBOX_BACKEND` environment variable.

---

## Design principles (from P1)

1. **Same API** — every backend speaks append/query/project/trace
2. **Same contract test** — no backend is production until it passes
3. **Immutable writes** — append-only; never edit or delete
4. **Computed views** — projection is idempotent; same ledger = same views
5. **Transparent** — contract is in code, not prose; tests are the truth

---

## Future backends

Potential backends (not V1):

- **PostgreSQL** — multi-tenant SaaS, scalable queries
- **DuckDB** — analytical queries, single-file
- **S3/Blob** — cloud-native (append to ledger objects, fetch views)
- **Dataverse** — Microsoft enterprise (dynamic 365)
- **Custom** — your internal system (implement 3 methods)

---

## See also

- `scripts/store.py` — Store implementation (4 operations)
- `scripts/backends/` — reference implementations (files, sqlite)
- `scripts/backends/test_contract.py` — the contract (20 test scenarios)
- `docs/PRD.md` §1a — P1 principle (storage abstraction)
