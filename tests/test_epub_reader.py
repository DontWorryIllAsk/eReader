import tempfile
import zipfile
from pathlib import Path

import pytest

from src.readers.epub_reader import EpubReader, Chapter


@pytest.fixture
def sample_epub(tmp_path: Path) -> Path:
    """Create a minimal EPUB file for testing."""
    epub_path = tmp_path / "test_book.epub"

    mimetype_content = b"application/epub+zip"

    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

    content_opf = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">test-book-001</dc:identifier>
    <dc:title>Test Book Title</dc:title>
    <dc:creator>Test Author Name</dc:creator>
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

    chapter1_xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter One</title></head>
<body>
  <h1>Chapter One</h1>
  <p>This is the first chapter of the test book.</p>
  <p>It contains some sample text for testing.</p>
</body>
</html>"""

    chapter2_xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter Two</title></head>
<body>
  <h1>Chapter Two</h1>
  <p>This is the second chapter of the test book.</p>
  <p>More sample text here.</p>
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
        zf.writestr("mimetype", mimetype_content, compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container_xml)
        zf.writestr("OEBPS/content.opf", content_opf)
        zf.writestr("OEBPS/chapter1.xhtml", chapter1_xhtml)
        zf.writestr("OEBPS/chapter2.xhtml", chapter2_xhtml)
        zf.writestr("OEBPS/nav.xhtml", nav_xhtml)

    return epub_path


class TestEpubReaderInit:
    """Tests for EpubReader initialization."""

    def test_load_valid_epub(self, sample_epub: Path) -> None:
        reader = EpubReader(sample_epub)
        assert reader.title == "Test Book Title"
        assert reader.author == "Test Author Name"

    def test_load_nonexistent_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            EpubReader("/nonexistent/path/book.epub")

    def test_load_non_epub_file(self, tmp_path: Path) -> None:
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not an epub")
        with pytest.raises(ValueError, match="Not an EPUB file"):
            EpubReader(txt_file)


class TestEpubReaderChapters:
    """Tests for chapter extraction."""

    def test_chapters_extracted(self, sample_epub: Path) -> None:
        reader = EpubReader(sample_epub)
        assert len(reader.chapters) >= 2

    def test_chapter_has_content(self, sample_epub: Path) -> None:
        reader = EpubReader(sample_epub)
        chapter = reader.get_chapter(0)
        assert chapter is not None
        assert "first chapter" in chapter.html_content.lower()

    def test_get_chapter_by_index(self, sample_epub: Path) -> None:
        reader = EpubReader(sample_epub)
        chapter = reader.get_chapter(1)
        assert chapter is not None
        assert "second chapter" in chapter.html_content.lower()

    def test_get_chapter_out_of_range(self, sample_epub: Path) -> None:
        reader = EpubReader(sample_epub)
        assert reader.get_chapter(999) is None

    def test_total_chapters(self, sample_epub: Path) -> None:
        reader = EpubReader(sample_epub)
        assert reader.total_chapters >= 2


class TestEpubReaderMetadata:
    """Tests for metadata extraction."""

    def test_title(self, sample_epub: Path) -> None:
        reader = EpubReader(sample_epub)
        assert reader.title == "Test Book Title"

    def test_author(self, sample_epub: Path) -> None:
        reader = EpubReader(sample_epub)
        assert reader.author == "Test Author Name"

    def test_metadata_dict(self, sample_epub: Path) -> None:
        reader = EpubReader(sample_epub)
        assert "title" in reader.metadata
        assert "author" in reader.metadata


class TestEpubReaderLinkResolution:
    """Tests for internal link resolution."""

    def test_resolve_internal_link(self, sample_epub: Path) -> None:
        reader = EpubReader(sample_epub)
        result = reader.resolve_chapter_link("chapter2.xhtml")
        assert result is not None
        assert result == 1

    def test_resolve_link_with_anchor(self, sample_epub: Path) -> None:
        reader = EpubReader(sample_epub)
        result = reader.resolve_chapter_link("chapter1.xhtml#section1")
        assert result is not None
        assert result == 0

    def test_resolve_external_link_returns_none(self, sample_epub: Path) -> None:
        reader = EpubReader(sample_epub)
        assert reader.resolve_chapter_link("http://example.com") is None
        assert reader.resolve_chapter_link("mailto:test@test.com") is None

    def test_resolve_nonexistent_link_returns_none(self, sample_epub: Path) -> None:
        reader = EpubReader(sample_epub)
        assert reader.resolve_chapter_link("nonexistent.xhtml") is None
