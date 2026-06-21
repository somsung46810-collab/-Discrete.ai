#!/usr/bin/env bash
set -Eeuo pipefail

DEPLOY_ROOT="${1:?deploy root is required}"
SOURCE_RELEASE_ID="${2:?source release id is required}"
TARGET_RELEASE_ID="${3:?target release id is required}"

validate_release_id() {
  local value="$1"
  if [[ ! "$value" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "Invalid release id: $value" >&2
    exit 2
  fi
}

validate_release_id "$SOURCE_RELEASE_ID"
validate_release_id "$TARGET_RELEASE_ID"

if [[ "$SOURCE_RELEASE_ID" == "$TARGET_RELEASE_ID" ]]; then
  echo "Source and target release ids must differ" >&2
  exit 2
fi

RELEASES_DIR="$DEPLOY_ROOT/releases"
SOURCE_DIR="$RELEASES_DIR/$SOURCE_RELEASE_ID"
TARGET_DIR="$RELEASES_DIR/$TARGET_RELEASE_ID"
SHARED_DIR="$DEPLOY_ROOT/shared"

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Source release does not exist: $SOURCE_DIR" >&2
  exit 3
fi

if [[ -e "$TARGET_DIR" ]]; then
  echo "Target release already exists: $TARGET_DIR" >&2
  exit 4
fi

mkdir -p "$RELEASES_DIR" "$SHARED_DIR/storage"
mkdir -p "$TARGET_DIR"

cleanup() {
  if [[ "${DUPE_COMPLETE:-0}" != "1" ]]; then
    rm -rf "$TARGET_DIR"
  fi
}
trap cleanup EXIT

# Copy the immutable application release. Shared data is never copied.
# Existing storage links are replaced with the target environment's shared link.
cp -a --reflink=auto "$SOURCE_DIR/." "$TARGET_DIR/"
rm -rf "$TARGET_DIR/storage"
ln -sfn "$SHARED_DIR/storage" "$TARGET_DIR/storage"

cat > "$TARGET_DIR/DUPE_MANIFEST.json" <<EOF
{
  "operation": "DUPE",
  "source_release": "$SOURCE_RELEASE_ID",
  "target_release": "$TARGET_RELEASE_ID",
  "shared_storage": "$SHARED_DIR/storage"
}
EOF

DUPE_COMPLETE=1
trap - EXIT

echo "DUPE complete: $SOURCE_RELEASE_ID -> $TARGET_RELEASE_ID"
