# 00 — Glossary

Terms used across `rules/01`–`rules/07`. Read once per session; referenced, not repeated.

| Term | Meaning |
|---|---|
| **swarm level (L0–L3)** | Output of `01-swarm-gate.md`. How much delegation a task needs: L0 = orchestrator answers inline, no Toolbox; L1 = one tool, no agent; L2 = one subagent; L3 = decomposed swarm with a Validator. |
| **tier (T0–T3)** | Output of `02-orchestrator-model.md`. Which model class runs the orchestrator or an agent: T0 local/free, T1 cheap cloud, T2 mid, T3 frontier. Defined per model in `views/models.yaml`. |
| **category** (gate output) | Output of `03-category-gate.md`, per subtask: `kb \| schedule \| script \| mcp \| skill \| model \| subagent`. Not the same as a tool's `category` field (§6.1 of the PRD, which is a domain tag for shortlisting) — this is the *gate's* output vocabulary. |
| **candidate** | A tool that reached decision 4's ranking step for a subtask, whether it wins or not. `04-tool-ranking.md`'s output logs **every** candidate, not just the winner (PRD P2). |
| **routable** | A tool with a `verified` date (ran once on a real subtask, not stale) — eligible for normal ranking. |
| **seed-unverified** | A tool discovered but never run; `review_status: seed-unverified`, no `verified` date. Not routable on its own — enters ranking only as a bounded `trial_candidate` (D-008, see `04-tool-ranking.md` §C). |
| **effective score** | The single number decision 4 ranks candidates by — `04-tool-ranking.md`'s weighted sum of `my_score_ctx`, `local_capable`, `agent_ready`, cost rank, and freshness. |
| **`my_score_current`** | ⚙ Global, task-type-agnostic fold of a tool's (or model's) `score.*` events — EMA α=0.3, 90-day decay, human×1.5. Computed once by `store project`, shown in `views/tools.yaml`/`views/scores-summary.yaml`. Never computed by a rule file directly. |
| **`my_score_ctx`** | Per-query, task-type-weighted mean of the same events (1.0/0.5/0.25 by task-type match), computed live by `04-tool-ranking.md` at query time. Distinct from `my_score_current` (PRD D-013) — never stored in a view. |
| **decision** | One `store append --kind decision` event per routed task (PRD §6.3). Carries swarm level, tier, and every subtask's candidates/winner/reason. What `/toolbox:route` writes and `/toolbox:trace` reads back. |
| **profile** | `profiles/<actor>.yaml` — the acting human's weights, privacy default, license policy, budget, task-type affinity. Read by decision 4 (weights) and decision 1/3 (privacy). |
| **task type** | One tag from the PRD §6.4 vocabulary (`file-batch`, `code-python`, `hebrew-report`, `cad`, …) assigned to a task/subtask. Drives `my_score_ctx`'s relevance weighting and the profile's `task_type_affinity`. |
| **gap** | A subtask that reached decision 3 or 4 with no fitting candidate. Logged via `gap.opened`/`gap.hit`, shown in `views/gaps.md`. Not a failure to route — routing still proceeds with the closest fit. |

See `docs/schema.md` for the full event/payload shapes these terms map to, and
`docs/PRD.md` §7 for the five decisions these rule files implement.
