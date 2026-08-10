#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath


def _color_distance(a: QColor, b: QColor) -> int:
    return abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue())


def _sample_border_color(img: QImage) -> QColor:
    w, h = img.width(), img.height()
    points = (
        (0, 0),
        (w - 1, 0),
        (0, h - 1),
        (w - 1, h - 1),
        (w // 2, 0),
        (w // 2, h - 1),
        (0, h // 2),
        (w - 1, h // 2),
    )
    rs: list[int] = []
    gs: list[int] = []
    bs: list[int] = []
    for x, y in points:
        c = img.pixelColor(x, y)
        rs.append(c.red())
        gs.append(c.green())
        bs.append(c.blue())
    rs.sort()
    gs.sort()
    bs.sort()
    mid = len(rs) // 2
    return QColor(rs[mid], gs[mid], bs[mid])


def _row_bg_ratio(img: QImage, y: int, bg: QColor, threshold: int) -> float:
    w = img.width()
    matches = 0
    for x in range(w):
        c = img.pixelColor(x, y)
        if c.alpha() > 245 and _color_distance(c, bg) <= threshold:
            matches += 1
    return matches / w


def _col_bg_ratio(img: QImage, x: int, bg: QColor, threshold: int) -> float:
    h = img.height()
    matches = 0
    for y in range(h):
        c = img.pixelColor(x, y)
        if c.alpha() > 245 and _color_distance(c, bg) <= threshold:
            matches += 1
    return matches / h


def _trim_border(img: QImage, threshold: int = 18, ratio: float = 0.985) -> QImage:
    bg = _sample_border_color(img)
    left, right = 0, img.width() - 1
    top, bottom = 0, img.height() - 1

    while top < bottom and _row_bg_ratio(img, top, bg, threshold) >= ratio:
        top += 1
    while bottom > top and _row_bg_ratio(img, bottom, bg, threshold) >= ratio:
        bottom -= 1
    while left < right and _col_bg_ratio(img, left, bg, threshold) >= ratio:
        left += 1
    while right > left and _col_bg_ratio(img, right, bg, threshold) >= ratio:
        right -= 1

    if (right - left) < img.width() * 0.4 or (bottom - top) < img.height() * 0.4:
        return img
    return img.copy(left, top, right - left + 1, bottom - top + 1)


def _compose_macos_icon(src: QImage, size: int = 1024, inset_ratio: float = 824 / 1024, corner_ratio: float = 0.225) -> QImage:
    canvas = QImage(size, size, QImage.Format_ARGB32)
    canvas.fill(Qt.GlobalColor.transparent)

    target_size = max(1, int(size * inset_ratio))
    scaled = src.scaled(target_size, target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    x = (size - scaled.width()) // 2
    y = (size - scaled.height()) // 2

    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    corner = size * corner_ratio
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size, size), corner, corner)
    painter.setClipPath(path)
    painter.drawImage(x, y, scaled)
    painter.end()

    return canvas


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a macOS-style app icon (trim border + rounded mask).")
    parser.add_argument("source", type=Path, help="Input PNG file")
    parser.add_argument("output", type=Path, help="Output PNG file")
    parser.add_argument("--size", type=int, default=1024, help="Output size, default: 1024")
    parser.add_argument("--inset", type=float, default=824 / 1024,
                        help="Content inset ratio; Apple's icon grid puts the shape at 824/1024")
    parser.add_argument("--corner", type=float, default=0.225, help="Corner radius ratio, default: 0.225")
    args = parser.parse_args()

    if not args.source.exists():
        raise FileNotFoundError(f"Source icon not found: {args.source}")

    img = QImage(str(args.source))
    if img.isNull():
        raise RuntimeError(f"Failed to read image: {args.source}")

    img = img.convertToFormat(QImage.Format_ARGB32)
    if img.width() != args.size or img.height() != args.size:
        img = img.scaled(args.size, args.size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)

    trimmed = _trim_border(img)
    out = _compose_macos_icon(trimmed, size=args.size, inset_ratio=args.inset, corner_ratio=args.corner)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not out.save(str(args.output), "PNG"):
        raise RuntimeError(f"Failed to save output icon: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
