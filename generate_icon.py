"""Generate app icon (ICO) from SVG for Windows EXE."""
import struct
import zlib
from pathlib import Path

from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray, QBuffer
from PySide6.QtWidgets import QApplication
import sys

APP_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">'
    '<defs>'
    '<linearGradient id="cover" x1="0%" y1="0%" x2="100%" y2="100%">'
    '<stop offset="0%" style="stop-color:#4A90D9;stop-opacity:1" />'
    '<stop offset="100%" style="stop-color:#2C5F8A;stop-opacity:1" />'
    '</linearGradient>'
    '<linearGradient id="spine" x1="0%" y1="0%" x2="100%" y2="0%">'
    '<stop offset="0%" style="stop-color:#1E3A5F;stop-opacity:1" />'
    '<stop offset="100%" style="stop-color:#2C5F8A;stop-opacity:1" />'
    '</linearGradient>'
    '<linearGradient id="pages" x1="0%" y1="0%" x2="0%" y2="100%">'
    '<stop offset="0%" style="stop-color:#FFFFFF;stop-opacity:1" />'
    '<stop offset="100%" style="stop-color:#E8E8E8;stop-opacity:1" />'
    '</linearGradient>'
    '</defs>'
    '<rect x="40" y="20" width="180" height="220" rx="8" ry="8" fill="url(#pages)" stroke="#BBB" stroke-width="2"/>'
    '<rect x="48" y="20" width="172" height="220" rx="6" ry="6" fill="url(#cover)"/>'
    '<rect x="40" y="20" width="16" height="220" rx="4" ry="0" fill="url(#spine)"/>'
    '<line x1="80" y1="60" x2="190" y2="60" stroke="rgba(255,255,255,0.6)" stroke-width="3" stroke-linecap="round"/>'
    '<line x1="80" y1="80" x2="170" y2="80" stroke="rgba(255,255,255,0.4)" stroke-width="2" stroke-linecap="round"/>'
    '<line x1="80" y1="96" x2="180" y2="96" stroke="rgba(255,255,255,0.4)" stroke-width="2" stroke-linecap="round"/>'
    '<line x1="80" y1="112" x2="160" y2="112" stroke="rgba(255,255,255,0.4)" stroke-width="2" stroke-linecap="round"/>'
    '<line x1="80" y1="128" x2="185" y2="128" stroke="rgba(255,255,255,0.4)" stroke-width="2" stroke-linecap="round"/>'
    '<line x1="80" y1="144" x2="150" y2="144" stroke="rgba(255,255,255,0.4)" stroke-width="2" stroke-linecap="round"/>'
    '<line x1="80" y1="160" x2="175" y2="160" stroke="rgba(255,255,255,0.4)" stroke-width="2" stroke-linecap="round"/>'
    '<line x1="80" y1="176" x2="140" y2="176" stroke="rgba(255,255,255,0.4)" stroke-width="2" stroke-linecap="round"/>'
    '</svg>'
)


def pixmap_to_dib(pm: QPixmap) -> bytes:
    img = pm.toImage().convertToFormat(
        pm.toImage().Format.Format_RGBA8888
    )
    w = img.width()
    h = img.height()
    bpp = 32
    row_size = w * 4
    pixel_data_size = row_size * h
    mask_row_size = ((w + 31) // 32) * 4
    mask_data_size = mask_row_size * h
    dib_size = 40 + pixel_data_size + mask_data_size

    header = struct.pack("<IiiHHIIiiII",
        40, w, h * 2, 1, bpp, 0, pixel_data_size + mask_data_size,
        0, 0, 0, 0)

    pixels = bytearray(pixel_data_size)
    for y in range(h):
        src_y = h - 1 - y
        for x in range(w):
            c = img.pixelColor(x, src_y)
            off = (y * w + x) * 4
            pixels[off] = c.blue()
            pixels[off + 1] = c.green()
            pixels[off + 2] = c.red()
            pixels[off + 3] = c.alpha()

    mask = bytearray(mask_data_size)
    for y in range(h):
        src_y = h - 1 - y
        for x_byte in range(mask_row_size):
            byte_val = 0
            for bit in range(8):
                px = x_byte * 8 + bit
                if px < w:
                    c = img.pixelColor(px, src_y)
                    if c.alpha() == 0:
                        byte_val |= (1 << (7 - bit))
            mask[y * mask_row_size + x_byte] = byte_val

    return header + bytes(pixels) + bytes(mask)


def main():
    app = QApplication(sys.argv)
    renderer = QSvgRenderer(QByteArray(APP_ICON_SVG.encode("utf-8")))
    if not renderer.isValid():
        print("ERROR: SVG rendering failed")
        sys.exit(1)

    output_dir = Path(__file__).parent / "resources" / "icons"
    output_dir.mkdir(parents=True, exist_ok=True)

    sizes = [16, 20, 24, 32, 48, 64, 128, 256]
    for size in sizes:
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        print(f"  {size}x{size} rendered")

    ico_path = output_dir / "app_icon.ico"
    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    dib_threshold = 48
    image_data_list = []
    for size in ico_sizes:
        pm = QPixmap(size, size)
        pm.fill(QColor(0, 0, 0, 0))
        p = QPainter(pm)
        renderer.render(p)
        p.end()
        if size <= dib_threshold:
            data = pixmap_to_dib(pm)
            fmt = "DIB"
        else:
            buf = QBuffer()
            buf.open(QBuffer.OpenModeFlag.WriteOnly)
            pm.save(buf, "PNG")
            buf.close()
            data = bytes(buf.buffer().data())
            fmt = "PNG"
        image_data_list.append((size, data))
        print(f"  {size}x{size} {fmt} rendered ({len(data)} bytes)")

    with open(str(ico_path), "wb") as f:
        num = len(image_data_list)
        f.write(struct.pack("<HHH", 0, 1, num))
        offset = 6 + num * 16
        for i, (size, data) in enumerate(image_data_list):
            w = 0 if size == 256 else size
            h = w
            f.write(struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offset))
            offset += len(data)
        for _, data in image_data_list:
            f.write(data)
    print(f"ICO saved to: {ico_path} (sizes: {ico_sizes})")

    png_path = output_dir / "app_icon.png"
    pm256 = QPixmap(256, 256)
    pm256.fill(QColor(0, 0, 0, 0))
    p256 = QPainter(pm256)
    renderer.render(p256)
    p256.end()
    pm256.save(str(png_path), "PNG")
    print(f"PNG saved to: {png_path}")


if __name__ == "__main__":
    main()
