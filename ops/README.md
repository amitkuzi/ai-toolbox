# ops/ — Self-hosted scheduling

Alternative to GitHub Actions. Run curator/auditor tasks via Docker or local cron.

## Quick start

### Docker (recommended for fresh installs)

```bash
# Build the image
docker compose build

# Run daily refresh
docker compose run --rm runner

# Run weekly refresh
docker compose run -e TASK_TYPE=weekly --rm runner

# Run monthly audit
docker compose run -e TASK_TYPE=monthly --rm runner
```

### Local cron (if you already have the repo on a server)

```bash
# Make the script executable
chmod +x ops/run-task.sh

# Test it once manually
./ops/run-task.sh daily

# Add to crontab (runs at 07:00 every day)
# crontab -e
# 0 7 * * * cd /path/to/ai-toolbox && ./ops/run-task.sh daily
# 0 8 * * 1 cd /path/to/ai-toolbox && ./ops/run-task.sh weekly
# 0 9 1 * * cd /path/to/ai-toolbox && ./ops/run-task.sh monthly
```

## Environment variables

- `CLAUDE_API_KEY` — required for Claude-powered curator/auditor tasks (Phase 5+)
- `TOOLBOX_BASE_DIR` — optional; defaults to `./catalog`

## Workflow

Each task run:

1. **Validate** — `scripts/validate.py` (append-only guard, schema check)
2. **Run curator/auditor** — invoke Claude agent (Phase 5+)
3. **Project views** — `store.py project` (regenerate YAML views)
4. **Validate again** — ensure no violations
5. **Commit** — if changes exist
6. **Push** — to origin

Logs go to `../logs/curator-{daily|weekly|monthly}-*.log`.

## Troubleshooting

### "Validation failed; aborting"

Check `scripts/validate.py` output. Common issues:
- A line was deleted from `catalog/ledger/*.jsonl` (P4 violation)
- `views/` was hand-edited (P4 violation)
- Missing required fields on an event (`ts`, `actor`, `reason`)

### "Push failed"

Network issue; the local commit succeeded. Next run will retry.

### "No changes; task complete"

Curator ran but found no new tools to add, no sources to update, etc. This is normal.

---

## See also

- `.github/workflows/` — GitHub Actions alternative
- `skills/toolbox-curate/` — curator task definition
- `agents/toolbox-curator.md` — curator agent role
