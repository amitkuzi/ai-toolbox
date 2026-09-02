# Changelog — AI Toolbox

**Format:** Semantic versioning (`MAJOR.MINOR.PATCH`)  
**Release cycle:** Phases (v0.x = pre-release, v1.0.0 = production)

---

## [v0.5.0] — 2026-09-02 · Curator/Assessor/Auditor agents + scheduled runs

**Phase 4 complete.** Autonomous agents for discovery, assessment, and audit. GitHub Actions + Docker/ops for scheduling.

### Added

- **Agents:** `toolbox-curator` (T1, daily/weekly discovery), `toolbox-assessor` (T2, structural scoring), `toolbox-auditor` (T2, monthly audit)
- **Skill:** `toolbox-curate` (daily/weekly routines: discover, validate, close gaps)
- **Workflows:** `.github/workflows/{daily-refresh,weekly-sources,monthly-audit}.yml` (scheduled on cron)
- **Self-hosted:** `ops/` (Docker, docker-compose, run-task.sh, notify.sh for local/cron execution)
- **Commands:** `/toolbox:add <id>`, `/toolbox:audit`
- **Notifications:** ntfy.sh + Slack alert support on failure

### Changed

- Phase 3 handoff notes (outcome scoring loop complete, hooks working)

### Verified

- All append-only P4 compliance maintained
- Validation passes (schema, append-only guard, views == project output)
- No `Edit` on ledger/views (CI enforces)

---

## [v0.4.0] — 2026-09-02 · Outcome scoring loop + hooks

**Phase 3 complete.** Closed-loop feedback: decisions → outcomes → score fold.

### Added

- **Rule 5:** `rules/05-outcome-scoring.md` (outcome events, EMA fold, regret analysis)
- **Skill:** `toolbox-outcome` (record outcomes: success/partial/fail, duration, cost, score)
- **Commands:** `/toolbox:outcome <id>`, `/toolbox:project` (re-fold views)
- **Hooks:** `SubagentStop` + `Stop` → `remind_outcome.py` (reminder to close open decision)
- **Validator fix:** `verified` field now genuinely computed from `score.outcome` (not just docs)

### Changed

- `catalog/views/scores-summary.yaml` re-projected with `verified` fold
- `scripts/store.py` — `_fold_scores()` now computes `verified` date per tool

### Verified

- `python scripts/validate.py` — all checks pass
- `python hooks/test_remind_outcome.py` — open-decision detection, once-only reminder
- 9×2 contract tests (files + sqlite backends) — all pass

### Not done (scope note)

- 3.5 acceptance test (L3 task with auto:validator) — no L3 in flight this session
- SessionStart/UserPromptSubmit hooks — assigned but not in Phase 3's task list
- Regret analysis code — documented; auditor implements (Phase 4)

---

## [v0.3.0] — 2026-09-02 · Decision rules 1–4 + toolbox-route skill

**Phase 2 complete.** Core routing engine and decision rules.

### Added

- **Rules 1–4:**
  - `rules/01-swarm-gate.md` (L0–L3 classification)
  - `rules/02-orchestrator-model.md` (T0–T3 tier selection)
  - `rules/03-category-gate.md` (type: script|mcp|skill|etc.)
  - `rules/04-tool-ranking.md` (effective score, weights, winner+runner-up)
  - `rules/06-safety.md` (guardrails)
  - `rules/07-data-contract.md` (P1–P4 for agents)
  - `rules/00-glossary.md` (terminology)

- **Skill:** `toolbox-route` (reads rules 00–04, appends decision event with full reasoning)
- **Commands:** `/toolbox:route`, `/toolbox:trace` (full decision chain), `/toolbox:gaps`
- **Hooks:** `SessionStart` → catalog summary + active profile

### Changed

- `scripts/store.py` — `_project_tools()` now includes `rules_version` validation

### Verified

- Routing skill eval: 10 tasks, 8/10 correct routing (80%)
- All decisions logged with `candidates[]`, `reason`, `rules_version`

---

## [v0.2.1] — 2026-09-02 · Fix: resolve six open ADRs from Phase 1 catalog data

**Patch.** Data cleanup and schema alignment.

### Fixed

- ADRs D-008, D-009, D-010, D-011, D-012, D-013 — decisions about routing architecture
- Migrated catalog: all 72 tools now have consistent `type` + `category`
- No duplicate tool IDs
- All events carry required fields (`ts`, `actor`, `reason`)

---

## [v0.2.0] — 2026-09-02 · Catalog Store + append-only ledger + migrated catalog

**Phase 1 complete.** Foundation: storage, schema, migration.

### Added

- **Catalog Store:** `scripts/store.py` (append/query/project/trace API)
- **Backends:** `files.py` (JSONL), `sqlite.py` (for testing)
- **Ledger schema:** event envelope (event_id, ts, kind, subject_id, actor, via, reason, payload)
- **Ledger collections:** `tools`, `sources`, `models`, `scores`, `decisions`, `gaps` (append-only JSONL files)
- **Views:** generated projections (tools.yaml, models.yaml, scores-summary.yaml, etc.)
- **Migration:** 72 tools from two sources + historical changelog + 7 ADRs + 5 gaps → events
- **Validation:** `scripts/validate.py` (schema, append-only guard, views == project output)
- **Profiles:** `amit.yaml`, `_default.yaml` (weights, privacy, budget, paths)

### Changed

- `tools.yaml` is now a view (generated), not source of truth
- Ledger is the source of truth (immutable, auditable)

### Verified

- 0 duplicate tool IDs (72 unique)
- All migrated events have `type`, `category`, required fields
- Contract test: files.py and sqlite.py produce byte-identical views
- CI: `validate.py` enforces append-only, P1–P4 compliance

---

## [v0.1.0] — 2026-09-02 · Initial skeleton

**Phase 0 complete.** Repository created, PRD approved, work plan set.

### Added

- Repository: `github.com/amitkuzi/ai-toolbox` (MIT license)
- Documentation: `docs/PRD.md` (requirements, five decisions, four principles)
- Work plan: `docs/he/WorkPlan.md` (7 phases, dependencies, timeline)
- Basic structure: `.claude-plugin/`, `skills/`, `agents/`, `commands/`, `hooks/`, `rules/`, `catalog/`, `profiles/`, `scripts/`, `ops/`, `docs/`
- Architecture review: ADRs D-001–D-007 (design decisions captured)

### Status

- Ready for Phase 1 (Catalog Store)
- PRD + work plan reviewed and approved

---

## Roadmap (pre-release phases)

| Version | Phase | Status | Delivery |
|---|---|---|---|
| v0.1 | 0 | ✅ | Repository skeleton, PRD, work plan |
| v0.2 | 1 | ✅ | Catalog Store, ledger, migration |
| v0.2.1 | — | ✅ | Data cleanup (6 ADRs) |
| v0.3 | 2 | ✅ | Rules 1–4, routing skill |
| v0.4 | 3 | ✅ | Rule 5, outcome scoring, hooks |
| v0.5 | 4 | ✅ | Curator/assessor/auditor agents, workflows |
| v0.6 | 5 | 🔄 | Documentation, packaging |
| v0.7-rc | 6 | ⏳ | Validation, pilot, eval suite |
| v1.0.0 | 7 | ⏳ | Release, marketplace |

---

## Contributing

See `CLAUDE.md` for development instructions (hard rules, git discipline, agent roles, team).

For issues, feature requests, or security vulnerabilities:
- Open a GitHub Issue (public repo)
- Contact Amit (private discussions)

---

## License

MIT — see `LICENSE` file. The plugin code is open; users' catalogs and score logs are theirs.
