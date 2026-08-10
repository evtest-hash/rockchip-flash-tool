# Rockchip Flash Tool

[![Build](https://github.com/evtest-hash/rockchip-flash-tool/actions/workflows/build-release.yml/badge.svg)](https://github.com/evtest-hash/rockchip-flash-tool/actions/workflows/build-release.yml)
[![Release](https://img.shields.io/github/v/release/evtest-hash/rockchip-flash-tool)](https://github.com/evtest-hash/rockchip-flash-tool/releases/latest)
![Platforms](https://img.shields.io/badge/platforms-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)

Flash a Rockchip board in two steps: choose a firmware image, click **Start Flash**.
The tool works out the rest — which chip is attached, which mode it is in, which
loader it needs, and how the image has to be written.

[English](README.md) · [简体中文](README.zh-CN.md)

| Light | Dark |
|---|---|
| ![Light theme](assets/screenshots/ui-light.png) | ![Dark theme](assets/screenshots/ui-dark.png) |

## Download

| Platform | File | Notes |
|---|---|---|
| macOS 11+ | [Rockchip-Flash-Tool-macOS-universal.dmg](https://github.com/evtest-hash/rockchip-flash-tool/releases/latest/download/Rockchip-Flash-Tool-macOS-universal.dmg) | Universal — Apple silicon and Intel |
| Windows 10/11 | [Rockchip-Flash-Tool-windows-x64.zip](https://github.com/evtest-hash/rockchip-flash-tool/releases/latest/download/Rockchip-Flash-Tool-windows-x64.zip) | Installs the Rockchip USB driver on first run |
| Linux x86_64 | [Rockchip-Flash-Tool-linux-x86_64.AppImage](https://github.com/evtest-hash/rockchip-flash-tool/releases/latest/download/Rockchip-Flash-Tool-linux-x86_64.AppImage) | Needs FUSE2, see below |

Every release is built and smoke-tested on all three operating systems before it
is published. [All releases →](https://github.com/evtest-hash/rockchip-flash-tool/releases)

## Installation notes

### macOS: "Developer Cannot Be Verified"

If macOS blocks the app after install:

1. In Finder, right-click the app and choose **Open**.
2. Click **Open** again in the confirmation dialog.

If it is still blocked, open **System Settings → Privacy & Security**, find the
blocked app message in the Security section, and click **Open Anyway**.

If Gatekeeper quarantine metadata still blocks launch:

```bash
xattr -dr com.apple.quarantine "/Applications/Rockchip Flash Tool.app"
```

### Linux: AppImage requires FUSE2

The AppImage may show a FUSE error on first launch. Install the FUSE2 runtime:

| Distribution | Command |
|---|---|
| Ubuntu / Debian (≤ 22.04) | `sudo apt install libfuse2` |
| Ubuntu 24.04+ | `sudo apt install libfuse2t64` |
| Fedora | `sudo dnf install fuse-libs` |
| Arch Linux | `sudo pacman -S fuse2` |
| openSUSE | `sudo zypper install libfuse2` |

If you cannot install FUSE2, run in extract mode instead:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./Rockchip-Flash-Tool-linux-x86_64.AppImage
```

## Why this tool exists

Flashing a Rockchip board is rarely one procedure. The right steps depend on
which chip is on the board, which mode it booted into, what format the image is
in, and which operating system you happen to be sitting at — and the usual answer
is a different tool on each platform.

This tool absorbs those differences instead of passing them to the operator:

- **One workflow on macOS, Windows and Linux.** Same window, same two steps.
- **Fewer decisions, fewer mistakes.** The chip, the mode and the image format
  are detected rather than asked about.
- **Short onboarding.** A new operator does not need to learn the underlying
  flashing mechanics to get a correct result.

Built for lab benches, production lines, and field support.

## License

[Apache-2.0](LICENSE).

Each release also bundles the Qt runtime (LGPL-3.0) and binaries prebuilt by
Rockchip, which keep their own terms — see [THIRD_PARTY.md](THIRD_PARTY.md).
