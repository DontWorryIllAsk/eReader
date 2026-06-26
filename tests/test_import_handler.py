import tempfile
import zipfile
from pathlib import Path

import pytest

from src.models.database import Database
from src.models.book import Book, BookRepository
from src.library.import_handler import ImportHandler


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """Provide a connected database."""
    database = Database(tmp_path / "test.db")
    database.connect()
    yield database
    database.close()


@pytest.fixture
def book_repo(db: Database) -> BookRepository:
    """Provide a BookRepository instance."""
    return BookRepository(db)


@pytest.fixture
def handler(book_repo: BookRepository) -> ImportHandler:
    """Provide an ImportHandler instance."""
    return ImportHandler(book_repo)


@pytest.fixture
def sample_epub(tmp_path: Path) -> Path:
    """Create a minimal EPUB file for testing."""
    epub_path = tmp_path / "import_test.epub"

    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

    content_opf = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">import-test-001</dc:identifier>
    <dc:title>Import Test Book</dc:title>
    <dc:creator>Test Author</dc:creator>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chapter1"/>
  </spine>
</package>"""

    chapter1_xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter One</title></head>
<body><h1>Chapter One</h1><p>Test content.</p></body>
</html>"""

    with zipfile.ZipFile(str(epub_path), "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", b"application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container_xml)
        zf.writestr("OEBPS/content.opf", content_opf)
        zf.writestr("OEBPS/chapter1.xhtml", chapter1_xhtml)

    return epub_path


class TestImportEpub:
    """Tests for importing single EPUB files."""

    def test_import_epub_returns_book_id(self, handler: ImportHandler, sample_epub: Path) -> None:
        book_id = handler.import_epub(sample_epub)
        assert isinstance(book_id, int)
        assert book_id > 0

    def test_import_epub_creates_book_record(
        self, handler: ImportHandler, book_repo: BookRepository, sample_epub: Path
    ) -> None:
        book_id = handler.import_epub(sample_epub)
        book = book_repo.get_by_id(book_id)
        assert book is not None
        assert book.title == "Import Test Book"
        assert book.author == "Test Author"
        assert book.file_path == str(sample_epub)

    def test_import_duplicate_returns_same_id(
        self, handler: ImportHandler, sample_epub: Path
    ) -> None:
        id1 = handler.import_epub(sample_epub)
        id2 = handler.import_epub(sample_epub)
        assert id1 == id2

    def test_import_nonexistent_file_raises(self, handler: ImportHandler) -> None:
        with pytest.raises(FileNotFoundError):
            handler.import_epub("/nonexistent/book.epub")

    def test_import_non_epub_raises(self, handler: ImportHandler, tmp_path: Path) -> None:
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not an epub")
        with pytest.raises(ValueError, match="Not an EPUB file"):
            handler.import_epub(txt_file)

    def test_import_epub_stores_file_hash(
        self, handler: ImportHandler, book_repo: BookRepository, sample_epub: Path
    ) -> None:
        book_id = handler.import_epub(sample_epub)
        book = book_repo.get_by_id(book_id)
        assert book is not None
        assert len(book.file_hash) > 0


class TestImportFiles:
    """Tests for batch importing."""

    def test_import_multiple_files(
        self, handler: ImportHandler, sample_epub: Path, tmp_path: Path
    ) -> None:
        epub2_path = tmp_path / "book2.epub"
        import shutil
        shutil.copy2(str(sample_epub), str(epub2_path))

        book_ids = handler.import_files([str(sample_epub), str(epub2_path)])
        assert len(book_ids) == 2

    def test_import_files_skips_invalid(self, handler: ImportHandler, sample_epub: Path) -> None:
        book_ids = handler.import_files([str(sample_epub), "/nonexistent.epub"])
        assert len(book_ids) == 1

    def test_import_empty_list(self, handler: ImportHandler) -> None:
        book_ids = handler.import_files([])
        assert book_ids == []
