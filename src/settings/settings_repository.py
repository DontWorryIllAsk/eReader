import json
from typing import Optional

from PySide6.QtCore import QByteArray

from src.models.database import Database
from src.settings.settings import ReaderSettings


SETTINGS_KEY = "reader_settings"


class SettingsRepository:
    """Persistence layer for reader settings using the settings table."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, settings: ReaderSettings) -> None:
        """Save reader settings to database."""
        value = json.dumps(settings.to_dict())
        self._db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (SETTINGS_KEY, value),
        )
        self._db.commit()

    def load(self) -> ReaderSettings:
        """Load reader settings from database. Returns defaults if not found."""
        row = self._db.execute(
            "SELECT value FROM settings WHERE key = ?",
            (SETTINGS_KEY,),
        ).fetchone()
        if row is None:
            return ReaderSettings()
        try:
            data = json.loads(row["value"])
            return ReaderSettings.from_dict(data)
        except (json.JSONDecodeError, ValueError, KeyError):
            return ReaderSettings()

    def save_window_geometry(self, geometry_bytes: bytes | QByteArray) -> None:
        """Save window geometry to database."""
        raw = bytes(geometry_bytes)
        self._db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("window_geometry", raw.hex()),
        )
        self._db.commit()

    def load_window_geometry(self) -> Optional[bytes]:
        """Load window geometry from database."""
        row = self._db.execute(
            "SELECT value FROM settings WHERE key = ?",
            ("window_geometry",),
        ).fetchone()
        if row is None:
            return None
        try:
            return bytes.fromhex(row["value"])
        except ValueError:
            return None

    def save_splitter_state(self, state_bytes: bytes | QByteArray) -> None:
        """Save splitter layout state to database."""
        raw = bytes(state_bytes)
        self._db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("splitter_state", raw.hex()),
        )
        self._db.commit()

    def load_splitter_state(self) -> Optional[bytes]:
        """Load splitter layout state from database."""
        row = self._db.execute(
            "SELECT value FROM settings WHERE key = ?",
            ("splitter_state",),
        ).fetchone()
        if row is None:
            return None
        try:
            return bytes.fromhex(row["value"])
        except ValueError:
            return None

    def save_last_book_id(self, book_id: int | None) -> None:
        """Save the last opened book ID."""
        value = str(book_id) if book_id is not None else ""
        self._db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("last_book_id", value),
        )
        self._db.commit()

    def load_last_book_id(self) -> Optional[int]:
        """Load the last opened book ID."""
        row = self._db.execute(
            "SELECT value FROM settings WHERE key = ?",
            ("last_book_id",),
        ).fetchone()
        if row is None:
            return None
        try:
            value = row["value"]
            if value:
                return int(value)
            return None
        except (ValueError, TypeError):
            return None
