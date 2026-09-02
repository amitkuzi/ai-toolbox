# 02 — Orchestrator model

Decision 2 of 5 (PRD §7.2). Runs after the swarm gate (L1+) — picks the model
tier for the orchestrator and, separately, for each delegated agent.

## Input

The swarm level from `01-swarm-gate.md`, the subtask breakdown (if L3), the
active profile's `privacy_default`/`budget_usd_per_task`, and `views/models.yaml`
(via `store query models`) for concrete model ids per tier.

## Tiers

| Tier | Examples | Use |
|---|---|---|
| **T0** local, $0 | `local-fast` (gemma4:12b), `local-coder` (qwen2.5-coder:14b) | Classification, summarization, extraction, routing, first drafts, anything `data_residency: local` |
| **T1** cheap cloud | Haiku 4.5, gemini-2.5-flash-lite, gpt-5-nano, GLM-4.7-Flash, deepseek-v4-flash | Well-specified subtasks, schema validation, 24/7 agents |
| **T2** mid | Sonnet 5, kimi-coder, gemini-2.5-pro | Code, research, inbox writing, orchestrator for L3 |
| **T3** frontier | Opus 5 / Fable 5 | Architecture, irreversible decisions, Validator on customer deliverables, escalation from T2 |

## Selection rules, in order — stop at the first that fixes a tier

1. **`privacy: local` ⇒ T0 only.** Hard constraint — not a preference, an
   exclusion of every other tier.
2. **Orchestrator tier = hardest subtask's tier, minus one, minimum T1 for L3.**
   The orchestrator decomposes and delegates; it doesn't need to match the
   hardest agent it's dispatching to.
3. **Agent tier by work kind:** script/mcp → T0–T1; writing/code → T2;
   judgement/final validation → T2–T3.
4. **Escalation:** fail or `partial` on first attempt ⇒ tier + 1, once,
   recorded in the outcome (`escalated_from`). Never escalate twice in a row
   without a human checkpoint.
5. **Budget:** never exceed `budget_usd_per_task`. Prefer the Batch API
   (−50%) for anything not time-critical.
6. **Cache-first:** large shared context ⇒ prefer a provider with cheap
   `cache_hit_usd_mtok`.

## Output

`orchestrator_tier`, `orchestrator_model` (a concrete id from `views/models.yaml`),
and per-agent tier, each with a one-line `tier_reason` citing which rule
fixed it. These become the `decision` event's `orchestrator_tier`/`tier_reason`
fields.

## Examples — one per rule

**Rule 1 (privacy) — "Summarize this internal HR file, must stay on-device."**
`data_residency: local` on the task ⇒ T0 only, full stop, regardless of task
difficulty. `tier_reason`: "rule 1 — local-only data, T0 hard constraint."

**Rule 2 (orchestrator = hardest − 1) — L3 task with a code subtask at T2.**
Hardest subtask is T2 (code) ⇒ orchestrator is T1 (T2 − 1), not T2. The
orchestrator only decomposes and dispatches; it isn't writing the code itself.
`tier_reason`: "rule 2 — hardest subtask T2, orchestrator T2−1 = T1."

**Rule 3 (agent tier by kind) — L3 subtask is "call the weather MCP."**
Pure MCP call, no judgement ⇒ T0–T1 agent, not T2. `tier_reason`: "rule 3 —
mcp call, no judgement required, T1."

**Rule 4 (escalation) — first pass at a code subtask on T1 returns `partial`
(tests fail).**
Retry once at T2, record `escalated_from: T1` in the outcome. Do not retry a
second time at T3 without a human checkpoint. `tier_reason`: "rule 4 —
escalated once from T1 after partial result."

**Rule 5 (budget) — a research subtask would cost $0.80 against a $0.50
task budget on T2.**
Drop to T1 or use Batch API to stay under budget, rather than exceed it
silently. `tier_reason`: "rule 5 — T2 estimate exceeds budget_usd_per_task,
switched to Batch API / T1."

**Rule 6 (cache-first) — L3 subtask re-reads a 50k-token shared spec across
5 agent calls.**
Prefer the provider with the cheapest `cache_hit_usd_mtok` for that shared
context, all else equal. `tier_reason`: "rule 6 — large shared context reused
5×, picked provider with cheapest cache-hit pricing."

## Do not

- Do not let the orchestrator match the hardest agent's tier by default —
  rule 2 explicitly subtracts one.
- Do not escalate more than once per subtask without a human checkpoint.
- Do not pick a tier above `budget_usd_per_task` and hope it's fine — switch
  tier or switch to Batch API first.
- Do not apply rule 3's kind-based defaults when rule 1's privacy constraint
  already fixed T0 — rule 1 wins outright once triggered.
