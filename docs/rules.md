# Rules — Decision logic in AI Toolbox

**Version:** 0.5 · **Date:** 2026-09-02

The five routing decisions are encoded as Markdown rules (human-readable, versioned, auditable).
Every time a task is routed, the LLM reads these rules, applies them step by step, and logs the result
as a `decision` event with full reasoning.

---

## The five decisions (read order)

```
Task arrives → Load rules/ (00–07) + profile → Decision 1–5 → Append decision event
```

### Decision 1: Swarm gate (rules/01-swarm-gate.md)

**Question:** How many agents should handle this?

**Levels:**
- **L0** — Trivial inline answer (knowledge, quick lookup, no delegation)  
  → Answer now; stop; no decision event written
- **L1** — Single deterministic subtask (one agent, one tool, predictable)  
  → Route and execute
- **L2** — Multi-step workflow (routing required; agent may escalate mid-task)  
  → Route; prepare fallback
- **L3** — Complex, unpredictable (multiple agents, reasoning, judgment calls)  
  → Orchestrator routes, swarm runs in parallel, Validator reviews output

**Examples:**
- L0: "What's the capital of France?" → Answer inline
- L1: "Rename 200 STL files by convention" → Route to script or T0 agent
- L2: "Summarize this 50-page PDF and extract key decisions" → Route to summarizer
- L3: "Design a CAD model for a 3D-printed part; validate for manufacturability; estimate cost" → Swarm

---

### Decision 2: Orchestrator model (rules/02-orchestrator-model.md)

**Question:** Which model should orchestrate this task?

**Tiers (cost ascending):**
- **T0** — Local, free (Python, Bash, local tools)
- **T1** — Cheap cloud (Haiku, smaller open-source)
- **T2** — Mid-tier (Sonnet, GPT-4, balanced cost/capability)
- **T3** — Frontier (Opus, latest, expensive, best reasoning)

**Rules:**
1. Match subtask complexity to model tier
2. Respect privacy constraint (if data is sensitive, stay T0/local)
3. Budget cap (if task will cost > limit, downgrade tier or fall back)
4. Profile affinity (user's typical patterns boost preferred tier)

**Reasoning:**
- Simplest subtask's tier sets the floor (don't over-orchestrate)
- Most complex subtask's tier sets the ceiling (don't under-power)
- Aggregate tier = weighted by subtask complexity

**Example:** CAD design task:
- Subtask 1 (shape spec) → T1 sufficient  
- Subtask 2 (validate manufacturability) → T2 needed  
- Subtask 3 (estimate cost) → T1 sufficient  
→ Orchestrator = T2 (min of max + safety margin)

---

### Decision 3: Category gate (rules/03-category-gate.md)

**Question:** What type of work is this subtask?

**Categories (per subtask):**
- **script** — Bash, Python, shell commands
- **mcp** — Model Context Protocol (AI-native tool)
- **skill** — Claude Code skill (built-in or plugin)
- **subagent** — Autonomous agent (Implementor, Researcher, etc.)
- **model** — Direct LLM call (no tools, just reasoning)
- **schedule** — Cron, periodic task (curator, auditor runs)
- **kb** — Knowledge base query or context retrieval

**Gate (yes/no questions per subtask):**
1. Is the work procedural/deterministic? → **script**
2. Is it human-like reasoning? → **model** or **skill**
3. Does it need autonomy (multiple decisions)? → **subagent**
4. Is it a real-time tool/API? → **mcp**
5. Is it routine/scheduled? → **schedule**
6. Is it knowledge-heavy? → **kb**

---

### Decision 4: Tool ranking (rules/04-tool-ranking.md)

**Question:** Which specific tool should run?

**Scoring:**
1. Filter candidates by `type` (from decision 3)
2. Hard filter: `review_status != dead`, prefer `verified` over `seed-unverified`
3. Soft score (1–10 per dimension):
   - `my_score_current` (outcome history, EMA-smoothed) — 40% weight
   - `local_capable` (local runtime available) — 20%
   - `agent_ready` (CLI/API for agents) — 15%
   - `cost` (free > cheap > metered > paid) — 15%
   - `fresh` (recently verified) — 10%

4. Compute `effective_score = my_score * sum(weights)` per tool
5. Pick highest; log runner-up and all candidates

**Context:** Scores are task-type-weighted. A tool's `my_score_current` is global; `my_score_ctx` is re-weighted per this task's `task_type_affinity`.

**Example ranking:**
```
script | type-filtered candidates:
├─ python3:        my_score: 9.2, local: yes, cost: free     → effective: 0.92
├─ bash:           my_score: 8.5, local: yes, cost: free     → effective: 0.85
├─ powershell:     my_score: 6.0, local: yes, cost: free     → effective: 0.60
└─ something-else: my_score: 4.0, local: no,  cost: paid      → effective: 0.38

→ Pick python3 (winner), bash (runner-up), log all 4
```

---

### Decision 5: Outcome scoring (rules/05-outcome-scoring.md)

**Question:** How well did the tool do?

**Events:**
- `score.outcome` — automatic measurement (result, duration, cost, automated score)
- `score.human` — human review (Amit rates the outcome, counts 1.5× in fold)
- `score.retract` — correction (if the outcome was wrong, supersede it)

**Fold:** `my_score_current` = EMA(outcomes, α=0.3) + decay(90 days) + human × 1.5

**Thresholds:**
- ✅ score ≥ 7 → green (good)
- ⚠ 4–6 → yellow (investigate)
- ❌ < 4 → red (regret candidate; consider delisting)

**Regret analysis:** Tools with high cost + low average score + declining trend → flag for audit.

---

## Supporting rules

### Rule 00: Glossary (rules/00-glossary.md)

Defines terms (L0–L3, T0–T3, swarm, tier, profile, etc.) so rules are unambiguous.

### Rule 06: Safety (rules/06-safety.md)

Guardrails:
- No delegation for high-risk tasks (sensitive PII, destructive ops) without human approval
- Escalation protocol (if a tier fails, move up; log the failure)
- Privacy constraints (respect `data_residency` and `license_policy`)

### Rule 07: Data contract (rules/07-data-contract.md)

Bindings for all agents and skills:
- ✅ May: append events via `store.py`, read rules/profiles, query views
- ❌ Cannot: edit ledger/views, hardcode catalog paths, edit existing events
- 📋 Must: every event has `ts`, `actor`, `via`, `reason`

---

## Version and hash

Every `decision` event carries a `rules_version` field:

```
rules_version: "1.0.0+a1b2c3"
```

Where:
- `1.0.0` = semver in `rules/VERSION` (hand-bumped)
- `a1b2c3` = short git hash of the `rules/` tree

If rules change, version and hash change; old decisions are still auditable ("what rules were in force when this decision was made?").

---

## How to read a decision event

Example:

```json
{
  "event_id": "01J...",
  "ts": "2026-09-02T10:00:00Z",
  "kind": "decision",
  "subject_id": "d-20260902-001",
  "actor": "agent:orchestrator",
  "via": "route",
  "reason": "User task: 'rename STL files by convention'",
  "payload": {
    "task": "rename 200 STL files by convention",
    "task_type": "file-batch",
    "profile": "amit",
    "swarm_level": "L1",
    "swarm_reason": "single deterministic subtask, no external service",
    "orchestrator_tier": "T0",
    "orchestrator_model": "local-fast",
    "tier_reason": "hardest subtask is script → T0; privacy local",
    "subtasks": [
      {
        "id": "s1",
        "gate_answer": "Q1 yes — reproducible",
        "type": "script",
        "candidates": [
          {
            "tool_id": "python3",
            "effective": 0.91,
            "my_score_ctx": 9.2,
            "samples": 14
          },
          {
            "tool_id": "powershell",
            "effective": 0.74,
            "my_score_ctx": 7.0,
            "samples": 3,
            "estimate": true
          }
        ],
        "chosen": "python3",
        "runner_up": "powershell",
        "reason": "highest effective; verified 12 d ago; free/local"
      }
    ],
    "rules_version": "1.0.0+a1b2c3"
  }
}
```

**Read it:**
- Task: "rename 200 STL files"
- Level: L1 (single subtask, deterministic)
- Model: T0 (local; privacy and complexity allow it)
- Subtask s1: chose python3 (9.2 score, verified) over powershell (7.0, estimate)
- Rules version: 1.0.0 + git hash (for audit trail)

---

## Extending rules

To add a new decision rule (e.g. Decision 6):

1. Create `rules/06-new-decision.md` (increment number, keep read order)
2. Bump `rules/VERSION` (e.g. 1.0.0 → 1.1.0)
3. Update the skill/agent that uses it (e.g. `skills/toolbox-route/SKILL.md`)
4. Next decision event will have the new `rules_version` automatically

The rules are **binding** per `docs/PRD.md` §1a. Skills must read and follow them.

---

## See also

- `rules/` directory (the actual Markdown rules)
- `docs/PRD.md` §1–5 (requirements behind each rule)
- `docs/architecture.md` (system overview)
- `skills/toolbox-route/SKILL.md` (implements rules 1–4)
- `skills/toolbox-outcome/SKILL.md` (implements rule 5)
