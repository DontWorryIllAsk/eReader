from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from src.settings.settings import ReaderSettings, ThemeMode, THEME_COLORS


FONT_FAMILIES = [
    "Serif",
    "Sans-Serif",
    "Monospace",
    "Arial",
    "Georgia",
    "Times New Roman",
    "Verdana",
    "Courier New",
]

FONT_SIZE_MIN = 12
FONT_SIZE_MAX = 36
FONT_SIZE_DEFAULT = 18

THEME_LABELS = {
    ThemeMode.LIGHT: "Light",
    ThemeMode.DARK: "Dark",
    ThemeMode.SEPIA: "Sepia",
    ThemeMode.GREEN: "Green",
}


class SettingsWidget(QWidget):
    """Settings panel for reader customization."""

    settings_changed = Signal(ReaderSettings)

    def __init__(self, current_settings: ReaderSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = current_settings
        self._setup_ui()
        self._load_settings(current_settings)

    def _setup_ui(self) -> None:
        """Initialize the settings UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(self._create_font_group())
        layout.addWidget(self._create_theme_group())
        layout.addStretch()

    def _create_font_group(self) -> QGroupBox:
        """Create font settings group."""
        group = QGroupBox("Font Settings")
        layout = QVBoxLayout(group)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Font:"))
        self._font_combo = QComboBox()
        self._font_combo.addItems(FONT_FAMILIES)
        self._font_combo.currentTextChanged.connect(self._on_settings_changed)
        font_row.addWidget(self._font_combo, 1)
        layout.addLayout(font_row)

        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Size:"))
        self._font_size_slider = QSlider()
        self._font_size_slider.setRange(FONT_SIZE_MIN, FONT_SIZE_MAX)
        self._font_size_slider.setOrientation(Qt.Orientation.Horizontal)
        self._font_size_slider.valueChanged.connect(self._on_font_size_changed)
        size_row.addWidget(self._font_size_slider, 1)
        self._font_size_label = QLabel(f"{self._settings.font_size}px")
        self._font_size_label.setMinimumWidth(40)
        size_row.addWidget(self._font_size_label)
        layout.addLayout(size_row)

        return group

    def _create_theme_group(self) -> QGroupBox:
        """Create theme selection group."""
        group = QGroupBox("Reading Theme")
        layout = QHBoxLayout(group)

        self._theme_buttons: dict[ThemeMode, QPushButton] = {}
        for theme_mode in ThemeMode:
            btn = QPushButton(THEME_LABELS[theme_mode])
            colors = THEME_COLORS[theme_mode]
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {colors['bg']}; color: {colors['text']}; "
                f"border: 2px solid #888; border-radius: 6px; padding: 12px 16px; font-weight: bold; }}"
                f"QPushButton:checked {{ border: 3px solid #2196F3; }}"
            )
            btn.setCheckable(True)
            btn.setProperty("theme_mode", theme_mode)
            btn.clicked.connect(lambda checked, tm=theme_mode: self._on_theme_clicked(tm))
            layout.addWidget(btn)
            self._theme_buttons[theme_mode] = btn

        return group

    def _load_settings(self, settings: ReaderSettings) -> None:
        """Apply current settings to UI controls."""
        self._font_combo.blockSignals(True)
        idx = self._font_combo.findText(settings.font_family)
        if idx >= 0:
            self._font_combo.setCurrentIndex(idx)
        self._font_combo.blockSignals(False)

        self._font_size_slider.blockSignals(True)
        self._font_size_slider.setValue(settings.font_size)
        self._font_size_slider.blockSignals(False)
        self._font_size_label.setText(f"{settings.font_size}px")

        for theme_mode, btn in self._theme_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(theme_mode == settings.theme)
            btn.blockSignals(False)

    @Slot(str)
    def _on_font_size_changed(self, value: int) -> None:
        """Handle font size slider change."""
        self._font_size_label.setText(f"{value}px")
        self._on_settings_changed()

    @Slot(ThemeMode)
    def _on_theme_clicked(self, theme_mode: ThemeMode) -> None:
        """Handle theme button click."""
        for tm, btn in self._theme_buttons.items():
            btn.setChecked(tm == theme_mode)
        self._on_settings_changed()

    @Slot()
    def _on_settings_changed(self) -> None:
        """Collect current UI state and emit settings_changed signal."""
        font_family = self._font_combo.currentText()
        font_size = self._font_size_slider.value()

        active_theme = self._settings.theme
        for theme_mode, btn in self._theme_buttons.items():
            if btn.isChecked():
                active_theme = theme_mode
                break

        new_settings = ReaderSettings(
            font_family=font_family,
            font_size=font_size,
            theme=active_theme,
        )
        self._settings = new_settings
        self.settings_changed.emit(new_settings)

    @property
    def current_settings(self) -> ReaderSettings:
        """Current settings from UI controls."""
        return self._settings
