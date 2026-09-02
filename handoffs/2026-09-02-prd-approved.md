# Handoff — 2026-09-02 · PRD + work plan done, repo skeleton created

**From:** Orchestrator (Cowork session, Claude) · **To:** next session / Architect + Implementor
**Repo:** `D:\Development\ai-toolbox` (local only — **not yet on GitHub, not yet `git init`'d if this file is the first thing you read; see "State" below**)
**Branch to use:** `ai-toolbox` (project branch per `D:\Development\.claude\skills\git-conventions`)

---

## TL;DR

- PRD v0.2 and work plan v0.2 are written and live in this repo under `docs/`. Read `docs/PRD.md` §1a first — the four data principles are binding and were added at Amit's explicit request after v0.1.
- Repo skeleton exists (folders + README, CLAUDE.md, LICENSE, plugin.json, .gitignore). Everything else is `.gitkeep`.
- **Next action:** phase 0 of the work plan — `git init`, first commit, GitHub repo, then phase 0.3 (Architect "grill me" on the five decisions + P1–P4).

---

## State of the world

| Item | Status | Where |
|---|---|---|
| Hebrew PRD v0.2 | done | `docs/he/PRD.md` |
| Hebrew work plan v0.2 | done | `docs/he/WorkPlan.md` |
| English PRD v0.2 (canonical) | done | `docs/PRD.md` |
| Repo skeleton | done | this folder |
| git | **not initialised** — a `git init` attempt from the Cowork sandbox failed (it cannot unlink lock files); the broken `.git` was renamed to `_to_delete-git-broken-locks/`. **Delete that folder and run phase 0.1 from a normal shell on the Windows host.** | run phase 0.1 |
| GitHub remote | **does not exist** | Amit creates `amitkuzi/ai-toolbox` or approves creation via `gh` |
| Source fragments (read-only inputs) | untouched | `D:\Development\AiAgent\ai-toolbox`, `D:\Development\Luctures\TaskTriagOrcetrator\ai-toolbox`, `D:\Development\ai-gateway\docs` |
| Old copy | to discard after migration | `D:\Development\Amit Kuzi Google Dominance Plan\ai-toolbox\tools.yaml` |

Measured on 2026-09-02 from the source files: supply `tools.yaml` = 36 tools / 9 categories, `sources.yaml` = 32 sources; demand `tools.yaml` = 36 tools / 5 types; 7 ADRs; 5 open gaps.

---

## Decisions Amit made this session (do not re-open)

1. **New repo, packaged as a Claude Code plugin** (skills + agents + commands + hooks + data). The `Skills` repo only gets a thin pointer skill (phase 5.5).
2. **Decision logic = Markdown rules interpreted by the LLM.** No deterministic routing CLI, no HTTP router in V1. (The store adapter `scripts/store.py` is *data access*, not decision logic — that is allowed and required by P1.)
3. **Curator runs on GitHub Actions by default; Docker + cron (`ops/`) is the documented alternative.** Same skill, different runner.
4. **Four data principles (P1–P4)** — see `docs/PRD.md` §1a:
   - P1 storage behind an abstraction (`store` with `append / query / project / trace`; backends `files` now, `sqlite` before V1, DB/enterprise later)
   - P2 every decision + reasoning logged and traceable (`/toolbox:trace`; decisions carry all candidates and `rules_version`)
   - P3 scores are additive — `score.*` events; `my_score_current` is a computed projection
   - P4 data immutable; the LLM only appends, with `ts`, `actor`, `via`, `reason`; views are generated, never edited; CI enforces

---

## Open questions for Amit (PRD §12) — ask before phase 1 ends

1. Default customer profile name: `_default` or `team`?
2. Does `models.yaml` (prices) ship in the public plugin, or only in the private catalog?
3. Is the Hebrew `report` skill bundled in the plugin or an external dependency?

---

## Next steps, in order

### Phase 0 (0.5 day)

```
cd D:\Development\ai-toolbox
git init -b development
git add -A
git commit -m "init: ai-toolbox plugin skeleton + PRD v0.2 + work plan (v0.1.0)"
git checkout -b ai-toolbox
# then: gh repo create amitkuzi/ai-toolbox --private --source . --push   (needs Amit's OK / PAT)
```

- 0.2 `.claude-plugin/marketplace.json` — Guide agent (claude-code-guide) knows the current format; `plugin.json` already exists.
- 0.3 Architect (T3, once): grill the five decisions **and** P1–P4 for contradictions. Output goes to `catalog/ledger/decisions.jsonl` as `adr.added` events once the store exists — until then, write them to `docs/decisions-draft.md` and migrate in phase 1.6.
- 0.4 Register the project in Amit's workspace `projects/` registry (note: `D:\Development\projects` is an old code folder, not the registry — ask Amit where the registry actually lives, or create `D:\Development\AiAgent\projects\ai-toolbox.md`).

### Phase 1 (3 days) — the big one

Order matters: **1.1 schema → 1.2 store + files backend → 1.4 validate → 1.5 migration**. Do not start the migration script before the store exists, or the migration will write files directly and violate P1 on day one.

Migration rule of thumb: one `tool.added` event per record with `via: migration`, `actor: system:migration`, `reason: "imported from <path> (last_reviewed <date>)"`, plus one `score.seed` per record carrying the old `my_score` and its `score_rationale` as `reason`. Preserve the original `changelog.jsonl` timestamps as historical events — history is not thrown away.

### Model tiers for the work (work plan §4)

Migration / validation / backends / hooks → T1. `store.py` + contract test, rules, skills, docs → T2. Architecture review (0.3) and the eval suite (6.1) → T3, once each.

---

## Gotchas learned this session

- `D:\Development` root is **not** a git repo and its root `CLAUDE.md` describes a workspace layout (`inbox/`, `projects/`, `LLM/`…) that mostly does not exist at root. `inbox/` was created this session; the Hebrew docs originally delivered there were **moved into this repo** (`docs/he/`) at Amit's request — `D:\Development\inbox\ai-toolbox\` may still hold the v0.1 copies; treat this repo as canonical.
- Long `find`/`grep` over `D:\Development` times out through the device shell (2 min cap) — scope searches to a subfolder.
- **Do not run `git init`/`git commit` from the Cowork device shell** — it has no delete permission, git cannot remove its own lock/tmp files, and the repo ends up with stale locks (same failure mode as `Luctures/TaskTriagOrcetrator/_to_delete/git-stale-locks`). Run git from the Windows host (or Claude Code on the host).
- `D:\Development\inbox\ai-toolbox\` still holds the v0.1 copies (delete permission was declined this session). They are superseded by `docs/` here — safe to delete by hand.
- Two existing `tools.yaml` files disagree on `my_score` semantics; `selection-rules.md` §2a documents a measured ~1-point optimism bias in seed estimates. Keep that rule: an estimate never outranks a measurement.
- `ai-gateway/docs/PRD.md` §4.3–4.4 (Mission Router, scores log F-401…F-410) is the origin of the outcome-log design — reuse its IDs when writing `rules/05-outcome-scoring.md` so the two PRDs stay traceable to each other.

---

## Definition of "this handoff is consumed"

- [ ] `git log` shows the phase-0 commit on branch `ai-toolbox`
- [ ] `handoffs/2026-09-02-prd-approved.md` (this file) is committed
- [ ] A new handoff file exists for whatever phase you stop in
