from pathlib import Path

import pytest

from src.models.database import Database
from src.models.annotation import (
    Annotation,
    AnnotationRepository,
    Bookmark,
    ANNOTATION_HIGHLIGHT,
    ANNOTATION_UNDERLINE,
    ANNOTATION_STRIKETHROUGH,
)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """Provide a connected database."""
    database = Database(tmp_path / "test.db")
    database.connect()
    yield database
    database.close()


@pytest.fixture
def repo(db: Database) -> AnnotationRepository:
    """Provide an AnnotationRepository instance."""
    return AnnotationRepository(db)


@pytest.fixture
def book_id(db: Database) -> int:
    """Create a test book and return its ID."""
    cursor = db.execute(
        "INSERT INTO books (title, file_path) VALUES (?, ?)",
        ("Test Book", "/test.epub"),
    )
    db.commit()
    return cursor.lastrowid  # type: ignore[return-value]


class TestAnnotationAdd:
    """Tests for adding annotations."""

    def test_add_highlight(self, repo: AnnotationRepository, book_id: int) -> None:
        annotation = Annotation(
            book_id=book_id,
            annotation_type=ANNOTATION_HIGHLIGHT,
            chapter_index=0,
            start_offset=10,
            end_offset=50,
            text_content="highlighted text",
            color="#FFFF00",
        )
        ann_id = repo.add_annotation(annotation)
        assert isinstance(ann_id, int)
        assert ann_id > 0

    def test_add_underline(self, repo: AnnotationRepository, book_id: int) -> None:
        annotation = Annotation(
            book_id=book_id,
            annotation_type=ANNOTATION_UNDERLINE,
            chapter_index=0,
            start_offset=10,
            end_offset=50,
        )
        ann_id = repo.add_annotation(annotation)
        assert ann_id > 0

    def test_add_invalid_type_raises(self, repo: AnnotationRepository, book_id: int) -> None:
        annotation = Annotation(
            book_id=book_id,
            annotation_type="invalid_type",
            chapter_index=0,
            start_offset=10,
            end_offset=50,
        )
        with pytest.raises(ValueError, match="Invalid annotation type"):
            repo.add_annotation(annotation)


class TestAnnotationGet:
    """Tests for retrieving annotations."""

    def test_get_annotations_for_book(self, repo: AnnotationRepository, book_id: int) -> None:
        repo.add_annotation(Annotation(
            book_id=book_id, annotation_type=ANNOTATION_HIGHLIGHT,
            chapter_index=0, start_offset=10, end_offset=50,
        ))
        repo.add_annotation(Annotation(
            book_id=book_id, annotation_type=ANNOTATION_UNDERLINE,
            chapter_index=1, start_offset=20, end_offset=60,
        ))
        annotations = repo.get_annotations_for_book(book_id)
        assert len(annotations) == 2

    def test_get_annotations_for_chapter(self, repo: AnnotationRepository, book_id: int) -> None:
        repo.add_annotation(Annotation(
            book_id=book_id, annotation_type=ANNOTATION_HIGHLIGHT,
            chapter_index=0, start_offset=10, end_offset=50,
        ))
        repo.add_annotation(Annotation(
            book_id=book_id, annotation_type=ANNOTATION_UNDERLINE,
            chapter_index=1, start_offset=20, end_offset=60,
        ))
        chapter_annotations = repo.get_annotations_for_chapter(book_id, 0)
        assert len(chapter_annotations) == 1
        assert chapter_annotations[0].annotation_type == ANNOTATION_HIGHLIGHT


class TestAnnotationDelete:
    """Tests for deleting annotations."""

    def test_delete_annotation(self, repo: AnnotationRepository, book_id: int) -> None:
        ann_id = repo.add_annotation(Annotation(
            book_id=book_id, annotation_type=ANNOTATION_HIGHLIGHT,
            chapter_index=0, start_offset=10, end_offset=50,
        ))
        repo.delete_annotation(ann_id)
        annotations = repo.get_annotations_for_book(book_id)
        assert len(annotations) == 0


class TestBookmark:
    """Tests for bookmarks."""

    def test_add_bookmark(self, repo: AnnotationRepository, book_id: int) -> None:
        bookmark = Bookmark(
            book_id=book_id,
            chapter_index=2,
            position_in_chapter=0.5,
            label="Important section",
        )
        bm_id = repo.add_bookmark(bookmark)
        assert bm_id > 0

    def test_get_bookmarks_for_book(self, repo: AnnotationRepository, book_id: int) -> None:
        repo.add_bookmark(Bookmark(book_id=book_id, chapter_index=0, label="Start"))
        repo.add_bookmark(Bookmark(book_id=book_id, chapter_index=5, label="Middle"))
        bookmarks = repo.get_bookmarks_for_book(book_id)
        assert len(bookmarks) == 2

    def test_delete_bookmark(self, repo: AnnotationRepository, book_id: int) -> None:
        bm_id = repo.add_bookmark(Bookmark(book_id=book_id, chapter_index=0))
        repo.delete_bookmark(bm_id)
        bookmarks = repo.get_bookmarks_for_book(book_id)
        assert len(bookmarks) == 0
