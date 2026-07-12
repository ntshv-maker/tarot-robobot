#!/bin/bash
# Деплой на Amvera: остановить локально → push main → master
set -e
cd "$(dirname "$0")/.."

REMOTE="${AMVERA_REMOTE:-amvera}"
URL="${AMVERA_GIT_URL:-https://git.amvera.ru/ntshvrabota/run-tarot-robobot}"

echo "==> Stopping local bot (avoid token conflict)..."
bash scripts/stop_local.sh

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  git remote add "$REMOTE" "$URL"
  echo "Added remote $REMOTE -> $URL"
fi

if [[ -f .env ]]; then
  echo ""
  echo "⚠️  Убедись, что в Amvera → Переменные окружения заданы:"
  echo "   BOT_TOKEN, KIE_API_KEY, DASHBOARD_PASSWORD, REFERRAL_BOT_USERNAME=tarot_robobot"
  echo "   Шаблон: amvera.env.example"
  echo ""
fi

echo "==> Push to Amvera (main -> master)..."
git push "$REMOTE" main:master

echo ""
echo "✅ Код отправлен. Открой панель Amvera → run-tarot-robobot"
echo "   Дождись статуса «Успешно развернуто», затем проверь /start в Telegram."
