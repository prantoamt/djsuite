#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# log-whisperer setup — runs on the EB EC2 host after every deployment.
#
# Installs log-whisperer, creates an analysis wrapper script, sets up a cron
# job, and enables a post-deploy baseline learning window so expected log
# changes don't trigger false alerts
# ---------------------------------------------------------------------------

# Source EB environment variables
if [ -f /opt/elasticbeanstalk/deployment/env.json ] && command -v jq >/dev/null 2>&1; then
  eval "$(jq -r 'to_entries|map("export \(.key)=\(.value|@sh)")|.[]' \
    /opt/elasticbeanstalk/deployment/env.json)"
elif [ -f /opt/elasticbeanstalk/deployment/env ]; then
  set -a
  # shellcheck disable=SC1091
  source /opt/elasticbeanstalk/deployment/env
  set +a
fi

# ── Master switch ──────────────────────────────────────────────────────────
if [ "${LOG_WHISPERER_ENABLED:-false}" != "true" ]; then
  echo "[log-whisperer] Disabled. Set LOG_WHISPERER_ENABLED=true to activate."
  # Clean up if previously installed but now disabled
  (crontab -l 2>/dev/null | grep -v 'logwhisperer' | crontab -) 2>/dev/null || true
  exit 0
fi

# ── Install log-whisperer ──────────────────────────────────────────────────
echo "[log-whisperer] Installing / upgrading log-whisperer..."
# Amazon Linux 2023 (Docker platform) may not have pip3 pre-installed
command -v pip3 >/dev/null 2>&1 || {
  echo "[log-whisperer] pip3 not found, installing..."
  dnf install -y python3-pip
}
pip3 install --upgrade --break-system-packages log-whisperer 2>/dev/null \
  || pip3 install --upgrade log-whisperer

# ── Resolve role ───────────────────────────────────────────────────────────
ROLE="${APP_ROLE:-unknown}"
echo "[log-whisperer] Detected APP_ROLE=${ROLE}"

# ── Persist env vars for cron ─────────────────────────────────────────────
# EB deployment env files are cleaned up after hooks finish, so the cron job
# can't read them at runtime. Save the relevant vars to a persistent file.
mkdir -p /opt/logwhisperer
# Values are single-quoted to safely handle special characters in passwords etc.
cat > /opt/logwhisperer/env << ENVFILE
APP_ROLE='${ROLE}'
LOG_WHISPERER_ENABLED='${LOG_WHISPERER_ENABLED:-false}'
LOG_WHISPERER_CRON_INTERVAL='${LOG_WHISPERER_CRON_INTERVAL:-15}'
LOG_WHISPERER_MIN_SEVERITY='${LOG_WHISPERER_MIN_SEVERITY:-WARN}'
LOG_WHISPERER_BASELINE_MINUTES='${LOG_WHISPERER_BASELINE_MINUTES:-30}'
LOG_WHISPERER_NTFY_TOPIC='${LOG_WHISPERER_NTFY_TOPIC:-}'
LOG_WHISPERER_NTFY_URL='${LOG_WHISPERER_NTFY_URL:-}'
LOG_WHISPERER_TELEGRAM_TOKEN='${LOG_WHISPERER_TELEGRAM_TOKEN:-}'
LOG_WHISPERER_TELEGRAM_CHAT='${LOG_WHISPERER_TELEGRAM_CHAT:-}'
LOG_WHISPERER_EMAIL_TO='${LOG_WHISPERER_EMAIL_TO:-}'
LOG_WHISPERER_EMAIL_FROM='${LOG_WHISPERER_EMAIL_FROM:-}'
LOG_WHISPERER_SMTP_HOST='${LOG_WHISPERER_SMTP_HOST:-}'
LOG_WHISPERER_SMTP_PORT='${LOG_WHISPERER_SMTP_PORT:-}'
LOG_WHISPERER_SMTP_USER='${LOG_WHISPERER_SMTP_USER:-}'
LOG_WHISPERER_SMTP_PASSWORD='${LOG_WHISPERER_SMTP_PASSWORD:-}'
ENVFILE
chmod 600 /opt/logwhisperer/env

# ── Create role-specific state directory ──────────────────────────────────
# Web and worker have very different log patterns, so each role gets its own
# pattern DB to avoid cross-contamination.
mkdir -p "/opt/logwhisperer/state/${ROLE}"

# ── Write the analysis wrapper script ──────────────────────────────────────
cat > /opt/logwhisperer/run.sh << 'WRAPPER'
#!/usr/bin/env bash
set -euo pipefail

# Source persisted env vars (written by postdeploy hook)
if [ -f /opt/logwhisperer/env ]; then
  set -a
  # shellcheck disable=SC1091
  source /opt/logwhisperer/env
  set +a
fi

# Bail out if disabled (env var may have changed since cron was installed)
if [ "${LOG_WHISPERER_ENABLED:-false}" != "true" ]; then
  exit 0
fi

# ── Resolve role for tagging ──────────────────────────────────────────────
ROLE="${APP_ROLE:-unknown}"
STATE_DB="/opt/logwhisperer/state/${ROLE}/patterns.db"
BASELINE_STATE="/opt/logwhisperer/state/${ROLE}/baseline"
LOG_TAG="log-whisperer[${ROLE}]"

# ── Find the app container ─────────────────────────────────────────────────
CID=$(docker ps -q -f "name=^/app$" | head -n1 || true)
[ -z "$CID" ] && CID=$(docker ps -q -f "publish=80" | head -n1 || true)
[ -z "$CID" ] && CID=$(docker ps -q -f "ancestor=aws_beanstalk/current-app:latest" | head -n1 || true)

if [ -z "$CID" ]; then
  echo "[log-whisperer] No app container found, skipping."
  exit 0
fi

# ── Configuration ─────────────────────────────────────────────────────────
INTERVAL="${LOG_WHISPERER_CRON_INTERVAL:-15}"
MIN_SEV="${LOG_WHISPERER_MIN_SEVERITY:-WARN}"

# ── Check baseline learning window ────────────────────────────────────────
BASELINE_FILE="/opt/logwhisperer/state/${ROLE}/baseline_until"
if [ -f "$BASELINE_FILE" ]; then
  BASELINE_UNTIL=$(cat "$BASELINE_FILE")
  NOW=$(date +%s)
  if [ "$NOW" -lt "$BASELINE_UNTIL" ]; then
    REMAINING=$(( (BASELINE_UNTIL - NOW) / 60 ))
    echo "[${LOG_TAG}] In baseline learning window (${REMAINING}m remaining). Learning only."
    log-whisperer \
      --docker "$CID" \
      --since "${INTERVAL}m" \
      --state-db "$STATE_DB" \
      --baseline-state "$BASELINE_STATE" \
      --baseline-learn "${INTERVAL}m" \
      2>&1 | logger -t "$LOG_TAG"
    exit 0
  else
    rm -f "$BASELINE_FILE"
  fi
fi

# ── Build notification flags ──────────────────────────────────────────────
NOTIFY_FLAGS=""

# ntfy (recommended — zero setup)
if [ -n "${LOG_WHISPERER_NTFY_TOPIC:-}" ]; then
  NOTIFY_FLAGS="${NOTIFY_FLAGS} --notify-ntfy-topic ${LOG_WHISPERER_NTFY_TOPIC}"
  [ -n "${LOG_WHISPERER_NTFY_URL:-}" ] && \
    NOTIFY_FLAGS="${NOTIFY_FLAGS} --notify-ntfy-server ${LOG_WHISPERER_NTFY_URL}"
fi

# Telegram
if [ -n "${LOG_WHISPERER_TELEGRAM_TOKEN:-}" ] && [ -n "${LOG_WHISPERER_TELEGRAM_CHAT:-}" ]; then
  NOTIFY_FLAGS="${NOTIFY_FLAGS} --notify-telegram-token ${LOG_WHISPERER_TELEGRAM_TOKEN} --notify-telegram-chat-id ${LOG_WHISPERER_TELEGRAM_CHAT}"
fi

# Email
if [ -n "${LOG_WHISPERER_EMAIL_TO:-}" ]; then
  NOTIFY_FLAGS="${NOTIFY_FLAGS} --notify-email-to ${LOG_WHISPERER_EMAIL_TO}"
  [ -n "${LOG_WHISPERER_EMAIL_FROM:-}" ] && \
    NOTIFY_FLAGS="${NOTIFY_FLAGS} --notify-email-from ${LOG_WHISPERER_EMAIL_FROM}"
  [ -n "${LOG_WHISPERER_SMTP_HOST:-}" ] && \
    NOTIFY_FLAGS="${NOTIFY_FLAGS} --notify-email-host ${LOG_WHISPERER_SMTP_HOST}"
  [ -n "${LOG_WHISPERER_SMTP_PORT:-}" ] && \
    NOTIFY_FLAGS="${NOTIFY_FLAGS} --notify-email-port ${LOG_WHISPERER_SMTP_PORT}"
  [ -n "${LOG_WHISPERER_SMTP_USER:-}" ] && \
    NOTIFY_FLAGS="${NOTIFY_FLAGS} --notify-email-user ${LOG_WHISPERER_SMTP_USER}"
  [ -n "${LOG_WHISPERER_SMTP_PASSWORD:-}" ] && \
    NOTIFY_FLAGS="${NOTIFY_FLAGS} --notify-email-pass ${LOG_WHISPERER_SMTP_PASSWORD}"
fi

# ── Run log-whisperer ─────────────────────────────────────────────────────
# shellcheck disable=SC2086
log-whisperer \
  --docker "$CID" \
  --since "${INTERVAL}m" \
  --state-db "$STATE_DB" \
  --baseline-state "$BASELINE_STATE" \
  --show-new \
  --min-severity "$MIN_SEV" \
  $NOTIFY_FLAGS \
  2>&1 | logger -t "$LOG_TAG"

WRAPPER
chmod +x /opt/logwhisperer/run.sh

# ── Set up cron ────────────────────────────────────────────────────────────
INTERVAL="${LOG_WHISPERER_CRON_INTERVAL:-15}"
CRON_ENTRY="*/${INTERVAL} * * * * /opt/logwhisperer/run.sh"

# Remove any old entry, then add the new one
(crontab -l 2>/dev/null | grep -v 'logwhisperer' || true; echo "$CRON_ENTRY") | crontab -

# ── Enable baseline learning window ───────────────────────────────────────
BASELINE_MIN="${LOG_WHISPERER_BASELINE_MINUTES:-30}"
BASELINE_UNTIL=$(date -d "+${BASELINE_MIN} minutes" +%s)
echo "$BASELINE_UNTIL" > "/opt/logwhisperer/state/${ROLE}/baseline_until"

echo "[log-whisperer] Installed (role=${ROLE}). Cron every ${INTERVAL}m. Baseline learning for ${BASELINE_MIN}m."
