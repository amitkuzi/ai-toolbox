# Validation procedures — Append-only proof + model consistency

**Version:** 0.6 · **Date:** 2026-09-02 · **Purpose:** Prove P4 holds in practice; measure routing consistency

---

## Task 6.1b: Append-only verification (P4 proof)

### Why this matters

**P4 (immutability):** The ledger is append-only. Every line added is permanent; no edits or deletes.  
**Threat:** A skill/agent accidentally edits a line instead of appending a new one.  
**Defense:** CI gate (`scripts/validate.py`) catches deletions/edits before they reach the ledger.

**This task proves:** Running a full daily curator run + 10 route/outcome decisions doesn't violate P4.

### Procedure

#### Step 1: Baseline snapshot

Before running the curator + routing:

```bash
# Get hash of every ledger line
cd catalog/ledger
for f in *.jsonl; do
  git hash-object "$f" > "${f%.jsonl}.hash.baseline"
done
```

Store: `baseline-hashes-<date>/`

#### Step 2: Run full daily curator

```bash
/toolbox:curate daily
# or: docker compose run --rm runner
```

#### Step 3: Route 10 decisions

```bash
for i in {1..10}; do
  /toolbox:route <sample-task-$i>
  /toolbox:outcome <decision-id>
done
```

#### Step 4: Check for modifications

```bash
# Re-hash all ledger files
cd catalog/ledger
for f in *.jsonl; do
  git hash-object "$f" > "${f%.jsonl}.hash.after"
done

# Compare: every line should either be unchanged or added
git diff --unified=0 HEAD -- catalog/ledger/ | grep "^-" && \
  echo "❌ FAILED: line deleted or modified (P4 violation)" || \
  echo "✅ PASSED: append-only preserved"
```

#### Step 5: Verify line counts

```python
import json

baseline = {}  # load baseline line counts
after = {}     # load after line counts

for collection in baseline:
    added = after[collection] - baseline[collection]
    if added >= 0:
        print(f"✅ {collection}: +{added} events appended")
    else:
        print(f"❌ {collection}: {added} events lost (P4 violation)")
```

### Success criterion

- ✅ No lines deleted or modified (git diff shows only `+` lines)
- ✅ Line count increased for tools.jsonl, scores.jsonl, decisions.jsonl
- ✅ `python scripts/validate.py` passes before and after

### Acceptable results

- ✅ `+10` new decision events (from routing)
- ✅ `+10–20` score.outcome events (outcomes)
- ✅ `+5–10` tool.added events (curator discovered new tools)
- ✅ `+0–3` source.revised or tool.status events (validation)

### Failure modes

| Symptom | Cause | Action |
|---|---|---|
| Line count decreased | Agent edited/deleted a line | Debug the agent; this is a P4 violation |
| `validate.py` fails | Schema error or append-only violation | Check validator output; fix and re-run |
| Hash mismatch | Trailing whitespace or line reordering | Check line endings (Windows/Unix) and file encoding |

---

## Task 6.2: Model consistency test

### Why this matters

Routing decisions should be **consistent:** if T1 (Haiku) and T2 (Sonnet) see the same task,
they should pick the same tier (or adjacent tiers). Large divergence → bug in rules or weights.

**Goal:** ≥ 80% agreement, < 20% divergence (else open ADR for V2 deterministic CLI).

### Procedure

#### Step 1: Prepare 15 test cases

Use `docs/evals/routing-suite.md` (or your own 15-20 real tasks).

#### Step 2: Route with T1 model

Set Claude Code to use Haiku (T1):

```bash
/model haiku
```

Run each test case:

```bash
for i in 1..15; do
  task=$(sed -n "${i}p" test-cases.txt)
  /toolbox:route "$task"
done

# Export results
python scripts/store.py query scores --filter 'kind=decision' \
  > routing-t1-results.jsonl
```

#### Step 3: Route with T2 model

Switch to Sonnet (T2):

```bash
/model sonnet
```

Repeat:

```bash
for i in 1..15; do
  task=$(sed -n "${i}p" test-cases.txt)
  /toolbox:route "$task"
done

# Export results
python scripts/store.py query scores --filter 'kind=decision' \
  > routing-t2-results.jsonl
```

#### Step 4: Compare tier choices

```python
import json

t1_results = [json.loads(line) for line in open('routing-t1-results.jsonl')]
t2_results = [json.loads(line) for line in open('routing-t2-results.jsonl')]

# Sort by task (match T1 and T2 results)
t1_by_task = {r['payload']['task']: r for r in t1_results}
t2_by_task = {r['payload']['task']: r for r in t2_results}

same = 0
adjacent = 0
divergent = 0

for task in t1_by_task:
    t1_tier = t1_by_task[task]['payload']['orchestrator_tier']
    t2_tier = t2_by_task[task]['payload']['orchestrator_tier']
    
    if t1_tier == t2_tier:
        same += 1
    elif abs(tier_order(t1_tier) - tier_order(t2_tier)) <= 1:
        adjacent += 1
    else:
        divergent += 1
        print(f"⚠️ Divergent: {task}")
        print(f"  T1: {t1_tier}, T2: {t2_tier}")

total = len(t1_by_task)
agreement_pct = (same + adjacent) / total * 100
divergence_pct = divergent / total * 100

print(f"\n✅ Same tier: {same}/{total} ({same/total*100:.1f}%)")
print(f"⚠️ Adjacent: {adjacent}/{total} ({adjacent/total*100:.1f}%)")
print(f"❌ Divergent: {divergent}/{total} ({divergence_pct:.1f}%)")
print(f"\nOverall agreement: {agreement_pct:.1f}% (goal: ≥80%)")

if divergence_pct > 20:
    print("⚠️ Divergence > 20% — consider opening ADR for V2")
else:
    print("✅ Consistency within acceptable range")

def tier_order(tier):
    return {'T0': 0, 'T1': 1, 'T2': 2, 'T3': 3}[tier]
```

### Success criteria

- ✅ **Same tier:** ≥ 65% of decisions (T1 and T2 agree exactly)
- ✅ **Adjacent tier:** ≤ 25% (T0↔T1, T1↔T2, T2↔T3 acceptable)
- ✅ **Divergent:** < 20% (T0↔T2, T0↔T3, T1↔T3 → investigate)

### Expected results

Typical routing consistency for well-written rules:

| Metric | Value |
|---|---|
| Same tier | 70–80% |
| Adjacent | 15–25% |
| Divergent | < 10% |

### Failure mode: high divergence

If divergence > 20%:

1. **Check rules:** Are L1/L2/L3 gates clear and unambiguous?
2. **Check weights:** Do profiles weights match the task types?
3. **Check rule version:** Are both runs using same rules version?
4. **Check model capability:** Does T1 have different reasoning than T2 on the task?

**Action:** Open ADR (Architecture Decision Record) for Phase 7 (deterministic CLI routing).

---

## Measurement: cost impact (G3)

From the 15 routing decisions:

```python
# Tier distribution
tier_counts = {}
for result in t1_results + t2_results:
    tier = result['payload']['orchestrator_tier']
    tier_counts[tier] = tier_counts.get(tier, 0) + 1

t0_t1_count = tier_counts.get('T0', 0) + tier_counts.get('T1', 0)
total = len(t1_results) + len(t2_results)
pct_cheap = t0_t1_count / total * 100

print(f"Routed to T0/T1: {t0_t1_count}/{total} ({pct_cheap:.1f}%)")
print(f"G3 success: {'✅ YES' if pct_cheap >= 40 else '❌ NO'} (goal: ≥ 40%)")
```

**Typical result:** If routing is well-tuned, ≥ 50% pick T0/T1 (beats G3 goal of 40%).

---

## See also

- `docs/evals/routing-suite.md` (15 test cases)
- `docs/PRD.md` §3 (G3 metric)
- `rules/02-orchestrator-model.md` (tier selection rules)
- `scripts/validate.py` (P4 compliance checker)
