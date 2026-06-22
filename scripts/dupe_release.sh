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

mkdir -p "$RELEASES_DIR" "$SHARED_DIR/storage" "$TARGET_DIR"

cleanup() {
  if [[ "${DUPE_COMPLETE:-0}" != "1" ]]; then
    rm -rf "$TARGET_DIR"
  fi
}
trap cleanup EXIT

cp -a --reflink=auto "$SOURCE_DIR/." "$TARGET_DIR/"
rm -rf "$TARGET_DIR/storage"
ln -sfn "$SHARED_DIR/storage" "$TARGET_DIR/storage"

for runtime_path in \
  cyglobsgl_generation.py \
  graphics_runtime.py \
  cyglobsgl.js \
  cyglobsgl.css \
  cyglobs_app.py \
  media_conversion.py \
  scripts/convert_media.py \
  cyglobs_framework/__init__.py \
  cyglobs_framework/comparators.py \
  cyglobs_framework/config.py \
  cyglobs_framework/contingency.py \
  cyglobs_framework/inverse_ops.py \
  cyglobs_framework/protocol.py \
  cyglobs_framework/services.py; do
  if [[ ! -f "$TARGET_DIR/$runtime_path" ]]; then
    echo "CyGlobs full-stack runtime missing after DUPE: $runtime_path" >&2
    exit 5
  fi
done

cat > "$TARGET_DIR/DUPE_MANIFEST.json" <<EOF
{
  "operation": "DUPE_AND_DEDUPE",
  "source_release": "$SOURCE_RELEASE_ID",
  "target_release": "$TARGET_RELEASE_ID",
  "shared_storage": "$SHARED_DIR/storage",
  "runtime": "CyGlobs Python Framework For Full Stack Developers",
  "renderer": "CyGlobsGL",
  "framework_injected": true,
  "cyglobsgl_injected": true,
  "media_interjection": "audio_to_video_to_image",
  "media_dedupe": "sha256 canonical output index",
  "external_provider": false,
  "dedupe_strategy": "single canonical active framework and media outputs"
}
EOF

DUPE_COMPLETE=1
trap - EXIT

echo "DUPE complete with CyGlobs full-stack media framework: $SOURCE_RELEASE_ID -> $TARGET_RELEASE_ID"
