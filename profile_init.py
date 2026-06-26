"""Profile EpubReader init in detail."""
import time
from pathlib import Path
from ebooklib import epub
from bs4 import BeautifulSoup

epub_path = Path(r"D:\MyProgramming\codeagent\eReader\data\Architecting_Modern_Systems_A_Practical_-_Aarav_Joshi.epub")

t0 = time.perf_counter()
book = epub.read_epub(str(epub_path))
t1 = time.perf_counter()
print(f"epub.read_epub: {t1 - t0:.2f}s")

# Count items
all_items = list(book.get_items())
doc_items = [i for i in all_items if i.get_type() == 9]
img_items = [i for i in all_items if i.get_type() in (1, 10)]
print(f"Total items: {len(all_items)}, documents: {len(doc_items)}, images: {len(img_items)}")

# Check spine
print(f"Spine length: {len(book.spine)}")

# Time chapter extraction (what _extract_chapters does)
t2 = time.perf_counter()
chapters = []
for item_id, _linear in book.spine:
    item = book.get_item_with_id(item_id)
    if item is None or item.get_type() != 9:
        continue
    content = item.get_content()
    html = content.decode("utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text().strip() if title_tag else ""
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text().strip()
    if not title:
        h2 = soup.find("h2")
        if h2:
            title = h2.get_text().strip()
    chapters.append((title, len(html)))
t3 = time.perf_counter()
print(f"Chapter extraction (with BeautifulSoup): {t3 - t2:.2f}s")

# Time without BeautifulSoup (just get_content)
t4 = time.perf_counter()
for item_id, _linear in book.spine:
    item = book.get_item_with_id(item_id)
    if item is None or item.get_type() != 9:
        continue
    content = item.get_content()
    html = content.decode("utf-8", errors="replace")
t5 = time.perf_counter()
print(f"Chapter extraction (without BS4): {t5 - t4:.2f}s")

# Check get_content() timing
t6 = time.perf_counter()
for item_id, _linear in book.spine:
    item = book.get_item_with_id(item_id)
    if item is None or item.get_type() != 9:
        continue
    content = item.get_content()
t7 = time.perf_counter()
print(f"Just get_content() calls: {t7 - t6:.2f}s")

# Total HTML size
total = sum(c[1] for c in chapters)
print(f"Total HTML: {total / 1024 / 1024:.1f} MB")
for i, (title, size) in enumerate(chapters):
    print(f"  Ch {i}: {size / 1024:.0f} KB - {title[:60]}")
