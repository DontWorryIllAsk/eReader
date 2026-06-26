"""Replace EXE icon resources with proper multi-size icons.

PyInstaller only supports PNG format icons, which don't render correctly
at small sizes (16x16) in Windows Explorer. This script uses Win32
UpdateResource API to add DIB-format small icons + PNG large icons.

IMPORTANT: We do NOT use pefile to patch the PE directly, because pefile
drops the PKG overlay data that PyInstaller appends after the last section,
which breaks the EXE ("could not load embedded Pkg archive").
UpdateResourceW is safe — it only modifies the resource section and
preserves all other PE data including the overlay.
"""
import ctypes
import struct
import sys
from ctypes import wintypes
from pathlib import Path

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

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

BeginUpdateResourceW = kernel32.BeginUpdateResourceW
BeginUpdateResourceW.argtypes = [wintypes.LPCWSTR, wintypes.BOOL]
BeginUpdateResourceW.restype = wintypes.HANDLE

UpdateResourceW = kernel32.UpdateResourceW
UpdateResourceW.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.WORD,
    wintypes.LPVOID,
    wintypes.DWORD,
]
UpdateResourceW.restype = wintypes.BOOL

EndUpdateResourceW = kernel32.EndUpdateResourceW
EndUpdateResourceW.argtypes = [wintypes.HANDLE, wintypes.BOOL]
EndUpdateResourceW.restype = wintypes.BOOL


def MAKEINTRESOURCE(i: int) -> wintypes.LPCWSTR:
    return ctypes.cast(i, wintypes.LPCWSTR)


RT_ICON = MAKEINTRESOURCE(3)
RT_GROUP_ICON = MAKEINTRESOURCE(14)
LANG_NEUTRAL = 0x0000


def pixmap_to_dib(pm) -> bytes:
    img = pm.toImage().convertToFormat(pm.toImage().Format.Format_RGBA8888)
    w = img.width()
    h = img.height()
    bpp = 32
    row_size = w * 4
    pixel_data_size = row_size * h
    mask_row_size = ((w + 31) // 32) * 4
    mask_data_size = mask_row_size * h

    header = struct.pack(
        "<IiiHHIIiiII",
        40, w, h * 2, 1, bpp, 0, pixel_data_size + mask_data_size,
        0, 0, 0, 0,
    )

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
                        byte_val |= 1 << (7 - bit)
            mask[y * mask_row_size + x_byte] = byte_val

    return header + bytes(pixels) + bytes(mask)


def build_icon_resources() -> tuple[list[dict], bytes]:
    from PySide6.QtGui import QPixmap, QPainter, QColor
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtCore import QByteArray, QBuffer
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    renderer = QSvgRenderer(QByteArray(APP_ICON_SVG.encode("utf-8")))
    if not renderer.isValid():
        print("ERROR: SVG rendering failed")
        sys.exit(1)

    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    dib_threshold = 48
    icons = []
    for idx, size in enumerate(ico_sizes):
        pm = QPixmap(size, size)
        pm.fill(QColor(0, 0, 0, 0))
        p = QPainter(pm)
        renderer.render(p)
        p.end()

        if size <= dib_threshold:
            icon_data = pixmap_to_dib(pm)
            fmt = "DIB"
        else:
            buf = QBuffer()
            buf.open(QBuffer.OpenModeFlag.WriteOnly)
            pm.save(buf, "PNG")
            buf.close()
            icon_data = bytes(buf.buffer().data())
            fmt = "PNG"

        w_byte = 0 if size == 256 else size
        icons.append(
            {
                "width": w_byte,
                "height": w_byte,
                "planes": 1,
                "bpp": 32,
                "size": len(icon_data),
                "data": icon_data,
                "id": idx + 1,
                "actual_size": size,
                "format": fmt,
            }
        )

    group_data = struct.pack("<HHH", 0, 1, len(icons))
    for entry in icons:
        group_data += struct.pack(
            "<BBBBHHIH",
            entry["width"],
            entry["height"],
            0,
            0,
            entry["planes"],
            entry["bpp"],
            entry["size"],
            entry["id"],
        )

    return icons, group_data


def add_icon_resources(exe_path: str) -> bool:
    icons, group_data = build_icon_resources()
    print(f"ICO: {len(icons)} sizes")
    for ic in icons:
        print(f"  {ic['actual_size']}x{ic['actual_size']} {ic['format']}, {len(ic['data'])} bytes")

    exe_w = str(Path(exe_path).resolve())
    hUpdate = BeginUpdateResourceW(exe_w, False)
    if not hUpdate:
        err = ctypes.get_last_error()
        print(f"BeginUpdateResource failed: error {err}")
        return False

    try:
        for icon in icons:
            icon_id = icon["id"]
            idata = (ctypes.c_ubyte * len(icon["data"]))(*icon["data"])
            if not UpdateResourceW(
                hUpdate, RT_ICON, MAKEINTRESOURCE(icon_id), LANG_NEUTRAL, idata, len(icon["data"])
            ):
                err = ctypes.get_last_error()
                print(f"  RT_ICON id={icon_id} failed: error {err}")
                return False
            print(f"  Added RT_ICON id={icon_id}: {icon['actual_size']}x{icon['actual_size']} {icon['format']}")

        gdata = (ctypes.c_ubyte * len(group_data))(*group_data)
        if not UpdateResourceW(
            hUpdate, RT_GROUP_ICON, MAKEINTRESOURCE(1), LANG_NEUTRAL, gdata, len(group_data)
        ):
            err = ctypes.get_last_error()
            print(f"  RT_GROUP_ICON failed: error {err}")
            return False
        print(f"  Added RT_GROUP_ICON with {len(icons)} entries")

        if not EndUpdateResourceW(hUpdate, False):
            err = ctypes.get_last_error()
            print(f"EndUpdateResource failed: error {err}")
            return False

        print("Icon resources added successfully")
        return True

    except Exception as e:
        print(f"Error: {e}")
        EndUpdateResourceW(hUpdate, True)
        return False


if __name__ == "__main__":
    exe_path = str(Path(__file__).parent / "dist" / "eReader" / "eReader.exe")

    if not Path(exe_path).exists():
        print(f"ERROR: {exe_path} not found. Run pyinstaller first.")
        sys.exit(1)

    print("=== Adding icon resources (DIB for small, PNG for large) ===")
    if not add_icon_resources(exe_path):
        sys.exit(1)

    print("\n=== Done! ===")
