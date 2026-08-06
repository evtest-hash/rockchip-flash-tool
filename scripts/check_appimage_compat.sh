#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <path-to-appimage>" >&2
  exit 2
fi

APPIMAGE="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
if [[ ! -f "$APPIMAGE" ]]; then
  echo "AppImage not found: $APPIMAGE" >&2
  exit 2
fi

TIMEOUT_BIN="${TIMEOUT_BIN:-timeout}"
AUTO_EXIT_MS="${RK_FLASH_TOOL_AUTO_EXIT_MS:-2500}"
RUN_TIMEOUT_SECONDS="${RUN_TIMEOUT_SECONDS:-20}"
LOG_DIR="${LOG_DIR:-$(pwd)/appimage-compat-logs}"
mkdir -p "$LOG_DIR"

FILE_LOG="$LOG_DIR/file.txt"
EXTRACT_LOG="$LOG_DIR/extract.log"
DIRECT_LOG="$LOG_DIR/direct-run.log"
EXTRACT_RUN_LOG="$LOG_DIR/extract-and-run.log"
LDD_LOG="$LOG_DIR/ldd.txt"
SUMMARY_LOG="$LOG_DIR/summary.md"
REASON_FILE="$LOG_DIR/failure_reason.txt"

format_excerpt() {
  local log_file="$1"
  [[ -f "$log_file" ]] || return 0
  sed -n '1,12p' "$log_file" | sed 's/^/    /'
}

fail() {
  local reason="$1"
  local details="$2"
  local log_file="${3:-}"
  printf '%s\n' "$reason" > "$REASON_FILE"
  {
    echo "## AppImage compatibility check"
    echo
    echo "- Result: FAIL"
    echo "- Reason: $reason"
    echo "- Details: $details"
    if [[ -n "$log_file" && -f "$log_file" ]]; then
      echo "- Log excerpt:"
      echo
      echo '```text'
      format_excerpt "$log_file"
      echo '```'
    fi
  } > "$SUMMARY_LOG"
  echo "FAIL: $reason - $details" >&2
  exit 1
}

pass() {
  {
    echo "## AppImage compatibility check"
    echo
    echo "- Result: PASS"
    echo "- Direct launch: ok"
    echo "- Extract mode: ok"
    echo "- Qt platform plugin load: ok"
  } > "$SUMMARY_LOG"
  echo "PASS: AppImage compatibility checks succeeded"
}

classify_failure() {
  local log_file="$1"
  local default_reason="$2"
  if grep -Eqi 'fuse|libfuse|Cannot mount AppImage|AppImages require FUSE' "$log_file"; then
    echo "FUSE missing"
    return
  fi
  if grep -Eqi 'platform plugin|could not load the Qt platform plugin|xcb' "$log_file"; then
    echo "Qt plugin missing"
    return
  fi
  if grep -Eqi 'GLIBC_[0-9]|version .* not found|No such file or directory|error while loading shared libraries' "$log_file"; then
    echo "glibc/runtime mismatch"
    return
  fi
  if grep -Eqi 'timed out|timeout:' "$log_file"; then
    echo "startup timeout"
    return
  fi
  echo "$default_reason"
}

run_launch_check() {
  local mode="$1"
  local log_file="$2"
  shift 2

  set +e
  env RK_FLASH_TOOL_AUTO_EXIT_MS="$AUTO_EXIT_MS" QT_DEBUG_PLUGINS=1 "$@" >"$log_file" 2>&1
  local rc=$?
  set -e

  if [[ $rc -ne 0 ]]; then
    local reason
    if [[ $rc -eq 124 ]]; then
      reason="startup timeout"
      echo "timeout: launch exceeded ${RUN_TIMEOUT_SECONDS}s" >>"$log_file"
    else
      reason="$(classify_failure "$log_file" "${mode} failed")"
    fi
    fail "$reason" "${mode} failed with exit code $rc" "$log_file"
  fi

  if grep -Eqi 'platform plugin|could not load the Qt platform plugin' "$log_file"; then
    fail "Qt plugin missing" "${mode} launched but Qt platform plugin load failed" "$log_file"
  fi
}

echo "Inspecting AppImage: $APPIMAGE"
file "$APPIMAGE" | tee "$FILE_LOG"
if ! grep -Eqi 'ELF 64-bit.*x86-64|x86-64.*AppImage|AppImage' "$FILE_LOG"; then
  fail "glibc/runtime mismatch" "artifact is not a 64-bit x86_64 AppImage" "$FILE_LOG"
fi

WORK_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

cp "$APPIMAGE" "$WORK_DIR/app-under-test.AppImage"
chmod +x "$WORK_DIR/app-under-test.AppImage"

pushd "$WORK_DIR" >/dev/null
set +e
./app-under-test.AppImage --appimage-extract >"$EXTRACT_LOG" 2>&1
extract_rc=$?
set -e
if [[ $extract_rc -ne 0 ]]; then
  reason="$(classify_failure "$EXTRACT_LOG" "extract failed")"
  fail "$reason" "AppImage extraction failed with exit code $extract_rc" "$EXTRACT_LOG"
fi

if [[ ! -x squashfs-root/AppRun ]]; then
  fail "glibc/runtime mismatch" "missing squashfs-root/AppRun after extraction" "$EXTRACT_LOG"
fi

main_bin="squashfs-root/usr/bin/Rockchip-Flash-Tool"
if [[ ! -x "$main_bin" ]]; then
  main_bin="$(find squashfs-root/usr/lib -maxdepth 2 -type f -perm -111 | head -n 1 || true)"
fi
if [[ -z "$main_bin" ]]; then
  fail "glibc/runtime mismatch" "missing extracted main binary under squashfs-root/usr/lib" "$EXTRACT_LOG"
fi

desktop_file="$(find squashfs-root -maxdepth 2 -name '*.desktop' | head -n 1 || true)"
if [[ -z "$desktop_file" ]]; then
  fail "glibc/runtime mismatch" "missing desktop entry after extraction" "$EXTRACT_LOG"
fi

if command -v ldd >/dev/null 2>&1; then
  ldd "$main_bin" >"$LDD_LOG" 2>&1 || true
else
  echo "ldd not available in container" >"$LDD_LOG"
fi

# Self-containment. An AppImage does not bundle everything: the AppImage project
# maintains an excludelist of libraries that must come from the host, because
# bundling them breaks (graphics drivers, fontconfig, core X/xcb, glibc). So an
# unresolved dependency is a packaging defect only when the library is NOT on
# that list. ldd also has to see the same search path AppRun exports, or the
# bundle's own Qt libraries would look missing.
EXCLUDELIST="${EXCLUDELIST:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/appimage-excludelist.txt}"
app_base="$(cd "$(dirname "$main_bin")" && pwd)"
bundle_ld_path="$PWD/squashfs-root/usr/lib:$app_base:$app_base/_internal:$app_base/_internal/PySide6/Qt/lib"

# Unresolved libraries that are the host's job, printed once for the record.
host_provided() {
  local soname="$1"
  [[ -f "$EXCLUDELIST" ]] || return 1
  grep -qx -- "$soname" "$EXCLUDELIST"
}

# Echoes the sonames that are genuinely missing from the bundle.
missing_from_bundle() {
  local target="$1"
  local out="$2"
  command -v ldd >/dev/null 2>&1 || return 0
  env LD_LIBRARY_PATH="$bundle_ld_path" ldd "$target" >"$out" 2>&1 || true
  local soname
  while read -r soname; do
    [[ -n "$soname" ]] || continue
    if host_provided "$soname"; then
      echo "  host-provided (excludelist): $soname" >&2
    else
      echo "$soname"
    fi
  done < <(awk '/not found/ {print $1}' "$out")
}

assert_bundled() {
  local target="$1"
  local label="$2"
  local out="$3"
  local missing
  missing="$(missing_from_bundle "$target" "$out")"
  if [[ -n "$missing" ]]; then
    echo "missing from the AppImage, needed by $label:" >&2
    echo "$missing" | sed 's/^/  /' >&2
    printf '%s\n' "$missing" >>"$out"
    fail "bundle not self-contained" \
      "$label needs $(echo "$missing" | tr '\n' ' ')which the AppImage does not carry" "$out"
  fi
  echo "ok: $label has no unbundled dependencies"
}

assert_bundled "$main_bin" "main binary" "$LDD_LOG"

# Qt dlopens its platform plugin, so it never shows up in the main binary's
# dependency list -- this is exactly where a missing libxcb-* or libxkbcommon
# hides. Only the xcb plugin is load-bearing for us; the others are reported but
# not enforced, since a plugin we never load cannot break the app.
qxcb="$(find squashfs-root -type f -name 'libqxcb.so' -print -quit 2>/dev/null || true)"
if [[ -n "$qxcb" ]]; then
  assert_bundled "$qxcb" "libqxcb.so (Qt xcb platform plugin)" "$LOG_DIR/ldd-libqxcb.txt"
else
  fail "Qt plugin missing" "libqxcb.so not found in the AppImage" "$EXTRACT_LOG"
fi

while IFS= read -r plugin; do
  [[ "$plugin" == "$qxcb" ]] && continue
  other="$(missing_from_bundle "$plugin" "$LOG_DIR/ldd-$(basename "$plugin").txt")"
  if [[ -n "$other" ]]; then
    echo "note: $(basename "$plugin") (unused) is missing $(echo "$other" | tr '\n' ' ')"
  fi
done < <(find squashfs-root -type f -path '*/plugins/platforms/*.so' 2>/dev/null || true)

run_launch_check \
  "direct launch" \
  "$DIRECT_LOG" \
  "$TIMEOUT_BIN" "${RUN_TIMEOUT_SECONDS}s" \
  xvfb-run -a ./app-under-test.AppImage

run_launch_check \
  "extract-and-run launch" \
  "$EXTRACT_RUN_LOG" \
  "$TIMEOUT_BIN" "${RUN_TIMEOUT_SECONDS}s" \
  xvfb-run -a env APPIMAGE_EXTRACT_AND_RUN=1 ./app-under-test.AppImage

popd >/dev/null

pass
