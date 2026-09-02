---
description: Record what happened after a routed subtask finished — appends score.outcome/score.human, never edits.
argument-hint: <decision_id> <success|partial|fail> [score] [reason]
---

Run the `toolbox-outcome` skill for decision `$ARGUMENTS`.

Follow `skills/toolbox-outcome/SKILL.md` step by step: gather the result per
tool that ran, append one `score.outcome` (or `score.human` if this is a
human score) per tool, then `python scripts/store.py project` so the views
pick up the new fold.
