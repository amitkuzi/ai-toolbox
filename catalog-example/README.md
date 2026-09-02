# catalog-example

Example catalog for the public AI Toolbox plugin. Contains 5–10 sample tools for demonstration.

**Use this if:** you're installing the plugin and want to try it without a custom catalog.

**Replace this if:** you have your own tool catalog (point `TOOLBOX_BASE_DIR` to your catalog directory).

---

## Contents

- `ledger/` — append-only event log (tools, scores, sources, gaps)
  - `tools.jsonl` — sample tools (python3, bash, pandas, etc.)
  - `sources.jsonl` — sample sources (PyPI, GitHub trending)
  - `models.jsonl` — sample models (T0–T3)
  - `scores.jsonl` — sample outcomes for demo

- `views/` — generated projections (run `store project` to regenerate)
  - `tools.yaml` — human-readable tool listing
  - `sources.yaml` — source quality scores
  - `models.yaml` — model rankings
  - `scores-summary.yaml` — outcome trends

- `evals/` — assessor evaluation files (one per tool)

---

## Use with the plugin

```bash
# Default: uses catalog-example/ from the installed plugin
/toolbox:route rename 200 files

# Or explicitly:
python scripts/store.py query tools --base-dir ./catalog-example
```

---

## Replace with your own catalog

If you have a private catalog repository:

```bash
# Clone your private catalog
git clone https://github.com/you/your-catalog private-catalog

# Point the plugin to it
export TOOLBOX_BASE_DIR=./private-catalog

# Now all queries use your real catalog
/toolbox:route <task>
```

---

## See also

- `docs/customer-guide.md` — installation instructions
- `docs/catalog-split.md` — public vs. private catalog setup
