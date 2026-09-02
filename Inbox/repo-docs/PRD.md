# PRD — AI Toolbox Plugin

**Version:** 0.1 · **Date:** 2026-09-02 · **Owner:** Amit Kuzi · **Status:** draft for approval
**Target repo:** `github.com/amitkuzi/ai-toolbox` · **Package:** Claude Code plugin (Agent-Skills compatible)

> Internal, English. This is the seed for `docs/PRD.md` in the new repo. The Hebrew user-facing version lives in `inbox/ai-toolbox/PRD-ai-toolbox.md`.

---

## 1. Summary

AI Toolbox is an "operating system for tool selection": a self-maintaining catalog of AI tools, a five-step decision procedure written as Markdown rules that an LLM orchestrator follows before delegating any work, and an append-only outcome log that feeds scores back into the catalog. It unifies three existing fragments — the supply catalog in `AiAgent/ai-toolbox`, the demand-side selection gate in `TaskTriagOrcetrator/ai-toolbox`, and the Mission Router requirements in `ai-gateway/docs/PRD.md` — into one installable, exportable, sellable plugin.

**V1 decisions already taken:**

| Decision | Choice |
|---|---|
| Packaging | New repo `amitkuzi/ai-toolbox` as a Claude Code plugin (skills + agents + commands + hooks + data). The `Skills` repo gets a thin pointer skill only. |
| Decision engine | Markdown rules interpreted by the LLM. No deterministic CLI or HTTP router in V1 (data format is designed so either can be added later without migration). |
| Scheduled curator | GitHub Actions by default; Docker + host cron (`ops/`) as a documented self-host option. Both run the same `toolbox-curate` skill. |
| Licensing | Plugin code MIT. Amit's real catalog and score log stay private; the public plugin ships with `catalog-example/`. |

---

## 2. Problem

| Symptom | Root cause |
|---|---|
| Every task defaults to the most expensive path (a sub-agent on a frontier model) | No cost-ordered decision gate; no orchestrator-model rule |
| Two `tools.yaml` files with incompatible schemas (`category` vs `type`, different `my_score` semantics, `last_reviewed` vs `verified`) | Supply and demand were built separately |
| A tool discovered daily never reaches the selection gate; a tool that fails in use never loses score in the catalog | No shared data path, no feedback loop |
| Nothing is distributable — paths, Caddy, status-app and OneDrive are baked in | Never designed as a product |

---

## 3. Goals and success metrics (V1)

| ID | Goal | Metric |
|---|---|---|
| G1 | One catalog, one schema | 100% of records from both files merged, `scripts/validate.py` passes in CI |
| G2 | Five decisions documented and executed | Every routed task writes a `decision` record with all five fields |
| G3 | Measurable cost reduction | ≥ 40% of tasks routed to T0/T1 (local / cheap) instead of frontier |
| G4 | Closed feedback loop | Every task ends with an `outcome` record; `my_score` auto-updates after ≥ 5 samples |
| G5 | Living catalog | Daily run adds/validates tools unattended; weekly run reviews sources |
| G6 | Distributable | Clean install in 3 commands, no dependency on Amit's machine, clear license |

**Non-goals (V1):** HTTP router service, deterministic routing CLI, web UI, model fine-tuning.

---

## 4. Users

| User | Need |
|---|---|
| Amit (operator) | Give a task, trust that the cheapest correct tool was picked, see why |
| Orchestrating agent (Claude Code) | Catalog + rule + memory before every delegation |
| Scheduled curator agent | Discover, validate, first-assess, commit — unattended |
| External customer | Install the plugin on their own catalog and profile |
| Amit as lecturer | `decisions.md` + `scores.jsonl` as live proof for the talk |

---

## 5. Architecture

### 5.1 Repository layout

```
ai-toolbox/
├── .claude-plugin/{plugin.json, marketplace.json}
├── skills/
│   ├── toolbox-route/SKILL.md      # decisions 1–4, before delegation
│   ├── toolbox-outcome/SKILL.md    # decision 5, after completion
│   └── toolbox-curate/SKILL.md     # daily / weekly / monthly routines
├── agents/{toolbox-curator, toolbox-assessor, toolbox-auditor}.md
├── commands/{route, outcome, add, gaps, audit}.md
├── hooks/hooks.json                # SessionStart, UserPromptSubmit, SubagentStop, Stop
├── rules/                          # the logic — numbered in read order
│   ├── 00-glossary.md
│   ├── 01-swarm-gate.md
│   ├── 02-orchestrator-model.md
│   ├── 03-category-gate.md
│   ├── 04-tool-ranking.md
│   ├── 05-outcome-scoring.md
│   └── 06-safety.md
├── catalog/                        # source of truth (private in Amit's copy; catalog-example/ in public)
│   ├── tools.yaml  sources.yaml  models.yaml
│   ├── scores.jsonl  changelog.jsonl        # append-only
│   ├── decisions.md  gaps.md
│   └── evals/<tool-id>.md
├── profiles/{_default, amit}.yaml  # "who is using it" — weights, privacy, license policy, paths
├── scripts/{validate.py, rescore.py}
├── ops/                            # Docker + cron alternative
├── .github/workflows/{validate, daily-refresh, weekly-sources, monthly-audit}.yml
├── docs/
├── CLAUDE.md  README.md  CHANGELOG.md  LICENSE
```

### 5.2 Runtime flow

```
user task
  → [SessionStart hook] inject catalog summary + active profile
  → skill toolbox-route
      1 swarm gate        → L0 | L1 | L2 | L3
      2 model tier        → T0..T3 for orchestrator and for each agent
      3 category gate     → per subtask: kb|schedule|script|mcp|skill|model|subagent
      4 tool ranking      → winner + runner-up + install/auth + reason
      write decision → catalog/scores.jsonl
  → execution
  → [SubagentStop / Stop hooks] remind to close
  → skill toolbox-outcome
      5 outcome           → success/partial/fail, rework, cost, duration, score, scored_by
      append outcome → scores.jsonl
  → daily run: scripts/rescore.py folds outcomes into tools.yaml / models.yaml
```

### 5.3 Scheduled flow (curator)

| Run | When | Agent | Does |
|---|---|---|---|
| `daily-refresh` | 07:00 | `toolbox-curator` (T1, `--max-turns 40`, tools `Read,Edit,WebSearch,WebFetch`) | discover from `sources.yaml` (value_score ≥ 3) → `seed-unverified`; validate oldest slice → verified/stale/dead; `rescore.py`; try to close gaps; changelog; commit |
| `weekly-sources` | Mon 08:00 | `toolbox-curator` | re-score sources, hunt new ones, list `needs_user_action` in commit message |
| `monthly-audit` | 1st | `toolbox-auditor` | stale > 90 d, licenses, run `evals/` for every routable tool, propose weight changes **as a PR** |
| `first-assessment` | on discover / on demand | `toolbox-assessor` | structural score from docs only (license, autonomy, local_capable, cost, maturity, agent_ready) + write `evals/<id>.md` + propose a bounded trial. **Never executes the tool.** |

---

## 6. Data schemas

### 6.1 `tools.yaml` (unified; ★ = required)

| Field | Type | Notes |
|---|---|---|
| ★ `id`, ★ `name` | slug, string | |
| ★ `type` | `script` \| `mcp` \| `skill` \| `subagent` \| `model` \| `plugin` \| `schedule` \| `kb` | **how it is invoked** — drives decision 3 |
| ★ `category` | `runtime` \| `model` \| `agent-framework` \| `agent-infra` \| `coding-agent` \| `api` \| `gateway` \| `mcp` \| `skill` \| `tool` | **domain** — shortlist only |
| ★ `purpose` | string | one line |
| `abilities`, `pros`, `cons` | list | |
| ★ `domains` | list | shortlist tags |
| ★ `task_types` | list | task types this tool fits (see 6.4) |
| ★ `cost` | `free` \| `included` \| `metered` \| `paid` | + `cost_notes`, optional `cost_per_use_usd` |
| ★ `local_capable`, ★ `agent_ready` | bool | |
| ★ `data_residency` | `local` \| `cloud` \| `hybrid` | hard privacy constraint |
| ★ `autonomy` | 1–5 | |
| ★ `license` | SPDX | + `license_notes` |
| ★ `install`, ★ `auth`, `entrypoint` | string | `auth`: `none` \| `account` \| `api-key` \| `oauth` \| `local-path` |
| `published_score` | string + source | used **only** to rank the trial queue |
| ★ `my_score` | 1–10 | empirical once `score_samples ≥ 5`, otherwise a flagged estimate |
| `score_rationale`, `score_samples` | string, int | |
| ★ `review_status` | `seed-unverified` \| `verified` \| `stale` \| `dead` | |
| ★ `verified` | date | last successful real use; stale after 90 d. Absent ⇒ *candidate*, not *routable* |
| `last_reviewed` | date | last metadata check |
| `maturity`, `tags`, `homepage`, `repo`, `notes` | | |

### 6.2 `models.yaml`

`id`, `provider`, `model`, `tier` (T0 local free · T1 cheap cloud · T2 mid · T3 frontier), `input_usd_mtok`, `output_usd_mtok`, `cache_hit_usd_mtok`, `context_k`, `tokens_per_sec`, `data_residency`, `strengths` (`coding | reasoning | classification | hebrew | vision | long-context`), `my_score`, `score_samples`, `verified`.

### 6.3 `scores.jsonl` (append-only; adopts F-401…F-410 from the ai-gateway PRD)

```jsonl
{"ts":"2026-09-02T10:00:00Z","kind":"decision","decision_id":"d-20260902-001","task":"rename 200 STL files by convention","task_type":"file-batch","actor":"human:amit","profile":"amit","swarm_level":"L1","orchestrator_model":"T0:local-fast","subtasks":[{"id":"s1","type":"script","tool_id":"python3","alt":"agent-implementor","reason":"Q1 reproducible"}]}
{"ts":"2026-09-02T10:00:09Z","kind":"outcome","decision_id":"d-20260902-001","tool_id":"python3","success":true,"partial":false,"rework":false,"duration_s":4,"cost_usd":0,"score":9,"scored_by":"auto:validator","reason":"200/200 renamed, dry-run diff matched"}
{"ts":"2026-09-02T10:05:00Z","kind":"outcome","decision_id":"d-20260902-001","tool_id":"python3","score":10,"scored_by":"human:amit","reason":"exactly what I wanted"}
{"ts":"2026-09-03T08:00:00Z","kind":"retraction","retracts":"<record_id>","reason":"scored the wrong tool"}
```

Rules: `scored_by` ∈ `agent:<name>` | `human:<id>` | `auto:<check>`; multiple outcomes per decision are expected; no edits, only retractions; `tools.yaml` is never written by the loop at task time — only by the daily `rescore.py` (F-410).

### 6.4 `profiles/<actor>.yaml` — "who is using it"

```yaml
id: amit
privacy_default: hybrid          # local | hybrid | cloud
license_policy: commercial-ok    # internal-only | commercial-ok
budget_usd_per_task: 0.50
weights:                         # decision 4
  score: 0.40
  local: 0.20
  agent_ready: 0.15
  cost: 0.15
  fresh: 0.10
task_type_affinity:              # which task types this actor runs most; used for score context
  file-batch: 1.0
  cad: 1.0
  hebrew-report: 1.0
  code-csharp: 0.8
paths:
  cad_source: "C:/Users/Amit.kuzi/OneDrive/Documents/3dModel"
```

`task_type` vocabulary (extendable): `file-batch`, `code-csharp`, `code-python`, `research`, `hebrew-report`, `cad`, `materials`, `3dprint`, `classification`, `summarize`, `email`, `ops`.

---

## 7. The five decisions (rule specifications)

Each rule file has the same shape: **Input → Questions → Output → Examples → Do not.** ≤ 150 lines each; decision table first, examples last.

### 7.1 `01-swarm-gate.md` — does this need the Toolbox and a swarm?

Output: level.

| Level | Condition | Effect |
|---|---|---|
| **L0 inline** | answer from knowledge; no file output; no external service; < ~500 words | orchestrator answers; Toolbox **not** consulted |
| **L1 single tool** | one subtask, deterministic or one external service | Toolbox yes, agent no (script / mcp / skill) |
| **L2 single agent** | needs judgement or writing; one domain; no independent check needed | one subagent + its tools |
| **L3 swarm** | ≥ 3 subtasks across ≥ 2 categories, or parallelizable, or needs an independent Validator, or produces an `inbox/` deliverable | decompose → parallel delegation → Validator |

Swarm signals (any 2): multiple distinct outputs · multiple domains · multiple external services · writer/reviewer independence required · high stakes (irreversible / customer-facing).
Anti-default rule: doubt between L1/L2 → L1; between L2/L3 → L2. Under-routing is cheap to correct; over-routing is not.

### 7.2 `02-orchestrator-model.md` — which model orchestrates?

| Tier | Examples (from `models.yaml`) | Use |
|---|---|---|
| T0 local, $0 | `local-fast` (gemma4:12b), `local-coder` (qwen2.5-coder:14b) | classification, summarization, extraction, routing, first drafts, anything `privacy: local` |
| T1 cheap cloud | Haiku 4.5, gemini-2.5-flash-lite, gpt-5-nano, GLM-4.7-Flash, deepseek-v4-flash | well-specified subtasks, schema validation, 24/7 agents |
| T2 mid | Sonnet 5, kimi-coder, gemini-2.5-pro | code, research, inbox writing, orchestrator for L3 |
| T3 frontier | Opus 5 / Fable 5 | architecture, irreversible decisions, Validator on customer deliverables, escalation from T2 |

Selection rules, in order:

1. `privacy: local` ⇒ T0 only. Hard constraint.
2. Orchestrator tier = tier of the hardest subtask **minus one**, minimum T1 for L3. The orchestrator decomposes and delegates; it does not need to be the smartest model.
3. Agent tier by work kind: script/mcp → T0–T1; writing/code → T2; judgement/final validation → T2–T3.
4. Escalation: fail or `partial` on first attempt ⇒ tier + 1, once, recorded in the outcome (`escalated_from`).
5. Budget: never exceed `budget_usd_per_task`; use Batch API (−50%) for anything not time-critical.
6. Cache-first: large shared context ⇒ prefer providers with cheap cache hits.

### 7.3 `03-category-gate.md` — which tool type per subtask?

Unchanged from `selection-rules.md` §1 (ADR D-002), with two pre-questions:

| # | Question | Type |
|---|---|---|
| 0a | Is this a lookup of existing knowledge? | `kb` |
| 0b | Must this run repeatedly on a schedule? | `schedule` |
| 1 | Must output be reproducible bit-for-bit? | `script` |
| 2 | Needs data or action in an external service? | `mcp` |
| 3 | Done this same procedure 3+ times? | `skill` |
| 4 | Needs a modality a text LLM lacks, **or independence from the writing model** (D-007)? | `model` |
| 5 | Otherwise | `subagent` |

Stop at the first YES. Type-specific traps (§3 of the current rules) carry over verbatim.

### 7.4 `04-tool-ranking.md` — which tool within the type?

**A. Hard filters** — fail any ⇒ excluded: license compatible with profile's `license_policy`; `data_residency` compatible with task privacy; `auth` available in the environment (otherwise flagged "needs user action", never silently chosen); `review_status != dead`.

**B. Effective score**

```
effective = w_score · my_score_ctx
          + w_local · local_capable
          + w_agent · agent_ready
          + w_cost  · (1 − cost_rank/3)        # free=0 included=1 metered=2 paid=3
          + w_fresh · fresh(verified)          # 1.0 if < 30 d, linear to 0 at 90 d
```

`my_score_ctx` = weighted mean of outcome scores for this tool: same `task_type` × 1.0, adjacent × 0.5, any × 0.25; `human:*` × 1.5; decay after 90 days; if `score_samples < 5` ⇒ fall back to the catalog `my_score`, flagged as estimate. Weights `w_*` come from the active profile.

**C. Cold start** — unchanged from `selection-rules.md` §2a: an estimate never outranks a measurement; `seed-unverified` candidates enter only through a bounded trial (one low-stakes subtask against the incumbent); `published_score` ranks the trial queue and nothing else.

**Output:** winner, runner-up, one-line install/auth, `reason`. No candidate ⇒ increment `gaps.md` (`hits`), proceed with closest fit, state the compromise.

### 7.5 `05-outcome-scoring.md` — assess and update

Collected per participating `tool_id`: `success | partial | fail`, `rework`, `duration_s`, `cost_usd` (measured via LiteLLM when present, else agent estimate prefixed `est:`), `score` 1–10 + `reason`, `scored_by`, `escalated_from`.

Score update (daily, by `rescore.py`): if `score_samples ≥ 5` ⇒ `my_score = EMA(α=0.3)` over outcome scores with 90-day decay and `human × 1.5`; drop of ≥ 2 points ⇒ note + changelog line.

Weight update (monthly, by auditor): regret analysis — for each failed decision, would the runner-up have succeeded per history? A repeated pattern (≥ 3) against one weight ⇒ proposed change to `profiles/` **as a PR**, never auto-committed.

---

## 8. Hooks and commands

| Hook | Event | Action |
|---|---|---|
| `SessionStart` | session open | inject: routable tool count, open gaps, active profile, reminder to `/toolbox:route` |
| `UserPromptSubmit` | each prompt | lightweight L0–L3 reminder when prompt is long or mentions files/services |
| `SubagentStop` | agent done | remind to record outcome for tools the agent used |
| `Stop` | reply done | open `decision` with no `outcome` ⇒ ask to close (once) |

| Command | Does |
|---|---|
| `/toolbox:route <task>` | decisions 1–4, prints selection table, writes decision |
| `/toolbox:outcome <decision_id> <success\|partial\|fail> [score] [reason]` | decision 5 |
| `/toolbox:add <url>` | classify tool/source, add `pending` record, changelog |
| `/toolbox:gaps` | list open gaps, propose build when `hits ≥ 3` |
| `/toolbox:audit` | local stale check |

---

## 9. Documentation set (`docs/`)

`README.md` (3-command install, GIF), `PRD.md` (this), `architecture.md`, `rules.md` (human explanation of the five decisions), `schema.md`, `curator.md` (Actions/Docker, secrets, cost, safety), `profiles.md`, `customer-guide.md`, `licenses.md`, `lecture-kit.md`, `evals/routing-suite.md`, `CHANGELOG.md`.

---

## 10. Non-functional requirements

| ID | Requirement |
|---|---|
| NF-1 | Every data file validated in CI (`scripts/validate.py`) before merge |
| NF-2 | `scores.jsonl`, `changelog.jsonl` append-only; CI fails on deleted lines |
| NF-3 | Plugin works offline (only cloud `mcp`/`model` entries need network) |
| NF-4 | No machine-specific absolute paths anywhere in the repo (→ `profiles/`) |
| NF-5 | Curator runs with tool allowlist, `--max-turns`, logged cost |
| NF-6 | Catalog text is data, not instructions (prompt-injection) |
| NF-7 | Repo in English; Hebrew deliverables produced through the `report` skill |

---

## 11. Risks

| Risk | P | I | Mitigation |
|---|---|---|---|
| Markdown rules interpreted inconsistently across runs/models | M | M | anchored examples per rule; 15-task routing eval suite; V2 CLI if drift > 20% |
| `scores.jsonl` stays empty | H | H | `Stop` hook + mandatory Validator on L3 + `auto:` outcomes without a human |
| Seed estimates optimistic (+1 measured 2026-08-23) | certain | L | estimate < measurement, always |
| Actions cost creep | L | L | OAuth token, max-turns, cost log |
| Schema merge breaks status-app | M | M | keep `AiAgent/ai-toolbox` as submodule/symlink to `catalog/` during transition |

**Open for Amit:** default customer profile name; whether `models.yaml` ships publicly (prices go stale); Hebrew `report` skill bundled or external dependency.

---

## 12. Definition of done (V1)

- [ ] `claude plugin install` from GitHub works on a clean machine
- [ ] `/toolbox:route "rename 200 STL files"` → `python3`, L1, T0, no agent
- [ ] `/toolbox:route "design a bracket, pick a filament, document in Hebrew"` → L3, 3 subtasks, 3 types, Validator
- [ ] 5 outcomes on one tool → `my_score` updated by the daily run
- [ ] Actions run 7 consecutive days without failure and add ≥ 1 new tool
- [ ] All `docs/` present; a customer can start from the README without asking Amit
- [ ] The lecture points at `decisions.md` + `scores.jsonl` in the new repo
