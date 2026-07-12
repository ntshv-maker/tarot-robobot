# Асторобот / Лея

Telegram-бот: нумерология, Таро, астрология.

## Локальный запуск без Docker (самый простой)

```bash
cd /Users/admin/Desktop/bot
chmod +x scripts/run_local.sh
./scripts/run_local.sh
```

Используется SQLite (файл `data/astorobot.db`) и память вместо Redis — **ничего ставить не нужно**, только Python.

Или вручную:

```bash
export LOCAL_DEV=true
export DATABASE_URL=sqlite+aiosqlite:///./data/astorobot.db
export REDIS_URL=memory://local
pip install -e ".[dev]"
PYTHONPATH=. python3 scripts/init_local_db.py
PYTHONPATH=. python3 -m src.main
```

## Запуск с Docker (PostgreSQL + Redis)

```bash
cp .env.example .env
# заполните BOT_TOKEN, KIE_API_KEY, ADMIN_IDS

docker compose up -d postgres redis
pip install -e ".[dev]"
alembic upgrade head
python -m src.main
```

## Админ-команды

- `/confirm_payment <purchase_id>` — подтвердить оплату (заглушка)
- `/stats` — статистика пользователей
- `/llm_cost` — расход токенов Gemini в рублях

## Веб-дэшборд (заявки + переписка)

```bash
# В .env задай DASHBOARD_PASSWORD=...
chmod +x scripts/run_dashboard.sh
./scripts/run_dashboard.sh
```

Открой http://127.0.0.1:8080 — заявки на оплату, подтверждение/отклонение, история чатов пользователей.

Подробнее: [docs/admin.md](docs/admin.md)

## Деплой на Amvera

```bash
git remote add amvera https://git.amvera.ru/ntshvrabota/run-tarot-robobot
git push amvera main:master
```

В интерфейсе Amvera задай переменные из [docs/deploy-amvera.md](docs/deploy-amvera.md) (`BOT_TOKEN`, `KIE_API_KEY`, `DASHBOARD_PASSWORD`, `ADMIN_IDS`).

Подробная инструкция: [docs/deploy-amvera.md](docs/deploy-amvera.md)

## Тесты

```bash
pytest
```
