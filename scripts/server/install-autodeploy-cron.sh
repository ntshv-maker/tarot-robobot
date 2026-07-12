#!/bin/bash
# Установить автодеплой через cron (каждые 5 минут проверка git)
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/tarot-robobot}"
CRON_LINE="*/5 * * * * cd ${APP_DIR} && git fetch origin main >/dev/null 2>&1 && [ \$(git rev-parse HEAD) = \$(git rev-parse origin/main) ] || ${APP_DIR}/scripts/server/deploy.sh >> /var/log/tarot-robobot-deploy.log 2>&1"

( crontab -l 2>/dev/null | grep -v "tarot-robobot-deploy" || true
  echo "$CRON_LINE"
) | crontab -

echo "Autodeploy cron installed (every 5 minutes)"
