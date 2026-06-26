from PySide6.QtWidgets import QApplication, QWidget

from src.settings.settings import ThemeMode
from src.settings.themes import APP_THEMES


class ThemeManager:
    """Manages application-wide QSS theme styling."""

    _current_theme: str = "light"

    @classmethod
    def apply_theme(cls, theme_mode: ThemeMode) -> None:
        """Apply the app chrome theme matching the reading theme mode."""
        app = QApplication.instance()
        if app is None:
            return
        theme_key = theme_mode.value
        qss = APP_THEMES.get(theme_key, APP_THEMES["light"])
        app.setStyleSheet(qss)
        cls._current_theme = theme_key

    @classmethod
    def current_theme(cls) -> str:
        """Get the current app theme key."""
        return cls._current_theme

    @classmethod
    def get_stylesheet(cls) -> str:
        """Get the current theme QSS string."""
        return APP_THEMES.get(cls._current_theme, APP_THEMES["light"])

    @classmethod
    def apply_to_widget(cls, widget: QWidget) -> None:
        """Apply the current theme stylesheet to a specific widget (for popup windows)."""
        widget.setStyleSheet(cls.get_stylesheet())
