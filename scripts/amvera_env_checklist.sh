#!/bin/bash
# Показать переменные из .env для копирования в Amvera (без вывода полных секретов в лог)
set -e
cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "Файл .env не найден"
  exit 1
fi

mask() {
  local v="$1"
  local n=${#v}
  if (( n <= 8 )); then
    echo "****"
  else
    echo "${v:0:4}...${v: -4}"
  fi
}

echo "=== Скопируй в Amvera → Проект → Переменные окружения ==="
echo ""

while IFS='=' read -r key value; do
  [[ -z "$key" || "$key" =~ ^# ]] && continue
  value="${value%$'\r'}"
  case "$key" in
    BOT_TOKEN|KIE_API_KEY|DASHBOARD_PASSWORD|DASHBOARD_SECRET)
      echo "$key=$(mask "$value")  ← вставь полное значение из .env"
      ;;
    DATABASE_URL|REDIS_URL|LOCAL_DEV|DASHBOARD_HOST|DASHBOARD_PORT|PYTHONUNBUFFERED)
      echo "# $key уже в Dockerfile, можно не задавать"
      ;;
    *)
      echo "$key=$value"
      ;;
  esac
done < .env

echo ""
echo "Обязательно: BOT_TOKEN, KIE_API_KEY, DASHBOARD_PASSWORD, REFERRAL_BOT_USERNAME"
echo "Рекомендуется: ADMIN_IDS (твой Telegram ID)"
