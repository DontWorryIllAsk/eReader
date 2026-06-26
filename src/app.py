import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from src.library.main_window import MainWindow
from src.models.database import Database
from src.settings.settings import ReaderSettings, ThemeMode
from src.settings.settings_repository import SettingsRepository
from src.settings.theme_manager import ThemeManager


class EReaderApp:
    """Main application controller."""

    def __init__(self) -> None:
        self._app: Optional[QApplication] = None
        self._db: Optional[Database] = None
        self._main_window: Optional[MainWindow] = None

    def run(self) -> int:
        """Initialize and run the application. Returns exit code."""
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("eReader")
        self._app.setOrganizationName("eReader")

        self._db = Database()
        self._db.connect()

        settings_repo = SettingsRepository(self._db)
        settings = settings_repo.load()
        ThemeManager.apply_theme(settings.theme)

        self._main_window = MainWindow(self._db)
        self._main_window.show()

        epub_args = self._collect_epub_args()
        if epub_args:
            QTimer.singleShot(100, lambda: self._main_window.import_and_open(epub_args[0]))

        return self._app.exec()

    def _collect_epub_args(self) -> list[str]:
        """Collect .epub file paths from command line arguments."""
        epub_files = []
        for arg in self._app.arguments()[1:]:
            path = Path(arg)
            if path.suffix.lower() == ".epub" and path.exists():
                epub_files.append(str(path.resolve()))
        return epub_files
