#!/bin/bash
# notify.sh — Send failure alerts to ntfy.sh or Slack
# Usage: ./notify.sh <event> <message> [optional-context]
# Example: ./notify.sh curator-fail "daily-refresh failed at 07:15 UTC"

EVENT=$1
MESSAGE=$2
CONTEXT=${3:-""}

# Configuration (set via environment or edit here)
NOTIFY_URL=${NOTIFY_URL:-"https://ntfy.sh/ai-toolbox"}
SLACK_WEBHOOK=${SLACK_WEBHOOK:-""}

# Send to ntfy.sh (default, minimal setup)
if [ -n "$NOTIFY_URL" ]; then
  curl -X POST \
    -H "Title: AI Toolbox Alert — ${EVENT}" \
    -H "Priority: high" \
    -d "${MESSAGE}${CONTEXT:+

$CONTEXT}" \
    "$NOTIFY_URL" 2>/dev/null || true
fi

# Send to Slack (optional, if webhook is set)
if [ -n "$SLACK_WEBHOOK" ]; then
  curl -X POST "$SLACK_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d '{
      "text": ":warning: AI Toolbox Alert",
      "attachments": [{
        "color": "danger",
        "title": "'$EVENT'",
        "text": "'$MESSAGE'",
        "footer": "ai-toolbox scheduled run"
      }]
    }' 2>/dev/null || true
fi
