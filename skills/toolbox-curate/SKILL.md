---
name: toolbox-curate
description: Scheduled routines (daily/weekly) to discover, validate, and score tools from sources. Reads and appends to ledger through store.py (P1/P4). Daily run updates catalog daily; weekly run hunts new sources.
---

# toolbox-curate

Implements §5.3 of `docs/PRD.md` (daily-refresh, weekly-sources). Works only through
`scripts/store.py append/query/project` (P1/P4) — never edits a view or ledger line directly.
Curator is **T1 only** (`--max-turns 40`); see `agents/toolbox-curator.md` for tool allowlist.

---

## Daily run — `daily-refresh`

Called by `.github/workflows/daily-refresh.yml` at 07:00 UTC. Discover new tools from
high-confidence sources, validate oldest records, close closed gaps.

### Steps (append-only flow)

1. **Query routable sources**
   ```bash
   python scripts/store.py query sources --filter "value_score>=3,last_checked<1-day"
   ```
   Scope: only sources where `value_score >= 3` (high confidence) and not checked today.

2. **Per source: discover new tools**
   - Scan the source (web, API, docs, changelog) for new or updated tool records
   - Skip if already cataloged (check `id` uniqueness)
   - For each new tool:
     ```bash
     python scripts/store.py append --kind tool.added --subject-id <tool-slug> \
       --actor agent:toolbox-curator --via daily-run --reason "<source name>, <reason for adding>" \
       --payload '{...}'
     ```
   - Immediately append an initial `score.seed` at `estimate: true` based on first-glance assessment:
     ```bash
     python scripts/store.py append --kind score.seed --subject-id <tool-slug> \
       --actor agent:toolbox-curator --via daily-run --reason "<rubric: cost/local/agent_ready/license>" \
       --payload '{"score": <1-10>, "task_type": "general"}'
     ```

3. **Validate oldest `seed-unverified` slice**
   - Query: `python scripts/store.py query tools --filter "review_status=seed-unverified" --limit 5`
   - For each tool, spot-check docs for breaking changes or deprecation
   - If still valid: `python scripts/store.py append --kind tool.status --subject-id <id> --actor agent:toolbox-curator --via daily-run --reason "re-validated: <what was checked>" --payload '{"review_status": "verified"}'`
   - If dead/stale: `--payload '{"review_status": "dead", "reason_retired": "...}'`

4. **Try to close gaps** (query open gaps from the ledger)
   - Query: `python scripts/store.py query gaps --filter "kind=gap.opened,status!=closed"`
   - For each gap (e.g. "need a free hebrew OCR tool"), re-check sources
   - If a tool now covers it: `python scripts/store.py append --kind gap.closed --subject-id <gap-id> --actor agent:toolbox-curator --via daily-run --reason "found: <tool-id>" --payload '{}'`

5. **Reproject the catalog**
   ```bash
   python scripts/store.py project
   ```

6. **Validate the tree**
   ```bash
   python scripts/validate.py
   ```
   Fails if ledger has a deletion/edit, if a view is hand-edited, or if schema is broken.

7. **Commit** (if changes)
   ```bash
   git add ledger/ views/
   git commit -m "curate: daily refresh (N new tools, M verified)" -m "Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
   ```

---

## Weekly run — `weekly-sources`

Called by `.github/workflows/weekly-sources.yml` at 08:00 UTC Monday.
Re-score sources for freshness and hunt for new sources.

### Steps

1. **Re-score existing sources** (rescore each source's `value_score` if `last_checked > 7 days`)
   - Fetch the source again
   - Count: new tools found, deprecations, breaking changes
   - Recompute `value_score` (1–5 scale; see `rules/07-data-contract.md` for rubric)
   - If score changed: `python scripts/store.py append --kind source.revised --subject-id <source-id> --actor agent:toolbox-curator --via weekly-run --reason "re-scored: <metric delta>" --payload '{"value_score": <new-score>}'`

2. **Hunt new sources**
   - Scan for sources mentioned in tool changelogs, discussions, or tool homepages
   - Assess each against the `value_score` rubric
   - For promising sources (`value_score >= 3`): `python scripts/store.py append --kind source.added --subject-id <source-slug> --actor agent:toolbox-curator --via weekly-run --reason "<description>" --payload '{...}'`

3. **List needs_user_action** in commit message
   - Flag any source that dropped below `value_score: 2` (deprecated, too noisy, etc.)
   - List in commit body for Amit to review — curator does not retire sources, human does

4. **Reproject and validate**
   ```bash
   python scripts/store.py project
   python scripts/validate.py
   ```

5. **Commit**
   ```bash
   git add ledger/ views/
   git commit -m "curate: weekly source refresh" -m "needs_user_action:
   - source:xyz dropped to value_score:1 (deprecated)"
   ```

---

## Safety (P1–P4 compliance)

- ✅ **P1:** All data written via `store.py append` — never direct file edit
- ✅ **P2:** Every event has `reason` (why this tool/source), `ts`, `actor`, `via`
- ✅ **P3:** Scores are `score.seed` (immutable estimate) or `score.retract` (correction)
- ✅ **P4:** Only `*.added` / `*.revised` / `*.status` events; never edits or deletes

---

## Do not

- Do not edit the views directory — `store project` is the only writer
- Do not delete or edit a ledger line — append a `*.retired` event instead
- Do not append `tool.added` without a preceding `score.seed`
- Do not use `actor: human:*` for curator events — curator is always `agent:toolbox-curator`
- Do not skip validation before commit — `python scripts/validate.py` must pass
- Do not retire a source directly — append `needs_user_action` flag in commit message for Amit to decide

---

## Running locally (for testing)

```bash
export TOOLBOX_BASE_DIR=./catalog
python scripts/store.py query sources --filter "value_score>=3" --limit 3
# Then follow steps 2–7 for a subset
```
