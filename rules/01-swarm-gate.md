# 01 — Swarm gate

Decision 1 of 5 (PRD §7.1). Runs once per task, before any tool is chosen.
Decides whether the Toolbox is consulted at all, and how much delegation the
task needs.

## Input

The task as given, unmodified. No decomposition yet — that happens *after*
this gate, inside L3.

## Questions → Output: level

| Level | Condition | Effect |
|---|---|---|
| **L0 inline** | Answer from knowledge; no file output; no external service; < ~500 words | Orchestrator answers directly. Toolbox **not** consulted — no `decision` event. |
| **L1 single tool** | One subtask, deterministic or one external service | Toolbox yes, agent no. Decisions 3–4 pick a `script`/`mcp`/`skill`/`kb`. |
| **L2 single agent** | Needs judgement or writing; one domain; no independent check needed | One subagent, plus whatever tools that subagent needs. |
| **L3 swarm** | ≥ 3 subtasks across ≥ 2 categories, or parallelizable, or needs an independent Validator, or produces an `inbox/` deliverable | Decompose → parallel delegation → Validator. |

**Swarm signals** (any 2 of these push toward L3): multiple distinct outputs ·
multiple domains · multiple external services · writer/reviewer independence
required · high stakes (irreversible or customer-facing).

**Anti-default rule:** doubt between L1/L2 → pick **L1**. Doubt between L2/L3
→ pick **L2**. Under-routing is cheap to correct (escalate mid-task); over-routing
burns a subagent or a swarm you didn't need.

## Output

One of `L0 | L1 | L2 | L3`, plus a one-line `swarm_reason` — this becomes the
`decision` event's `swarm_level`/`swarm_reason` fields (skip both for L0,
since L0 writes no decision at all).

## Examples

**1. L0 — "What's the difference between TCP and UDP?"**
Answer from knowledge, no file, no service, under 500 words. `swarm_reason`:
"knowledge question, no output artifact." Toolbox not consulted.

**2. L1 — "Rename 200 STL files by convention."**
One subtask, deterministic, reproducible bit-for-bit. `swarm_reason`: "single
deterministic subtask, no external service, no judgement needed."

**3. L1/L2 boundary — "Summarize this PDF into 5 bullet points."**
One subtask, but it needs judgement (what's worth keeping) — not purely
deterministic like example 2. Only one domain, no independent check needed.
Doubt call: this is closer to L2 (judgement required) than L1, so it's **L2**,
not the anti-default L1 — the anti-default rule is for genuine ties, and
"needs judgement" is L2's own defining condition, not a tie. `swarm_reason`:
"single domain, requires judgement on relevance — L2 by definition, not a
close call."

**4. L2 — "Draft a Hebrew status report on this week's builds."**
One subagent (writing + judgement), one domain, no independent reviewer
needed for an internal draft. `swarm_reason`: "single writing task, internal
draft, no customer-facing stakes requiring a Validator."

**5. L2/L3 boundary — "Design a bracket, pick a filament, document in Hebrew."**
Three distinct outputs (CAD file, material choice, Hebrew doc) across three
domains (CAD, materials, docs) — this hits L3's own threshold (≥3 subtasks,
≥2 categories) directly, so it is **not** actually a doubt case once counted;
it's a clean L3. The boundary worth naming: if it were *two* of these (e.g.
just "design a bracket and pick a filament," no document), that's 2 subtasks,
2 domains — under L3's "≥3 subtasks" bar but hitting 2 swarm signals (multiple
domains, multiple distinct outputs) → still L3 by the signal count, not the
subtask count. `swarm_reason`: "3 subtasks, 3 domains, produces an inbox/
deliverable → Validator required."

**6. L3 — "Research 3 competitor pricing pages, compare them, write a
recommendation memo to inbox/."**
Multiple external services (3 pages) + independent output + inbox/
deliverable (customer/decision-facing) → Validator needed before it ships.
`swarm_reason`: "parallelizable research across 3 sources, inbox/ deliverable
needs independent validation before it's trusted."

## Do not

- Do not consult the Toolbox for L0 — that's the point of the gate.
- Do not decompose before this gate runs — decomposition is L3's job, not a
  prerequisite for deciding the level.
- Do not use "high stakes" as an excuse to over-route a task with one clear
  deterministic subtask (example 2) to L2/L3 — the anti-default rule cuts
  both ways, but only where there's genuine doubt.
- Do not skip writing `swarm_reason` even when the level feels obvious — it's
  what `/toolbox:trace` shows later; an unstated level is not traceable (P2).
