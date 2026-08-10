#!/usr/bin/env python3
"""Build a multi-size Windows .ico from a square PNG.

Windows picks the closest embedded size for each context (16 px in the title
bar, 32 px in Alt-Tab, 48 px in Explorer). A single large entry forces the
shell to downscale on the fly, which destroys fine detail.
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
from pathlib import Path

# Qt image handling needs an application instance; offscreen keeps it headless.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QByteArray, Qt
from PySide6.QtGui import QGuiApplication, QImage

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SIZES = (16, 24, 32, 48, 64, 128, 256)

_app: QGuiApplication | None = None


def _png_bytes(image: QImage, size: int) -> bytes:
    scaled = image.scaled(
        size, size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation
    )
    data = QByteArray()  # QBuffer only borrows this; it must stay referenced
    buffer = QBuffer(data)
    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
    if not scaled.save(buffer, "PNG"):
        raise RuntimeError(f"Failed to encode {size}x{size} frame")
    buffer.close()
    return bytes(data)


def build_ico(png_bytes_by_size: dict[int, bytes]) -> bytes:
    entries = sorted(png_bytes_by_size.items())
    header = struct.pack("<HHH", 0, 1, len(entries))
    offset = len(header) + 16 * len(entries)

    directory = b""
    for size, png in entries:
        # 0 means 256 in an ICONDIRENTRY; sizes above 256 are not representable.
        dim = 0 if size >= 256 else size
        directory += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        offset += len(png)

    return header + directory + b"".join(png for _, png in entries)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Windows .ico from a PNG.")
    parser.add_argument("source_png", help="Source PNG path")
    parser.add_argument("output_ico", help="Output ICO path")
    args = parser.parse_args()

    src = Path(args.source_png)
    out = Path(args.output_ico)
    if not src.exists():
        raise FileNotFoundError(f"Source PNG not found: {src}")
    if not src.read_bytes().startswith(PNG_SIGNATURE):
        raise ValueError(f"Source is not a PNG file: {src}")

    global _app
    _app = QGuiApplication(sys.argv[:1])  # must outlive every QImage operation
    image = QImage(str(src))
    if image.isNull():
        raise ValueError(f"Could not decode PNG: {src}")
    if image.width() != image.height():
        raise ValueError(f"Source must be square, got {image.width()}x{image.height()}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(build_ico({size: _png_bytes(image, size) for size in SIZES}))
    print(f"Wrote {out} ({', '.join(f'{s}x{s}' for s in SIZES)})")


if __name__ == "__main__":
    main()
