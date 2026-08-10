#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_NAME="Rockchip Flash Tool"
# Reverse-DNS, as macOS expects. PyInstaller otherwise derives it from --name,
# which yields "Rockchip Flash Tool" -- spaces and all.
BUNDLE_ID="${BUNDLE_ID:-com.focalcrest.rockchip-flash-tool}"
DMG_NAME="${DMG_NAME:-Rockchip-Flash-Tool-macOS-universal.dmg}"
ICON_PNG="${ICON_PNG:-assets/icon-1024.png}"
ICON_ICNS="${ICON_ICNS:-assets/icon.icns}"
TARGET_ARCH="${TARGET_ARCH:-universal2}"
DEPLOY_TARGET="${DEPLOY_TARGET:-10.15}"
VENV_DIR="${VENV_DIR:-}"
PYTHON_BIN="${PYTHON_BIN:-}"

if [[ "$TARGET_ARCH" == "universal2" ]]; then
  # /usr/bin/python3 is a universal binary on macOS and avoids arm64-only Homebrew Python issues.
  VENV_DIR="${VENV_DIR:-.venv-universal2}"
  PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
else
  VENV_DIR="${VENV_DIR:-.venv}"
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

cd "$ROOT_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install -U pip
pip install --no-compile -r requirements.txt pyinstaller

if [[ ! -f "$ICON_PNG" ]]; then
  echo "Icon source not found: $ICON_PNG"
  exit 1
fi

# Rebuild icon when missing, when source changed, or when explicitly requested.
if [[ ! -f "$ICON_ICNS" || "$ICON_PNG" -nt "$ICON_ICNS" || "${FORCE_ICON_REBUILD:-0}" == "1" ]]; then
  bash "packaging/icons/make_icns.sh" "$ICON_PNG" "$ICON_ICNS"
fi

export MACOSX_DEPLOYMENT_TARGET="$DEPLOY_TARGET"

python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --target-arch "$TARGET_ARCH" \
  --name "$APP_NAME" \
  --osx-bundle-identifier "$BUNDLE_ID" \
  --icon "$ICON_ICNS" \
  --add-data "vendor/upgrade_tool/darwin:vendor/upgrade_tool/darwin" \
  --add-data "vendor/rkbin:vendor/rkbin" \
  rockchip_flash_tool/__main__.py

STAGE_DIR="dist/dmg-stage"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
cp -R "dist/${APP_NAME}.app" "$STAGE_DIR/"
ln -s /Applications "$STAGE_DIR/Applications"

# hdiutil intermittently fails with "Resource busy" on CI runners
# (actions/runner-images#7522), so retry rather than lose a release build.
for attempt in $(seq 1 10); do
  if hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$STAGE_DIR" \
    -ov \
    -format UDZO \
    "dist/${DMG_NAME}"; then
    break
  fi
  if [[ "$attempt" -eq 10 ]]; then
    echo "hdiutil create failed after 10 attempts" >&2
    exit 1
  fi
  echo "hdiutil create failed (attempt $attempt), retrying in 5s..." >&2
  sleep 5
done

rm -rf "$STAGE_DIR"
echo "Done: dist/${DMG_NAME}"
