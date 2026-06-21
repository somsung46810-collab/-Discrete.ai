#!/usr/bin/env bash
set -Eeuo pipefail

DATABASE_PATH="${1:?database path is required}"
BACKUP_DIR="${2:?backup directory is required}"
RETENTION_DAYS="${3:-14}"

mkdir -p "$BACKUP_DIR"
if [[ ! -f "$DATABASE_PATH" ]]; then
  echo "Database does not exist: $DATABASE_PATH" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BASENAME="discrete-art-studio-$STAMP.db"
TARGET="$BACKUP_DIR/$BASENAME"

python3 - "$DATABASE_PATH" "$TARGET" <<'PY'
import sqlite3
import sys

source, target = sys.argv[1:3]
with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
    src.backup(dst)
    result = dst.execute("PRAGMA integrity_check").fetchone()
    if not result or result[0] != "ok":
        raise SystemExit(f"backup integrity check failed: {result}")
PY

sha256sum "$TARGET" > "$TARGET.sha256"
find "$BACKUP_DIR" -type f -name 'discrete-art-studio-*.db*' -mtime "+$RETENTION_DAYS" -delete

echo "Backup complete: $TARGET"
