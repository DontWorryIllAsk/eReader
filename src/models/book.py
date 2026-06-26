import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from src.models.database import Database


@dataclass
class Book:
    """Represents a book in the library."""

    id: Optional[int] = None
    title: str = ""
    author: str = ""
    file_path: str = ""
    cover_path: str = ""
    file_hash: str = ""
    added_at: Optional[str] = None
    last_opened_at: Optional[str] = None
    reading_progress: float = 0.0
    chapter_index: int = 0
    position_in_chapter: float = 0.0


class BookRepository:
    """Data access layer for books."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def add(self, book: Book) -> int:
        """Add a new book to the library. Returns the book ID."""
        cursor = self._db.execute(
            """INSERT INTO books (title, author, file_path, cover_path, file_hash)
               VALUES (?, ?, ?, ?, ?)""",
            (book.title, book.author, book.file_path, book.cover_path, book.file_hash),
        )
        self._db.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def get_by_id(self, book_id: int) -> Optional[Book]:
        """Get a book by its ID."""
        row = self._db.execute(
            "SELECT * FROM books WHERE id = ?", (book_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_book(row)

    def get_by_file_path(self, file_path: str) -> Optional[Book]:
        """Get a book by its file path."""
        row = self._db.execute(
            "SELECT * FROM books WHERE file_path = ?", (file_path,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_book(row)

    def get_all(self) -> list[Book]:
        """Get all books in the library."""
        rows = self._db.execute(
            "SELECT * FROM books ORDER BY added_at DESC"
        ).fetchall()
        return [self._row_to_book(row) for row in rows]

    def search_by_title(self, keyword: str) -> list[Book]:
        """Search books by title keyword (case-insensitive)."""
        rows = self._db.execute(
            "SELECT * FROM books WHERE title LIKE ? ORDER BY added_at DESC",
            (f"%{keyword}%",),
        ).fetchall()
        return [self._row_to_book(row) for row in rows]

    def update_reading_progress(
        self, book_id: int, chapter_index: int, position_in_chapter: float
    ) -> None:
        """Update reading progress for a book."""
        progress = self._calculate_progress(book_id, chapter_index, position_in_chapter)
        self._db.execute(
            """UPDATE books
               SET chapter_index = ?, position_in_chapter = ?,
                   reading_progress = ?, last_opened_at = ?
               WHERE id = ?""",
            (chapter_index, position_in_chapter, progress, datetime.now().isoformat(), book_id),
        )
        self._db.commit()

    def delete(self, book_id: int) -> None:
        """Delete a book from the library."""
        self._db.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self._db.commit()

    def _calculate_progress(
        self, book_id: int, chapter_index: int, position_in_chapter: float
    ) -> float:
        """Calculate overall reading progress as a fraction."""
        try:
            from src.readers.epub_reader import EpubReader

            book = self.get_by_id(book_id)
            if book is None:
                return 0.0
            reader = EpubReader(book.file_path)
            total_chapters = len(reader.chapters)
            if total_chapters == 0:
                return 0.0
            return (chapter_index + position_in_chapter) / total_chapters
        except Exception:
            return 0.0

    @staticmethod
    def _row_to_book(row: sqlite3.Row) -> Book:
        """Convert a database row to a Book dataclass."""
        return Book(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            file_path=row["file_path"],
            cover_path=row["cover_path"],
            file_hash=row["file_hash"],
            added_at=row["added_at"],
            last_opened_at=row["last_opened_at"],
            reading_progress=row["reading_progress"],
            chapter_index=row["chapter_index"],
            position_in_chapter=row["position_in_chapter"],
        )
