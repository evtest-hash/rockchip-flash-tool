# Changelog

## 1.2.0

### Added

- With several boards attached, which one gets written is now a choice. The
  device panel lists each attached board as a chip, and every command the flash
  issues is pinned to the selected one. A single board looks exactly as it did
  before — there is nothing to choose between.
- The device panel shows the selected board's mode, port id and serial.

### Changed

- A board is identified by its `LocationID`, which is the USB port path it is
  plugged into and the only identifier a board in Maskrom exposes. Moving a
  board to a different port therefore changes how it is listed, and two boards
  swapped between the same two ports are indistinguishable.
- Flashing refuses to start when two attached boards report the same
  `LocationID`. Distinct port paths can alias, because each hub level is masked
  to four bits, and `upgrade_tool` would answer an ambiguous selector by taking
  whichever board it enumerated first.
- The status text sits beside the flash button; the separate status bar is gone.
  Pressing on the right and reading the result on the left were two places to
  look, with an empty row between them.
- The app icon is the full-bleed Rockchip master.

### Fixed

- Whichever board `upgrade_tool` happened to enumerate first was the one that
  got written. That order is not stable — it was observed swapping after a
  bootloader download — so with more than one board attached the target could
  change with nobody touching anything.
- Bootloader download no longer asks the device listing for a second opinion
  when `upgrade_tool` reports neither success nor a zero exit. That check could
  not be right either way: a board running its spl loader still lists as
  Maskrom, so a download that worked read as a failure, and the listing was not
  restricted to the board being written, so another board sitting in Loader
  answered on behalf of the one that failed.
- The README's download links resolve against whichever repository the file is
  read from. They named one outright, so the same README read from the
  organisation's fork sent people to a personal account for the download.
- The window no longer opens with a focus ring around **Refresh**. Fusion, unlike
  the macOS style, puts buttons in the tab chain, so the first one built took
  focus as soon as the window became active.
- `upgrade_tool` no longer drops its `~/upgrade_tool` work directory into the
  user's home. The wrapper points the tool's `HOME` (and `USERPROFILE`) at a
  private temp directory for the life of the app, so launching it leaves no
  folder behind.

## 1.1.0

### Added

- Firmware images can be dropped onto the window.
- The file dialog reopens in the directory the last firmware came from.
- The window follows the system light/dark setting, switching live.
- `pyproject.toml` with project metadata; the version is read from
  `rockchip_flash_tool.__version__` and the dependencies from `requirements.txt`.
- `THIRD_PARTY.md` recording the origin and version of every vendored Rockchip
  binary.
- Apache-2.0 licence. `THIRD_PARTY.md` also records the Qt runtime's LGPL-3.0
  terms and reproduces Rockchip's in `vendor/rkbin/LICENSE`.

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
- The status bar kept the last flash progress line as its standing text, so the
  result message expired into a stale line rather than back to `Ready`.
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
