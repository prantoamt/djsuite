#!/usr/bin/env bash
set -euo pipefail

# Remove any existing log-whisperer cron entries before the new deployment
# sets them up again. Prevents duplicate cron entries on config changes.
(crontab -l 2>/dev/null | grep -v 'logwhisperer' | crontab -) 2>/dev/null || true

echo "[log-whisperer] Cleaned up old cron entries."
