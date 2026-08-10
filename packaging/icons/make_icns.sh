#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <source-1024x1024.png> [output.icns]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_PNG="$1"
OUT_ICNS="${2:-assets/icon.icns}"
ICONSET_DIR="$(mktemp -d /tmp/rkflash-iconset.XXXXXX).iconset"
PREPARED_BASE="$(mktemp /tmp/rkflash-icon-processed.XXXXXX)"
PREPARED_PNG="${PREPARED_BASE}.png"
INPUT_FOR_ICONSET="$SRC_PNG"

if [[ ! -f "$SRC_PNG" ]]; then
  echo "Source PNG not found: $SRC_PNG"
  exit 1
fi

mkdir -p "$(dirname "$OUT_ICNS")"
mkdir -p "$ICONSET_DIR"
mv "$PREPARED_BASE" "$PREPARED_PNG"
trap 'rm -rf "$ICONSET_DIR"; rm -f "$PREPARED_PNG"' EXIT

# Normalize icon for macOS: trim border + rounded mask.
if python3 -c "import PySide6" >/dev/null 2>&1; then
  if python3 "$SCRIPT_DIR/prepare_macos_icon.py" "$SRC_PNG" "$PREPARED_PNG"; then
    INPUT_FOR_ICONSET="$PREPARED_PNG"
  fi
fi

# Apple iconset sizes required by iconutil.
sips -z 16 16     "$INPUT_FOR_ICONSET" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null
sips -z 32 32     "$INPUT_FOR_ICONSET" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null
sips -z 32 32     "$INPUT_FOR_ICONSET" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null
sips -z 64 64     "$INPUT_FOR_ICONSET" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null
sips -z 128 128   "$INPUT_FOR_ICONSET" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null
sips -z 256 256   "$INPUT_FOR_ICONSET" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null
sips -z 256 256   "$INPUT_FOR_ICONSET" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null
sips -z 512 512   "$INPUT_FOR_ICONSET" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null
sips -z 512 512   "$INPUT_FOR_ICONSET" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null
sips -z 1024 1024 "$INPUT_FOR_ICONSET" --out "$ICONSET_DIR/icon_512x512@2x.png" >/dev/null

iconutil -c icns "$ICONSET_DIR" -o "$OUT_ICNS"

echo "Done: $OUT_ICNS"
