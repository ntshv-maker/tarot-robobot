#!/bin/bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/tarot-robobot}"
BRANCH="${BRANCH:-main}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

cd "$APP_DIR"

echo "==> Pull latest code"
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

echo "==> Rebuild and restart containers"
docker compose -f "$COMPOSE_FILE" up -d --build --remove-orphans

echo "==> Cleanup old images"
docker image prune -f

echo "==> Status"
docker compose -f "$COMPOSE_FILE" ps
