# Profiles — User configuration

**Version:** 0.5 · **Date:** 2026-09-02

How to set up and customize profiles for different users or contexts.

---

## What is a profile?

A profile is a YAML file that defines:
- **Weights:** how much each dimension (score, cost, local, agent-ready, fresh) matters
- **Privacy default:** local | hybrid | cloud (affects tool selection)
- **License policy:** commercial-ok | internal-only (filters out incompatible tools)
- **Budget:** cost cap per task
- **Task type affinity:** which task types this user typically runs (personalizes score context)
- **Paths:** custom file paths (CAD source, output directory, etc.)

Every `/toolbox:route` call loads a profile (explicit or default) and uses its weights to rank tools.

---

## Profile location and naming

Profiles live in `profiles/` directory:

```
profiles/
├── _default.yaml       # Fallback for any user
├── amit.yaml           # Amit's personal profile
├── team-dev.yaml       # Shared dev team profile
├── team-ops.yaml       # Ops team (cost-focused)
└── customer-acme.yaml  # A customer's profile
```

Name by owner/team/context. Start with `_default.yaml` as a template.

---

## Example profile: `profiles/amit.yaml`

```yaml
id: amit
privacy_default: hybrid          # local | hybrid | cloud
license_policy: commercial-ok    # internal-only | commercial-ok
budget_usd_per_task: 0.50

weights:                         # decision 4
  score: 0.40          # Tool outcome history (40%)
  local: 0.20          # Can run locally? (20%)
  agent_ready: 0.15    # Can an agent automate it? (15%)
  cost: 0.15           # Is it free/cheap? (15%)
  fresh: 0.10          # Recently verified? (10%)

task_type_affinity:              # personalizes score context
  file-batch: 1.0      # Amit does lots of file ops
  cad: 1.0             # Amit does CAD work
  hebrew-report: 1.0   # Hebrew document tasks
  code-csharp: 0.8     # Some C# work
  api-integration: 0.3 # Rarely integrates APIs

paths:
  cad_source: "C:/Users/Amit.kuzi/OneDrive/Documents/3dModel"
  output: "~/ai-toolbox-results"
```

---

## Profile fields

### Core settings

| Field | Type | Default | Notes |
|---|---|---|---|
| `id` | string | required | Profile identifier (username, team name, etc.) |
| `privacy_default` | enum | `hybrid` | `local` (all tools local), `hybrid` (OK for cloud APIs), `cloud` (no preference) |
| `license_policy` | enum | `commercial-ok` | `internal-only` (no proprietary/GPL), `commercial-ok` (allow anything) |
| `budget_usd_per_task` | float | 1.00 | Fail if estimated cost exceeds this; encourages T0/T1 choices |

### Weights (decision 4 scoring)

Sum should equal 1.0 (normalized). Adjust to reflect priorities:

```yaml
weights:
  score: 0.40          # Past outcomes (outcome history, EMA-smoothed)
  local: 0.20          # Autonomy: tool runnable locally without cloud?
  agent_ready: 0.15    # Agent-friendly (CLI/API vs. GUI-only)
  cost: 0.15           # Cost clarity (free > cheap > metered > paid)
  fresh: 0.10          # Recency (verified recently vs. stale)
```

**Example tunings:**

- **Cost-conscious profile** (Ops, limited budget):
  ```yaml
  weights:
    cost: 0.35         # Prioritize cheapness
    score: 0.25        # Secondary: quality
    local: 0.20
    agent_ready: 0.15
    fresh: 0.05
  ```

- **Privacy-focused profile** (Sensitive data):
  ```yaml
  weights:
    local: 0.40        # Prioritize local tools
    score: 0.30
    cost: 0.10         # Cost is secondary
    agent_ready: 0.15
    fresh: 0.05
  privacy_default: local  # and enforce local in privacy_default
  ```

- **Speed-focused profile** (Real-time systems):
  ```yaml
  weights:
    score: 0.50        # Highest performers only
    agent_ready: 0.20
    fresh: 0.15        # Recently validated
    local: 0.10
    cost: 0.05         # Cost doesn't matter
  ```

### Task type affinity (0–1 scale)

Personalizes `my_score_ctx` at routing time. If a tool fits a task type this user does often, its score gets boosted.

```yaml
task_type_affinity:
  file-batch: 1.0      # Amit runs lots of file operations
  cad: 1.0
  hebrew-report: 1.0
  code-csharp: 0.8
  api-integration: 0.3 # Rarely
  web-scrape: 0.1      # Seldom
  # (omitted types default to 0.5)
```

When ranking tools for a `file-batch` task, a tool tagged with `task_type: file-batch` gets a score boost; for `web-scrape`, most tools get penalized.

### Paths (optional, per-user)

Custom file paths for I/O:

```yaml
paths:
  cad_source: "~/3dModel"
  output: "~/results"
  data: "~/data"
```

Used by tools and skills to locate user files. Avoid absolute Windows paths here (use `~` for portability).

---

## Default profile

`profiles/_default.yaml` is the fallback. Keep it neutral:

```yaml
id: _default
privacy_default: hybrid
license_policy: commercial-ok
budget_usd_per_task: 1.00

weights:
  score: 0.40
  local: 0.20
  agent_ready: 0.15
  cost: 0.15
  fresh: 0.10

task_type_affinity: {}  # All tasks equally weighted (0.5 default)

paths: {}
```

---

## How routing uses a profile

1. **Explicit profile:** `/toolbox:route --profile team-ops` uses `profiles/team-ops.yaml`
2. **Default:** `/toolbox:route` uses `profiles/amit.yaml` (if Amit is logged in) or `_default.yaml`
3. **Fallback:** if named profile doesn't exist, use `_default.yaml`

When route runs, it:
- Loads the profile
- Reads the weights
- Scores each tool candidate as: `effective_score = my_score_ctx × sum(weights)`
- Picks the highest

---

## Sharing profiles

For teams:

1. **Shared team profile** (e.g. `profiles/team-dev.yaml`):
   ```yaml
   id: team-dev
   privacy_default: cloud
   license_policy: commercial-ok
   budget_usd_per_task: 2.00
   
   weights:
     score: 0.35
     agent_ready: 0.25    # Devs value autonomy
     cost: 0.20
     local: 0.15
     fresh: 0.05
   ```

2. **Commit to repo** so all team members use consistent scoring

3. **Override locally** by creating personal profile: `/toolbox:route --profile amit` wins over `team-dev`

---

## Privacy and budget enforcement

### Privacy constraint

If a tool's `data_residency` conflicts with the profile's `privacy_default`:
- Tool: `cloud-only`, Profile: `privacy_default: local` → **Skip this tool** (not a candidate)
- Tool: `hybrid`, Profile: `privacy_default: hybrid` → **OK** (candidate)

### Budget cap

Estimated cost > `budget_usd_per_task`:
- Warn the user or reject the tool
- Orchestrator may downgrade tier to stay under budget
- Curator proposes `tool.status: over-budget` for audit

---

## Creating a new profile

1. Copy `_default.yaml`:
   ```bash
   cp profiles/_default.yaml profiles/my-team.yaml
   ```

2. Edit:
   ```yaml
   id: my-team
   privacy_default: hybrid
   budget_usd_per_task: 0.25    # Tight budget
   
   weights:
     cost: 0.35           # Prioritize cost
     score: 0.25
     agent_ready: 0.20
     local: 0.15
     fresh: 0.05
   ```

3. Test:
   ```bash
   /toolbox:route --profile my-team "summarize a PDF"
   ```

4. Iterate until you're happy with tool selections

---

## See also

- `docs/customer-guide.md` — installation and first-time setup
- `rules/02-orchestrator-model.md` — how tier selection uses profiles
- `rules/04-tool-ranking.md` — how weights are applied
- `scripts/store.py` — query for tools filtered by privacy/budget
