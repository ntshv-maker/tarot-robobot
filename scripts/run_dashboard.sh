#!/bin/bash
set -e
cd "$(dirname "$0")/.."

export LOCAL_DEV="${LOCAL_DEV:-true}"
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./data/astorobot.db}"

echo "==> Установка зависимостей..."
python3 -m pip install -e ".[dev]" -q

echo "==> Обновление схемы SQLite..."
PYTHONPATH=. python3 scripts/init_local_db.py

if [ -z "$DASHBOARD_PASSWORD" ] && [ -f .env ]; then
  export $(grep -E '^DASHBOARD_PASSWORD=' .env | xargs) 2>/dev/null || true
fi

if [ -z "$DASHBOARD_PASSWORD" ]; then
  echo "Ошибка: задай DASHBOARD_PASSWORD в .env"
  echo "Пример: DASHBOARD_PASSWORD=admin123"
  exit 1
fi

PORT="${DASHBOARD_PORT:-8080}"
echo "==> Дэшборд: http://127.0.0.1:${PORT}"
PYTHONPATH=. python3 -m src.dashboard
