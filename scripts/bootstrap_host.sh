#!/usr/bin/env bash
set -Eeuo pipefail

DEPLOY_USER="${1:?deployment user is required}"
STAGING_ROOT="${2:-/home/$DEPLOY_USER/apps/staging}"
PRODUCTION_ROOT="${3:-/home/$DEPLOY_USER/apps/production}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this script as root" >&2
  exit 1
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3 python3-venv python3-pip bash tar curl openssh-server caddy sqlite3

if ! id "$DEPLOY_USER" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "$DEPLOY_USER"
fi

install -d -o "$DEPLOY_USER" -g "$DEPLOY_USER" "$STAGING_ROOT" "$PRODUCTION_ROOT"
install -d -o "$DEPLOY_USER" -g "$DEPLOY_USER" \
  "$STAGING_ROOT/shared/storage" "$STAGING_ROOT/shared/backups" \
  "$PRODUCTION_ROOT/shared/storage" "$PRODUCTION_ROOT/shared/backups"

loginctl enable-linger "$DEPLOY_USER"
systemctl enable --now ssh
systemctl enable --now caddy

cat <<EOF
Host bootstrap complete.

Next actions:
1. Add the deployment SSH public key to /home/$DEPLOY_USER/.ssh/authorized_keys
2. Copy deploy/Caddyfile.example to /etc/caddy/Caddyfile and replace domain placeholders
3. Run: caddy validate --config /etc/caddy/Caddyfile
4. Run: systemctl reload caddy
5. Configure GitHub staging and production environments
EOF
