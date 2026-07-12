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

echo "==> Starting Telegram bot"
python3 -m src.main &
BOT_PID=$!

cleanup() {
  kill "${BOT_PID}" 2>/dev/null || true
}
trap cleanup EXIT

echo "==> Starting admin dashboard on ${DASHBOARD_HOST}:${DASHBOARD_PORT}"
exec python3 -m src.dashboard
