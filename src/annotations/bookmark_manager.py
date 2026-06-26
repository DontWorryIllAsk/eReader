from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.models.annotation import Bookmark


class BookmarkManager(QWidget):
    """Panel for managing bookmarks in the current book."""

    bookmark_selected = Signal(int, float)
    bookmark_delete_requested = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._bookmarks: list[Bookmark] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        header_layout = QHBoxLayout()
        header = QLabel("Bookmarks")
        header_layout.addWidget(header)
        header_layout.addStretch()

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._on_delete)
        header_layout.addWidget(self._delete_btn)

        layout.addLayout(header_layout)

        self._list_widget = QListWidget()
        self._list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list_widget.customContextMenuRequested.connect(self._on_context_menu)
        self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list_widget)

        self._list_widget.itemSelectionChanged.connect(self._on_selection_changed)

    def load_bookmarks(self, bookmarks: list[Bookmark]) -> None:
        """Load and display bookmarks."""
        self._bookmarks = bookmarks
        self._list_widget.clear()
        for bm in bookmarks:
            self._add_bookmark_item(bm)

    def _add_bookmark_item(self, bm: Bookmark) -> None:
        """Add a single bookmark item to the list."""
        label = bm.label if bm.label else f"Chapter {bm.chapter_index + 1} — {bm.position_in_chapter:.0%}"
        item = QListWidgetItem(label)
        item.setData(0x100, bm.id)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self._list_widget.addItem(item)

    def add_bookmark(self, bookmark: Bookmark) -> None:
        """Add a single bookmark to the list."""
        self._bookmarks.append(bookmark)
        self._add_bookmark_item(bookmark)

    def remove_bookmark(self, bookmark_id: int) -> None:
        """Remove a bookmark from the list by ID."""
        self._bookmarks = [bm for bm in self._bookmarks if bm.id != bookmark_id]
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item and item.data(0x100) == bookmark_id:
                self._list_widget.takeItem(i)
                break
        self._delete_btn.setEnabled(False)

    @Slot()
    def _on_selection_changed(self) -> None:
        """Enable/disable buttons based on selection."""
        has_selection = len(self._list_widget.selectedItems()) > 0
        self._delete_btn.setEnabled(has_selection)

    @Slot(QListWidgetItem)
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle single click - select the item."""
        item.setSelected(True)

    @Slot(QListWidgetItem)
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Navigate to the double-clicked bookmark."""
        self._navigate_to_item(item)

    @Slot()
    def _on_delete(self) -> None:
        """Request deletion of the selected bookmark."""
        items = self._list_widget.selectedItems()
        if items:
            bm_id = items[0].data(0x100)
            if bm_id is not None:
                self.bookmark_delete_requested.emit(bm_id)

    def _on_context_menu(self, pos) -> None:
        """Show context menu for bookmark items."""
        item = self._list_widget.itemAt(pos)
        if item is None:
            return
        item.setSelected(True)
        menu = QMenu(self)
        goto_action = QAction("Go To", self)
        goto_action.triggered.connect(lambda: self._navigate_to_item(item))
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._on_delete())
        menu.addAction(goto_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.exec(self._list_widget.mapToGlobal(pos))

    def _navigate_to_item(self, item: QListWidgetItem) -> None:
        """Emit bookmark_selected signal for the given list item."""
        bm_id = item.data(0x100)
        for bm in self._bookmarks:
            if bm.id == bm_id:
                self.bookmark_selected.emit(bm.chapter_index, bm.position_in_chapter)
                break
