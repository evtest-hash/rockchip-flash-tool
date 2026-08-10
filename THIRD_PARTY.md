# Third-party components

Everything under `vendor/` is prebuilt by Rockchip. It is not this project's
source and is redistributed as-is.

| Path | What | Version |
|---|---|---|
| `vendor/upgrade_tool/darwin`, `linux` | Rockchip upgrade_tool | v2.44 |
| `vendor/upgrade_tool/windows` | Rockchip upgrade_tool | v2.46 |
| `vendor/upgrade_tool/windows/driver` | rockusb USB driver, x86 + x64, Win7–Win10 | 5.13.0000.0 (2023-11-09) |
| `vendor/rkbin` | Bootloaders, from <https://github.com/rockchip-linux/rkbin> | see filenames |

Tool versions come from each directory's `revision.txt`; loader versions are in
the filenames. The upstream `rkbin` commit was not recorded when these were
vendored.

**Open question:** the licence Rockchip applies to redistributing these binaries
has not been confirmed.
