from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.models.annotation import (
    ANNOTATION_HIGHLIGHT,
    ANNOTATION_STRIKETHROUGH,
    ANNOTATION_UNDERLINE,
    Annotation,
)
from src.settings.theme_manager import ThemeManager
from src.icons import get_icon


class AnnotationToolBar(QWidget):
    """Floating popup toolbar for annotation actions (highlight, underline, strikethrough)."""

    annotation_requested = Signal(str, str, int, int)
    annotation_delete_requested = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._current_text: str = ""
        self._current_start: int = 0
        self._current_end: int = 0
        self._selected_annotation_id: Optional[int] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(6, 4, 6, 4)
        frame_layout.setSpacing(2)

        self._info_label = QLabel("No selection")
        frame_layout.addWidget(self._info_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        highlight_btn = QAction(get_icon("highlight"), "Highlight", self)
        highlight_btn.triggered.connect(lambda: self._on_annotate(ANNOTATION_HIGHLIGHT))

        underline_btn = QAction(get_icon("underline"), "Underline", self)
        underline_btn.triggered.connect(lambda: self._on_annotate(ANNOTATION_UNDERLINE))

        strikethrough_btn = QAction(get_icon("strikethrough"), "Strike", self)
        strikethrough_btn.triggered.connect(lambda: self._on_annotate(ANNOTATION_STRIKETHROUGH))

        toolbar = QToolBar()
        toolbar.addAction(highlight_btn)
        toolbar.addAction(underline_btn)
        toolbar.addAction(strikethrough_btn)

        self._delete_btn = QAction(get_icon("delete"), "Delete", self)
        self._delete_btn.setVisible(False)
        self._delete_btn.triggered.connect(self._on_delete)
        toolbar.addAction(self._delete_btn)

        btn_layout.addWidget(toolbar)
        frame_layout.addLayout(btn_layout)

        layout.addWidget(frame)

        self.setFixedWidth(280)

    def show_at_position(self, text: str, start_offset: int, end_offset: int, global_pos: tuple[int, int]) -> None:
        """Show toolbar for a new text selection at the given global position."""
        self._current_text = text
        self._current_start = start_offset
        self._current_end = end_offset
        self._selected_annotation_id = None
        self._delete_btn.setVisible(False)
        display = text if len(text) <= 40 else text[:37] + "..."
        self._info_label.setText(f'"{display}"')
        ThemeManager.apply_to_widget(self)
        self.move(global_pos[0], global_pos[1])
        self.show()

    def show_for_selection(self, text: str, start_offset: int, end_offset: int) -> None:
        """Show toolbar for a new text selection."""
        self._current_text = text
        self._current_start = start_offset
        self._current_end = end_offset
        self._selected_annotation_id = None
        self._delete_btn.setVisible(False)
        display = text if len(text) <= 40 else text[:37] + "..."
        self._info_label.setText(f'"{display}"')
        self.show()
        self.raise_()

    def show_for_annotation(self, annotation: Annotation) -> None:
        """Show toolbar for an existing annotation click."""
        self._selected_annotation_id = annotation.id
        self._current_text = annotation.text_content
        self._current_start = annotation.start_offset
        self._current_end = annotation.end_offset
        self._delete_btn.setVisible(True)
        display = annotation.text_content if len(annotation.text_content) <= 40 else annotation.text_content[:37] + "..."
        self._info_label.setText(f'"{display}"')
        ThemeManager.apply_to_widget(self)
        self.show()
        self.raise_()

    @Slot()
    def _on_annotate(self, ann_type: str) -> None:
        """Emit annotation request with current selection."""
        if self._current_text:
            self.annotation_requested.emit(
                ann_type, self._current_text, self._current_start, self._current_end
            )
            self.hide()

    @Slot()
    def _on_delete(self) -> None:
        """Emit delete request for selected annotation."""
        if self._selected_annotation_id is not None:
            self.annotation_delete_requested.emit(self._selected_annotation_id)
            self.hide()

    def clear_selection(self) -> None:
        """Reset and hide the toolbar."""
        self._current_text = ""
        self._current_start = 0
        self._current_end = 0
        self._selected_annotation_id = None
        self.hide()
