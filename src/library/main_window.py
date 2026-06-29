import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QSize, Slot, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QToolBar,
    QWidget,
)

from src.models.database import Database
from src.models.book import Book, BookRepository
from src.models.annotation import (
    ANNOTATION_HIGHLIGHT,
    ANNOTATION_STRIKETHROUGH,
    ANNOTATION_UNDERLINE,
    Annotation,
    AnnotationRepository,
    Bookmark,
)
from src.library.library_widget import LibraryWidget
from src.library.import_handler import ImportHandler
from src.readers.reader_widget import ReaderWidget
from src.settings.settings import ReaderSettings, ThemeMode
from src.settings.settings_widget import SettingsWidget
from src.settings.settings_repository import SettingsRepository
from src.settings.theme_manager import ThemeManager
from src.annotations.annotation_widget import AnnotationToolBar
from src.annotations.bookmark_manager import BookmarkManager
from src.icons import get_icon


VIEW_LIBRARY = 0
VIEW_READER = 1


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, db: Database) -> None:
        super().__init__()
        self._db = db
        self._book_repo = BookRepository(db)
        self._annotation_repo = AnnotationRepository(db)
        self._settings_repo = SettingsRepository(db)
        self._settings = self._settings_repo.load()
        self._import_handler = ImportHandler(self._book_repo)
        self._settings_panel_visible = False
        self._current_book_id: Optional[int] = None
        self._fullscreen = False
        self._pending_progress: Optional[tuple[int, float]] = None
        self._set_window_icon()
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_shortcuts()
        self._restore_geometry()
        self._restore_splitter_state()

    def _set_window_icon(self) -> None:
        if getattr(sys, 'frozen', False):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent.parent.parent
        icon_path = base_path / "resources" / "icons" / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _setup_ui(self) -> None:
        """Initialize the main UI layout."""
        self.setWindowTitle("eReader")
        self.setMinimumSize(QSize(900, 650))
        self.resize(1200, 800)
        self.setAcceptDrops(True)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._library_widget = LibraryWidget(self._book_repo)
        self._library_widget.open_book_requested.connect(self._on_open_book)
        self._library_widget.import_requested.connect(self._on_import_files)
        self._stack.addWidget(self._library_widget)

        self._reader_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._reader_widget = ReaderWidget(self._settings)
        self._reader_widget.exit_fullscreen_requested.connect(self.toggle_fullscreen)
        self._reader_widget.toggle_ribbon_requested.connect(self._toggle_ribbon)
        self._reader_widget.reading_progress_changed.connect(self._on_reading_progress_debounced)
        self._reader_widget.text_selected.connect(self._on_text_selected)
        self._reader_widget.annotation_clicked.connect(self._on_annotation_clicked)
        self._reader_widget.chapter_changed.connect(self._on_chapter_changed)
        self._reader_widget.link_clicked.connect(self._on_link_clicked)
        self._reader_splitter.addWidget(self._reader_widget)

        self._annotation_toolbar = AnnotationToolBar()
        self._annotation_toolbar.annotation_requested.connect(self._on_annotation_requested)
        self._annotation_toolbar.annotation_delete_requested.connect(self._on_annotation_delete)
        self._annotation_toolbar.hide()

        self._settings_widget = SettingsWidget(self._settings)
        self._settings_widget.settings_changed.connect(self._on_settings_changed)
        self._settings_widget.setMaximumWidth(320)
        self._settings_widget.setMinimumWidth(240)
        self._settings_widget.hide()
        self._reader_splitter.addWidget(self._settings_widget)

        self._bookmark_manager = BookmarkManager()
        self._bookmark_manager.setMaximumWidth(280)
        self._bookmark_manager.setMinimumWidth(200)
        self._bookmark_manager.bookmark_selected.connect(self._on_bookmark_selected)
        self._bookmark_manager.bookmark_delete_requested.connect(self._on_bookmark_delete)
        self._bookmark_manager.hide()
        self._reader_splitter.addWidget(self._bookmark_manager)

        self._reader_splitter.setStretchFactor(0, 1)
        self._reader_splitter.setStretchFactor(1, 0)
        self._reader_splitter.setStretchFactor(2, 0)
        self._stack.addWidget(self._reader_splitter)



        self._library_widget.refresh()
        self._reopen_last_book()

    def _setup_menu(self) -> None:
        """Create the menu bar."""
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")

        import_action = QAction(get_icon("import"), "&Import EPUB...", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self._on_import_files)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = menu_bar.addMenu("&View")

        self._library_action = QAction(get_icon("library"), "&Library", self)
        self._library_action.setShortcut(QKeySequence("Ctrl+L"))
        self._library_action.triggered.connect(self._show_library)
        view_menu.addAction(self._library_action)

        toggle_settings_action = QAction(get_icon("settings"), "Settings &Panel", self)
        toggle_settings_action.setShortcut(QKeySequence("Ctrl+,"))
        toggle_settings_action.setCheckable(True)
        toggle_settings_action.triggered.connect(self._toggle_settings_panel)
        view_menu.addAction(toggle_settings_action)
        self._toggle_settings_action = toggle_settings_action

        view_menu.addSeparator()

        prev_chapter_action = QAction(get_icon("prev-chapter"), "Previous Chapter", self)
        prev_chapter_action.triggered.connect(self._reader_widget.prev_chapter)
        view_menu.addAction(prev_chapter_action)

        next_chapter_action = QAction(get_icon("next-chapter"), "Next Chapter", self)
        next_chapter_action.triggered.connect(self._reader_widget.next_chapter)
        view_menu.addAction(next_chapter_action)

        view_menu.addSeparator()

        self._fullscreen_action = QAction(get_icon("fullscreen"), "&Fullscreen", self)
        self._fullscreen_action.setShortcut(QKeySequence("F11"))
        self._fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(self._fullscreen_action)

        view_menu.addSeparator()

        self._bookmark_panel_action = QAction(get_icon("bookmarks"), "&Bookmarks", self)
        self._bookmark_panel_action.setShortcut(QKeySequence("Ctrl+B"))
        self._bookmark_panel_action.setCheckable(True)
        self._bookmark_panel_action.triggered.connect(self._toggle_bookmark_panel)
        view_menu.addAction(self._bookmark_panel_action)

        annotate_menu = menu_bar.addMenu("&Annotate")

        add_bookmark_action = QAction(get_icon("bookmark"), "Add &Bookmark", self)
        add_bookmark_action.setShortcut(QKeySequence("Ctrl+D"))
        add_bookmark_action.triggered.connect(self._on_add_bookmark)
        annotate_menu.addAction(add_bookmark_action)

        annotate_menu.addSeparator()

        highlight_action = QAction(get_icon("highlight"), "&Highlight", self)
        highlight_action.triggered.connect(lambda: self._on_quick_annotate(ANNOTATION_HIGHLIGHT))
        annotate_menu.addAction(highlight_action)

        underline_action = QAction(get_icon("underline"), "&Underline", self)
        underline_action.triggered.connect(lambda: self._on_quick_annotate(ANNOTATION_UNDERLINE))
        annotate_menu.addAction(underline_action)

        strikethrough_action = QAction(get_icon("strikethrough"), "&Strikethrough", self)
        strikethrough_action.triggered.connect(lambda: self._on_quick_annotate(ANNOTATION_STRIKETHROUGH))
        annotate_menu.addAction(strikethrough_action)

    def _setup_toolbar(self) -> None:
        """Create the main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        library_action = QAction(get_icon("library"), "Library", self)
        library_action.setShortcut(QKeySequence("Ctrl+L"))
        library_action.triggered.connect(self._show_library)
        toolbar.addAction(library_action)

        toolbar.addSeparator()

        import_action = QAction(get_icon("import"), "Import", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self._on_import_files)
        toolbar.addAction(import_action)

        toolbar.addSeparator()

        settings_action = QAction(get_icon("settings"), "Settings", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._toggle_settings_panel)
        toolbar.addAction(settings_action)

        toolbar.addSeparator()

        fullscreen_action = QAction(get_icon("fullscreen"), "Fullscreen", self)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        toolbar.addAction(fullscreen_action)

        toolbar.addSeparator()

        bookmark_action = QAction(get_icon("bookmark"), "Bookmark", self)
        bookmark_action.triggered.connect(self._on_add_bookmark)
        toolbar.addAction(bookmark_action)

        bookmarks_panel_action = QAction(get_icon("bookmarks"), "Bookmarks", self)
        bookmarks_panel_action.triggered.connect(self._toggle_bookmark_panel)
        toolbar.addAction(bookmarks_panel_action)

        self._main_toolbar = toolbar

        self._ribbon_collapsed = False

    def _setup_shortcuts(self) -> None:
        """Set up global shortcuts that work even when web engine has focus."""
        self._esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self._esc_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._esc_shortcut.activated.connect(self._on_esc_shortcut)

        ribbon_shortcut = QShortcut(QKeySequence("Ctrl+F1"), self)
        ribbon_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        ribbon_shortcut.activated.connect(self._toggle_ribbon)

        for i, theme_mode in enumerate([ThemeMode.LIGHT, ThemeMode.DARK, ThemeMode.SEPIA, ThemeMode.GREEN], 1):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(lambda tm=theme_mode: self._on_theme_shortcut(tm))
            setattr(self, f"_theme_shortcut_{i}", shortcut)

    @Slot()
    def _on_esc_shortcut(self) -> None:
        """Handle Escape shortcut for exiting fullscreen."""
        if self._fullscreen:
            self._exit_fullscreen()

    @Slot()
    def _on_theme_shortcut(self, theme_mode: ThemeMode) -> None:
        """Handle Ctrl+1/2/3/4 theme shortcut."""
        self._settings = ReaderSettings(
            font_family=self._settings.font_family,
            font_size=self._settings.font_size,
            theme=theme_mode,
            line_spacing=self._settings.line_spacing,
        )
        self._reader_widget.apply_settings(self._settings)
        ThemeManager.apply_theme(theme_mode)
        self._settings_widget._load_settings(self._settings)
        self._settings_repo.save(self._settings)

    @Slot()
    def _show_library(self) -> None:
        """Switch to library view."""
        self._flush_reading_progress()
        self._save_current_progress()
        if self._fullscreen:
            self._exit_fullscreen()
        self._stack.setCurrentIndex(VIEW_LIBRARY)
        self._library_widget.refresh()

    @Slot()
    def _show_reader(self) -> None:
        """Switch to reader view."""
        self._stack.setCurrentIndex(VIEW_READER)

    @Slot(int)
    def _on_open_book(self, book_id: int) -> None:
        """Open a book from the library."""
        book = self._book_repo.get_by_id(book_id)
        if book is None:
            return
        self._current_book_id = book_id
        self._show_reader()
        chapter_index = book.chapter_index
        position = book.position_in_chapter

        annotations = self._annotation_repo.get_annotations_for_chapter(
            book_id, chapter_index
        )
        ann_dicts = [
            {
                "id": a.id,
                "annotation_type": a.annotation_type,
                "start_offset": a.start_offset,
                "end_offset": a.end_offset,
                "color": a.color,
            }
            for a in annotations
        ]
        self._reader_widget.set_pending_annotations(ann_dicts)

        bookmarks = self._annotation_repo.get_bookmarks_for_book(book_id)
        self._bookmark_manager.load_bookmarks(bookmarks)

        QTimer.singleShot(50, lambda: self._reader_widget.load_book(
            book.file_path, chapter_index, position
        ))


    @Slot()
    def _toggle_settings_panel(self) -> None:
        """Toggle the settings panel visibility."""
        self._settings_panel_visible = not self._settings_panel_visible
        if self._settings_panel_visible:
            self._settings_widget.show()
            sizes = self._reader_splitter.sizes()
            if len(sizes) >= 2 and sizes[1] == 0:
                total = sum(sizes)
                settings_width = 300
                sizes[1] = settings_width
                sizes[0] = max(total - settings_width, 400)
                self._reader_splitter.setSizes(sizes)
        else:
            self._settings_widget.hide()
        self._toggle_settings_action.setChecked(self._settings_panel_visible)

    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen reading mode."""
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            self._enter_fullscreen()
        else:
            self._exit_fullscreen()

    @Slot()
    def _toggle_ribbon(self) -> None:
        """Toggle menu bar and toolbar visibility (collapse/expand ribbon)."""
        self._ribbon_collapsed = not self._ribbon_collapsed
        if self._ribbon_collapsed:
            self.menuBar().hide()
            self._main_toolbar.hide()
        else:
            self.menuBar().show()
            self._main_toolbar.show()
        self._reader_widget.set_ribbon_collapsed(self._ribbon_collapsed)
        QTimer.singleShot(500, self._reader_widget.repaginate)

    def _enter_fullscreen(self) -> None:
        """Enter fullscreen reading mode."""
        self._settings_widget.hide()
        self._settings_panel_visible = False
        self._toggle_settings_action.setChecked(False)
        self._bookmark_manager.hide()
        self._bookmark_panel_action.setChecked(False)
        self._annotation_toolbar.hide()
        self.menuBar().hide()
        self._main_toolbar.hide()
        self._reader_widget.set_fullscreen_mode(True)
        self.showFullScreen()

    def _exit_fullscreen(self) -> None:
        """Exit fullscreen reading mode."""
        self._fullscreen = False
        if self._ribbon_collapsed:
            self.menuBar().hide()
            self._main_toolbar.hide()
        else:
            self.menuBar().show()
            self._main_toolbar.show()
        self._reader_widget.set_fullscreen_mode(False)
        self.showNormal()

    def keyPressEvent(self, event) -> None:
        """Handle key events for fullscreen toggle, escape, and chapter navigation."""
        if event.key() == Qt.Key.Key_Escape and self._fullscreen:
            self._exit_fullscreen()
            return
        if event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Home and self._stack.currentIndex() == VIEW_READER:
                self._reader_widget._display_chapter(0)
                self._reader_widget.chapter_changed.emit(0)
                return
            if event.key() == Qt.Key.Key_End and self._stack.currentIndex() == VIEW_READER:
                if self._reader_widget._epub_reader:
                    last = self._reader_widget._epub_reader.total_chapters - 1
                    self._reader_widget._display_chapter(last)
                    self._reader_widget.chapter_changed.emit(last)
                return
        super().keyPressEvent(event)

    @Slot(ReaderSettings)
    def _on_settings_changed(self, settings: ReaderSettings) -> None:
        """Apply settings changes to the reader and persist them."""
        self._settings = settings
        self._reader_widget.apply_settings(settings)
        ThemeManager.apply_theme(settings.theme)
        self._settings_repo.save(settings)

    @Slot()
    def _on_import_files(self) -> None:
        """Handle import action - open file dialog."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import EPUB Books",
            "",
            "EPUB Files (*.epub);;All Files (*)",
        )
        if file_paths:
            self._import_and_refresh(file_paths)

    def _import_and_refresh(self, file_paths: list[str]) -> None:
        """Import EPUB files and refresh the library."""
        book_ids = self._import_handler.import_files(file_paths)
        self._library_widget.refresh()
        count = len(book_ids)

    def import_and_open(self, file_path: str) -> None:
        """Import an EPUB file and open it for reading."""
        book_ids = self._import_handler.import_files([file_path])
        self._library_widget.refresh()
        if book_ids:
            self._on_open_book(book_ids[0])


    def dragEnterEvent(self, event) -> None:
        """Accept drag events with EPUB files."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith(".epub") for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        """Handle dropped EPUB files."""
        epub_files = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.toLocalFile().lower().endswith(".epub")
        ]
        if epub_files:
            self._import_and_refresh(epub_files)

    def _restore_geometry(self) -> None:
        """Restore window geometry from settings."""
        geometry = self._settings_repo.load_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1200, 800)

    def _restore_splitter_state(self) -> None:
        """Restore splitter layout from settings."""
        state = self._settings_repo.load_splitter_state()
        if state:
            self._reader_splitter.restoreState(state)

    def _reopen_last_book(self) -> None:
        """Reopen the last book that was being read."""
        last_book_id = self._settings_repo.load_last_book_id()
        if last_book_id is not None:
            book = self._book_repo.get_by_id(last_book_id)
            if book is not None:
                QTimer.singleShot(100, lambda: self._on_open_book(last_book_id))

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self._flush_reading_progress()
        self._save_current_progress()
        self._reader_widget._closing = True
        try:
            self._reader_widget._web_view.page().titleChanged.disconnect(
                self._reader_widget._on_title_changed
            )
        except RuntimeError:
            pass
        self._reader_widget._epub_reader = None
        self._reader_widget._web_view.setHtml(
            "<html><body style='margin:0;'></body>"
            "<script>function initPagination(){} function computePageBreaks(){return true}"
            " function showPage(){} function nextPage(){} function prevPage(){}"
            " function getSelectedTextInfo(){return null} function applyAnnotation(){return false}"
            " function removeAnnotation(){} function loadAnnotations(){} function clearAnnotations(){}"
            " var currentPage=0; var pageBreaks=[0]; var paginationReady=false;"
            " var annotations=[]; var nextAnnId=1;"
            " document.title='';</script></html>"
        )
        geometry = self.saveGeometry()
        self._settings_repo.save_window_geometry(geometry)
        splitter_state = self._reader_splitter.saveState()
        self._settings_repo.save_splitter_state(splitter_state)
        self._settings_repo.save_last_book_id(self._current_book_id)
        self._settings_repo.save(self._settings)
        self._db.close()
        event.accept()

    def _save_current_progress(self) -> None:
        """Save reading progress for the current book."""
        if self._current_book_id is not None:
            chapter_index, position = self._reader_widget.get_current_progress()
            self._book_repo.update_reading_progress(
                self._current_book_id, chapter_index, position
            )

    @Slot(int, float)
    def _on_reading_progress_debounced(self, chapter_index: int, position: float) -> None:
        """Debounce reading progress saves to avoid DB writes on every page turn."""
        self._pending_progress = (chapter_index, position)
        if not hasattr(self, '_progress_timer'):
            from PySide6.QtCore import QTimer
            self._progress_timer = QTimer(self)
            self._progress_timer.setSingleShot(True)
            self._progress_timer.timeout.connect(self._flush_reading_progress)
        self._progress_timer.start(2000)

    def _flush_reading_progress(self) -> None:
        """Actually save the reading progress to DB."""
        if self._current_book_id is not None and self._pending_progress is not None:
            chapter_index, position = self._pending_progress
            self._book_repo.update_reading_progress(
                self._current_book_id, chapter_index, position
            )
            self._pending_progress = None

    @Slot(int, float)
    def _save_reading_progress(self, chapter_index: int, position: float) -> None:
        """Save reading progress when page changes."""
        if self._current_book_id is not None:
            self._book_repo.update_reading_progress(
                self._current_book_id, chapter_index, position
            )

    @Slot(str, int, int)
    def _on_text_selected(self, text: str, start_offset: int, end_offset: int) -> None:
        """Handle text selection in the reader - show annotation toolbar."""
        if self._current_book_id is None:
            return
        global_pos = self._reader_widget.mapToGlobal(
            self._reader_widget.rect().center()
        )
        self._annotation_toolbar.show_at_position(
            text, start_offset, end_offset,
            (global_pos.x() - 140, global_pos.y() - 80)
        )

    @Slot(int)
    def _on_annotation_clicked(self, ann_id: int) -> None:
        """Handle click on an existing annotation in the reader."""
        if self._current_book_id is None:
            return
        chapter = self._reader_widget.current_chapter_index
        annotations = self._annotation_repo.get_annotations_for_chapter(
            self._current_book_id, chapter
        )
        for ann in annotations:
            if ann.id == ann_id:
                global_pos = self._reader_widget.mapToGlobal(
                    self._reader_widget.rect().center()
                )
                self._annotation_toolbar.move(global_pos.x() - 140, global_pos.y() - 80)
                self._annotation_toolbar.show_for_annotation(ann)
                break

    @Slot(str, str, int, int)
    def _on_annotation_requested(self, ann_type: str, text: str, start_offset: int, end_offset: int) -> None:
        """Handle annotation creation request from the annotation toolbar."""
        if self._current_book_id is None:
            return
        color = "#FFFF00" if ann_type == ANNOTATION_HIGHLIGHT else ""
        annotation = Annotation(
            book_id=self._current_book_id,
            annotation_type=ann_type,
            chapter_index=self._reader_widget.current_chapter_index,
            start_offset=start_offset,
            end_offset=end_offset,
            text_content=text,
            color=color,
        )
        ann_id = self._annotation_repo.add_annotation(annotation)
        self._reader_widget.apply_annotation(ann_id, ann_type, start_offset, end_offset, color)

    @Slot(int)
    def _on_annotation_delete(self, ann_id: int) -> None:
        """Handle annotation deletion request."""
        self._annotation_repo.delete_annotation(ann_id)
        self._reader_widget.remove_annotation(ann_id)

    @Slot(int)
    def _on_chapter_changed(self, chapter_index: int) -> None:
        """Load annotations when chapter changes."""
        if self._current_book_id is None:
            return
        annotations = self._annotation_repo.get_annotations_for_chapter(
            self._current_book_id, chapter_index
        )
        ann_dicts = [
            {
                "id": a.id,
                "annotation_type": a.annotation_type,
                "start_offset": a.start_offset,
                "end_offset": a.end_offset,
                "color": a.color,
            }
            for a in annotations
        ]
        self._reader_widget.set_pending_annotations(ann_dicts)
        self._reader_widget._load_pending_annotations()
        self._annotation_toolbar.clear_selection()

    @Slot(str)
    def _on_link_clicked(self, href: str) -> None:
        """Handle internal link click - navigate to the referenced chapter."""
        epub_reader = self._reader_widget.epub_reader
        if epub_reader is None:
            return
        chapter_index = epub_reader.resolve_chapter_link(href)
        if chapter_index is not None:
            self._reader_widget._display_chapter(chapter_index)
            self._reader_widget.chapter_changed.emit(chapter_index)

    @Slot()
    def _on_add_bookmark(self) -> None:
        """Add a bookmark at the current reading position and show the panel."""
        if self._current_book_id is None:
            return
        chapter_index, position = self._reader_widget.get_current_progress()
        bookmark = Bookmark(
            book_id=self._current_book_id,
            chapter_index=chapter_index,
            position_in_chapter=position,
        )
        bm_id = self._annotation_repo.add_bookmark(bookmark)
        bookmark.id = bm_id
        self._bookmark_manager.add_bookmark(bookmark)
        if not self._bookmark_manager.isVisible():
            self._bookmark_manager.show()
            self._bookmark_panel_action.setChecked(True)
            sizes = self._reader_splitter.sizes()
            if len(sizes) >= 3 and sizes[2] == 0:
                total = sum(sizes)
                sizes[2] = 250
                sizes[0] = max(total - 250, 400)
                self._reader_splitter.setSizes(sizes)

    @Slot()
    def _toggle_bookmark_panel(self) -> None:
        """Toggle the bookmark manager panel."""
        if self._bookmark_manager.isVisible():
            self._bookmark_manager.hide()
            self._bookmark_panel_action.setChecked(False)
        else:
            self._bookmark_manager.show()
            self._bookmark_panel_action.setChecked(True)
            sizes = self._reader_splitter.sizes()
            if len(sizes) >= 3 and sizes[2] == 0:
                total = sum(sizes)
                sizes[2] = 250
                sizes[0] = max(total - 250, 400)
                self._reader_splitter.setSizes(sizes)

    @Slot(int, float)
    def _on_bookmark_selected(self, chapter_index: int, position: float) -> None:
        """Navigate to a bookmark position."""
        if self._current_book_id is None:
            return
        book = self._book_repo.get_by_id(self._current_book_id)
        if book is None:
            return
        annotations = self._annotation_repo.get_annotations_for_chapter(
            self._current_book_id, chapter_index
        )
        ann_dicts = [
            {
                "id": a.id,
                "annotation_type": a.annotation_type,
                "start_offset": a.start_offset,
                "end_offset": a.end_offset,
                "color": a.color,
            }
            for a in annotations
        ]
        self._reader_widget.set_pending_annotations(ann_dicts)
        self._reader_widget.load_book(book.file_path, chapter_index, position)

    @Slot(int)
    def _on_bookmark_delete(self, bookmark_id: int) -> None:
        """Delete a bookmark."""
        self._annotation_repo.delete_bookmark(bookmark_id)
        self._bookmark_manager.remove_bookmark(bookmark_id)

    @Slot(str)
    def _on_quick_annotate(self, ann_type: str) -> None:
        """Quick-annotate selected text from menu/keyboard."""
        if self._current_book_id is None:
            return
        self._reader_widget._web_view.page().runJavaScript(
            "getSelectedTextInfo()", self._on_quick_annotate_result(ann_type)
        )

    def _on_quick_annotate_result(self, ann_type: str):
        """Callback for quick annotate after getting selection info from JS."""
        def handler(result):
            if result is None:
                return
            text = result.get("text", "")
            start = result.get("startOffset", 0)
            end = result.get("endOffset", 0)
            if text:
                self._on_annotation_requested(ann_type, text, start, end)
        return handler
