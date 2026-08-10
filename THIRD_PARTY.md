# Third-party components

## Bundled into every release artifact

| Component | Licence |
|---|---|
| Qt 6, via PySide6 | LGPL-3.0 |

Qt and PySide6 are used unmodified and under the LGPL. Each release keeps them
as separate shared libraries inside the bundle rather than linking them into the
executable, so they can be replaced with another build of the same version.
Their source is published by the Qt Company at <https://download.qt.io>.

## Vendored binaries

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

Rockchip's terms for the `rkbin` bootloaders are reproduced verbatim in
[`vendor/rkbin/LICENSE`](vendor/rkbin/LICENSE). They grant a non-exclusive
licence to use, copy and distribute the software, and prohibit reverse
engineering it or removing its notices.
