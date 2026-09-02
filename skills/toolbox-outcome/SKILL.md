---
name: toolbox-outcome
description: Records what happened after a routed subtask ran — decision 5 of the AI Toolbox (PRD §7.5). Appends score.outcome/score.human events, never edits a score. Use right after a tool chosen by toolbox-route finishes (success, partial, or fail), and once per tool that participated.
---

# toolbox-outcome

Implements decision 5 (`docs/PRD.md` §7.5, `rules/05-outcome-scoring.md`).
Reads and writes catalog data only through `scripts/store.py` (P1/P4) —
never open a catalog data file directly.

## When to run this

After every subtask a `decision` event routed to a tool, once that subtask
is done — success, `partial`, or `fail` all count. If the subtask used more
than one tool (e.g. a fallback after escalation), record one outcome per
tool. Skip only for an L0 task (`toolbox-route` never wrote a `decision` for
it, so there's nothing to close).

## Steps

1. **Find the open decision.** You already have the `decision_id` from the
   `toolbox-route` step that routed this subtask (`d-YYYYMMDD-NNN`). If not,
   `python scripts/store.py query scores --filter kind=decision` and match
   on the task description, or check the `Stop` hook's reminder.

2. **Gather the outcome per tool that ran.** `result` (`success | partial |
   fail`), `rework` (bool — did a human/agent have to redo this by hand),
   `duration_s`, `cost_usd` (from LiteLLM if the run went through it, else
   an agent estimate — prefix the `reason` with `est:` when it's a guess),
   `score` 1–10 with a one-line justification, `task_type` if known,
   `escalated_from` (the tier that failed first, if this is a retry).

3. **Append one `score.outcome` per tool.**
   ```
   python scripts/store.py append --kind score.outcome --subject-id <decision_id> \
     --actor auto:validator --via outcome --reason "<what happened, one line>" \
     --payload '{"tool_id": "python3", "result": "success", "rework": false,
                  "duration_s": 4, "cost_usd": 0, "score": 9, "task_type": "file-batch"}'
   ```
   `actor` is `auto:<role>` for an automated check (e.g. `auto:validator` on
   an L3 subtask a Validator checked) or the acting agent's own identity —
   never `human:*` for this event kind.

4. **A human review or correction is `score.human`**, same payload shape
   minus `result`/`duration_s`/`cost_usd` (just `tool_id`, `score`, optional
   `task_type`), `actor: human:<id>`. Use this when Amit (or another user)
   scores the outcome directly — it counts 1.5× in the fold.

5. **Escalation:** if this outcome follows a failed lower-tier attempt, set
   `escalated_from` to the tier that failed and still append the failed
   attempt's own `score.outcome` first if it wasn't already recorded — don't
   let a retry erase the losing attempt's history.

6. **Wrong outcome recorded?** Never edit or re-append over it — append
   `score.retract` with `--supersedes <event_id>` and a `reason` explaining
   the correction. The fold drops it automatically.

7. **Project the views.** `python scripts/store.py project` (or
   `--collection tools` to skip the others) so `views/tools.yaml` and
   `views/scores-summary.yaml` reflect the new fold before anyone reads them.

8. **Validator auto-recording (L3 only).** When this subtask ran inside an
   L3 swarm (`rules/01-swarm-gate.md`), the Validator that checks the swarm's
   output is the one that appends the `score.outcome` for each tool used,
   with `actor: auto:validator` — this is what closes the loop without
   waiting on a human to score every subtask. The Validator still applies
   steps 2–4 above exactly as any other actor would; the only difference is
   *who* appends, not the event shape.

## Do not

- Do not edit or delete a `score.*` event to fix a mistake — `score.retract`
  only, with `supersedes` and a `reason`.
- Do not batch multiple tools' outcomes into one payload — one `score.outcome`
  event per `tool_id`.
- Do not use `human:*` as the actor on `score.outcome` — that's what
  `score.human` is for.
- Do not skip recording a `fail` — regret analysis (`rules/05-outcome-scoring.md`
  §C) needs failed outcomes at least as much as successful ones.
- Do not compute or write `my_score_current`/`verified` yourself — those are
  `store project`'s job, folded from the events you appended.
