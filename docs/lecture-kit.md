# Lecture kit — Slide ↔ Code linkage

**For:** Amit's talk on AI Toolbox (see slides in presentation deck)  
**Purpose:** Map each slide to code artifacts that prove the concept

---

## Slide 1–2: Intro + problem statement

**Slide:** "The problem: every task defaults to expensive"

**Proof:**
- `docs/PRD.md` §2 (Problem: no cost-ordered gate, incompatible schemas, no feedback loop)
- `rules/02-orchestrator-model.md` (cost-based tier selection, rules at decision 2)
- Real example: `catalog/ledger/tools.jsonl` shows 72 tools with cost ranging free → $10/use

---

## Slide 3: Five decisions (high level)

**Slide:** "Five routing decisions, end-to-end"

**Proof:**
- `rules/01-swarm-gate.md` — Decision 1 (L0–L3)
- `rules/02-orchestrator-model.md` — Decision 2 (T0–T3)
- `rules/03-category-gate.md` — Decision 3 (script | mcp | skill | …)
- `rules/04-tool-ranking.md` — Decision 4 (effective score, weights)
- `rules/05-outcome-scoring.md` — Decision 5 (outcome → score fold)

**Live example:**
```
/toolbox:trace d-20260902-001
```
(outputs full decision chain with all candidates, scores, and outcome history)

---

## Slide 4: Data principles (P1–P4)

**Slide:** "Four binding principles"

**Proof:**

| Principle | Code | Evidence |
|---|---|---|
| **P1 — Storage abstraction** | `scripts/store.py` (append/query/project/trace) | `docs/storage.md` explains backends |
| **P2 — Full traceability** | `catalog/ledger/scores.jsonl` (decision events log all candidates) | `/toolbox:trace` shows full chain |
| **P3 — Additive scores** | `rules/05-outcome-scoring.md` (score.seed/outcome/human/retract) | `_fold_scores()` in `store.py` computes, never overwrites |
| **P4 — Immutable ledger** | `scripts/validate.py` (append-only guard, fails on `-` lines) | CI enforces: `git diff ledger/ | grep "^-"` → fail |

**Live demo:**
```bash
# Append an event
python scripts/store.py append --kind tool.added ...

# Try to edit it (CI will catch)
# Fails: "line deleted from ledger (P4 violation)"
```

---

## Slide 5: The Catalog Store

**Slide:** "Storage behind an abstraction"

**Proof:**
- `scripts/store.py` — single API (append/query/project/trace)
- `scripts/backends/files.py` — JSONL + YAML backend
- `scripts/backends/sqlite.py` — SQLite backend (same API)
- `scripts/backends/test_contract.py` — contract test; both backends pass identically

**Command:**
```bash
# Same call, different backends
python scripts/store.py query tools --backend files | head -5
python scripts/store.py query tools --backend sqlite | head -5
# Output: identical
```

---

## Slide 6: Tools + scores (catalog state)

**Slide:** "Catalog at 2026-09-02"

**Proof:**
- `catalog/views/tools.yaml` — all 72 tools with current state
- `catalog/views/scores-summary.yaml` — per-tool: my_score_current, samples, trend
- Example: `python3` (score 9.2, 14 outcomes, trend up)

**Live:**
```bash
python scripts/store.py query tools --filter "my_score_current >= 8" | wc -l
# Shows top performers
```

---

## Slide 7–8: Decision 1 — Swarm gate

**Slide:** "L0–L3: when does this task need agents?"

**Proof:**
- `rules/01-swarm-gate.md` — six example tasks, classified L0–L3
- `skills/toolbox-route/SKILL.md` step 3 — implementation
- `catalog/ledger/scores.jsonl` — real decisions logged with `swarm_level` and `swarm_reason`

**Example decision:**
```json
{
  "swarm_level": "L1",
  "swarm_reason": "single deterministic subtask, no external service"
}
```

---

## Slide 9–10: Decision 2 — Model tier

**Slide:** "T0 (local) → T3 (frontier)"

**Proof:**
- `rules/02-orchestrator-model.md` — tier selection rules
- `catalog/views/models.yaml` — all 20+ models ranked by tier
- `profiles/amit.yaml` — weights and privacy constraints

**Real example (from rule):**
```
Task: CAD design + validation + cost estimate
  Subtask 1 (shape spec) → T1 sufficient
  Subtask 2 (validate) → T2 needed
  Subtask 3 (cost) → T1 sufficient
  Orchestrator = T2 (min of max + margin)
```

---

## Slide 11: Decision 3 — Category gate

**Slide:** "Type: script | mcp | skill | …"

**Proof:**
- `rules/03-category-gate.md` — six-question gate
- `catalog/views/tools.yaml` — every tool has a `type` field
- Query: tools by type
  ```bash
  python scripts/store.py query tools --filter "type=script" | head -3
  ```

---

## Slide 12: Decision 4 — Tool ranking

**Slide:** "Effective score: my_score × weights"

**Proof:**
- `rules/04-tool-ranking.md` — scoring formula and rubric
- `profiles/amit.yaml` — weights (score 40%, local 20%, agent_ready 15%, cost 15%, fresh 10%)
- Real decision:
  ```json
  {
    "candidates": [
      {"tool_id": "python3", "effective": 0.91, "my_score_ctx": 9.2, "samples": 14},
      {"tool_id": "bash", "effective": 0.81, "samples": 8}
    ],
    "chosen": "python3",
    "reason": "highest effective; verified 3 days ago; free/local"
  }
  ```

---

## Slide 13: Decision 5 — Outcome scoring

**Slide:** "Every task appends an outcome"

**Proof:**
- `rules/05-outcome-scoring.md` — outcome schema (result, duration, cost, score)
- `skills/toolbox-outcome/SKILL.md` — how to log outcomes
- `catalog/ledger/scores.jsonl` — real outcomes appended
  ```json
  {
    "kind": "score.outcome",
    "subject_id": "d-20260902-001",
    "payload": {
      "tool_id": "python3",
      "result": "success",
      "duration_s": 4,
      "cost_usd": 0,
      "score": 9
    }
  }
  ```

---

## Slide 14–15: Curator agents (daily/weekly)

**Slide:** "Automated discovery and validation"

**Proof:**
- `agents/toolbox-curator.md` — role definition (T1, max-turns 40)
- `skills/toolbox-curate/SKILL.md` — daily run (discover, validate), weekly run (re-score sources)
- `.github/workflows/daily-refresh.yml` — scheduled at 07:00 UTC
- Example output:
  ```
  curate: daily refresh
  
  - Discovered: pandas-polars, curl-test
  - Verified: sqlalchemy, requests
  - Closed gap: "need free OCR" → Tesseract-OCR
  ```

---

## Slide 16: Assessor agent (on-demand)

**Slide:** "Structural scoring from docs only"

**Proof:**
- `agents/toolbox-assessor.md` — role (T2, reads no code, scores 5 dimensions)
- `docs/curator.md` — rubric example (license, autonomy, cost, maturity, agent-ready)
- `catalog/evals/<tool-id>.md` — sample assessment file with rubric
- Never executes tools (see "Do not" section)

---

## Slide 17: Auditor agent (monthly)

**Slide:** "Audit for stale, licenses, regret"

**Proof:**
- `agents/toolbox-auditor.md` — role (T2, reads-only, proposes PR)
- `rules/05-outcome-scoring.md` §C — regret analysis (high cost, low score, trend down)
- Draft PR example (commit message):
  ```
  audit: monthly audit 202609 — 3 stale, 2 regret, license OK
  ```

---

## Slide 18: P4 in practice (append-only)

**Slide:** "Edit? No. Append with reason."

**Proof:**
- `rules/07-data-contract.md` (P1–P4 explained for agents)
- Example correction:
  ```bash
  # Old (wrong) event is immutable
  {"event_id": "01J…", "kind": "score.seed", "payload": {"score": 3}}
  
  # Add retraction
  python scripts/store.py append --kind score.retract \
    --subject-id <id> \
    --supersedes 01J… \
    --reason "re-assessed; score was too low"
  
  # Add new score
  python scripts/store.py append --kind score.seed \
    --subject-id <id> \
    --reason "revised estimate" \
    --payload {"score": 7}
  
  # Result: fold ignores retracted, uses new score
  ```

---

## Slide 19: Full trace example

**Slide:** "Everything is logged"

**Proof:**
```bash
/toolbox:trace d-20260902-001
```

Output shows:
- Task input + profile
- Decision 1 (swarm level + reason)
- Decision 2 (tier + reason)
- Decision 3 (type + reason)
- Decision 4 (candidates, scores, chosen, runner-up, reason)
- All outcomes so far (success/fail, scores, dates)
- Score trend (EMA, decay, human weight)
- Rules version (what version of rules were in force)

---

## Slide 20: Deployment (Docker or GitHub Actions)

**Slide:** "Self-hosted or GitHub Actions"

**Proof:**
- GitHub Actions: `.github/workflows/{daily-refresh,weekly-sources,monthly-audit}.yml` (cron-scheduled)
- Docker: `ops/Dockerfile`, `ops/docker-compose.yml`, `ops/run-task.sh`
- Local cron:
  ```bash
  # crontab -e
  0 7 * * * cd /opt/ai-toolbox && ./ops/run-task.sh daily
  ```

---

## Slide 21: Cost impact (G3 metric)

**Slide:** "≥ 40% of tasks routed to T0/T1"

**Proof:**
- `catalog/ledger/scores.jsonl` — search for `orchestrator_tier` field
  ```bash
  grep "orchestrator_tier" catalog/ledger/scores.jsonl | \
  jq -r '.payload.orchestrator_tier' | sort | uniq -c
  ```
- Phase 6 (pilot) will run a full week and measure: what % of decisions picked T0/T1?
- Goal: ≥ 40% (G3 success metric from `docs/PRD.md` §3)

---

## Slide 22: Questions?

**Live demo fallback:**
```bash
/toolbox:route rename 200 STL files by convention
/toolbox:trace <decision-id>
/toolbox:audit
```

---

## Key files to review before the talk

1. **PRD:** `docs/PRD.md` (requirements, five decisions, schemas)
2. **Rules:** `rules/0*.md` (the actual decision logic)
3. **Examples:** Real decision: `catalog/ledger/scores.jsonl` (search for "decision")
4. **Live:** `/toolbox:route`, `/toolbox:trace`, `/toolbox:audit` (commands to demo)

---

## See also

- `docs/architecture.md` — system overview
- `docs/rules.md` — how each decision works
- `docs/customer-guide.md` — user perspective
- `CLAUDE.md` — development notes
