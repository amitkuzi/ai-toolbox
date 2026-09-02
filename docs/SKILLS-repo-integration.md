# Skills repo integration — Pointer skill

**For:** Anthropic Skills repository (https://github.com/anthropics/Skills)  
**Task:** Create a thin pointer skill that directs users to this plugin

---

## What goes in Skills repo

File: `Skills/ai-toolbox/SKILL.md`

```markdown
---
name: ai-toolbox
description: Operating system for tool selection — route tasks to the right tools, track outcomes, improve over time.
---

# ai-toolbox

**An operating system for tool selection.**

This is a pointer to the full AI Toolbox plugin. To use it:

1. **Install:** `/plugin marketplace add amitkuzi/ai-toolbox` then `/plugin install ai-toolbox@ai-toolbox`
2. **Route:** `/toolbox:route <task>`
3. **Trace:** `/toolbox:trace <decision-id>`
4. **Audit:** `/toolbox:audit`

---

## What it does

- **Five routing decisions:** swarm gate, model tier, category gate, tool ranking, outcome scoring
- **Self-maintaining catalog:** curator discovers tools, assessor scores them, auditor audits
- **Fully traceable:** every decision logs candidates and reasoning; trace any decision back to source
- **Append-only data:** all history is immutable; feedback loop is audit trail

---

## Quick start

```
/toolbox:route rename 200 STL files by convention
# → recommends best tool

/toolbox:outcome d-20260902-001
# → logs outcome (success/fail, time, cost, your rating)

/toolbox:trace d-20260902-001
# → shows full decision chain + outcomes + score trends
```

---

## See also

- **GitHub:** https://github.com/amitkuzi/ai-toolbox
- **Docs:** See the plugin's `docs/` folder for full guides
- **Customer guide:** `/toolbox:curate daily` (automatic daily catalog updates)

---

## Install & configure

See the plugin README for installation, configuration, and first steps.
```

---

## Update Skills README

Add to `Skills/README.md` (or `Skills/CATALOG.md`):

```markdown
### ai-toolbox

**Routing engine for task → tool matching.** Decision rules (swarm level, model tier, category, ranking, outcome scoring), self-maintaining catalog with curator/assessor/auditor agents, full decision tracing.

**Install:** `/plugin marketplace add amitkuzi/ai-toolbox` then `/plugin install ai-toolbox@ai-toolbox`  
**Repo:** https://github.com/amitkuzi/ai-toolbox
```

---

## Scope note

The pointer skill in Skills repo is thin (just points to the plugin). The real work lives in the plugin repo:
- All code (skills, agents, commands, hooks, store)
- All documentation
- All development

The Skills repo just helps discoverability.

---

## Timeline

- Phase 5 (now): Create stub SKILL.md and add to Skills README
- Phase 6–7: Update link once v1.0.0 released
