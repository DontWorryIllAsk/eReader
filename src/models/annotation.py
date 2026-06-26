import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.models.database import Database


ANNOTATION_HIGHLIGHT = "highlight"
ANNOTATION_UNDERLINE = "underline"
ANNOTATION_STRIKETHROUGH = "strikethrough"

VALID_ANNOTATION_TYPES = {
    ANNOTATION_HIGHLIGHT,
    ANNOTATION_UNDERLINE,
    ANNOTATION_STRIKETHROUGH,
}


@dataclass
class Annotation:
    """Represents a text annotation in a book."""

    id: Optional[int] = None
    book_id: int = 0
    annotation_type: str = ANNOTATION_HIGHLIGHT
    chapter_index: int = 0
    start_offset: int = 0
    end_offset: int = 0
    text_content: str = ""
    color: str = "#FFFF00"
    note: str = ""
    created_at: Optional[str] = None


@dataclass
class Bookmark:
    """Represents a bookmark in a book."""

    id: Optional[int] = None
    book_id: int = 0
    chapter_index: int = 0
    position_in_chapter: float = 0.0
    label: str = ""
    created_at: Optional[str] = None


class AnnotationRepository:
    """Data access layer for annotations and bookmarks."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def add_annotation(self, annotation: Annotation) -> int:
        """Add a new annotation. Returns the annotation ID."""
        if annotation.annotation_type not in VALID_ANNOTATION_TYPES:
            raise ValueError(
                f"Invalid annotation type: {annotation.annotation_type}. "
                f"Must be one of {VALID_ANNOTATION_TYPES}"
            )
        cursor = self._db.execute(
            """INSERT INTO annotations
               (book_id, annotation_type, chapter_index, start_offset, end_offset,
                text_content, color, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                annotation.book_id,
                annotation.annotation_type,
                annotation.chapter_index,
                annotation.start_offset,
                annotation.end_offset,
                annotation.text_content,
                annotation.color,
                annotation.note,
            ),
        )
        self._db.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def get_annotations_for_book(self, book_id: int) -> list[Annotation]:
        """Get all annotations for a book."""
        rows = self._db.execute(
            "SELECT * FROM annotations WHERE book_id = ? ORDER BY chapter_index, start_offset",
            (book_id,),
        ).fetchall()
        return [self._row_to_annotation(row) for row in rows]

    def get_annotations_for_chapter(
        self, book_id: int, chapter_index: int
    ) -> list[Annotation]:
        """Get annotations for a specific chapter."""
        rows = self._db.execute(
            """SELECT * FROM annotations
               WHERE book_id = ? AND chapter_index = ?
               ORDER BY start_offset""",
            (book_id, chapter_index),
        ).fetchall()
        return [self._row_to_annotation(row) for row in rows]

    def delete_annotation(self, annotation_id: int) -> None:
        """Delete an annotation."""
        self._db.execute("DELETE FROM annotations WHERE id = ?", (annotation_id,))
        self._db.commit()

    def add_bookmark(self, bookmark: Bookmark) -> int:
        """Add a new bookmark. Returns the bookmark ID."""
        cursor = self._db.execute(
            """INSERT INTO bookmarks (book_id, chapter_index, position_in_chapter, label)
               VALUES (?, ?, ?, ?)""",
            (bookmark.book_id, bookmark.chapter_index, bookmark.position_in_chapter, bookmark.label),
        )
        self._db.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def get_bookmarks_for_book(self, book_id: int) -> list[Bookmark]:
        """Get all bookmarks for a book."""
        rows = self._db.execute(
            "SELECT * FROM bookmarks WHERE book_id = ? ORDER BY chapter_index",
            (book_id,),
        ).fetchall()
        return [self._row_to_bookmark(row) for row in rows]

    def delete_bookmark(self, bookmark_id: int) -> None:
        """Delete a bookmark."""
        self._db.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        self._db.commit()

    @staticmethod
    def _row_to_annotation(row: sqlite3.Row) -> Annotation:
        """Convert a database row to an Annotation dataclass."""
        return Annotation(
            id=row["id"],
            book_id=row["book_id"],
            annotation_type=row["annotation_type"],
            chapter_index=row["chapter_index"],
            start_offset=row["start_offset"],
            end_offset=row["end_offset"],
            text_content=row["text_content"],
            color=row["color"],
            note=row["note"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_bookmark(row: sqlite3.Row) -> Bookmark:
        """Convert a database row to a Bookmark dataclass."""
        return Bookmark(
            id=row["id"],
            book_id=row["book_id"],
            chapter_index=row["chapter_index"],
            position_in_chapter=row["position_in_chapter"],
            label=row["label"],
            created_at=row["created_at"],
        )
