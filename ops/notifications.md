# Notifications — Failure alerts

Curator and auditor runs send failure alerts to ntfy.sh (default) or Slack (optional).

## Setup

### ntfy.sh (default, no auth required)

Create a private topic (append a random suffix to make it hard to guess):

```bash
# Test: send a message to your topic
curl -X POST -d "Test message from ai-toolbox" https://ntfy.sh/ai-toolbox-xyz123

# You'll see messages at: https://ntfy.sh/ai-toolbox-xyz123
```

Then set the environment variable:

```bash
# In GitHub Actions secrets:
NOTIFY_URL=https://ntfy.sh/ai-toolbox-xyz123

# Or locally:
export NOTIFY_URL=https://ntfy.sh/ai-toolbox-xyz123
```

Subscribe on your phone:
- iOS: ntfy app → "subscribe" → enter topic name
- Android: ntfy app → "+" → enter topic name
- Browser: visit the URL above and enable browser notifications

### Slack (optional)

Create an incoming webhook:
1. Go to Slack workspace → Settings → Apps & integrations → Manage → Custom integrations
2. Create an Incoming Webhook → choose channel → copy the URL
3. Set the environment variable:

```bash
# In GitHub Actions secrets:
SLACK_WEBHOOK=https://hooks.slack.com/services/T.../B.../xxxx

# Or locally:
export SLACK_WEBHOOK=https://hooks.slack.com/services/T.../B.../xxxx
```

### Both (redundancy)

Set both `NOTIFY_URL` and `SLACK_WEBHOOK` for dual delivery.

---

## What triggers a notification

- ❌ **Validation failed** — ledger corruption, schema error, append-only violation
- ❌ **Commit failed** — git error (e.g. merge conflict, permission denied)
- ❌ **Push failed** (warning) — network issue; commit is local, will retry next run
- ❌ **Agent execution failed** — Claude API error, network timeout (Phase 5+)

---

## Customizing

Edit `ops/notify.sh` to:
- Change default topic/webhook
- Add email (ntfy supports `@subject` emails)
- Add Discord, Teams, or other webhooks
- Customize message format

Examples:

```bash
# Email via ntfy
NOTIFY_URL=https://ntfy.sh/ai-toolbox?email=amit@example.com

# Twilio SMS (DIY with a webhook)
# Discord webhook
# PagerDuty incident
```

---

## Testing

```bash
# Test ntfy
bash ops/notify.sh test-event "This is a test message"

# Test Slack (if configured)
export SLACK_WEBHOOK=https://hooks.slack.com/...
bash ops/notify.sh test-event "Slack test"
```

---

## See also

- `ops/run-task.sh` — calls `notify.sh` on error
- `.github/workflows/*.yml` — GitHub Actions calls `notify.sh` on failure
