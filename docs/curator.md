# Curator, Assessor, Auditor — Automated agents guide

**Version:** 0.5 · **Date:** 2026-09-02

How the three autonomous agents keep the catalog fresh: discovering tools, validating them, and proposing improvements.

---

## Overview

Three agents run on schedules to maintain the catalog automatically:

| Agent | Schedule | What | Output |
|---|---|---|---|
| **Curator** | Daily 07:00 UTC, Weekly Mon 08:00 UTC | Discover new tools, validate old ones, close gaps | `tool.added` / `tool.status` / `gap.closed` events |
| **Assessor** | On-demand (or triggered by curator) | Score new tools from documentation | `score.seed` events + `evals/<id>.md` files |
| **Auditor** | Monthly 1st @ 09:00 UTC | Audit for stale tools, licenses, regret | Draft PR with proposed fixes |

---

## The Curator (T1, daily + weekly)

**Tier:** T1 (local/cheap) · **Max turns:** 40 · **Model:** Opus 4.8 (cost-optimized)

### Daily run (07:00 UTC)

Discovers new tools from trusted sources, validates old ones, closes gaps in one shot:

1. Query high-confidence sources (`value_score >= 3`)
2. Scan each source for new tools (PyPI, GitHub trending, ArXiv, etc.)
3. For each new tool:
   - Append `tool.added` event with reason (what source, why)
   - Append `score.seed` event with initial estimate based on rubric
4. Re-validate oldest 5 `seed-unverified` tools (spot-check docs)
5. Append `tool.status` for verified or dead tools
6. Query open gaps; try to find covering tools; append `gap.closed` if found
7. Regenerate views (`store project`)
8. Validate and commit

**Example output** (commit message):
```
curate: daily refresh

- Discovered: pandas-polars (new Python dataframe tool), curl-test (bash utility)
- Verified: sqlalchemy (still active), requests (stable)
- Closed gap: "need free OCR" → found Tesseract-OCR
```

### Weekly run (Mon 08:00 UTC)

Re-scores sources and hunts new ones:

1. Re-fetch existing sources; recompute `value_score` (1–5)
2. Append `source.revised` if score changed
3. Hunt for new sources (check tool changelogs for references)
4. For promising sources (`value_score >= 3`): append `source.added`
5. List low-scoring sources (`value_score < 2`) in commit message for Amit to review
6. Validate and commit

**Example output:**
```
curate: weekly source refresh

needs_user_action:
- source:old-api dropped to value_score:1 (no updates in 18 months)
```

---

## The Assessor (T2, on-demand or triggered)

**Tier:** T2 (mid-tier, reasoning-heavy) · **Max turns:** 60 · **Model:** Opus 5

Provides a structural assessment of new tools **without executing them**. Reads docs, GitHub activity, license, etc.

### Workflow

1. Receives tool ID from curator or manual `/toolbox:add <id>` command
2. Reads (no execution):
   - Homepage + purpose
   - README + setup instructions
   - API/CLI docs
   - License file (SPDX)
   - Changelog (maintenance velocity)
3. Scores five dimensions (1–5 each):
   - License clarity
   - Autonomy (local_capable)
   - Cost clarity
   - Maturity (years in production)
   - Agent-ready (can an LLM automate it?)
4. Writes `catalog/evals/<tool-id>.md` with rubric + evidence
5. Appends `score.seed` event (if none exists) or `score.retract` + new `score.seed` (if refining)

### Example assessment file

```markdown
# Assessment — pandas-polars

**Tool ID:** `pandas-polars`  
**Date:** 2026-09-02  
**Assessor:** agent:toolbox-assessor  
**Status:** `structural` (docs-only, no execution)

## Rubric

| Dimension | Score | Evidence |
|---|---|---|
| License clarity | 4 | MIT in repo root; permissive |
| Autonomy | 3 | Installable via pip; cloud-native optional |
| Cost clarity | 5 | Free open-source |
| Maturity | 4 | Stable since 2020; 1000+ GitHub stars |
| Agent-ready | 4 | Python API documented; CLI available |

**Weighted score:** 4.2 → assign `my_score_current: 4` in seed

## Summary

pandas-polars is a DataFrame library, mature and well-documented. Strengths: free, 
local-capable, agent-ready. Constraints: Python-only, data-in-memory limits.

## Recommendation

- **Trial scope:** data transformation, not ETL pipelines
- **First check:** performance on 1M+ row datasets
- **Risk:** memory usage can spike on large datasets
```

### When to re-assess

- Curator triggered it (new tool discovered)
- Manual `/toolbox:add <id>` command
- Scheduled (monthly before audit)
- If `score.seed` is old (> 6 months) and marked `estimate: true`

---

## The Auditor (T2, monthly 1st @ 09:00 UTC)

**Tier:** T2 (analytical, graph-oriented) · **Max turns:** 80 · **Model:** Opus 5

Monthly audit for stale tools, license compliance, and regret analysis. **Proposes** changes as a PR; humans approve/merge.

### Three audit checks

#### 1. Stale tool audit

Tools with `verified > 90 days ago`:
- Check repo activity (commits, releases, issue responses)
- If no activity in 1+ year → propose `tool.retired`
- If active → keep `verified` (next real use will refresh it)
- If concerning (deprecation warning) → propose `tool.status: dead`

#### 2. License audit

Check:
- Do tools' licenses match Amit's profile policy? (e.g. `commercial-ok`, `internal-only`)
- Are published licenses accurate vs. SPDX in `views/tools.yaml`?
- Any GPL/AGPL tools if policy doesn't allow copyleft?

Propose `tool.revised` to correct license field if mismatch.

#### 3. Regret analysis

For high-cost tools (cost > $0.10 per use):
- Gather outcomes: how many uses, average score, trend
- If average score < 5 AND trend down → flag as regret candidate
- Propose `tool.status` with `needs_investigation: true`

Also propose profile weight changes if a pattern emerges  
(e.g. "cost is over-weighted; 3 regret cases show expensive tools don't deliver").

### Output: Draft PR

Title: `audit: monthly audit <YYYYMM> — <N> stale, <M> regret, <K> license review`

Body sections:
- Stale tools (action per tool: keep/retire/re-validate)
- License audit (compliance findings)
- Regret analysis (cost-benefit flagging)
- Proposed weight changes (if any)

Human reviews and merges.

---

## Integration: curator → assessor → auditor

Typical flow:

```
Daily curator run
  ├─ Discovers new tool X
  │   Appends tool.added + score.seed (estimate: true, score 4)
  │   → Triggers assessor
  │
Assessor runs (same day or next)
  ├─ Reads docs for tool X
  │  Scores it (actual rubric)
  │  → Appends score.retract (supersedes curator's seed)
  │  → Appends score.seed (score 7, estimate: false after 5 outcomes)
  │
Later uses of tool X
  ├─ Append score.outcome events
  │   (e.g. 5 uses, scores 8, 7, 6, 9, 5)
  │   → my_score_current = EMA([8,7,6,9,5], α=0.3) ≈ 7.2
  │
Monthly auditor run
  ├─ Checks: tool X has 5 outcomes, average 7, trend flat
  │  → Keeps it (no regret)
  │
  ├─ But if tool X had low scores + high cost + trend down:
  │   → Flags for investigation in audit PR
```

---

## Running manually

Curator: `/toolbox:curate daily` or `/toolbox:curate weekly`  
Assessor: `/toolbox:add <tool-id>`  
Auditor: `/toolbox:audit`

Or via Docker:
```bash
docker compose run --rm runner         # runs daily by default
docker compose run -e TASK_TYPE=weekly --rm runner
docker compose run -e TASK_TYPE=monthly --rm runner
```

---

## Notifications

On failure (validation error, commit failure, agent error):
- **Ntfy.sh:** default, no auth required; set `NOTIFY_URL=https://ntfy.sh/ai-toolbox-<random>`
- **Slack:** optional webhook; set `SLACK_WEBHOOK=https://hooks.slack.com/...`

Check `ops/notifications.md` for setup.

---

## Calibration

### Score seed rubric (assessor)

| Score | Meaning |
|---|---|
| 8–10 | Ready for immediate trial (mature, clear cost, fits need) |
| 5–7 | Worth exploring if task matches (some uncertainty, cost/autonomy q) |
| 2–4 | Risky; docs unclear, beta, high cost, or restrictive license |
| 1 | Don't use (critical gaps in license/cost/autonomy) |

### Regret thresholds (auditor)

Flag as regret candidate when **all** of:
- Used 3+ times (sufficient data)
- Average score < 5 (below half-score)
- Cost > $0.10 per use (non-trivial)
- Trend = down (getting worse)

If 2/4 conditions: mention in PR but don't auto-flag.

---

## See also

- `agents/toolbox-curator.md`, `toolbox-assessor.md`, `toolbox-auditor.md` — agent role definitions
- `skills/toolbox-curate/SKILL.md` — skill implementation
- `.github/workflows/` — GitHub Actions schedules
- `ops/run-task.sh` — local/Docker execution
- `rules/05-outcome-scoring.md` — regret analysis details
