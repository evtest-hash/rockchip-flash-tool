from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ImageFormat(Enum):
    RKFW = "rkfw"
    RKAF = "rkaf"
    RAW = "raw"
    UNKNOWN = "unknown"

    @property
    def is_rk_format(self) -> bool:
        return self in (ImageFormat.RKFW, ImageFormat.RKAF)

    @property
    def display_name(self) -> str:
        return {
            ImageFormat.RKFW: "Rockchip Firmware (RKFW)",
            ImageFormat.RKAF: "Rockchip Firmware (RKAF)",
            ImageFormat.RAW: "Raw Disk Image",
            ImageFormat.UNKNOWN: "Unknown",
        }[self]


@dataclass
class ImageInfo:
    path: Path
    format: ImageFormat
    size_bytes: int

    @property
    def size_display(self) -> str:
        size = float(self.size_bytes)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024.0:
                return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


def detect_image_format(path: str | Path) -> ImageInfo:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"Image file not found: {p}")

    with p.open("rb") as f:
        header = f.read(4096)

    fmt = ImageFormat.UNKNOWN
    if header[:4] == b"RKFW":
        fmt = ImageFormat.RKFW
    elif header[:4] == b"RKAF":
        fmt = ImageFormat.RKAF
    elif len(header) >= 520 and header[512:520] == b"EFI PART":
        fmt = ImageFormat.RAW
    elif len(header) >= 512 and header[510:512] == b"\x55\xAA":
        fmt = ImageFormat.RAW

    return ImageInfo(path=p, format=fmt, size_bytes=p.stat().st_size)
