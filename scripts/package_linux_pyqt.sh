#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="${APP_NAME:-Rockchip-Flash-Tool}"
APPIMAGE_NAME="${APPIMAGE_NAME:-Rockchip-Flash-Tool-linux-x86_64.AppImage}"
VENV_DIR="${VENV_DIR:-.venv-linux}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ICON_PNG="${ICON_PNG:-assets-icon-1024.png}"
LINUXDEPLOY_URL="${LINUXDEPLOY_URL:-https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage}"
LINUXDEPLOY_BIN="${LINUXDEPLOY_BIN:-$ROOT_DIR/.cache/linuxdeploy-x86_64.AppImage}"

cd "$ROOT_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install -U pip
pip install --no-compile -r requirements.txt pyinstaller
pip install --no-compile pillow

if [[ ! -f "$ICON_PNG" ]]; then
  echo "Icon source not found: $ICON_PNG" >&2
  exit 1
fi

python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "$APP_NAME" \
  --add-data "tools:tools" \
  --add-data "rkbin:rkbin" \
  rk_flash_tool/__main__.py

APPDIR="$ROOT_DIR/dist/AppDir"
APP_LIB_DIR="$APPDIR/usr/lib/$APP_NAME"
APP_BIN="$APP_LIB_DIR/$APP_NAME"
LINUXDEPLOY_ICON="$ROOT_DIR/dist/rockchip-flash-tool-512.png"

rm -rf "$APPDIR"
mkdir -p "$APP_LIB_DIR" "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps"

ICON_SOURCE="$ICON_PNG" ICON_TARGET="$LINUXDEPLOY_ICON" python - <<'PY'
import os
from pathlib import Path
from PIL import Image

source = Path(os.environ["ICON_SOURCE"])
target = Path(os.environ["ICON_TARGET"])
target.parent.mkdir(parents=True, exist_ok=True)

with Image.open(source) as image:
    image = image.convert("RGBA")
    image.thumbnail((512, 512), Image.Resampling.LANCZOS)
    if image.size != (512, 512):
        image = image.resize((512, 512), Image.Resampling.LANCZOS)
    image.save(target)
PY

cp -R "dist/$APP_NAME/"* "$APP_LIB_DIR/"
ln -sf "../lib/$APP_NAME/$APP_NAME" "$APPDIR/usr/bin/$APP_NAME"

cat > "$APPDIR/AppRun" <<EOF
#!/usr/bin/env bash
HERE="\$(dirname "\$(readlink -f "\$0")")"
APP_BASE="\$HERE/usr/lib/$APP_NAME"
QT_PLUGIN_DIR=""

if [[ -d "\$APP_BASE/_internal/PySide6/Qt/plugins" ]]; then
  QT_PLUGIN_DIR="\$APP_BASE/_internal/PySide6/Qt/plugins"
elif [[ -d "\$APP_BASE/PyQt5/Qt5/plugins" ]]; then
  QT_PLUGIN_DIR="\$APP_BASE/PyQt5/Qt5/plugins"
fi

export LD_LIBRARY_PATH="\$HERE/usr/lib:\$APP_BASE:\$APP_BASE/_internal:\$APP_BASE/_internal/PySide6/Qt/lib:\${LD_LIBRARY_PATH:-}"
if [[ -n "\$QT_PLUGIN_DIR" ]]; then
  export QT_PLUGIN_PATH="\$QT_PLUGIN_DIR:\${QT_PLUGIN_PATH:-}"
  export QT_QPA_PLATFORM_PLUGIN_PATH="\$QT_PLUGIN_DIR/platforms"
fi
exec "\$HERE/usr/bin/$APP_NAME" "\$@"
EOF
chmod +x "$APPDIR/AppRun"

cp "$LINUXDEPLOY_ICON" "$APPDIR/.DirIcon"
cp "$LINUXDEPLOY_ICON" "$APPDIR/rockchip-flash-tool.png"
cp "$LINUXDEPLOY_ICON" "$APPDIR/usr/share/icons/hicolor/256x256/apps/rockchip-flash-tool.png"

cat > "$APPDIR/rockchip-flash-tool.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Rockchip Flash Tool
Exec=$APP_NAME
Icon=rockchip-flash-tool
Categories=Utility;
Terminal=false
StartupNotify=true
EOF
cp "$APPDIR/rockchip-flash-tool.desktop" "$APPDIR/usr/share/applications/rockchip-flash-tool.desktop"

mkdir -p "$ROOT_DIR/.cache"
if [[ ! -f "$LINUXDEPLOY_BIN" ]]; then
  curl -L -o "$LINUXDEPLOY_BIN" "$LINUXDEPLOY_URL"
  chmod +x "$LINUXDEPLOY_BIN"
fi

if [[ ! -x "$APP_BIN" ]]; then
  echo "Bundled app binary not found: $APP_BIN" >&2
  exit 1
fi

export OUTPUT=appimage
export ARCH=x86_64
export LDAI_OUTPUT="$ROOT_DIR/dist/$APPIMAGE_NAME"

# Qt loads its platform plugin with dlopen, so linuxdeploy's dependency walk over
# the main binary never reaches libqxcb.so and its libxcb/libxkbcommon needs are
# left to the host. Point linuxdeploy at the plugin directories so those land in
# the AppDir and the AppImage really is self-contained.
DEPLOY_DEPS_ARGS=()
for rel in "_internal/PySide6/Qt/plugins" "PySide6/Qt/plugins" "PyQt5/Qt5/plugins"; do
  plugin_root="$APP_LIB_DIR/$rel"
  [[ -d "$plugin_root" ]] || continue
  for sub in platforms xcbglintegrations platformthemes imageformats iconengines; do
    [[ -d "$plugin_root/$sub" ]] || continue
    DEPLOY_DEPS_ARGS+=(--deploy-deps-only "$plugin_root/$sub")
    echo "deploying deps of $rel/$sub"
  done
  break
done
if [[ ${#DEPLOY_DEPS_ARGS[@]} -eq 0 ]]; then
  echo "Warning: no Qt plugin directory found under $APP_LIB_DIR" >&2
fi

APPIMAGE_EXTRACT_AND_RUN=1 "$LINUXDEPLOY_BIN" \
  --appdir "$APPDIR" \
  --executable "$APP_BIN" \
  ${DEPLOY_DEPS_ARGS[@]+"${DEPLOY_DEPS_ARGS[@]}"} \
  --desktop-file "$APPDIR/usr/share/applications/rockchip-flash-tool.desktop" \
  --icon-file "$LINUXDEPLOY_ICON" \
  --output appimage

if [[ -f "$ROOT_DIR/dist/$APPIMAGE_NAME" ]]; then
  :
elif [[ -f "$ROOT_DIR/appimage" ]]; then
  mv "$ROOT_DIR/appimage" "dist/$APPIMAGE_NAME"
elif [[ -f "$ROOT_DIR/$APP_NAME"-x86_64.AppImage ]]; then
  mv "$ROOT_DIR/$APP_NAME"-x86_64.AppImage "dist/$APPIMAGE_NAME"
elif [[ -f "$ROOT_DIR/Rockchip_Flash_Tool-x86_64.AppImage" ]]; then
  mv "$ROOT_DIR/Rockchip_Flash_Tool-x86_64.AppImage" "dist/$APPIMAGE_NAME"
elif [[ -f "dist/$APP_NAME"-x86_64.AppImage ]]; then
  mv "dist/$APP_NAME"-x86_64.AppImage "dist/$APPIMAGE_NAME"
elif compgen -G "$ROOT_DIR/*.AppImage" > /dev/null; then
  mv "$ROOT_DIR/"*.AppImage "dist/$APPIMAGE_NAME"
fi

if [[ ! -f "dist/$APPIMAGE_NAME" ]]; then
  echo "linuxdeploy did not produce dist/$APPIMAGE_NAME" >&2
  exit 1
fi

chmod +x "dist/$APPIMAGE_NAME"
echo "Done: dist/$APPIMAGE_NAME"
