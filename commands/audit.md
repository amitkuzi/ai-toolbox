# `/toolbox:audit`

Run the monthly audit out-of-schedule and create a draft PR with findings.

## Usage

```
/toolbox:audit
```

or

```
/toolbox:audit --since 2026-08-01
```

## What it does

1. **Invoke auditor** (`agents/toolbox-auditor.md`)
   - Query stale tools (verified > 90 days)
   - Check licenses against profile policy
   - Analyze regret (high-cost, low-outcome tools)
   - Propose weight changes if patterns emerge

2. **Create draft PR** on branch `audit/manual-<YYYYMMDD>`
   - Title: `audit: manual audit <date>`
   - Body: stale tools, license findings, regret analysis, proposed changes

3. **Show summary** with recommendation

## Example output

```
🔍 Running audit (as of 2026-09-02)

Stale tools (verified > 90 d):
  • tool:old-api (verified 2026-05-10) → propose retire (0 uses in 4 m)
  • tool:beta-search (verified 2026-06-15) → re-check (active project)

Regret candidates (high cost, low outcome):
  • tool:premium-llm: avg score 4.2, cost $0.50/use, 8 uses, trend down
  → Propose: check whether routing rule is too aggressive

License audit:
  ✓ All tools match profile policy (commercial-ok)

Weight changes:
  Current: cost: 0.15, score: 0.40
  Proposed: cost: 0.20 (to penalize expensive options)
  Rationale: 3 regret cases suggest cost underweighted

PR: https://github.com/amitkuzi/ai-toolbox/pull/NN (draft)
```

## See also

- `/toolbox:audit --since <date>` — audit only events since a date
- `agents/toolbox-auditor.md` — audit logic
- `rules/05-outcome-scoring.md` §C — regret analysis
- `.github/workflows/monthly-audit.yml` — scheduled version
