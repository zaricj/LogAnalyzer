"""Render ``glint.svg`` into ``glint.png`` (512 px) and a multi-size ``glint.ico``.

Run from the project root after editing the SVG:  uv run assets/make_icons.py
"""

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ASSETS = Path(__file__).resolve().parent
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)


def render_png(renderer: QSvgRenderer, size: int) -> bytes:
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(data)


def write_ico(path: Path, images: list[tuple[int, bytes]]) -> None:
    """Write an ICO container with PNG-compressed entries (supported since Vista)."""
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    entries, blobs = b"", b""
    for size, png in images:
        dim = 0 if size >= 256 else size  # 0 means 256 in the ICO format
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        blobs += png
        offset += len(png)
    path.write_bytes(header + entries + blobs)


def main() -> None:
    QGuiApplication(sys.argv)
    renderer = QSvgRenderer(str(ASSETS / "glint.svg"))
    if not renderer.isValid():
        raise SystemExit("glint.svg could not be parsed")
    (ASSETS / "glint.png").write_bytes(render_png(renderer, 512))
    write_ico(ASSETS / "glint.ico", [(s, render_png(renderer, s)) for s in ICO_SIZES])
    print(f"Wrote {ASSETS / 'glint.png'} and {ASSETS / 'glint.ico'}")


if __name__ == "__main__":
    main()
