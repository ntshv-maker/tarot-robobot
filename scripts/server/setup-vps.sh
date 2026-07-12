#!/bin/bash
# Одноразовая настройка VPS. Запуск с Mac:
#   VPS_HOST=5.129.213.49 VPS_PASSWORD='...' ./scripts/server/setup-vps.sh
set -euo pipefail

VPS_HOST="${VPS_HOST:?Set VPS_HOST}"
VPS_USER="${VPS_USER:-root}"
APP_DIR="${APP_DIR:-/opt/tarot-robobot}"
REPO_URL="${REPO_URL:-https://github.com/ntshv-maker/tarot-robobot.git}"
DEPLOY_KEY="${DEPLOY_KEY:-$HOME/.ssh/tarot_robobot_deploy}"

if [[ -z "${VPS_PASSWORD:-}" ]] && ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${VPS_USER}@${VPS_HOST}" true 2>/dev/null; then
  echo "Set VPS_PASSWORD or configure SSH key access first."
  exit 1
fi

ssh_cmd() {
  if [[ -n "${VPS_PASSWORD:-}" ]] && ! command -v sshpass >/dev/null 2>&1; then
    export VPS_CMD="$*"
    expect "$(dirname "$0")/_ssh_expect.exp"
  elif [[ -n "${VPS_PASSWORD:-}" ]]; then
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=accept-new "${VPS_USER}@${VPS_HOST}" "$@"
  else
    ssh -o StrictHostKeyChecking=accept-new "${VPS_USER}@${VPS_HOST}" "$@"
  fi
}

scp_cmd() {
  if [[ -n "${VPS_PASSWORD:-}" ]] && ! command -v sshpass >/dev/null 2>&1; then
    export SCP_LOCAL="$1"
    export SCP_REMOTE="$2"
    expect "$(dirname "$0")/_scp_expect.exp"
  elif [[ -n "${VPS_PASSWORD:-}" ]]; then
    sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=accept-new "$@"
  else
    scp -o StrictHostKeyChecking=accept-new "$@"
  fi
}

if [[ ! -f "$DEPLOY_KEY" ]]; then
  echo "==> Generate deploy SSH key"
  ssh-keygen -t ed25519 -f "$DEPLOY_KEY" -N "" -C "github-actions-deploy-tarot-robobot"
fi

echo "==> Install Docker on VPS"
ssh_cmd bash -s <<'REMOTE'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
if ! command -v docker >/dev/null 2>&1; then
  apt-get update
  apt-get install -y ca-certificates curl git
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
fi
docker --version
docker compose version
REMOTE

echo "==> Clone repository"
ssh_cmd "mkdir -p $(dirname "$APP_DIR") && if [ ! -d '$APP_DIR/.git' ]; then git clone '$REPO_URL' '$APP_DIR'; fi"

echo "==> Install deploy key for GitHub Actions"
PUB_KEY="$(cat "${DEPLOY_KEY}.pub")"
ssh_cmd "mkdir -p ~/.ssh && chmod 700 ~/.ssh && grep -qxF '$PUB_KEY' ~/.ssh/authorized_keys 2>/dev/null || echo '$PUB_KEY' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

echo "==> Upload production .env"
scp_cmd <(python3 "$(dirname "$0")/build-server-env.py") "${VPS_USER}@${VPS_HOST}:${APP_DIR}/.env"
ssh_cmd "chmod 600 ${APP_DIR}/.env"

echo "==> First deploy"
ssh_cmd "cd '$APP_DIR' && chmod +x scripts/server/*.sh && ./scripts/server/deploy.sh"

echo "==> Install autodeploy cron"
ssh_cmd "cd '$APP_DIR' && ./scripts/server/install-autodeploy-cron.sh"

echo ""
echo "Deploy key (add to GitHub Secrets as VPS_SSH_KEY):"
echo "  cat ${DEPLOY_KEY}"
echo ""
echo "GitHub Secrets:"
echo "  VPS_HOST=${VPS_HOST}"
echo "  VPS_USER=${VPS_USER}"
echo "  VPS_SSH_KEY=<private key above>"
