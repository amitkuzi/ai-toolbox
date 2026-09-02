# 04 — Tool ranking

Decision 4 of 5 (PRD §7.4). Runs once per subtask, after `03-category-gate.md`
has fixed the `type`. Picks which specific tool of that type wins.

## Input

The subtask's `type` (from decision 3), its `task_type` tag if known, the
active profile (weights, `license_policy`, privacy default), and the
candidate list from `store query tools --routable` **plus** a bounded slice
of top-N (default 3) `seed-unverified` candidates by `published_score`,
each flagged `estimate: true` / `trial_candidate: true` (D-008 — this is what
makes cold start reachable at all; see §C).

## A. Hard filters — fail any ⇒ excluded

- `license` compatible with the profile's `license_policy`
- `data_residency` compatible with the task's privacy requirement
- `auth` available in this environment (otherwise flag "needs user action",
  never silently choose it)
- `review_status != dead`

## B. Effective score

```
effective = w_score · my_score_ctx
          + w_local · local_capable
          + w_agent · agent_ready
          + w_cost  · (1 − cost_rank/3)        # free=0 included=1 metered=2 paid=3
          + w_fresh · fresh(verified)          # 1.0 if < 30 d, linear to 0 at 90 d
```

`w_*` come from the active profile (`profiles/<actor>.yaml`).

**`my_score_ctx`** (D-013 — distinct from `views/tools.yaml`'s `my_score_current`,
never stored, computed live here): weighted mean of this tool's outcome
scores — same `task_type` × 1.0, adjacent × 0.5, any × 0.25 — with `human:*`
events × 1.5 and 90-day decay. If `score_samples < 5`, fall back to the
catalog's seed `my_score`, flagged `estimate: true`. `my_score_current`
(§6.1 of the PRD) is the other number: a global, task-type-agnostic EMA fold
computed once by `store project` and shown in views — the two never get
confused because `my_score_ctx` is never written to a view at all.

## C. Cold start

Unchanged from `selection-rules.md` §2a: an estimate never outranks a
measurement. A `trial_candidate` (D-008's bounded slice) computes an
`effective` score exactly like any other candidate, but even if that score
is numerically higher than a routable candidate's, it does **not** win —
it is logged as the runner-up and offered as a bounded trial (one low-stakes
subtask against the incumbent) instead. `published_score` ranks which
`seed-unverified` tools make it into that top-N slice in the first place —
it is never itself the ranking signal used against routable candidates.

## Output

Winner, runner-up, one-line install/auth note, `reason` — and (P2) **every**
candidate considered, each with its `effective`, `my_score_ctx`, `samples`,
and `estimate`/`trial_candidate` flags. No candidate fits ⇒ increment
`gaps.md` (`gap.hit`), proceed with the closest fit, state the compromise.

## Worked example — real records from `views/tools.yaml`

Subtask: "rename 200 STL files by convention" (`type: script`, from decision 3).
Weights from `profiles/amit.yaml`: `score 0.40, local 0.20, agent_ready 0.15,
cost 0.15, fresh 0.10`. Today: 2026-09-02.

| Candidate | `my_score_ctx` | `local` | `agent_ready` | `cost` (free→0) | `verified` | `fresh` |
|---|---|---|---|---|---|---|
| `python3` | 10 (samples=1<5, estimate) | 1 | 1 | 0 | 2026-08-13 (20d ago) | 1.0 |
| `git` | 10 (samples=1<5, estimate) | 1 | 1 | 0 | 2026-08-13 (20d ago) | 1.0 |
| `ollama` | 9 (seed, `trial_candidate`) | 1 | 1 | 0 | none | 0.0 |

```
effective(python3) = 0.40·10 + 0.20·1 + 0.15·1 + 0.15·1 + 0.10·1.0
                    = 4.00 + 0.20 + 0.15 + 0.15 + 0.10 = 4.60
effective(git)      = identical inputs = 4.60
effective(ollama)   = 0.40·9 + 0.20·1 + 0.15·1 + 0.15·1 + 0.10·0.0
                    = 3.60 + 0.20 + 0.15 + 0.15 + 0.00 = 4.10
```

`python3` and `git` **tie exactly** — both `verified`, `free`, `local_capable`,
`agent_ready`, same seed score. The formula alone doesn't break the tie
because neither candidate's `task_types` field is populated yet (a known
migration gap, not a rules bug — see `handoffs/2026-09-02-phase1-done.md`
judgement call 3). Fall back to `purpose`/`domains` fit as the tie-break of
last resort: `python3`'s purpose ("file generation, validation") fits a
file-rename subtask; `git`'s does not. **Winner: `python3`.** `ollama` is a
`trial_candidate` (cold start, C) — its `effective` is lower here anyway, but
per rule C it would not have won even if higher, since it's an estimate
against two measurements.

`reason`: "highest effective among fitting candidates; tied with `git` on the
formula, broken by purpose fit; `ollama` considered as cold-start trial
candidate, not selected — estimate vs. two verified measurements."

## Do not

- Do not let a `trial_candidate`'s `effective` outrank a routable candidate's
  — cold start never wins outright, only earns a bounded trial slot.
- Do not compute `my_score_ctx` from `views/scores-summary.yaml` — that view
  holds `my_score_current` (global). `my_score_ctx` is task-type-scoped and
  must be computed live from `store query scores`.
- Do not silently drop a subtask with no fitting candidate — log the gap,
  proceed with the closest fit, and say so in `reason`.
- Do not treat an identical-formula tie as license to skip a tie-break —
  fall back to `purpose`/`domains` fit and say so, rather than picking
  arbitrarily.
