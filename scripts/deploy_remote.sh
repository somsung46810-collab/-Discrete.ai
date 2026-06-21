#!/usr/bin/env bash
set -Eeuo pipefail

ENVIRONMENT="${1:?environment is required}"
ARCHIVE="${2:?archive path is required}"
DEPLOY_ROOT="${3:?deploy root is required}"
RELEASE_ID="${4:?release id is required}"
PORT="${5:?service port is required}"

RELEASES_DIR="$DEPLOY_ROOT/releases"
SHARED_DIR="$DEPLOY_ROOT/shared"
RELEASE_DIR="$RELEASES_DIR/$RELEASE_ID"
CURRENT_LINK="$DEPLOY_ROOT/current"
PREVIOUS_LINK="$DEPLOY_ROOT/previous"
SERVICE_NAME="discrete-ai-$ENVIRONMENT.service"
SYSTEMD_DIR="$HOME/.config/systemd/user"
HEALTH_URL="http://127.0.0.1:$PORT/api/health"

mkdir -p "$RELEASES_DIR" "$SHARED_DIR/storage" "$SYSTEMD_DIR"
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"
tar -xzf "$ARCHIVE" -C "$RELEASE_DIR"

if [[ -L "$CURRENT_LINK" ]]; then
  ln -sfn "$(readlink -f "$CURRENT_LINK")" "$PREVIOUS_LINK"
fi

ln -sfn "$SHARED_DIR/storage" "$RELEASE_DIR/storage"

if [[ ! -f "$SHARED_DIR/.env" ]]; then
  echo "Missing $SHARED_DIR/.env" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$SHARED_DIR/.env"
set +a
export DISCRETE_PORT="$PORT"
export DISCRETE_STORAGE_DIR="$SHARED_DIR/storage"
export DISCRETE_DATABASE_PATH="${DISCRETE_DATABASE_PATH:-$SHARED_DIR/discrete_art_studio.db}"

python3 -m venv "$RELEASE_DIR/.venv"
"$RELEASE_DIR/.venv/bin/python" -m pip install --upgrade pip
"$RELEASE_DIR/.venv/bin/python" -m pip install "$RELEASE_DIR"
"$RELEASE_DIR/.venv/bin/python" "$RELEASE_DIR/scripts/migrate.py"

cat > "$SYSTEMD_DIR/$SERVICE_NAME" <<UNIT
[Unit]
Description=Discrete Art Studio ($ENVIRONMENT)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$CURRENT_LINK
EnvironmentFile=$SHARED_DIR/.env
Environment=DISCRETE_PORT=$PORT
Environment=DISCRETE_STORAGE_DIR=$SHARED_DIR/storage
Environment=DISCRETE_DATABASE_PATH=$SHARED_DIR/discrete_art_studio.db
ExecStart=$CURRENT_LINK/.venv/bin/python -m cyglobs_app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
UNIT

ln -sfn "$RELEASE_DIR" "$CURRENT_LINK"
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user restart "$SERVICE_NAME"

health_ok=0
for _ in $(seq 1 20); do
  if curl --fail --silent --show-error "$HEALTH_URL" | grep -q '"status":"ok"'; then
    health_ok=1
    break
  fi
  sleep 3
done

if [[ "$health_ok" -ne 1 ]]; then
  echo "Health check failed; rolling back" >&2
  if [[ -L "$PREVIOUS_LINK" ]]; then
    ln -sfn "$(readlink -f "$PREVIOUS_LINK")" "$CURRENT_LINK"
    systemctl --user restart "$SERVICE_NAME"
    sleep 3
    curl --fail --silent --show-error "$HEALTH_URL" >/dev/null || true
  fi
  exit 1
fi

find "$RELEASES_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' \
  | sort -nr \
  | tail -n +6 \
  | cut -d' ' -f2- \
  | xargs -r rm -rf

echo "Deployment complete: $ENVIRONMENT $RELEASE_ID"
