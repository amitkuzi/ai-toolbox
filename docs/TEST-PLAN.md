# Test Plan — AI Toolbox v0.7.0-rc

**Version:** 1.0 · **Date:** 2026-09-02 · **Scope:** Unit, integration, and adversary testing

---

## Overview

Comprehensive test strategy covering:
1. **Unit tests** — Store API, backends, validation logic
2. **Integration tests** — End-to-end routing → outcome → score fold
3. **Adversary tests** — Multi-model consistency (Haiku vs Sonnet vs Kimi-K3)
4. **Acceptance tests** — 15 routing test cases (Phase 6 eval suite)

---

## Test objectives

| Objective | Success criterion | Owner |
|---|---|---|
| **P1–P4 compliance** | All validation checks pass; no catalog path references in rules/skills | Validator |
| **Routing consistency** | ≥ 80% agreement across T1 (Haiku), T2 (Sonnet), frontier (Kimi-K3) | Validator |
| **Cost goal (G3)** | ≥ 40% routed to T0/T1 (typical: 50–70%) | Validator |
| **Storage abstraction** | Files and SQLite backends produce identical views | Implementor |
| **Append-only (P4)** | No edits/deletes in ledger after 100+ appends | Validator |
| **Score accuracy** | EMA fold matches hand-computed expected values | Implementor |

---

## Test pyramid

```
                     Acceptance (15 test cases)
                    /
              Integration (20 scenarios)
            /
      Unit (50+ tests)
    /
Infrastructure (mocks, fixtures, test data)
```

---

## 1. Unit tests

**Framework:** Python 3.12 + pytest  
**Location:** `tests/unit/`  
**Run:** `pytest tests/unit/ -v`

### 1.1 Store API tests

**File:** `tests/unit/test_store.py`

```python
def test_append_creates_event_id():
    """Event IDs are ULIDs (time-sortable, unique)"""
    
def test_append_validates_schema():
    """Missing required fields → error"""
    
def test_append_requires_reason():
    """Every event must have a reason field (P4)"""
    
def test_query_returns_events_in_order():
    """Events returned in ts order, oldest first"""
    
def test_project_is_idempotent():
    """Same ledger → same views, always"""
    
def test_project_computes_verified_date():
    """verified field from latest score.outcome"""
    
def test_trace_shows_full_chain():
    """Decision → candidates → outcomes → scores"""
```

**Expected:** 8 tests, all green

### 1.2 Backend tests (files + sqlite)

**File:** `tests/unit/test_backends.py`

```python
def test_files_backend_appends_to_jsonl():
    """New events go to ledger/*.jsonl"""
    
def test_sqlite_backend_inserts_to_db():
    """New events go to SQLite table"""
    
def test_both_backends_read_identically():
    """Query result is same for files and sqlite"""
    
def test_contract_test_passes_all_backends():
    """20 scenarios on files == sqlite"""
```

**Expected:** 12 tests (6 per backend)

### 1.3 Validation tests

**File:** `tests/unit/test_validate.py`

```python
def test_schema_validation():
    """Missing fields caught"""
    
def test_append_only_guard():
    """Deleted line detected as violation"""
    
def test_views_match_projection():
    """Hand-edited view detected"""
    
def test_no_catalog_paths_in_rules():
    """rules/*.md can't reference catalog/"""
```

**Expected:** 8 tests

### 1.4 Scoring tests

**File:** `tests/unit/test_scoring.py`

```python
def test_ema_fold_basic():
    """[8, 7, 9, 6, 5] → EMA ≈ 7.0"""
    
def test_ema_fold_with_decay():
    """Score > 90 days old decayed by 20%"""
    
def test_human_weight_1_5x():
    """Human scores count 1.5× in fold"""
    
def test_retract_removes_from_fold():
    """Retracted outcome ignored in EMA"""
```

**Expected:** 6 tests

### 1.5 Rules tests

**File:** `tests/unit/test_rules.py`

```python
def test_rule_01_gate_l0():
    """Trivial task → L0 (answer inline)"""
    
def test_rule_02_tier_t0():
    """Local, free task → T0"""
    
def test_rule_04_effective_score():
    """Score × weights = effective"""
```

**Expected:** 12 tests (one per rule scenario)

---

## 2. Integration tests

**Framework:** pytest + fixtures  
**Location:** `tests/integration/`  
**Run:** `pytest tests/integration/ -v --timeout=30`

### 2.1 End-to-end flow

**File:** `tests/integration/test_e2e.py`

```python
def test_route_creates_decision_event():
    """Routing appends decision with candidates"""
    
def test_outcome_appends_to_existing_decision():
    """Score.outcome lands in correct decision"""
    
def test_score_fold_updates_my_score_current():
    """After outcome, score is recomputed"""
    
def test_full_flow_append_only():
    """Route → outcome → project: no edits, only appends"""
```

**Expected:** 8 tests

### 2.2 Curator simulation

**File:** `tests/integration/test_curator.py`

```python
def test_curator_discovers_tool():
    """tool.added event created"""
    
def test_curator_validates_tool():
    """tool.status appended for unverified tool"""
    
def test_curator_closes_gap():
    """gap.closed when covering tool found"""
    
def test_daily_run_append_only():
    """No edits to existing events"""
```

**Expected:** 6 tests

### 2.3 Multi-backend equivalence

**File:** `tests/integration/test_backends_equivalence.py`

```python
def test_files_and_sqlite_produce_same_views():
    """40 appends on files backend == sqlite backend"""
    
def test_hash_of_tools_yaml_identical():
    """Byte-for-byte same output"""
```

**Expected:** 4 tests

---

## 3. Adversary tests (Multi-model consistency)

**Framework:** pytest + LLM API calls  
**Location:** `tests/adversary/`  
**Models:** Claude Haiku (T1), Claude Sonnet (T2), Kimi-K3 (frontier)  
**Run:** `pytest tests/adversary/ -v --adversary-models=haiku,sonnet,kimi`

### 3.1 Routing consistency (15 test cases)

**File:** `tests/adversary/test_routing_consistency.py`

For each of 15 test cases from Phase 6 routing suite:

```python
def test_case_1_rename_files():
    """
    Route: "Rename 200 STL files"
    Expected: L1, T0, script, python3/bash
    
    Run on:
    - Haiku (T1)
    - Sonnet (T2)
    - Kimi-K3 (frontier)
    
    Measure:
    - Tier agreement (all pick T0? or diverge?)
    - Tool agreement (all pick python3? or different?)
    - Reasoning similarity (do reasons align?)
    """
    
    results = {
        "haiku": route_with_model("haiku", test_case),
        "sonnet": route_with_model("sonnet", test_case),
        "kimi": route_with_model("kimi", test_case),
    }
    
    # Check consistency
    assert_tier_agreement(results, tolerance=1)  # adjacent tiers OK
    assert_tool_in_category(results)  # all pick same type
    assert_reasoning_coherent(results)  # reasons should align
```

**Expected:** 15 tests (one per case)

### 3.2 Consistency metrics

**File:** `tests/adversary/test_consistency_metrics.py`

```python
def test_same_tier_percentage():
    """
    Haiku vs Sonnet: X% same tier (goal: ≥65%)
    Sonnet vs Kimi: X% same tier (goal: ≥65%)
    Haiku vs Kimi: X% same tier (goal: ≥60%, frontier may differ)
    """
    
def test_divergence_percentage():
    """
    T0 vs T3 divergence: <20% (goal: <20%)
    If >20%: ADR needed for V2 deterministic CLI
    """
    
def test_reasoning_agreement():
    """
    Do all models cite similar factors in their reasoning?
    (cost, freshness, autonomy, etc.)
    """
```

**Expected:** 4 tests

### 3.3 Cost goal (G3)

**File:** `tests/adversary/test_cost_goal.py`

```python
def test_g3_cheap_routing_percentage():
    """
    Run 15 test cases on T1, T2, frontier
    Count: how many picked T0/T1?
    
    Goal: ≥40% (typical: 50-70%)
    """
    
def test_cost_distribution():
    """
    T0: X%, T1: X%, T2: X%, T3: X%
    Expected: T0+T1 ≥ 40%
    """
```

**Expected:** 3 tests

---

## 4. Acceptance tests

**Framework:** pytest  
**Location:** `tests/acceptance/`  
**Basis:** Phase 6 routing suite (15 test cases)  
**Run:** `pytest tests/acceptance/ -v`

```python
def test_routing_suite_case_1_through_15():
    """
    15 real-world tasks, each with expected routing.
    Manual verification: did the tool pick match expected?
    """
```

**Expected:** 15 tests (one per case)

---

## 5. Test data and fixtures

**Location:** `tests/fixtures/`

### Sample ledger

```
catalog-test/
├── ledger/
│   ├── tools.jsonl (10 sample tools: python3, bash, pandas, etc.)
│   ├── scores.jsonl (20 sample outcomes)
│   ├── decisions.jsonl (5 sample decisions)
│   ├── sources.jsonl (3 sources)
│   └── models.jsonl (5 models: T0-T3 range)
└── views/ (generated by `store project`)
```

---

## 6. Test execution matrix

| Test type | Framework | Count | Duration | Models | Pass criteria |
|---|---|---|---|---|---|
| Unit | pytest | 50+ | < 5 sec | — | 100% |
| Integration | pytest | 20 | < 30 sec | — | 100% |
| Adversary | pytest + API | 22 | < 5 min | Haiku, Sonnet, Kimi | ≥80% consistency |
| Acceptance | pytest | 15 | < 2 min | — | 13/15 (87%) |
| **Total** | | **107** | **< 10 min** | | **All green** |

---

## 7. CI/CD integration

### GitHub Actions workflow

**File:** `.github/workflows/test.yml`

```yaml
name: test

on: [push, pull_request]

jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -q pytest pyyaml python-ulid
      - run: pytest tests/unit/ -v

  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -q pytest pyyaml python-ulid
      - run: pytest tests/integration/ -v

  validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -q pyyaml python-ulid
      - run: python scripts/validate.py

  adversary:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && contains(github.ref, 'main')
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      KIMI_API_KEY: ${{ secrets.KIMI_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -q pytest anthropic requests pyyaml python-ulid
      - run: pytest tests/adversary/ -v --adversary-models=haiku,sonnet,kimi
```

---

## 8. Local test execution

### Run all tests

```bash
pytest tests/ -v --tb=short

# With timing
pytest tests/ -v --durations=10

# Only unit
pytest tests/unit/ -v

# Only adversary
pytest tests/adversary/ -v --adversary-models=haiku,sonnet,kimi

# With coverage
pytest tests/ --cov=scripts --cov-report=html
```

### Expected output

```
tests/unit/test_store.py::test_append_creates_event_id PASSED
tests/unit/test_store.py::test_append_validates_schema PASSED
...
tests/integration/test_e2e.py::test_route_creates_decision_event PASSED
...
tests/adversary/test_routing_consistency.py::test_case_1_rename_files PASSED
...

======================== 107 passed in 8.23s ========================
```

---

## 9. Test coverage targets

| Module | Target | Current (Phase 6) |
|---|---|---|
| `scripts/store.py` | ≥ 90% | TBD (after impl) |
| `scripts/backends/` | ≥ 85% | TBD |
| `scripts/validate.py` | ≥ 80% | TBD |
| **Overall** | **≥ 85%** | **TBD** |

---

## 10. Known limitations (V1)

- ❌ No performance/load tests (routine discovery at 1000s tools: future)
- ❌ No chaos testing (corrupted ledger recovery: future)
- ❌ No GraphQL/API tests (no HTTP API in V1)
- ⚠️ Adversary tests require live API keys (can't mock Kimi-K3 responses easily)

---

## 11. Sign-off

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Adversary consistency ≥ 80%
- [ ] G3 goal (≥ 40% T0/T1) met
- [ ] Coverage ≥ 85%
- [ ] No open high-priority bugs

**Ready for v1.0.0 release:** ✅ (after all above checked)

---

## See also

- `docs/evals/routing-suite.md` (15 test cases)
- `scripts/validate.py` (P1–P4 validation)
- `.github/workflows/test.yml` (CI/CD)
