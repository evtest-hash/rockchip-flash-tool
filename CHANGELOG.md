# Changelog

## 1.1.0

### Added

- Firmware images can be dropped onto the window.
- The file dialog reopens in the directory the last firmware came from.
- The window follows the system light/dark setting, switching live.
- `pyproject.toml` with project metadata; the version is read from
  `rockchip_flash_tool.__version__` and the dependencies from `requirements.txt`.
- `THIRD_PARTY.md` recording the origin and version of every vendored Rockchip
  binary.

### Changed

- Colours are derived from the platform palette instead of being hard-coded, so
  the window matches the title bar the system draws.
- Buttons have hover, pressed and focus states.
- Font sizes are in points rather than pixels, so text follows a system
  font-size preference.
- The status bar is taller, and its text is larger, in body colour, and aligned
  with the panels above.
- The startup status reads `Ready` instead of naming an internal tool.
- An image that is neither an RK package nor a recognisable disk image is
  written straight out with `WL` instead of first attempting `UF`, which could
  only ever fail, and is reset afterwards like any other raw write.

### Fixed

- A board in Maskrom no longer reports a serial number. It has none, and
  `upgrade_tool` fills the field with an empty string on macOS and the literal
  `rockchip` on Windows, the latter reading as a genuine serial.
- Device detection stopped working for the rest of the session once a flash had
  run. The worker's progress callback outlived its QThread, so every poll raised
  `RuntimeError: Signal source has been deleted` inside `Flasher._emit`, which
  the polling loop reported as "No device connected".
- A status message given a timeout left the bar blank when it expired instead of
  restoring the standing message.
- Light-theme secondary text was below the WCAG AA contrast minimum.

### Removed

- Speculative code paths that nothing reached: the chip database's USB-PID
  lookup (its PID set was a subset of the parser's, so it never resolved
  anything), `Flasher.cancel()` (no UI entry point), `FlashProgress.progress_pct`
  (always 0, no progress bar consumes it), the `FlashStage` enum (no consumer
  read it), and `validate_firmware_for_chip()` (its result was emitted as a
  message and then ignored).
- Bootloader lookup no longer prefix-matches filenames or searches the firmware
  directory and `~/.rk-flash-tool/tools`. Chip-to-loader mapping is now the
  exact filename shipped in `vendor/rkbin/`.
- The Linux packaging script no longer guesses the AppImage output filename from
  six candidate locations, and no longer carries PyQt5 branches — this project
  ships PySide6.

## 1.0.0

First release. Cross-platform GUI (macOS DMG, Windows zip, Linux AppImage) that
wraps Rockchip's `upgrade_tool`:

- Automatic device detection with chip identification by USB PID.
- RKFW / RKAF / raw-image detection, with automatic bootloader download when the
  board is in Maskrom mode.
- In-process Rockchip USB driver installation on Windows.
- CI builds all three artifacts, smoke-tests each on its own OS, and gates
  publishing on those tests.
