FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml setup.py README.md ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
COPY prompts ./prompts
COPY assets ./assets
COPY scripts ./scripts

RUN pip install --no-cache-dir -e . \
    && chmod +x scripts/start_production.sh

ENV PYTHONUNBUFFERED=1 \
    LOCAL_DEV=false \
    DATABASE_URL=sqlite+aiosqlite:////data/astorobot.db \
    REDIS_URL=memory://local \
    DASHBOARD_HOST=0.0.0.0 \
    DASHBOARD_PORT=80

CMD ["/app/scripts/start_production.sh"]
