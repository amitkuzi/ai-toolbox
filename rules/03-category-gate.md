# 03 — Category gate

Decision 3 of 5 (PRD §7.3). Runs once **per subtask** (never per task — decompose
first, in L3, then run this gate once for each resulting subtask). Unchanged
from `selection-rules.md` §1 (ADR D-002), with two pre-questions added for
`kb`/`schedule`.

## Input

One subtask, already decomposed if this task is L3.

## Questions → Output: type

Stop at the first question that answers YES.

| # | Question | Type |
|---|---|---|
| 0a | Is this a lookup of existing knowledge? | `kb` |
| 0b | Must this run repeatedly on a schedule? | `schedule` |
| 1 | Must output be reproducible bit-for-bit? | `script` |
| 2 | Needs data or action in an external service? | `mcp` |
| 3 | Done this same procedure 3+ times? | `skill` |
| 4 | Needs a modality a text LLM lacks, **or independence from the writing model**? | `model` |
| 5 | Otherwise | `subagent` |

**D-009 note:** there is no `plugin` output here and never was reachable —
`plugin` is not a `type` a tool carries (PRD §6.1, resolved). A Claude Code
plugin bundle shows up in the catalog as several ordinary entries (one each
of whatever `skill`/`agent`/`command`/`mcp` it ships) sharing a
`tags: [plugin:<name>]` tag. If a subtask happens to be satisfied by one of
those entries, it was reached through this table's normal `skill`/`mcp`/
`subagent` row like any other tool — never through a `plugin`-specific path.

### Why this order

Earlier types are cheaper, more deterministic, and easier to audit. Reaching
for a subagent first is the most common failure mode — it burns context and
returns prose where a script would have returned a fact.

## Output

One `type` per subtask, feeding directly into `04-tool-ranking.md`'s
candidate shortlist for that type.

## Type-specific traps

Carried over verbatim from `selection-rules.md` §3, per the PRD's note that
these traps are unchanged:

- **subagent vs. specialized model** — a subagent is the same base model with
  a role prompt and a fresh context. A specialized model is a *different*
  model. Choose a subagent when you want focus; choose a model only when the
  capability is genuinely absent. "I want an expert" is not a reason to reach
  for a different model.
- **skill** — reading an output-format SKILL.md (docx/xlsx/pptx/pdf) before
  research is finished anchors on mechanics before there is correct content
  to put in the document. Research first, then read the skill.
- **mcp** — before concluding no connector exists, search the MCP registry.
  Only then log a gap.
- **mcp-chrome / mcp-computer-use** — fallback tiers, not defaults. Dedicated
  MCP > Chrome > computer use. If a plain fetch returns a JS shell, escalate
  to a browser tool; do not retry the fetch and do not route around a block
  with curl or requests.
- **script** — `pip` requires `--break-system-packages` in the sandbox. Each
  bash call is independent: no cwd or env carryover, absolute paths only.

## Examples

**"Fetch this week's email threads" → Q0a no, Q0b no, Q1 no, Q2 yes (external
service)** → `mcp`.

**"Rename 200 STL files by convention" → Q0a no, Q0b no, Q1 yes (reproducible)**
→ `script`. Stop — no need to reach Q2+.

**"What tools do we already have for CAD work?" → Q0a yes (lookup of existing
catalog knowledge)** → `kb`. Stop immediately.

## Do not

- Do not run this gate once for a whole L3 task — it is per-subtask, always.
- Do not skip straight to `subagent` because it feels like the safe default
  — that is exactly the failure mode this order is designed to catch.
- Do not invent a `plugin` type output — see the D-009 note above.
- Do not answer Q2 "yes" just because a web page is involved — Q2 is about
  *action or data inside a service*, not "the answer happens to live online"
  (that's often still `kb` or a plain fetch, not `mcp`).
