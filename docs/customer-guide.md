# Customer guide — Installation and first steps

**Version:** 0.5 · **Date:** 2026-09-02 · **For:** end users

How to install, configure, and start using AI Toolbox to route your tasks to the right tools.

---

## Installation (3 steps)

### 1. Install Claude Code

If you don't have Claude Code installed:

- **Web:** Visit [claude.ai/code](https://claude.ai/code)
- **Desktop:** Download from [claude.com/claude-code](https://claude.com/claude-code)
- **IDE:** VS Code or JetBrains extension (search "Claude")

### 2. Install the AI Toolbox plugin

In Claude Code, run:

```
/plugin marketplace add amitkuzi/ai-toolbox
/plugin install ai-toolbox@ai-toolbox
```

Or use the plugin browser:
1. Open Claude Code
2. `Plugins` → Search "AI Toolbox"
3. Click `Install`

The plugin adds skills, agents, commands, and data to your Claude Code workspace.

### 3. Set up your profile (optional)

The plugin comes with a default profile. To customize it:

1. Open the workspace: `~/.claude/projects/<workspace>`
2. Edit `profiles/_default.yaml` or create your own `profiles/myname.yaml` with your preferences
3. Set weights (cost, score, local, agent-ready, fresh)
4. Set privacy and budget defaults

See `docs/profiles.md` for details.

---

## Your first task

### Example: Rename 200 files

```
/toolbox:route rename 200 STL files by convention
```

This runs the AI Toolbox routing engine:

1. **Decision 1:** Is this a complex swarm task? → No, single deterministic step (L1)
2. **Decision 2:** What model should orchestrate? → Local (T0)
3. **Decision 3:** What type of work? → Script (deterministic file operations)
4. **Decision 4:** Which tool? → Python or Bash (ranked by your profile weights)
5. **Output:** Recommended tool + command to run

```
✅ Routed to: python3 (score 9.2/10, verified 3 days ago)

Run:
python3 rename_files.py --input ./models --pattern "{base}-{i:03d}.stl"

After running, log the outcome:
/toolbox:outcome <decision-id>
```

### Then log the outcome

After running the tool:

```
/toolbox:outcome d-20260902-001
```

This records:
- Did it succeed? Partial? Fail?
- How long did it take?
- How much did it cost (if applicable)?
- Your rating (1–10)

The score feeds back into the catalog; next time you use a similar tool, its score will be better or worse based on this experience.

---

## Common commands

### `/toolbox:route <task>`

Route a task to the best tool.

Examples:
```
/toolbox:route extract key decisions from a 50-page PDF
/toolbox:route set up a PostgreSQL database and load test data
/toolbox:route generate a Hebrew word cloud from this list
```

### `/toolbox:outcome <decision-id>`

Log the outcome after a tool ran. Records success/failure, time, cost, and your rating.

### `/toolbox:trace <decision-id>`

See the full decision chain: why this tool was picked, what other options were considered, and all past outcomes for that tool.

```
/toolbox:trace d-20260902-001
```

Output:
```
Decision d-20260902-001 (2026-09-02 10:00 UTC)
Task: "rename 200 STL files"

Routing:
  Level: L1 (single deterministic step)
  Model tier: T0 (local)
  Type: script
  Candidates for script-type tools:
    1. python3 (score 9.2, verified 3 days ago)
    2. bash (score 8.1)
    3. powershell (score 6.0, estimate)

  Chosen: python3
  Reason: highest score, verified recently, local

Outcomes:
  • 2026-09-02 10:00:09 → success (4 sec, $0, score 9)
  • 2026-09-02 13:00:00 → success (3 sec, $0, score 10 — human review)

Score history for python3:
  my_score_current: 9.2 (EMA over 14 outcomes)
  trend: up (improving)
  last verified: 2026-08-30
```

### `/toolbox:add <tool-id>`

Manually add a tool to the catalog. Triggers assessment.

```
/toolbox:add nodejs
```

### `/toolbox:audit`

Run a monthly audit out-of-schedule. Checks for stale tools, license issues, regret patterns.

---

## Scheduled runs (automatic)

The catalog updates itself automatically:

| When | What |
|---|---|
| **Daily @ 07:00 UTC** | Discover new tools, validate old ones |
| **Mon @ 08:00 UTC** | Re-score sources, hunt new sources |
| **1st @ 09:00 UTC** | Monthly audit (stale, licenses, regret) |

You can disable these or run them manually:

```
# GitHub Actions: disable the workflow in Settings → Actions
# Docker/local: comment out the crontab line or skip calling the script
# Manual: /toolbox:curate daily  (when you want)
```

---

## Configuration

### Change your weights

Edit your profile to prioritize what matters to you:

```yaml
# Cost-conscious:
weights:
  cost: 0.35
  score: 0.25
  local: 0.20
  agent_ready: 0.15
  fresh: 0.05

# Privacy-focused:
privacy_default: local
weights:
  local: 0.40
  score: 0.30
  agent_ready: 0.20
  cost: 0.05
  fresh: 0.05
```

See `docs/profiles.md` for more examples.

### Add a custom source

If you know a source (e.g. internal tool registry, ArXiv category) the curator should track:

```bash
python scripts/store.py append --kind source.added \
  --subject-id internal-tools \
  --actor human:me \
  --via manual \
  --reason "Company tool registry" \
  --payload '{"name": "Internal Tools", "url": "https://...", "value_score": 4}'
```

Then the curator will check it daily.

### Privacy constraints

Set `privacy_default` in your profile and `data_residency` in tools:

```yaml
# Profile:
privacy_default: local          # Only local tools unless explicit

# Tool (in the catalog):
data_residency: local           # Tool runs locally
# or
data_residency: cloud           # Tool calls cloud APIs
# or
data_residency: hybrid          # Option for both
```

If there's a mismatch, the tool is skipped (not a candidate for routing).

---

## Troubleshooting

### "No tools found for this task"

Possible causes:
1. The task type doesn't match any tool's `task_types`
2. All matching tools are marked `review_status: dead` or stale
3. Privacy constraint is too strict (profile is `local` only but all tools are cloud)

**Solution:** Run `/toolbox:audit` to check tool status, or manually add/assess a tool with `/toolbox:add`.

### "The routed tool didn't work"

Log the outcome to provide feedback:

```
/toolbox:outcome d-20260902-001
# Rating: 2/10 (failed to parse the input)
```

The score goes down. Next time, a different tool might be picked. Auditor will flag it for investigation.

### "I want to use a specific tool, not the recommended one"

Two options:

1. **Run it manually** (don't use `/toolbox:route`)
2. **Adjust your profile** to weight qualities this tool has (e.g. if you prefer open-source, boost `agent_ready` which correlates with open-source)

See `docs/profiles.md` to tune your weights.

---

## Support and feedback

- **Questions:** Read `docs/` files (architecture, rules, curator guide)
- **Bug report:** GitHub Issues (if open-source) or contact Amit
- **Feedback:** Rate tools and outcomes; auditor uses this to improve routing

---

## Next steps

1. ✅ Install the plugin
2. ✅ Try `/toolbox:route <task>`
3. ✅ Run the tool
4. ✅ Log the outcome with `/toolbox:outcome`
5. ✅ Trace decisions with `/toolbox:trace`
6. ✅ Adjust your profile (docs/profiles.md)
7. ✅ Let the curator discover new tools (automatic daily)

---

## See also

- `docs/architecture.md` — how the system works (for the curious)
- `docs/rules.md` — the five routing decisions explained
- `docs/profiles.md` — tune your preferences
- `docs/curator.md` — what the agents are doing in the background
