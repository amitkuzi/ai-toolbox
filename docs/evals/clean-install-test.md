# Clean install test — Validation checklist

**Version:** 0.6 · **Date:** 2026-09-02 · **Purpose:** Verify customer-guide.md actually works

---

## Scenario

A new user (not Amit) installs AI Toolbox for the first time on a fresh machine (or Docker container).
They follow `docs/customer-guide.md` exactly. Should work with no surprises.

---

## Prerequisites

- Fresh machine or container (or new user account on existing machine)
- Claude Code installed (or they install it following our guide)
- No existing AI Toolbox or catalog

---

## Test procedure

### Phase 1: Install (15 min)

**Test:** Follow `docs/customer-guide.md` §Installation (3 steps)

```bash
# Step 1: Install Claude Code
# (if not already installed — they download from claude.ai/code)

# Step 2: Install the plugin
/plugin marketplace add amitkuzi/ai-toolbox
/plugin install ai-toolbox@ai-toolbox

# Expected: ✅ Plugin installed successfully
# Check: ~/.claude/plugins/ai-toolbox exists and has skills/, agents/, etc.
```

**Checklist:**
- [ ] Plugin installs without errors
- [ ] README loads in Claude Code
- [ ] `skills/` directory exists
- [ ] No permission errors

### Phase 2: Configuration (optional, 10 min)

**Test:** If user wants to customize weights, follow §Configuration

```bash
# Edit the default profile or create a new one
# (Instructions in docs/customer-guide.md)
```

**Checklist:**
- [ ] Profile file exists in `profiles/`
- [ ] YAML syntax is valid (no parse errors)

### Phase 3: First task (10 min)

**Test:** Follow `docs/customer-guide.md` §Your first task

```bash
/toolbox:route rename 200 files by convention
```

**Expected output:**
```
✅ Routed to: python3 (score 9.2/10, verified 3 days ago)
Run: python3 rename_files.py --input ./models --pattern "{base}-{i:03d}.txt"
After running, log the outcome: /toolbox:outcome <decision-id>
```

**Checklist:**
- [ ] Command produces a routing decision
- [ ] Decision includes tier, tool name, score
- [ ] No cryptic errors
- [ ] `<decision-id>` format is clear (d-YYYYMMDD-NNN)

### Phase 4: Log outcome (5 min)

**Test:** Follow §Then log the outcome

```bash
/toolbox:outcome d-20260902-001
```

**Expected:** Outcome is recorded; no errors.

**Checklist:**
- [ ] Outcome command accepts the decision-id
- [ ] No "decision not found" errors
- [ ] Views are regenerated (no validation failures)

### Phase 5: Trace (5 min)

**Test:** Follow §Common commands → `/toolbox:trace`

```bash
/toolbox:trace d-20260902-001
```

**Expected:** Full decision chain displayed with candidates, tiers, reasoning.

**Checklist:**
- [ ] Trace output is human-readable
- [ ] Shows all candidates and scores
- [ ] Outcome(s) listed

### Phase 6: Common commands (5 min)

**Test:** Try each command from §Common commands

```bash
/toolbox:audit        # Should output audit summary (or "no audit needed")
/toolbox:add nodejs   # Should trigger assessment
```

**Checklist:**
- [ ] Commands don't crash
- [ ] Output is clear
- [ ] No missing documentation

---

## Success criterion

**All steps complete with no "Why doesn't this work?" questions.**

If user gets stuck:
1. **Step blocked:** Error is in docs/customer-guide.md (update docs)
2. **Unclear instruction:** Re-word for clarity
3. **Feature missing:** May need Phase 7 (release) work

---

## Failure modes

| Issue | Resolution |
|---|---|
| "Plugin not found" | Check that amitkuzi/ai-toolbox is in marketplace |
| "Decision ID format wrong" | Update docs with correct format |
| "Validation fails on clean install" | Debug catalog-example/ — may have bad JSON |
| "profile not recognized" | Check profiles/ directory permissions |
| "No such command: /toolbox:route" | Ensure skills are loaded in Claude Code |

---

## Tester notes

- **Don't help too much.** Let them read the docs. If they get stuck, that's a docs bug.
- **Time it.** Should take < 60 min from download to first decision logged.
- **Write down every question they ask.** Those are docs gaps.
- **Note any errors.** Even warnings; they might confuse users.

---

## Acceptance

✅ **Pass:** New user completes all 6 phases without asking for help.  
❌ **Fail:** User gets stuck or confused at any phase.

If fail → update docs or debug plugin → test again until pass.

---

## See also

- `docs/customer-guide.md` (what we're testing)
- `README.md` (install overview)
- `catalog-example/` (the data the plugin ships with)
