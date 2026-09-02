---
name: toolbox-route
description: Runs the AI Toolbox's four routing decisions (swarm level, model tier, category gate, tool ranking) before delegating any work, and logs the result as a traceable `decision` event. Use before starting any task that isn't a trivial inline answer — especially when a file, external service, or delegated agent might be involved.
---

# toolbox-route

Implements decisions 1–4 of the AI Toolbox (`docs/PRD.md` §7). Reads catalog
data only through `scripts/store.py` (P1) — never open a file under the data
directory this plugin's ledger/views live in directly.

## When to run this

Before delegating any task beyond a direct knowledge answer. If decision 1
below returns L0, stop there — most of this skill doesn't apply and no
`decision` event is written.

## Steps

1. **Load the rules.** Read, in order: `rules/00-glossary.md`, `rules/01-swarm-gate.md`,
   `rules/02-orchestrator-model.md`, `rules/03-category-gate.md`,
   `rules/04-tool-ranking.md`, `rules/07-data-contract.md`. (`rules/06-safety.md`
   applies throughout but doesn't drive a routing decision.)

2. **Load the active profile.** Default to `profiles/amit.yaml` unless the
   session names a different profile; fall back to `profiles/_default.yaml`
   if the named profile doesn't exist. This gives you `weights`, `privacy_default`,
   `license_policy`, `budget_usd_per_task`, `task_type_affinity`.

3. **Decision 1 — swarm gate** (`rules/01-swarm-gate.md`). Classify the task
   L0–L3. If **L0**: answer inline, do not continue to steps 4–8, do not
   write a `decision` event.

4. **Decompose if L3.** Break the task into subtasks only when the gate
   returned L3. L1/L2 tasks are already a single unit of work for the
   purposes of steps 5–7.

5. **Decision 2 — orchestrator model** (`rules/02-orchestrator-model.md`).
   Pick `orchestrator_tier`/`orchestrator_model` and, per subtask if L3, an
   agent tier. Query `python scripts/store.py query models --filter tier=T0`
   (repeat per tier, or query without a filter and read tiers off the result)
   for concrete model ids — never hardcode a model id from memory.

6. **Per subtask, decision 3 — category gate** (`rules/03-category-gate.md`).
   Run the six-question gate once per subtask to fix its `type`.

7. **Per subtask, decision 4 — tool ranking** (`rules/04-tool-ranking.md`).
   - Query candidates:
     `python scripts/store.py query tools --filter type=<type>` filtered to
     `review_status != dead` and (routable OR in the top-N `seed-unverified`
     slice by `published_score`, per D-008 — since `store query` doesn't
     compute this slice for you, pull the full `type` match and sort/filter
     it yourself: routable = has a `verified` date; the cold-start slice =
     the top 3 `seed-unverified` records by `published_score` among the rest).
   - Apply hard filters (§A) — license, data residency, auth, not dead.
   - Compute `effective` per surviving candidate (§B) — `my_score_ctx` is
     computed live here from `python scripts/store.py query scores --filter payload.tool_id=<id>`,
     never read off `views/tools.yaml`'s `my_score_current` (that's a
     different, global number — D-013).
   - Apply cold start (§C): a `trial_candidate`'s effective never outranks a
     routable candidate's, however it scores.
   - Record winner, runner-up, install/auth note, one-line `reason`. No
     fitting candidate ⇒ `store append --kind gap.hit ...` (or `gap.opened`
     if this gap is new), proceed with the closest fit, say so in `reason`.

8. **Print the selection table.** One row per subtask: `type`, candidates
   considered (id, effective, samples, estimate/trial flag), winner, runner-up,
   reason. This is what the human/orchestrator reads before execution starts.

9. **Write the `decision` event.**
   ```
   python scripts/store.py append --kind decision --subject-id d-<YYYYMMDD>-<NNN> \
     --actor agent:orchestrator --via route \
     --reason "<one line: what was routed and why>" \
     --payload '{"task": "...", "task_type": "...", "profile": "amit",
                  "swarm_level": "L1", "swarm_reason": "...",
                  "orchestrator_tier": "T0", "orchestrator_model": "local-fast",
                  "tier_reason": "...",
                  "subtasks": [{"id": "s1", "gate_answer": "...", "type": "script",
                                 "candidates": [...every candidate, not just the winner...],
                                 "chosen": "...", "runner_up": "...", "reason": "..."}]}'
   ```
   Do **not** pass `--rules-version` yourself — `store.py` computes it from
   `rules/VERSION` + the current git hash of `rules/` automatically (D-012).
   `decision_id` format: `d-YYYYMMDD-NNN`, `NNN` incrementing per day — check
   `python scripts/store.py query scores --filter kind=decision` if unsure
   of the next number.

10. **Proceed to execution** with the winning tool(s)/agent(s)/tier from
    the table. The `decision` event stays open until `toolbox-outcome`
    records what happened (a later skill, PRD §7.5).

## Do not

- Do not read any file under the catalog data directory directly — every
  read goes through `store query`, every write through `store append`
  (`rules/07-data-contract.md`).
- Do not write a `decision` event for an L0 task.
- Do not log only the winner — P2 requires every candidate considered, with
  its `effective` score and flags.
- Do not pass an explicit `rules_version` unless you are deliberately testing
  against a pinned version — the default computation is the source of truth.
- Do not treat this skill as optional for L1 "obviously one tool" tasks — the
  gate still runs and still writes a `decision`, even when the outcome feels
  obvious; that's what makes it traceable later.
