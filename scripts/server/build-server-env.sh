#!/bin/bash
set -euo pipefail

# Build .env for VPS from local .env (stdout)
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOCAL_ENV="${ROOT}/.env"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -hex 16)}"

if [[ ! -f "$LOCAL_ENV" ]]; then
  echo "Missing $LOCAL_ENV" >&2
  exit 1
fi

echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}"
echo "LOCAL_DEV=false"
echo "REDIS_URL=redis://redis:6379/0"
echo "DASHBOARD_HOST=0.0.0.0"
echo "DASHBOARD_PORT=8080"
echo "PYTHONUNBUFFERED=1"

grep -E '^(BOT_TOKEN|KIE_|USD_TO_RUB|LLM_|REFERRAL_BOT_USERNAME|ADMIN_IDS|DASHBOARD_|TIMEZONE|MORNING_|EVENING_|WEEKLY_|PRIVACY_|CONSENT_|OFFER_|TYPING_)=' "$LOCAL_ENV" \
  | grep -v '^DATABASE_URL=' \
  | grep -v '^REDIS_URL=' \
  | grep -v '^LOCAL_DEV=' \
  | grep -v '^DASHBOARD_HOST=' \
  | grep -v '^DASHBOARD_PORT='
