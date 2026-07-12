#!/bin/bash
# Деплой на Amvera: push main → master
set -e
cd "$(dirname "$0")/.."

REMOTE="${AMVERA_REMOTE:-amvera}"
URL="${AMVERA_GIT_URL:-https://git.amvera.ru/ntshvrabota/run-tarot-robobot}"

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  git remote add "$REMOTE" "$URL"
  echo "Added remote $REMOTE -> $URL"
fi

echo "==> Push to Amvera (main -> master)..."
git push "$REMOTE" main:master

echo "==> Готово. Проверь статус сборки в панели Amvera."
