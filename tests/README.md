# AI Toolbox Test Suite

Comprehensive testing for AI Toolbox including unit tests, integration tests, and adversary tests using Kimi-K3.

## Quick start

### Install test dependencies

```bash
pip install -r requirements-test.txt
```

### Run all tests

```bash
pytest tests/ -v
```

### Run specific test suite

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Adversary tests (requires API keys)
pytest tests/adversary/ -v
```

### Run with API keys for adversary tests

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export KIMI_API_KEY=sk-...

pytest tests/adversary/ -v
```

### Run with coverage

```bash
pytest tests/ --cov=scripts --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Run with timeout (prevent hanging tests)

```bash
pytest tests/ --timeout=300
```

---

## Test suite overview

| Suite | Location | Count | Duration | Purpose |
|---|---|---|---|---|
| **Unit** | `tests/unit/` | 50+ | < 5 sec | Store API, backends, validation |
| **Integration** | `tests/integration/` | 20 | < 30 sec | End-to-end flows, curator simulation |
| **Adversary** | `tests/adversary/` | 22 | < 5 min | Multi-model consistency (Haiku/Sonnet/Kimi) |
| **Acceptance** | (Phase 6) | 15 | < 2 min | 15 routing test cases |

---

## Key test files

### Unit tests
- `test_store.py` — Catalog Store API (append, query, project, trace)
- `test_backends.py` — Files and SQLite backends
- `test_validate.py` — Schema and P1–P4 compliance
- `test_scoring.py` — EMA fold, decay, human weight
- `test_rules.py` — Each decision rule scenario

### Integration tests
- `test_e2e.py` — Full routing → outcome → score flow
- `test_curator.py` — Tool discovery, validation, gap closing
- `test_backends_equivalence.py` — Files vs SQLite view comparison

### Adversary tests
- `test_routing_adversary.py` — Multi-model consistency (Haiku, Sonnet, Kimi-K3)
- `test_consistency_metrics.py` — Measure agreement percentages
- `test_cost_goal.py` — Verify G3 (≥ 40% T0/T1 routing)

---

## CI/CD integration

Tests run automatically on:
- **Push to any branch** → unit + integration + validation
- **Merge to main** → unit + integration + validation + adversary

See `.github/workflows/test.yml` for workflow config.

---

## Adversary testing (Kimi-K3 + Claude models)

The adversary test suite uses three frontier models to validate routing consistency:

1. **Claude Haiku (T1)** — Fast, cheap
2. **Claude Sonnet (T2)** — Balanced
3. **Kimi-K3 (frontier)** — High-reasoning

For each of 15 routing test cases:
- Route task on all three models
- Compare tier choices (goal: ≥80% agreement)
- Compare tool types (goal: exact match)
- Measure G3: % routed to T0/T1 (goal: ≥40%)

### Example run

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export KIMI_API_KEY=sk-...

pytest tests/adversary/test_routing_adversary.py::TestRoutingConsistency::test_case_1_rename_files -v -s

# Output:
#   haiku   → T0 / script     / python3
#   sonnet  → T0 / script     / python3
#   kimi    → T1 / script     / bash
#   ✅ Tier agreement: same/adjacent
#   ✅ Type agreement: script
```

---

## Test data fixtures

Sample catalog data in `tests/fixtures/`:

```
catalog-test/
├── ledger/
│   ├── tools.jsonl (10 sample tools)
│   ├── scores.jsonl (20 sample outcomes)
│   ├── decisions.jsonl (5 sample decisions)
│   └── models.jsonl (5 models T0–T3)
└── views/ (auto-generated)
```

---

## Troubleshooting

### Import errors

```bash
# Make sure scripts/ is in Python path
export PYTHONPATH=/path/to/ai-toolbox/scripts:$PYTHONPATH
pytest tests/unit/
```

### API key errors

```bash
# Set all required keys
export ANTHROPIC_API_KEY=sk-ant-...
export KIMI_API_KEY=sk-...

# Or skip adversary tests
pytest tests/ -m "not adversary"
```

### Slow tests

```bash
# Run with parallel execution (requires pytest-xdist)
pytest tests/ -n auto

# Or skip slow tests
pytest tests/ -m "not slow"
```

---

## Adding new tests

1. Create test file in appropriate directory (`tests/unit/`, `tests/integration/`, or `tests/adversary/`)
2. Name file `test_*.py`
3. Use `Test*` class names and `test_*` method names
4. Add docstrings to test functions
5. Use fixtures from `conftest.py`

Example:

```python
def test_my_feature(store, temp_catalog):
    """Brief description of what this tests"""
    # Arrange
    store.append(...)
    
    # Act
    result = store.query(...)
    
    # Assert
    assert result is not None
```

---

## Success criteria (before v1.0.0 release)

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Adversary consistency ≥ 80%
- [ ] G3 goal (≥ 40% T0/T1) met
- [ ] Code coverage ≥ 85%
- [ ] No high-priority bugs

See `docs/TEST-PLAN.md` for full test plan.
