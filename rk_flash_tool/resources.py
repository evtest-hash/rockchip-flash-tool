"""Location of the bundled resources.

Every path into vendor/ and assets/ is resolved here, so the on-disk layout is
described in exactly one place. PyInstaller unpacks the --add-data payload under
sys._MEIPASS, which is also where the package itself lands, so the frozen and
the source-tree layouts share a single base directory.
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path

_PLATFORM_DIR = {"Darwin": "darwin", "Linux": "linux", "Windows": "windows"}
_TOOL_BINARY = {"Darwin": "upgrade_tool", "Linux": "upgrade_tool", "Windows": "upgrade_tool.exe"}


def base_dir() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    return Path(meipass) if meipass else Path(__file__).resolve().parent.parent


def rkbin_dir() -> Path:
    return base_dir() / "vendor" / "rkbin"


def upgrade_tool_path() -> Path:
    system = platform.system()
    return (
        base_dir()
        / "vendor"
        / "upgrade_tool"
        / _PLATFORM_DIR.get(system, "")
        / _TOOL_BINARY.get(system, "upgrade_tool")
    )


def windows_driver_dir() -> Path:
    return base_dir() / "vendor" / "upgrade_tool" / "windows" / "driver"


def icon_path() -> Path | None:
    name = "icon.ico" if sys.platform.startswith("win") else "icon.icns"
    icon = base_dir() / "assets" / name
    return icon if icon.exists() else None
