"""Profile EPUB loading and chapter display performance."""
import time
from pathlib import Path
from src.readers.epub_reader import EpubReader

epub_path = Path(r"D:\MyProgramming\codeagent\eReader\data\Architecting_Modern_Systems_A_Practical_-_Aarav_Joshi.epub")

t0 = time.perf_counter()
reader = EpubReader(epub_path)
t1 = time.perf_counter()
print(f"EpubReader init: {t1 - t0:.2f}s")
print(f"  Title: {reader.title}")
print(f"  Total chapters: {reader.total_chapters}")

# Check chapter sizes
total_html_size = 0
large_chapters = []
for i in range(reader.total_chapters):
    ch = reader.get_chapter(i)
    size = len(ch.html_content)
    total_html_size += size
    if size > 100000:
        large_chapters.append((i, ch.title, size))

print(f"  Total HTML size: {total_html_size / 1024 / 1024:.1f} MB")
print(f"  Chapters > 100KB: {len(large_chapters)}")
for idx, title, size in large_chapters[:10]:
    print(f"    Ch {idx}: {title[:50]} ({size / 1024:.0f} KB)")

# Time resolve_images for first chapter
t2 = time.perf_counter()
ch0 = reader.get_chapter(0)
t3 = time.perf_counter()
print(f"\nget_chapter(0): {t3 - t2:.2f}s (html size: {len(ch0.html_content) / 1024:.0f} KB)")

t4 = time.perf_counter()
resolved = reader.resolve_images(ch0.html_content)
t5 = time.perf_counter()
print(f"resolve_images(0): {t5 - t4:.2f}s (resolved size: {len(resolved) / 1024:.0f} KB)")

# Time resolve_images for a large chapter
if large_chapters:
    idx = large_chapters[0][0]
    t6 = time.perf_counter()
    ch = reader.get_chapter(idx)
    t7 = time.perf_counter()
    print(f"\nget_chapter({idx}): {t7 - t6:.2f}s (html size: {len(ch.html_content) / 1024:.0f} KB)")

    t8 = time.perf_counter()
    resolved = reader.resolve_images(ch.html_content)
    t9 = time.perf_counter()
    print(f"resolve_images({idx}): {t9 - t8:.2f}s (resolved size: {len(resolved) / 1024:.0f} KB)")

# Count total images across all chapters
total_images = 0
total_image_bytes = 0
for i in range(reader.total_chapters):
    ch = reader.get_chapter(i)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(ch.html_content, "html.parser")
    imgs = soup.find_all("img")
    svgs = soup.find_all("svg")
    svg_images = []
    for svg in svgs:
        svg_images.extend(svg.find_all("image"))
    total_images += len(imgs) + len(svg_images)

print(f"\nTotal images across all chapters: {total_images}")

# Time _extract_body_content
from src.readers.reader_widget import ReaderWidget
from PySide6.QtWidgets import QApplication
import sys
app = QApplication(sys.argv)
widget = ReaderWidget()
widget._epub_reader = reader
widget._book_file_path = str(epub_path)

t10 = time.perf_counter()
content = widget._extract_body_content(ch0.html_content)
t11 = time.perf_counter()
print(f"_extract_body_content(0): {t11 - t10:.2f}s")

if large_chapters:
    idx = large_chapters[0][0]
    ch = reader.get_chapter(idx)
    t12 = time.perf_counter()
    content = widget._extract_body_content(ch.html_content)
    t13 = time.perf_counter()
    print(f"_extract_body_content({idx}): {t13 - t12:.2f}s")
