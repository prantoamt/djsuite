#!/usr/bin/env bash
set -euo pipefail
export PATH="/app/.venv/bin:$PATH"

ROLE="${APP_ROLE:-web}"
IS_LEADER="${EB_IS_COMMAND_LEADER:-false}"

echo "[entrypoint] APP_ROLE=${ROLE}  EB_IS_COMMAND_LEADER=${IS_LEADER}"

case "$ROLE" in
  web)
    exec supervisord -c /app/supervisord_app.conf
    ;;

  worker)
    echo "Worker environment detected: copying nginx/celery.conf to /etc/nginx/conf.d/default.conf"
    cp ./nginx/celery.conf /etc/nginx/conf.d/default.conf
    # sanity: ensure required configs exist
    echo "[entrypoint] Leader -> start worker + beat"
    exec supervisord -c /app/supervisord_worker_beat.conf
    ;;

  *)
    echo "[entrypoint] Unknown APP_ROLE=${ROLE}" >&2
    exit 1
    ;;
esac
