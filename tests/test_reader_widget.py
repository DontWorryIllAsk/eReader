import struct
import zipfile
import zlib
from pathlib import Path

import pytest

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QStackedWidget, QSplitter

from src.readers.reader_widget import ReaderWidget, CHAPTER_HTML_TEMPLATE
from src.readers.epub_reader import EpubReader
from src.settings.settings import ReaderSettings


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _process_events_until(qapp, predicate, timeout_ms=10000):
    import time
    start = time.time()
    while not predicate() and (time.time() - start) * 1000 < timeout_ms:
        qapp.processEvents()


def _make_valid_png(width=200, height=300, color=(100, 150, 200)) -> bytes:
    raw_rows = b''
    for y in range(height):
        raw_rows += b'\x00'
        for x in range(width):
            raw_rows += bytes(color)
    compressed = zlib.compress(raw_rows)
    def png_chunk(chunk_type, data):
        chunk = chunk_type + data
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)
    header = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    return header + png_chunk(b'IHDR', ihdr_data) + png_chunk(b'IDAT', compressed) + png_chunk(b'IEND', b'')


def _create_epub_with_tall_cover(tmp_path: Path) -> Path:
    epub_path = tmp_path / "tall_cover_book.epub"
    png_data = _make_valid_png(200, 800)

    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
    content_opf = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">tall-cover-001</dc:identifier>
    <dc:title>Tall Cover Book</dc:title>
    <dc:creator>Test Author</dc:creator>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="cover-image" href="cover.png" media-type="image/png" properties="cover-image"/>
  </manifest>
  <spine>
    <itemref idref="cover"/>
    <itemref idref="chapter1"/>
  </spine>
</package>"""

    cover_xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Cover</title></head>
<body>
  <div style="text-align: center;">
    <img src="cover.png" alt="Cover" style="max-width: 100%;"/>
  </div>
</body>
</html>"""

    paragraphs = "\n".join(
        f'<p>Paragraph {i}: This is a long paragraph with enough text to fill a page in the reader.</p>'
        for i in range(20)
    )

    chapter1_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter One</title></head>
<body>
  <h1>Chapter One</h1>
  {paragraphs}
</body>
</html>"""

    nav_xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Navigation</title></head>
<body>
  <nav epub:type="toc">
    <ol>
      <li><a href="cover.xhtml">Cover</a></li>
      <li><a href="chapter1.xhtml">Chapter One</a></li>
    </ol>
  </nav>
</body>
</html>"""

    with zipfile.ZipFile(str(epub_path), "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", b"application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container_xml)
        zf.writestr("OEBPS/content.opf", content_opf)
        zf.writestr("OEBPS/cover.xhtml", cover_xhtml)
        zf.writestr("OEBPS/chapter1.xhtml", chapter1_xhtml)
        zf.writestr("OEBPS/nav.xhtml", nav_xhtml)
        zf.writestr("OEBPS/cover.png", png_data)

    return epub_path


def _create_epub_with_long_chapter(tmp_path: Path) -> Path:
    epub_path = tmp_path / "long_book.epub"
    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
    content_opf = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">long-book-001</dc:identifier>
    <dc:title>Long Book</dc:title>
    <dc:creator>Test Author</dc:creator>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="chapter2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
  </manifest>
  <spine>
    <itemref idref="chapter1"/>
    <itemref idref="chapter2"/>
  </spine>
</package>"""
    paragraphs = "\n".join(
        f'<p>Paragraph {i}: This is a long paragraph with enough text to fill a page in the reader. '
        f'We need substantial content to test pagination across multiple pages properly.</p>'
        for i in range(30)
    )
    chapter1_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter One</title></head>
<body>
  <h1>Chapter One</h1>
  {paragraphs}
</body>
</html>"""
    chapter2_xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter Two</title></head>
<body>
  <h1>Chapter Two</h1>
  <p>Second chapter content.</p>
</body>
</html>"""
    nav_xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Navigation</title></head>
<body>
  <nav epub:type="toc">
    <ol>
      <li><a href="chapter1.xhtml">Chapter One</a></li>
      <li><a href="chapter2.xhtml">Chapter Two</a></li>
    </ol>
  </nav>
</body>
</html>"""
    with zipfile.ZipFile(str(epub_path), "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", b"application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container_xml)
        zf.writestr("OEBPS/content.opf", content_opf)
        zf.writestr("OEBPS/chapter1.xhtml", chapter1_xhtml)
        zf.writestr("OEBPS/chapter2.xhtml", chapter2_xhtml)
        zf.writestr("OEBPS/nav.xhtml", nav_xhtml)
    return epub_path


def _query_js(widget, js_code, qapp, timeout_ms=5000):
    results = {}
    def on_result(v):
        results["value"] = v
    widget._web_view.page().runJavaScript(js_code, on_result)
    _process_events_until(qapp, lambda: "value" in results, timeout_ms=timeout_ms)
    return results.get("value")


class TestPaginationFirstPage:
    def test_tall_cover_first_page_not_blank(self, qapp, tmp_path):
        epub_path = _create_epub_with_tall_cover(tmp_path)

        widget = ReaderWidget()
        widget.resize(800, 600)
        widget.show()

        load_events = {"count": 0}
        def on_load(ok):
            load_events["count"] += 1
        widget._web_view.page().loadFinished.connect(on_load)

        widget.load_book(epub_path)

        _process_events_until(qapp, lambda: load_events["count"] >= 1, timeout_ms=10000)
        _process_events_until(qapp, lambda: False, timeout_ms=3000)

        import json
        result = _query_js(widget, """(function() {
            var content = document.getElementById('reader-content');
            var viewport = document.getElementById('viewport');
            return JSON.stringify({
                viewportH: viewport ? viewport.clientHeight : -1,
                paginationReady: typeof paginationReady !== 'undefined' ? paginationReady : 'UNDEF',
                pageBreaks: typeof pageBreaks !== 'undefined' ? pageBreaks : 'UNDEF',
                currentPage: typeof currentPage !== 'undefined' ? currentPage : 'UNDEF',
                opacity: content ? content.style.opacity : 'NO_ELEM'
            });
        })()""", qapp)

        data = json.loads(result) if result else {}
        page_breaks = data.get("pageBreaks", [])

        assert data.get("paginationReady") is True, \
            f"paginationReady should be True, got {data.get('paginationReady')}"
        assert data.get("opacity") == "1", \
            f"opacity should be '1', got {data.get('opacity')}"

        if len(page_breaks) > 1:
            first_page_height = page_breaks[1] - page_breaks[0]
            vh = data.get("viewportH", 0)
            assert first_page_height > vh * 0.5, \
                f"First page should be substantial (>50% of viewport), got {first_page_height}px vs viewport {vh}px, pageBreaks={page_breaks}"

    def test_long_chapter_first_page_not_blank(self, qapp, tmp_path):
        epub_path = _create_epub_with_long_chapter(tmp_path)

        widget = ReaderWidget()
        widget.resize(800, 600)
        widget.show()

        load_events = {"count": 0}
        def on_load(ok):
            load_events["count"] += 1
        widget._web_view.page().loadFinished.connect(on_load)

        widget.load_book(epub_path)

        _process_events_until(qapp, lambda: load_events["count"] >= 1, timeout_ms=10000)
        _process_events_until(qapp, lambda: False, timeout_ms=3000)

        import json
        result = _query_js(widget, """(function() {
            var content = document.getElementById('reader-content');
            var viewport = document.getElementById('viewport');
            return JSON.stringify({
                viewportH: viewport ? viewport.clientHeight : -1,
                paginationReady: typeof paginationReady !== 'undefined' ? paginationReady : 'UNDEF',
                pageBreaks: typeof pageBreaks !== 'undefined' ? pageBreaks : 'UNDEF',
                currentPage: typeof currentPage !== 'undefined' ? currentPage : 'UNDEF',
                opacity: content ? content.style.opacity : 'NO_ELEM'
            });
        })()""", qapp)

        data = json.loads(result) if result else {}
        page_breaks = data.get("pageBreaks", [])

        assert data.get("paginationReady") is True, \
            f"paginationReady should be True, got {data.get('paginationReady')}"
        assert data.get("opacity") == "1", \
            f"opacity should be '1', got {data.get('opacity')}"

        if len(page_breaks) > 1:
            first_page_height = page_breaks[1] - page_breaks[0]
            vh = data.get("viewportH", 0)
            assert first_page_height > vh * 0.5, \
                f"First page should be substantial (>50% of viewport), got {first_page_height}px vs viewport {vh}px, pageBreaks={page_breaks}"

    def test_page_label_updates(self, qapp, tmp_path):
        epub_path = _create_epub_with_long_chapter(tmp_path)

        widget = ReaderWidget()
        widget.resize(800, 600)
        widget.show()

        load_events = {"count": 0}
        def on_load(ok):
            load_events["count"] += 1
        widget._web_view.page().loadFinished.connect(on_load)

        widget.load_book(epub_path)

        _process_events_until(qapp, lambda: load_events["count"] >= 1, timeout_ms=10000)
        _process_events_until(qapp, lambda: False, timeout_ms=3000)

        label = widget._page_label.text()
        assert "/" in label, f"Page label should contain '/', got '{label}'"
        assert label != "0 / 0", f"Page label should not be default '0 / 0', got '{label}'"


class TestReadingProgress:
    def test_get_page_position_default(self, qapp):
        widget = ReaderWidget()
        assert widget._get_page_position() == 0.0

    def test_get_page_position_from_label(self, qapp):
        widget = ReaderWidget()
        widget._page_label.setText("3/10")
        assert widget._get_page_position() == pytest.approx(0.2)

    def test_get_page_position_zero_total(self, qapp):
        widget = ReaderWidget()
        widget._page_label.setText("0/0")
        assert widget._get_page_position() == 0.0

    def test_get_current_progress_default(self, qapp):
        widget = ReaderWidget()
        chapter, position = widget.get_current_progress()
        assert chapter == 0
        assert position == 0.0

    def test_reading_progress_changed_signal(self, qapp, tmp_path):
        epub_path = _create_epub_with_long_chapter(tmp_path)
        widget = ReaderWidget()
        widget.resize(800, 600)
        widget.show()

        progress_events = []
        widget.reading_progress_changed.connect(
            lambda ch, pos: progress_events.append((ch, pos))
        )

        load_events = {"count": 0}
        def on_load(ok):
            load_events["count"] += 1
        widget._web_view.page().loadFinished.connect(on_load)

        widget.load_book(epub_path)

        _process_events_until(qapp, lambda: load_events["count"] >= 1, timeout_ms=10000)
        _process_events_until(qapp, lambda: len(progress_events) > 0, timeout_ms=5000)

        assert len(progress_events) > 0, "reading_progress_changed should be emitted"
        ch, pos = progress_events[0]
        assert ch == 0
        assert 0.0 <= pos <= 1.0

    def test_load_book_with_position(self, qapp, tmp_path):
        epub_path = _create_epub_with_long_chapter(tmp_path)
        widget = ReaderWidget()
        widget.resize(800, 600)
        widget.show()

        load_events = {"count": 0}
        def on_load(ok):
            load_events["count"] += 1
        widget._web_view.page().loadFinished.connect(on_load)

        widget.load_book(epub_path, chapter_index=0, position_in_chapter=0.5)

        _process_events_until(qapp, lambda: load_events["count"] >= 1, timeout_ms=10000)
        _process_events_until(qapp, lambda: False, timeout_ms=3000)

        result = _query_js(widget, "currentPage", qapp)
        assert result is not None and result > 0, \
            f"With position 0.5, should navigate past page 0, got currentPage={result}"

    def test_pending_position_reset_after_load(self, qapp, tmp_path):
        epub_path = _create_epub_with_long_chapter(tmp_path)
        widget = ReaderWidget()
        widget.resize(800, 600)
        widget.show()

        load_events = {"count": 0}
        def on_load(ok):
            load_events["count"] += 1
        widget._web_view.page().loadFinished.connect(on_load)

        widget.load_book(epub_path, position_in_chapter=0.5)
        assert widget._pending_position == 0.5

        _process_events_until(qapp, lambda: load_events["count"] >= 1, timeout_ms=10000)
        _process_events_until(qapp, lambda: False, timeout_ms=2000)

        assert widget._pending_position == 0.0


class TestFullscreenMode:
    def test_fullscreen_mode_hides_toolbar(self, qapp):
        widget = ReaderWidget()
        widget.resize(800, 600)
        widget.show()
        qapp.processEvents()

        assert widget._toolbar.isVisible()
        assert not widget._fullscreen_mode
        assert not widget._exit_fullscreen_action.isVisible()

        widget.set_fullscreen_mode(True)
        qapp.processEvents()

        assert widget._fullscreen_mode
        assert not widget._toolbar.isVisible()
        assert widget._exit_fullscreen_action.isVisible()

    def test_exit_fullscreen_shows_toolbar(self, qapp):
        widget = ReaderWidget()
        widget.resize(800, 600)
        widget.show()
        qapp.processEvents()

        widget.set_fullscreen_mode(True)
        qapp.processEvents()

        widget.set_fullscreen_mode(False)
        qapp.processEvents()

        assert not widget._fullscreen_mode
        assert widget._toolbar.isVisible()
        assert not widget._exit_fullscreen_action.isVisible()

    def test_exit_fullscreen_signal(self, qapp):
        widget = ReaderWidget()
        signal_received = {"called": False}
        widget.exit_fullscreen_requested.connect(
            lambda: signal_received.update({"called": True})
        )

        widget._request_exit_fullscreen()
        assert signal_received["called"]

    def test_mouse_hover_shows_toolbar_in_fullscreen(self, qapp):
        widget = ReaderWidget()
        widget.resize(800, 600)
        widget.show()
        qapp.processEvents()

        widget.set_fullscreen_mode(True)
        qapp.processEvents()
        assert not widget._toolbar.isVisible()

        from PySide6.QtCore import QPointF
        event = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            QPointF(100, 5),
            QPointF(100, 5),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        widget.mouseMoveEvent(event)
        assert widget._toolbar.isVisible()
        assert not widget._toolbar_auto_hidden

        event = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            QPointF(100, 200),
            QPointF(100, 200),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        widget.mouseMoveEvent(event)
        assert not widget._toolbar.isVisible()
        assert widget._toolbar_auto_hidden
