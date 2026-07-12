#!/bin/bash
set -euo pipefail
cd /app
echo "==> Running database migrations"
alembic upgrade head
alembic current
echo "==> Starting Telegram bot"
exec python -m src.main
