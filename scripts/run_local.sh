#!/bin/bash
# Локальный запуск без Docker: SQLite + память вместо Redis
set -e
cd "$(dirname "$0")/.."

export LOCAL_DEV=true
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./data/astorobot.db}"
export REDIS_URL="${REDIS_URL:-memory://local}"

echo "==> Установка зависимостей..."
python3 -m pip install -e ".[dev]" -q

echo "==> Создание локальной базы SQLite..."
PYTHONPATH=. python3 scripts/init_local_db.py

echo "==> Запуск бота (Ctrl+C для остановки)..."
PYTHONPATH=. python3 -m src.main
