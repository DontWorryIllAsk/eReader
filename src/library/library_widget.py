from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QAction, QPixmap, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.models.book import Book, BookRepository
from src.utils import format_file_size
from src.icons import get_icon


BOOK_CARD_MIN_WIDTH = 160
BOOK_CARD_MAX_WIDTH = 200
BOOK_CARD_HEIGHT = 260
COVER_WIDTH = 140
COVER_HEIGHT = 200
BOOKS_PER_BATCH = 30


class BookCardWidget(QFrame):
    """A single book card in the library grid."""

    open_book = Signal(int)
    delete_book = Signal(int)

    def __init__(self, book: Book, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._book = book
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize the card UI."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedSize(BOOK_CARD_MAX_WIDTH, BOOK_CARD_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            "BookCardWidget { border: 1px solid #ddd; border-radius: 8px; "
            "background: white; }"
            "BookCardWidget:hover { border: 2px solid #2196F3; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 6)
        layout.setSpacing(4)

        self._cover_label = QLabel()
        self._cover_label.setFixedSize(COVER_WIDTH, COVER_HEIGHT)
        self._cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover_label.setStyleSheet(
            "background: #e0e0e0; border-radius: 4px; font-size: 14px; color: #666;"
        )
        self._load_cover()
        layout.addWidget(self._cover_label, 0, Qt.AlignmentFlag.AlignHCenter)

        self._title_label = QLabel(self._book.title)
        self._title_label.setWordWrap(True)
        self._title_label.setMaximumHeight(36)
        layout.addWidget(self._title_label)

        self._author_label = QLabel(self._book.author or "Unknown")
        self._author_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self._author_label)

    def _load_cover(self) -> None:
        """Load cover image or show placeholder."""
        if self._book.cover_path and Path(self._book.cover_path).exists():
            pixmap = QPixmap(self._book.cover_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    COVER_WIDTH, COVER_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._cover_label.setPixmap(scaled)
                return
        self._cover_label.setText("No Cover")

    def mousePressEvent(self, event) -> None:
        """Handle click to open book."""
        if event.button() == Qt.MouseButton.LeftButton and self._book.id is not None:
            self.open_book.emit(self._book.id)
        else:
            super().mousePressEvent(event)

    def contextMenuEvent(self, event) -> None:
        """Show context menu."""
        menu = QMenu(self)
        open_action = menu.addAction("Open")
        delete_action = menu.addAction("Delete")
        action = menu.exec(event.globalPos())
        if action == open_action and self._book.id is not None:
            self.open_book.emit(self._book.id)
        elif action == delete_action and self._book.id is not None:
            self.delete_book.emit(self._book.id)

    @property
    def book(self) -> Book:
        """Get the book associated with this card."""
        return self._book


class LibraryWidget(QWidget):
    """Book library view with grid display, search, and infinite scroll."""

    open_book_requested = Signal(int)
    import_requested = Signal()

    def __init__(self, book_repo: BookRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._book_repo = book_repo
        self._book_cards: list[BookCardWidget] = []
        self._all_books: list[Book] = []
        self._displayed_count: int = 0
        self._search_keyword: str = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize the library UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._create_toolbar())

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)

        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(16)
        self._grid_layout.setContentsMargins(20, 20, 20, 20)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self._grid_container.setLayout(self._grid_layout)
        self._scroll_area.setWidget(self._grid_container)
        layout.addWidget(self._scroll_area)

        self._empty_label = QLabel("No books in library.\nClick 'Import' or drag EPUB files here.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty_label)
        self._empty_label.hide()

    def _create_toolbar(self) -> QToolBar:
        """Create library toolbar."""
        toolbar = QToolBar("Library Toolbar")
        toolbar.setMovable(False)

        import_action = QAction(get_icon("import"), "Import", self)
        import_action.triggered.connect(self.import_requested.emit)
        toolbar.addAction(import_action)

        toolbar.addSeparator()

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search books...")
        self._search_box.setClearButtonEnabled(True)
        self._search_box.setMaximumWidth(260)
        self._search_box.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self._search_box)

        toolbar.addSeparator()

        self._count_label = QLabel("0 books")
        toolbar.addWidget(self._count_label)

        return toolbar

    @Slot(str)
    def _on_search_changed(self, text: str) -> None:
        """Handle search box text change with debounce."""
        self._search_keyword = text.strip()
        self.refresh()

    def refresh(self) -> None:
        """Reload books from database and refresh the grid."""
        self._clear_grid()
        self._displayed_count = 0

        if self._search_keyword:
            self._all_books = self._book_repo.search_by_title(self._search_keyword)
        else:
            self._all_books = self._book_repo.get_all()

        if not self._all_books:
            self._empty_label.show()
            self._scroll_area.hide()
            self._count_label.setText("0 books")
            return

        self._empty_label.hide()
        self._scroll_area.show()
        total = len(self._all_books)
        if self._search_keyword:
            self._count_label.setText(f"{total} result{'s' if total != 1 else ''}")
        else:
            self._count_label.setText(f"{total} book{'s' if total != 1 else ''}")

        self._load_next_batch()

    def _load_next_batch(self) -> None:
        """Load the next batch of book cards into the grid."""
        columns = max(1, self.width() // (BOOK_CARD_MAX_WIDTH + 32))
        start = self._displayed_count
        end = min(start + BOOKS_PER_BATCH, len(self._all_books))

        for i in range(start, end):
            book = self._all_books[i]
            card = BookCardWidget(book)
            card.open_book.connect(self.open_book_requested.emit)
            card.delete_book.connect(self._on_delete_book)
            row, col = divmod(i, columns)
            self._grid_layout.addWidget(card, row, col)
            self._book_cards.append(card)

        self._displayed_count = end

    @Slot(int)
    def _on_scroll(self, value: int) -> None:
        """Load more books when scrolling near the bottom."""
        scrollbar = self._scroll_area.verticalScrollBar()
        if value >= scrollbar.maximum() - 100 and self._displayed_count < len(self._all_books):
            self._load_next_batch()

    def _clear_grid(self) -> None:
        """Remove all book cards from the grid."""
        for card in self._book_cards:
            self._grid_layout.removeWidget(card)
            card.deleteLater()
        self._book_cards.clear()

    @Slot(int)
    def _on_delete_book(self, book_id: int) -> None:
        """Handle book deletion request."""
        book = self._book_repo.get_by_id(book_id)
        if book is None:
            return
        reply = QMessageBox.question(
            self,
            "Delete Book",
            f"Remove '{book.title}' from library?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._book_repo.delete(book_id)
            self.refresh()

    def resizeEvent(self, event) -> None:
        """Re-layout grid on resize."""
        super().resizeEvent(event)
        if self._book_cards:
            self.refresh()

    def dragEnterEvent(self, event) -> None:
        """Accept drag events with EPUB files."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith(".epub") for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        """Handle dropped EPUB files."""
        epub_files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".epub"):
                epub_files.append(file_path)
        if epub_files:
            self._import_files(epub_files)

    def _import_files(self, file_paths: list[str]) -> None:
        """Import EPUB files - emits import_requested for each file."""
        from src.library.import_handler import ImportHandler
        handler = ImportHandler(self._book_repo)
        for fp in file_paths:
            handler.import_epub(fp)
        self.refresh()
