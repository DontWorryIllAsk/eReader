from pathlib import Path

import pytest

from src.models.database import Database
from src.models.book import Book, BookRepository


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """Provide a connected database."""
    database = Database(tmp_path / "test.db")
    database.connect()
    yield database
    database.close()


@pytest.fixture
def repo(db: Database) -> BookRepository:
    """Provide a BookRepository instance."""
    return BookRepository(db)


@pytest.fixture
def sample_book() -> Book:
    """Provide a sample Book instance."""
    return Book(
        title="Test Book",
        author="Test Author",
        file_path="/path/to/test.epub",
        file_hash="abc123",
    )


class TestBookAdd:
    """Tests for adding books."""

    def test_add_book_returns_id(self, repo: BookRepository, sample_book: Book) -> None:
        book_id = repo.add(sample_book)
        assert isinstance(book_id, int)
        assert book_id > 0

    def test_add_book_persists(self, repo: BookRepository, sample_book: Book) -> None:
        book_id = repo.add(sample_book)
        retrieved = repo.get_by_id(book_id)
        assert retrieved is not None
        assert retrieved.title == "Test Book"
        assert retrieved.author == "Test Author"
        assert retrieved.file_path == "/path/to/test.epub"


class TestBookGet:
    """Tests for retrieving books."""

    def test_get_by_id_not_found(self, repo: BookRepository) -> None:
        result = repo.get_by_id(9999)
        assert result is None

    def test_get_by_file_path(self, repo: BookRepository, sample_book: Book) -> None:
        repo.add(sample_book)
        result = repo.get_by_file_path("/path/to/test.epub")
        assert result is not None
        assert result.title == "Test Book"

    def test_get_by_file_path_not_found(self, repo: BookRepository) -> None:
        result = repo.get_by_file_path("/nonexistent.epub")
        assert result is None

    def test_get_all(self, repo: BookRepository) -> None:
        repo.add(Book(title="Book 1", file_path="/a.epub"))
        repo.add(Book(title="Book 2", file_path="/b.epub"))
        books = repo.get_all()
        assert len(books) == 2


class TestBookUpdate:
    """Tests for updating books."""

    def test_update_reading_progress(self, repo: BookRepository, sample_book: Book) -> None:
        book_id = repo.add(sample_book)
        repo.update_reading_progress(book_id, chapter_index=3, position_in_chapter=0.5)
        updated = repo.get_by_id(book_id)
        assert updated is not None
        assert updated.chapter_index == 3
        assert updated.position_in_chapter == 0.5
        assert updated.last_opened_at is not None


class TestBookDelete:
    """Tests for deleting books."""

    def test_delete_book(self, repo: BookRepository, sample_book: Book) -> None:
        book_id = repo.add(sample_book)
        repo.delete(book_id)
        assert repo.get_by_id(book_id) is None


class TestBookSearch:
    """Tests for searching books by title."""

    def test_search_by_title_match(self, repo: BookRepository) -> None:
        repo.add(Book(title="Architecting Modern Systems", file_path="/a.epub"))
        repo.add(Book(title="Clean Code", file_path="/b.epub"))
        repo.add(Book(title="Design Patterns", file_path="/c.epub"))
        results = repo.search_by_title("Modern")
        assert len(results) == 1
        assert results[0].title == "Architecting Modern Systems"

    def test_search_by_title_case_insensitive(self, repo: BookRepository) -> None:
        repo.add(Book(title="Clean Code", file_path="/a.epub"))
        results = repo.search_by_title("clean")
        assert len(results) == 1
        assert results[0].title == "Clean Code"

    def test_search_by_title_partial_match(self, repo: BookRepository) -> None:
        repo.add(Book(title="Architecting Modern Systems", file_path="/a.epub"))
        repo.add(Book(title="Modern Architecture Guide", file_path="/b.epub"))
        repo.add(Book(title="Clean Code", file_path="/c.epub"))
        results = repo.search_by_title("Modern")
        assert len(results) == 2

    def test_search_by_title_no_match(self, repo: BookRepository) -> None:
        repo.add(Book(title="Clean Code", file_path="/a.epub"))
        results = repo.search_by_title("Python")
        assert len(results) == 0

    def test_search_by_title_empty_keyword(self, repo: BookRepository) -> None:
        repo.add(Book(title="Clean Code", file_path="/a.epub"))
        repo.add(Book(title="Design Patterns", file_path="/b.epub"))
        results = repo.search_by_title("")
        assert len(results) == 2
