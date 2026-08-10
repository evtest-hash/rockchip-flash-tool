# Changelog

## Unreleased

### Removed

- Speculative code paths that nothing reached: the chip database's USB-PID
  lookup (its PID set was a subset of the parser's, so it never resolved
  anything), `Flasher.cancel()` (no UI entry point), `FlashProgress.progress_pct`
  (always 0, no progress bar consumes it), the `FlashStage` enum (no consumer
  read it), and `validate_firmware_for_chip()` (its result was emitted as a
  message and then ignored).
- Bootloader lookup no longer prefix-matches filenames or searches the firmware
  directory and `~/.rk-flash-tool/tools`. Chip-to-loader mapping is now the
  exact filename shipped in `rkbin/`.
- The Linux packaging script no longer guesses the AppImage output filename from
  six candidate locations, and no longer carries PyQt5 branches — this project
  ships PySide6.

### Added

- `pyproject.toml` with project metadata; the version is read from
  `rk_flash_tool.__version__` and the dependencies from `requirements.txt`, so
  neither is duplicated.
- `THIRD_PARTY.md` recording the origin, version and SHA-256 of every vendored
  Rockchip binary.

## 1.0.0

First release. Cross-platform GUI (macOS DMG, Windows zip, Linux AppImage) that
wraps Rockchip's `upgrade_tool`:

- Automatic device detection with chip identification by USB PID.
- RKFW / RKAF / raw-image detection, with automatic bootloader download when the
  board is in Maskrom mode.
- In-process Rockchip USB driver installation on Windows.
- CI builds all three artifacts, smoke-tests each on its own OS, and gates
  publishing on those tests.
