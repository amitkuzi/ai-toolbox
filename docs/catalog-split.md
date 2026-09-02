# Catalog split — Public vs. private

**Version:** 0.5 · **Date:** 2026-09-02

How to separate the public plugin (catalog-example) from Amit's private catalog (ai-toolbox-catalog repo).

---

## Overview

AI Toolbox ships as two separate repos:

| Repo | Public | Contents | Access |
|---|---|---|---|
| **amitkuzi/ai-toolbox** | ✅ Yes | Plugin (skills, agents, commands, rules, store, ops, docs), example catalog with 5–10 sample tools | GitHub public |
| **amitkuzi/ai-toolbox-catalog** | ❌ Private | Real catalog (72 tools, real sources, score history, real eval results) | Private (Amit only) |

The plugin can point to either catalog (configuration step).

---

## What goes in each repo

### Public (amitkuzi/ai-toolbox)

**Keep:**
- `skills/` — all skills (toolbox-route, toolbox-outcome, toolbox-curate)
- `agents/` — all agent definitions
- `commands/` — all command definitions
- `hooks/` — all hooks
- `rules/` — all decision rules
- `scripts/` — store.py, backends, validate.py
- `ops/` — Docker, cron setup
- `.github/workflows/` — CI validation
- `docs/` — all documentation (PRD, architecture, rules, guides)
- `profiles/_default.yaml` — shared default profile

**Replace:**
- `catalog/ledger/` → `catalog-example/ledger/` (5–10 sample tools, no real scores)
- `catalog/views/` → `catalog-example/views/` (generated from sample ledger)
- `profiles/amit.yaml` → remove (private to user, not part of public plugin)

**Remove:**
- Amit's real `catalog/ledger/scores.jsonl` (real scores, privacy)
- Amit's real `catalog/ledger/tools.jsonl` (all 72 tools, real details)
- Session handoffs (internal notes)

### Private (amitkuzi/ai-toolbox-catalog)

**Keep:**
- `ledger/` — all events (tools, scores, decisions, gaps, sources, models)
- `views/` — generated projections
- `evals/` — assessor evaluation files
- `profiles/amit.yaml` — personal config

**Share with plugin repo via git submodule (optional, Phase 6+):**
- `docs/` — any private notes
- `scripts/` — custom backends or extensions

---

## Setup (for a new user)

### Step 1: Clone the public plugin

```bash
git clone https://github.com/amitkuzi/ai-toolbox ~/.claude/plugins/ai-toolbox
cd ~/.claude/plugins/ai-toolbox
```

### Step 2: Initialize catalog-example (demo data)

The `catalog-example/` directory is included in the public repo. Sample tools:
- python3 (local script runtime)
- bash (local script runtime)
- pandas (Python library)
- nodejs (local runtime)
- claude (model, via API)

### Step 3: Use catalog-example or bring your own

**Option A: Use the example (default)**
```bash
python scripts/store.py query tools --base-dir catalog-example
```

**Option B: Link to your private catalog**
```bash
# Clone or link to your private catalog repo
git clone https://github.com/youruser/your-catalog private-catalog

# Point store.py to it
export TOOLBOX_BASE_DIR=./private-catalog

# Now queries use your real tools
python scripts/store.py query tools --base-dir ./private-catalog
```

---

## Migration (Amit → public release)

When releasing v1.0.0:

1. **Create the split:**
   ```bash
   # In amitkuzi/ai-toolbox (public)
   rm -rf catalog/ledger catalog/views  # remove private data
   mkdir -p catalog-example/ledger
   
   # Copy 5–10 public tools to catalog-example
   cp catalog/ledger/{sample-tools,sample-scores}.jsonl catalog-example/ledger/
   
   # Generate views from example ledger
   python scripts/store.py project --base-dir catalog-example
   ```

2. **Create private repo:**
   ```bash
   # In amitkuzi/ai-toolbox-catalog (private)
   git init
   mkdir -p ledger views evals
   
   # Move Amit's real catalog here
   cp -r /path/to/real/catalog/ledger/* ledger/
   cp -r /path/to/real/catalog/views/* views/
   cp -r /path/to/real/catalog/evals/* evals/
   ```

3. **Test both:**
   ```bash
   # Public version works with example
   cd ~/amitkuzi/ai-toolbox
   python scripts/store.py query tools --base-dir catalog-example | head
   
   # Private version works with real catalog
   export TOOLBOX_BASE_DIR=~/amitkuzi/ai-toolbox-catalog
   python scripts/store.py query tools | head  # should show 72 tools
   ```

4. **Tag and release:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   # Marketplace submission
   ```

---

## Maintaining both repos

### Public repo (amitkuzi/ai-toolbox)

- **Merge PRs:** auditor's monthly PRs (license, weight changes) go here
- **Update rules:** any rule changes propagate here
- **Update documentation:** docs evolve here
- **CI:** `validate.py` runs against catalog-example/ (ensures consistency)

### Private repo (amitkuzi/ai-toolbox-catalog)

- **Append events:** curator/assessor/auditor run against this ledger
- **Scores accumulate:** real outcomes are scored here
- **No merges:** append-only; no PRs, no conflicts

### Sync between repos (optional)

Docs and rules can be kept in sync via:
- Manual copy-paste (simple for small changes)
- Git subtree (advanced; keep single source of truth)

For now (Phase 5), just maintain separately.

---

## Example: catalog-example/ledger/tools.jsonl

```jsonl
{"event_id":"01J1234567890ABCDEFGHIJK1","ts":"2026-01-01T00:00:00Z","kind":"tool.added","subject_id":"python3","actor":"system:migration","via":"migration","reason":"example tool: Python 3","payload":{"name":"Python 3","type":"script","category":"runtime","cost":"free","local_capable":true,"agent_ready":true,"data_residency":"local","license":"PSF","purpose":"General-purpose scripting"}}
{"event_id":"01J1234567890ABCDEFGHIJK2","ts":"2026-01-02T00:00:00Z","kind":"tool.added","subject_id":"bash","actor":"system:migration","via":"migration","reason":"example tool: Bash","payload":{"name":"Bash","type":"script","category":"runtime","cost":"free","local_capable":true,"agent_ready":true,"data_residency":"local","license":"GPL-3.0-only","purpose":"Shell scripting"}}
```

---

## See also

- `README.md` — points to customer-guide (installation)
- `docs/customer-guide.md` — user setup instructions
- `catalog-example/` — the public example catalog
- [amitkuzi/ai-toolbox-catalog](https://github.com/amitkuzi/ai-toolbox-catalog) — Amit's private catalog (post-v1.0.0)
