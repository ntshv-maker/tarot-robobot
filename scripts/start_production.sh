#!/bin/bash
set -euo pipefail

mkdir -p /data

export LOCAL_DEV="${LOCAL_DEV:-false}"
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:////data/astorobot.db}"
export REDIS_URL="${REDIS_URL:-memory://local}"
export DASHBOARD_HOST="${DASHBOARD_HOST:-0.0.0.0}"
export DASHBOARD_PORT="${DASHBOARD_PORT:-80}"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"

cd /app

echo "==> Initializing database at ${DATABASE_URL}"
python3 scripts/init_local_db.py

if [[ -n "${DASHBOARD_PASSWORD:-}" ]]; then
  echo "==> Starting admin dashboard on ${DASHBOARD_HOST}:${DASHBOARD_PORT}"
  python3 -m src.dashboard &
  DASHBOARD_PID=$!
  cleanup() {
    kill "${DASHBOARD_PID}" 2>/dev/null || true
  }
  trap cleanup EXIT
else
  echo "==> DASHBOARD_PASSWORD not set — dashboard disabled"
fi

echo "==> Starting Telegram bot (foreground)"
exec python3 -m src.main
