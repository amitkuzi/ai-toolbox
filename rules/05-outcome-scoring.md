# 05 — Outcome scoring

Decision 5 of 5 (PRD §7.5). Runs once a routed subtask finishes. Closes the
loop that `01`–`04` opened: every `decision` event should eventually get at
least one `score.outcome`, or the `Stop` hook will keep asking (`06-safety.md`).

## Input

The `decision_id` this outcome closes, the `tool_id` that ran, and what
happened: `result` (`success | partial | fail`), `rework` (bool),
`duration_s`, `cost_usd` (measured via LiteLLM when available, else an agent
estimate prefixed `est:`), a `score` 1–10 with a one-line `reason`, and
`escalated_from` if this attempt followed a failed lower tier.

## A. What to append

One event per tool per outcome — never edit, never batch multiple tools into
one payload:

```
python scripts/store.py append --kind score.outcome --subject-id <decision_id> \
  --actor auto:validator --via outcome --reason "<what happened>" \
  --payload '{"tool_id": "python3", "result": "success", "rework": false,
              "duration_s": 4, "cost_usd": 0, "score": 9, "task_type": "file-batch"}'
```

A human correction or override is `score.human` (`actor: human:<id>`, same
shape minus `result`/`duration_s`/`cost_usd`) — weighted 1.5× in the fold
because it's a stronger signal than an automated check.

**Escalation:** if the first attempt at a subtask fails or comes back
`partial`, retry once at tier + 1 (`02-orchestrator-model.md`). Record the
retry's outcome with `escalated_from: "T1"` (or whichever tier failed) —
don't silently drop the failed attempt; it still gets its own `score.outcome`
so the losing tool's history stays honest.

## B. What `store project` computes (never a caller)

Per `tool_id`, folding `score.seed` + `score.outcome` + `score.human` minus
anything named by a `score.retract`'s `supersedes`:

```
events = all score.* events for this tool_id, minus retracted, sorted by ts
if len(events) < 5:
    my_score_current = seed.score      # or the first event if no seed exists
    estimate = true
else:
    my_score_current = EMA(alpha=0.3, by ts, 90-day linear decay, human x1.5)
    estimate = false
score_samples = len(events)
score_trend   = "up" if mean(second half) > mean(first half) else "down"/"flat"
verified      = latest ts (date only) among events where kind == score.outcome
                and result == "success" — this is what makes a tool *routable*
```

This lives in `scripts/store.py`'s `_fold_scores()`/`_project_tools()` — there
is no separate `rescore.py` entry point (the PRD's file layout listed one;
the projection already satisfies P3 as an inline part of `store project`, so
a second file would just be the same fold duplicated — reconciled here rather
than built twice). `store project` writes `views/tools.yaml` and
`views/scores-summary.yaml` (the latter also breaks the fold down `by_task_type`
and `by_actor`) — nothing is written back to the ledger.

**Min-samples:** below 5 events for a tool, `my_score_current` is just the
seed estimate, flagged `estimate: true` — not routable-strength evidence yet,
only enough to rank a `trial_candidate` in decision 4's cold-start slice.

**Retraction:** `score.retract` never deletes a line — it appends a new event
whose `supersedes` names the `event_id` being withdrawn. The fold excludes
that event_id from every computation above (`my_score_current`, `samples`,
`verified`) as if it had never happened. Use this for a scored outcome that
turns out to be wrong (bad measurement, wrong tool credited), not for a
disliked-but-accurate one.

**Drop alert:** if a fresh fold drops `my_score_current` by ≥ 2 points versus
the previous `views/tools.yaml`, append a `tool.status` event with a `reason`
noting the regression — this is an append, not an edit of the number itself.

## C. Regret analysis (monthly, by the auditor — not this rule's job to run)

For each `decision` whose chosen tool's outcome was `fail`, check whether the
logged runner-up would have succeeded, per that runner-up's own history on
comparable `task_type`s. A pattern repeating ≥ 3 times against the same
profile weight is a candidate for a weight change — proposed as a PR to
`profiles/<actor>.yaml`, never auto-committed (weights are a human decision,
even when the evidence is machine-gathered).

## Worked example

Tool `python3` has one `score.seed` (score 8, migration) and three
`score.outcome`s (9, 9, 8 — all `result: success`). That's 4 samples, so
`score_samples < 5` ⇒ `my_score_current = 8` (the seed), `estimate: true`,
and `verified` is set to the date of the most recent successful outcome
(not the seed — `score.seed` never counts toward `verified`).

A fifth event lands: `score.human` (actor `human:amit`, score 10, "exactly
what I wanted"). Now `samples = 5` ⇒ real EMA kicks in. Weighted contributions
(all recent, decay ≈ 1.0): seed 8×1.0, outcomes 9×1.0, 9×1.0, 8×1.0, human
10×1.5. `alpha = 0.3`: `ema` starts at 8, folds in 9 → 8.3, 9 → 8.51, 8 → 8.36,
then the human event at weight 1.5 → `0.3·1.5·10 + (1 − 0.45)·8.36 = 4.5 +
4.6 = 9.1`. Trend: first-half mean (8, 9, 9-ish) < second-half mean (8, 10)
⇒ `up`. `estimate` flips to `false` — this tool's `my_score_current` is now
a real measurement, and it stays `verified` (routable) as long as a success
lands within the last 90 days.

## Do not

- Do not edit or delete a `score.*` line to fix a mistake — append
  `score.retract` with `supersedes` and a `reason`.
- Do not let this rule (or any agent) write `my_score_current` directly —
  it is only ever the output of `store project`'s fold.
- Do not skip an outcome for a `fail` — a failed attempt is exactly the
  signal regret analysis and the next routing decision need most.
- Do not silently drop the previous attempt's outcome on an escalation —
  both attempts get their own `score.outcome`, linked by `escalated_from`.
