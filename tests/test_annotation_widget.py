from pathlib import Path

import pytest

from PySide6.QtWidgets import QApplication

from src.models.database import Database
from src.models.annotation import (
    ANNOTATION_HIGHLIGHT,
    ANNOTATION_UNDERLINE,
    ANNOTATION_STRIKETHROUGH,
    Annotation,
    AnnotationRepository,
    Bookmark,
)
from src.annotations.annotation_widget import AnnotationToolBar
from src.annotations.bookmark_manager import BookmarkManager


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def db(tmp_path: Path) -> Database:
    database = Database(tmp_path / "test.db")
    database.connect()
    yield database
    database.close()


@pytest.fixture
def repo(db: Database) -> AnnotationRepository:
    return AnnotationRepository(db)


@pytest.fixture
def book_id(db: Database) -> int:
    cursor = db.execute(
        "INSERT INTO books (title, file_path) VALUES (?, ?)",
        ("Test Book", "/test.epub"),
    )
    db.commit()
    return cursor.lastrowid


class TestAnnotationToolBar:
    def test_initial_state(self, qapp):
        toolbar = AnnotationToolBar()
        assert not toolbar.isVisible()
        assert toolbar._current_text == ""

    def test_show_for_selection(self, qapp):
        toolbar = AnnotationToolBar()
        toolbar.show_for_selection("hello world", 10, 21)
        assert toolbar.isVisible()
        assert toolbar._current_text == "hello world"
        assert toolbar._current_start == 10
        assert toolbar._current_end == 21
        assert not toolbar._delete_btn.isVisible()

    def test_show_for_annotation(self, qapp, book_id):
        toolbar = AnnotationToolBar()
        ann = Annotation(
            id=42,
            book_id=book_id,
            annotation_type=ANNOTATION_HIGHLIGHT,
            chapter_index=0,
            start_offset=10,
            end_offset=50,
            text_content="some highlighted text",
            color="#FFFF00",
        )
        toolbar.show_for_annotation(ann)
        assert toolbar.isVisible()
        assert toolbar._selected_annotation_id == 42
        assert toolbar._delete_btn.isVisible()

    def test_annotation_requested_signal(self, qapp):
        toolbar = AnnotationToolBar()
        toolbar.show_for_selection("test text", 0, 9)
        events = []
        toolbar.annotation_requested.connect(lambda *args: events.append(args))
        toolbar._on_annotate(ANNOTATION_HIGHLIGHT)
        assert len(events) == 1
        assert events[0] == (ANNOTATION_HIGHLIGHT, "test text", 0, 9)

    def test_delete_requested_signal(self, qapp, book_id):
        toolbar = AnnotationToolBar()
        ann = Annotation(
            id=99,
            book_id=book_id,
            annotation_type=ANNOTATION_UNDERLINE,
            chapter_index=0,
            start_offset=5,
            end_offset=15,
            text_content="underlined",
        )
        toolbar.show_for_annotation(ann)
        events = []
        toolbar.annotation_delete_requested.connect(lambda aid: events.append(aid))
        toolbar._on_delete()
        assert events == [99]

    def test_clear_selection(self, qapp):
        toolbar = AnnotationToolBar()
        toolbar.show_for_selection("text", 0, 4)
        toolbar.clear_selection()
        assert not toolbar.isVisible()
        assert toolbar._current_text == ""
        assert toolbar._selected_annotation_id is None

    def test_long_text_truncated(self, qapp):
        toolbar = AnnotationToolBar()
        long_text = "a" * 50
        toolbar.show_for_selection(long_text, 0, 50)
        assert "..." in toolbar._info_label.text()


class TestBookmarkManager:
    def test_initial_state(self, qapp):
        manager = BookmarkManager()
        assert manager._list_widget.count() == 0

    def test_load_bookmarks(self, qapp):
        manager = BookmarkManager()
        bookmarks = [
            Bookmark(id=1, book_id=1, chapter_index=0, position_in_chapter=0.0, label="Start"),
            Bookmark(id=2, book_id=1, chapter_index=2, position_in_chapter=0.5, label="Middle"),
        ]
        manager.load_bookmarks(bookmarks)
        assert manager._list_widget.count() == 2

    def test_add_bookmark(self, qapp):
        manager = BookmarkManager()
        bm = Bookmark(id=1, book_id=1, chapter_index=0, position_in_chapter=0.0, label="Test")
        manager.add_bookmark(bm)
        assert manager._list_widget.count() == 1

    def test_remove_bookmark(self, qapp):
        manager = BookmarkManager()
        bm = Bookmark(id=1, book_id=1, chapter_index=0, label="Test")
        manager.add_bookmark(bm)
        manager.remove_bookmark(1)
        assert manager._list_widget.count() == 0

    def test_bookmark_selected_signal(self, qapp):
        manager = BookmarkManager()
        bm = Bookmark(id=5, book_id=1, chapter_index=3, position_in_chapter=0.75)
        manager.add_bookmark(bm)
        events = []
        manager.bookmark_selected.connect(lambda ch, pos: events.append((ch, pos)))
        manager._list_widget.item(0).setSelected(True)
        manager._navigate_to_item(manager._list_widget.selectedItems()[0])
        assert len(events) == 1
        assert events[0] == (3, 0.75)

    def test_bookmark_delete_signal(self, qapp):
        manager = BookmarkManager()
        bm = Bookmark(id=7, book_id=1, chapter_index=0, label="Del")
        manager.add_bookmark(bm)
        events = []
        manager.bookmark_delete_requested.connect(lambda bid: events.append(bid))
        manager._list_widget.item(0).setSelected(True)
        manager._on_delete()
        assert events == [7]

    def test_default_label_when_no_label(self, qapp):
        manager = BookmarkManager()
        bm = Bookmark(id=1, book_id=1, chapter_index=2, position_in_chapter=0.5)
        manager.add_bookmark(bm)
        item = manager._list_widget.item(0)
        assert "Chapter 3" in item.text()

    def test_delete_button_disabled_without_selection(self, qapp):
        manager = BookmarkManager()
        bm = Bookmark(id=1, book_id=1, chapter_index=0, label="Test")
        manager.add_bookmark(bm)
        assert not manager._delete_btn.isEnabled()

    def test_delete_button_enabled_with_selection(self, qapp):
        manager = BookmarkManager()
        bm = Bookmark(id=1, book_id=1, chapter_index=0, label="Test")
        manager.add_bookmark(bm)
        manager._list_widget.item(0).setSelected(True)
        assert manager._delete_btn.isEnabled()
