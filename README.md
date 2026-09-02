# ai-toolbox

**An operating system for tool selection.** A self-maintaining catalog of AI tools, a five-step
cost-ordered decision gate an orchestrating agent follows before delegating work, and an
append-only, fully traceable outcome log that feeds scores back into the catalog.

Status: **v0.1.0 — skeleton. PRD and work plan approved; implementation starts at phase 0.**

| Read this | For |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | What is being built, the four data principles, the five decisions, schemas |
| [`docs/he/WorkPlan.md`](docs/he/WorkPlan.md) | Phased work plan (Hebrew) |
| [`handoffs/`](handoffs/) | Session-to-session handoff notes — start with the newest |

## The five decisions

1. **Swarm gate** — does this task need the Toolbox and a swarm of agents at all? (L0–L3)
2. **Orchestrator model** — which model tier runs the orchestrator and each agent? (T0 local → T3 frontier; never an expensive model for a light task)
3. **Category gate** — per subtask: script → mcp → skill → model → subagent, ordered by determinism and cost
4. **Tool ranking** — within the category: hard filters, then an effective score weighted by *who* is using it and *what kind* of task
5. **Outcome scoring** — every task appends an outcome; scores are computed from history, never overwritten

## The four data principles

1. Storage sits behind an abstraction (`scripts/store.py`) — files today, a database or enterprise store tomorrow.
2. Every decision and its reasoning is logged and traceable (`/toolbox:trace`).
3. Scores are additive — new events, never replaced values.
4. Data is immutable. The LLM only appends, with a timestamp and a reason.

## Layout

See `docs/PRD.md` §5.1. Empty directories carry a `.gitkeep` until their phase lands.

## License

MIT — see [LICENSE](LICENSE). The plugin is open; a user's own catalog and score ledger are theirs.
