# `/toolbox:add <tool-id>`

Manually add a new tool to the catalog and trigger an assessment.

## Usage

```
/toolbox:add python-polars
```

## What it does

1. **Validate** the tool exists (homepage/repo is reachable)
2. **Invoke assessor** (`agents/toolbox-assessor.md`)
   - Read docs, compute structural score
   - Write `evaluation file (evals/ directory)`
   - Append `score.seed` event
3. **Show summary** with recommendation and next steps

## Example output

```
✅ Tool added: python-polars

License:   MIT ✓
Autonomy:  local ✓
Cost:      free ✓
Maturity:  stable ✓
Agent-ready: yes ✓

Score: 9/10 (recommended for immediate trial)
Eval: evals/python-polars.md (assessment file)

Next: Use in a real task, then run /toolbox:outcome to log results.
```

## See also

- `/toolbox:assess <tool-id>` — re-assess an existing tool
- `/toolbox:audit` — monthly audit
- `agents/toolbox-assessor.md` — assessment logic
