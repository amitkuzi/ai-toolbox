#!/bin/bash
# run-task.sh — Execute curator/auditor tasks (daily/weekly/monthly)
# Usage: ./run-task.sh <daily|weekly|monthly>
# For cron: 0 7 * * * cd /opt/ai-toolbox && ./ops/run-task.sh daily

set -e

TASK_TYPE=${1:-daily}
WORKSPACE=${TOOLBOX_BASE_DIR:-.}
LOG_FILE="${WORKSPACE}/../logs/curator-${TASK_TYPE}-$(date +%Y%m%d-%H%M%S).log"

mkdir -p "${WORKSPACE}/../logs"

echo "[$(date)] Starting ${TASK_TYPE} run..." | tee -a "$LOG_FILE"

cd "$WORKSPACE" || {
  bash ops/notify.sh "curator-error" "Failed to cd to workspace"
  exit 1
}

# 1. Fetch latest
echo "[$(date)] Pulling latest changes..." | tee -a "$LOG_FILE"
git pull --quiet 2>>$LOG_FILE || true

# 2. Validate schema before proceeding
echo "[$(date)] Validating catalog..." | tee -a "$LOG_FILE"
python scripts/validate.py >>$LOG_FILE 2>&1 || {
  echo "❌ Validation failed; aborting"
  bash ops/notify.sh "curator-${TASK_TYPE}-fail" "Validation failed at $(date)"
  exit 1
}

# 3. Run the curator (actual invocation via Claude API)
# Phase 5 will integrate with Claude API; for now, just project the views
echo "[$(date)] Running curator agent for ${TASK_TYPE}..." | tee -a "$LOG_FILE"
case "$TASK_TYPE" in
  daily)
    # Daily: discover, validate, close gaps
    python scripts/store.py project >>$LOG_FILE 2>&1
    ;;
  weekly)
    # Weekly: re-score sources, hunt new ones
    python scripts/store.py project >>$LOG_FILE 2>&1
    ;;
  monthly)
    # Monthly: auditor (separate agent, creates PR)
    python scripts/store.py project >>$LOG_FILE 2>&1
    ;;
  *)
    echo "Unknown task type: $TASK_TYPE"
    exit 1
    ;;
esac

# 4. Re-project views (always after any changes)
echo "[$(date)] Projecting views..." | tee -a "$LOG_FILE"
python scripts/store.py project >>$LOG_FILE 2>&1

# 5. Validate again (ensure P4: append-only is still true)
echo "[$(date)] Final validation..." | tee -a "$LOG_FILE"
python scripts/validate.py >>$LOG_FILE 2>&1 || {
  echo "❌ Final validation failed; aborting commit"
  bash ops/notify.sh "curator-${TASK_TYPE}-fail" "Final validation failed at $(date)"
  exit 1
}

# 6. Commit if changes exist
echo "[$(date)] Checking for changes..." | tee -a "$LOG_FILE"
if git diff --quiet catalog/ledger/ catalog/views/; then
  echo "✅ No changes; task complete"
  exit 0
fi

echo "[$(date)] Committing changes..." | tee -a "$LOG_FILE"
git add catalog/ledger/ catalog/views/ 2>>$LOG_FILE
git commit -m "curate: ${TASK_TYPE} run" \
  -m "Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>" \
  2>>$LOG_FILE || {
  echo "❌ Commit failed"
  exit 1
}

# 7. Push
echo "[$(date)] Pushing to origin..." | tee -a "$LOG_FILE"
git push --quiet 2>>$LOG_FILE || {
  echo "⚠ Push failed (may be network issue); local commit OK"
}

echo "✅ ${TASK_TYPE} run complete at $(date)" | tee -a "$LOG_FILE"
