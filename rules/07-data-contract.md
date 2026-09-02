# 07 — Data contract (P1–P4)

Every rule, skill, agent and command in this plugin reaches catalog data through
`scripts/store.py` and nothing else. This file is the agent-facing version of
`docs/PRD.md` §1a; read that section if you need the "why."

## Input → what's allowed → what's forbidden

| You have | You may | You may never |
|---|---|---|
| A new tool/source/model to record | `store append --kind tool.added \|source.added\|model.added ...` | Write to the ledger's JSONL files with `Write`/`Edit` |
| A change to an existing tool's fields | `store append --kind tool.revised --reason "..."` | Edit the tool's earlier `tool.added` line, or any generated view file |
| A tool that stopped working / went dead | `store append --kind tool.retired --reason "..."` | Delete its ledger lines |
| Any information you need to read | `store query <collection> --filter key=value` | Open a ledger file or a view file directly with `Read`/`Grep` as if it were the source of truth |
| The current, human-readable catalog | `store project` (regenerates every view) then read the view file | Hand-edit a view file to "fix" something you saw — the fix belongs in the ledger, `project` will regenerate the view |
| A routing decision to log | `store append --kind decision --rules-version ... --reason "..."` with **every candidate considered** | Log only the winner, or skip logging because the choice felt obvious |
| An outcome/score to record | `store append --kind score.seed\|score.outcome\|score.human` | Overwrite an existing score field — there is no editable `my_score`, only new score events |
| A wrong score/event to correct | `store append --kind score.retract --supersedes <event_id> --reason "..."` | Delete or edit the wrong event |

## The one hard rule

**If your next action is `Write` or `Edit` on any path under the data directory
this plugin stores its ledger and views in, stop.** That is never the right
tool. Use `store append` instead — even for a "trivial" fix, even under time
pressure, even if you can see exactly which line is wrong in the ledger. CI
(`scripts/validate.py`) rejects any ledger diff that removes or changes a
line, and rejects any view that doesn't exactly match a fresh `store project`.
A hand-edit will fail the build, not just your intent.

This also means: no `rules/`, `skills/`, `agents/`, or `commands/` file may
name that data directory's path literally. If you need to reference "the
tools catalog" in prose, say so in words — access it through `store query`,
never by path. (This file talks *about* that rule without spelling the path
out, on purpose — CI checks this file too.)

## Examples

**Right — recording a newly discovered tool:**
```
python scripts/store.py append --kind tool.added --subject-id crawl4ai \
  --actor agent:toolbox-curator --via daily-run \
  --reason "discovered via awesome-mcp-registry, value_score 4" \
  --payload '{"name": "Crawl4AI", "type": "script", "category": "tool", ...}'
```

**Right — an outcome came back mediocre, scoring the tool down:**
```
python scripts/store.py append --kind score.outcome --subject-id d-20260902-004 \
  --actor auto:validator --via outcome --reason "output needed 2 rounds of rework" \
  --payload '{"tool_id": "aider", "result": "partial", "score": 5}'
```

**Wrong — "just fixing a typo" in a view file:**
```
Edit(file_path="<data dir>/views/tools.yaml", ...)   # never do this
```
The fix is a `tool.revised` event with a `reason`; `store project` regenerates
the view from it.

**Wrong — reading the ledger directly to answer "is X in the catalog?":**
```
Grep(pattern="crawl4ai", path="<data dir>/ledger/tools.jsonl")   # never do this
```
Use `store query tools --filter subject_id=crawl4ai` instead — the ledger's
on-disk shape (JSONL today, maybe sqlite/postgres tomorrow) is not a contract
you get to depend on.
