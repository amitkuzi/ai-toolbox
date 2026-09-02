# ai-toolbox — agent operating notes

Read before doing anything in this repo:

1. `docs/PRD.md` — especially §1a **Data principles (P1–P4)**. They are binding.
2. `handoffs/` — newest file first. It says where the last session stopped.
3. `docs/he/WorkPlan.md` — which phase and task you are on.

## Hard rules

- **Never edit a file under `catalog/ledger/`.** Append only, through `scripts/store.py append` once it exists. Every appended event carries `ts`, `actor`, `via`, and a `reason`.
- **Never hand-edit `catalog/views/`.** Views are produced by `scripts/store.py project`.
- **No file under `rules/`, `skills/`, `agents/`, `commands/` may reference a catalog path.** Access goes through `store`.
- Repo language is English. Deliverables for Amit are Hebrew and go to `docs/he/` (or his workspace `inbox/`).
- Branching and commit prefixes follow `D:\Development\.claude\skills\git-conventions` — work on `development` for workspace-level changes, on branch `ai-toolbox` for project work. Put the plugin version in every commit message.

## Where things go

| Thing | Path |
|---|---|
| Decision logic (Markdown rules) | `rules/NN-*.md` |
| Skills / agents / commands / hooks | `skills/`, `agents/`, `commands/`, `hooks/` |
| Storage adapter + backends | `scripts/store.py`, `scripts/backends/` |
| Source of truth (append-only) | `catalog/ledger/*.jsonl` |
| Generated views | `catalog/views/` |
| Per-user weights and constraints | `profiles/*.yaml` |
| Session handoffs | `handoffs/YYYY-MM-DD-*.md` |
