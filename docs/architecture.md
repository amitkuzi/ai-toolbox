# Architecture — AI Toolbox Plugin

**Version:** 0.5 · **Date:** 2026-09-02

## System overview

AI Toolbox is an operating system for tool selection. It unifies three things:
1. **A catalog** — tools, sources, models (append-only ledger + computed views)
2. **Decision rules** — five routing decisions encoded as Markdown (swarm level, model tier, category, tool ranking, outcome scoring)
3. **A feedback loop** — every decision and outcome is logged; scores improve over time

The whole system lives in one installable Claude Code plugin (skills + agents + commands + hooks + data).

---

## Core principles (P1–P4)

| # | Principle | Mechanism |
|---|---|---|
| **P1 — Storage abstraction** | Catalog data is never accessed directly; only through `Store` (`scripts/store.py`) | Backends: files (JSONL), SQLite, Postgres (future). Switch with `--backend` flag. |
| **P2 — Full traceability** | Every decision logs its task, profile, rules version, all candidates, winner, and reasoning | `/toolbox:trace <decision_id>` prints the full chain → outcomes → score impact |
| **P3 — Additive scores** | Scores are immutable events, never edited; `my_score_current` is a computed fold | New events: `score.seed`, `score.outcome`, `score.human`. Corrections: `score.retract`. |
| **P4 — Immutable data** | The ledger is append-only; every event carries `ts`, `actor`, `via`, `reason` | CI fails if a ledger line is deleted/modified or if an event lacks required fields. |

---

## Data model (event-sourced)

```
┌─ Ledger (source of truth) ──────────────┐
│ ledger/                                 │
│  ├─ tools.jsonl (tool.added/revised)   │
│  ├─ sources.jsonl (source.added)       │
│  ├─ models.jsonl (model.added)         │
│  ├─ scores.jsonl (decision + scores)   │
│  ├─ decisions.jsonl (ADRs)             │
│  └─ gaps.jsonl (gap.opened/closed)     │
│                                         │
│ Every line is immutable; only append.  │
└─────────────────────────────────────────┘
         ↓ (Store.project)
┌─ Views (computed projections) ──────────┐
│ views/                                  │
│  ├─ tools.yaml (current state per tool) │
│  ├─ sources.yaml (source quality)       │
│  ├─ models.yaml (model rankings)        │
│  ├─ scores-summary.yaml (trends)        │
│  ├─ decisions.md (decision log)         │
│  └─ gaps.md (open/closed gaps)          │
│                                         │
│ Never edited by hand; always derived.  │
└─────────────────────────────────────────┘
```

---

## Runtime flow (five decisions)

```
Task arrives
  ↓
[SessionStart hook]
  Load profile (weights, privacy, budget)
  ↓
skill: toolbox-route
  ┌─ Decision 1: Swarm gate (L0–L3?)
  │   L0 → answer inline, stop
  │   L1–L3 → continue
  │
  ├─ Decision 2: Orchestrator model (T0–T3?)
  │   Pick model tier for this task
  │
  ├─ Decision 3: Category gate (type of work?)
  │   script | mcp | skill | subagent | model | schedule | kb
  │
  ├─ Decision 4: Tool ranking (which tool?)
  │   Score all candidates (effective = score × weights)
  │   Pick highest; log all candidates
  │
  └─ Append decision event (with full reasoning)
  ↓
[Execution]
  Run the chosen tool
  ↓
[SubagentStop/Stop hooks]
  Remind to close the decision
  ↓
skill: toolbox-outcome
  └─ Decision 5: Outcome scoring
     Gather result, cost, duration, score
     Append score.outcome event
  ↓
[Curator runs (daily/weekly/monthly)]
  skill: toolbox-curate
  └─ Discover new tools, validate stale ones, close gaps
  ↓
[Auditor runs (monthly)]
  agent: toolbox-auditor
  └─ Audit for stale, licenses, regret; propose improvements
```

---

## File structure

```
ai-toolbox/
├── skills/                         # Reusable workflows
│   ├── toolbox-route/              # Decisions 1–4 (before delegation)
│   ├── toolbox-outcome/            # Decision 5 (after completion)
│   └── toolbox-curate/             # Daily/weekly discovery & validation
│
├── agents/                         # Autonomous agents (T1/T2)
│   ├── toolbox-curator.md          # Discovers, validates
│   ├── toolbox-assessor.md         # Scores new tools (docs-only)
│   └── toolbox-auditor.md          # Monthly audit & regret analysis
│
├── commands/                       # Manual entry points
│   ├── route.md                    # /toolbox:route <task>
│   ├── outcome.md                  # /toolbox:outcome <decision>
│   ├── add.md                      # /toolbox:add <tool-id>
│   ├── audit.md                    # /toolbox:audit [--since <date>]
│   └── ... (gaps, trace, project)
│
├── hooks/                          # Event triggers
│   ├── hooks.json                  # Register hooks
│   └── remind_outcome.py           # Remind to close open decision
│
├── rules/                          # Decision logic (P1–P4 binding)
│   ├── 00-glossary.md
│   ├── 01-swarm-gate.md            # Decision 1
│   ├── 02-orchestrator-model.md    # Decision 2
│   ├── 03-category-gate.md         # Decision 3
│   ├── 04-tool-ranking.md          # Decision 4
│   ├── 05-outcome-scoring.md       # Decision 5
│   ├── 06-safety.md
│   └── 07-data-contract.md         # P1–P4 for agents
│
├── catalog/
│   ├── ledger/                     # Source of truth (append-only)
│   │   ├── tools.jsonl
│   │   ├── sources.jsonl
│   │   ├── models.jsonl
│   │   ├── scores.jsonl
│   │   ├── decisions.jsonl
│   │   └── gaps.jsonl
│   │
│   ├── views/                      # Projections (generated)
│   │   ├── tools.yaml
│   │   ├── sources.yaml
│   │   ├── models.yaml
│   │   ├── scores-summary.yaml
│   │   ├── decisions.md
│   │   └── gaps.md
│   │
│   └── evals/                      # Assessor output
│       └── <tool-id>.md
│
├── profiles/                       # User preferences
│   ├── _default.yaml
│   └── amit.yaml                   # Amit's weights, privacy, budget
│
├── scripts/
│   ├── store.py                    # Catalog Store (append/query/project/trace)
│   ├── backends/                   # Storage backends
│   │   ├── files.py               # JSONL + YAML
│   │   └── sqlite.py              # SQLite (alternate)
│   └── validate.py                # CI gate (schema + append-only + P1–P4)
│
├── .github/workflows/
│   ├── daily-refresh.yml
│   ├── weekly-sources.yml
│   └── monthly-audit.yml
│
├── ops/                           # Self-hosted scheduling
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── run-task.sh
│   └── notify.sh
│
├── docs/
│   ├── PRD.md                     # Product requirements
│   ├── architecture.md            # This file
│   ├── rules.md                   # How rules work
│   ├── curator.md                 # Curator/assessor/auditor guide
│   ├── profiles.md                # Profile config
│   ├── customer-guide.md          # Installation + first steps
│   ├── storage.md                 # Store contract
│   ├── licenses.md                # License audit results
│   ├── lecture-kit.md             # Slide ↔ code linkage
│   └── he/                        # Hebrew versions
│       ├── PRD.md
│       └── WorkPlan.md
│
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
│
├── README.md
├── CHANGELOG.md
├── LICENSE (MIT)
└── CLAUDE.md (operating notes)
```

---

## Design decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Packaging** | Claude Code plugin (skills + agents + commands + hooks + data) | Installable, portable, no external service |
| **Decision engine** | Markdown rules (LLM-interpreted) | Transparent, versionable, human-auditable; deterministic CLI optional in V2 |
| **Scheduled curator** | GitHub Actions + Docker alternative | GitHub for public repo; Docker for self-hosted |
| **Data model** | Event-sourced (append-only ledger + projections) | Immutable, auditable, supports multi-backend, replayable |
| **Licensing** | Plugin code MIT; Amit's catalog private | Distributable plugin; private score data stays private |

---

## P1–P4 in practice

**P1 — Storage abstraction:** A skill never opens `catalog/` directly. All access goes through `Store` (4 ops: append, query, project, trace). Switching backends = changing `--backend` flag; skills don't change.

**P2 — Traceability:** Every `decision` event logs:
- Task input and profile
- Rules version (semver + git hash)
- All candidates per subtask with scores and reasoning
- Winner + runner-up
- Free-text `reason` field

**P3 — Additive scores:** No editable `my_score_current` field. Scores are immutable events; `my_score_current` is computed (EMA + decay + human weight) by `Store.project()`.

**P4 — Immutable ledger:** No skill, agent, or command ever edits an existing line. All "updates" are new events (`tool.revised`, `score.retract`, etc.) referencing the original `event_id`. CI fails if diff has `-` lines.

---

## Boundaries: what this solves, what it doesn't

**Solves:**
- ✅ Cost reduction (route to T0/T1 instead of frontier)
- ✅ Reproducible decisions (rules are versioned, decisions are logged)
- ✅ Feedback loop (scores improve from real outcomes)
- ✅ Audit trail (trace any decision back to the data in force)
- ✅ Pluggable storage (same ledger, different backends)

**Not in V1:**
- ❌ HTTP router service (Markdown rules work; deterministic API optional in V2)
- ❌ Web UI (CLI + commands only)
- ❌ Fine-tuning (scores feedback into orchestrator choices, not model weights)
- ❌ Real-time streaming (batch curator runs)

---

## Extending the system

### Add a new storage backend

Write `scripts/backends/postgres.py` implementing the same `Backend` interface as `files.py` and `sqlite.py`. Update `scripts/store.py`'s `BACKENDS` dict. Contract test runs identically against all backends.

### Add a new decision rule

1. Create `rules/NN-new-decision.md` (numbered, in read order)
2. Update `rules/VERSION` (bump semver)
3. Reference it in the appropriate skill
4. Every `decision` event will carry the new `rules_version` hash automatically

### Add a new agent role

1. Create `agents/toolbox-newrole.md` with tier, max-turns, tool allowlist
2. Invoke via `.github/workflows/` or CLI command
3. Agent appends events only; never edits

---

## See also

- `docs/PRD.md` — requirements and data schemas
- `docs/rules.md` — how each decision rule works
- `rules/` — the actual decision logic
- `scripts/store.py` — the Catalog Store implementation
- `CLAUDE.md` — operating notes for developers
