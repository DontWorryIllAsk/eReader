from pathlib import Path

import pytest

from src.models.database import Database
from src.settings.settings import ReaderSettings, ThemeMode
from src.settings.settings_repository import SettingsRepository


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """Provide a connected database."""
    database = Database(tmp_path / "test.db")
    database.connect()
    yield database
    database.close()


@pytest.fixture
def repo(db: Database) -> SettingsRepository:
    """Provide a SettingsRepository instance."""
    return SettingsRepository(db)


class TestSettingsSave:
    """Tests for saving settings."""

    def test_save_and_load_defaults(self, repo: SettingsRepository) -> None:
        settings = ReaderSettings()
        repo.save(settings)
        loaded = repo.load()
        assert loaded.font_family == "Serif"
        assert loaded.font_size == 18
        assert loaded.theme == ThemeMode.LIGHT

    def test_save_custom_settings(self, repo: SettingsRepository) -> None:
        settings = ReaderSettings(
            font_family="Arial",
            font_size=24,
            theme=ThemeMode.DARK,
            line_spacing=2.0,
        )
        repo.save(settings)
        loaded = repo.load()
        assert loaded.font_family == "Arial"
        assert loaded.font_size == 24
        assert loaded.theme == ThemeMode.DARK
        assert loaded.line_spacing == 2.0

    def test_save_overwrites_previous(self, repo: SettingsRepository) -> None:
        repo.save(ReaderSettings(font_family="Arial"))
        repo.save(ReaderSettings(font_family="Monospace"))
        loaded = repo.load()
        assert loaded.font_family == "Monospace"


class TestSettingsLoad:
    """Tests for loading settings."""

    def test_load_returns_defaults_when_empty(self, repo: SettingsRepository) -> None:
        loaded = repo.load()
        assert loaded == ReaderSettings()

    def test_load_handles_corrupt_data(self, db: Database) -> None:
        db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            ("reader_settings", "not valid json{{{"),
        )
        db.commit()
        repo = SettingsRepository(db)
        loaded = repo.load()
        assert loaded == ReaderSettings()


class TestWindowGeometry:
    """Tests for window geometry persistence."""

    def test_save_and_load_geometry(self, repo: SettingsRepository) -> None:
        geometry = b"\x01\x02\x03\x04\x05"
        repo.save_window_geometry(geometry)
        loaded = repo.load_window_geometry()
        assert loaded == geometry

    def test_load_geometry_returns_none_when_empty(self, repo: SettingsRepository) -> None:
        assert repo.load_window_geometry() is None

    def test_load_geometry_handles_corrupt_data(self, db: Database) -> None:
        db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            ("window_geometry", "not_valid_hex"),
        )
        db.commit()
        repo = SettingsRepository(db)
        assert repo.load_window_geometry() is None


class TestSplitterState:
    """Tests for splitter state persistence."""

    def test_save_and_load_splitter_state(self, repo: SettingsRepository) -> None:
        state = b"\x01\x02\x03\x04\x05"
        repo.save_splitter_state(state)
        loaded = repo.load_splitter_state()
        assert loaded == state

    def test_load_splitter_state_returns_none_when_empty(self, repo: SettingsRepository) -> None:
        assert repo.load_splitter_state() is None

    def test_load_splitter_state_handles_corrupt_data(self, db: Database) -> None:
        db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            ("splitter_state", "not_valid_hex"),
        )
        db.commit()
        repo = SettingsRepository(db)
        assert repo.load_splitter_state() is None


class TestLastBookId:
    """Tests for last book ID persistence."""

    def test_save_and_load_last_book_id(self, repo: SettingsRepository) -> None:
        repo.save_last_book_id(42)
        assert repo.load_last_book_id() == 42

    def test_load_last_book_id_returns_none_when_empty(self, repo: SettingsRepository) -> None:
        assert repo.load_last_book_id() is None

    def test_save_none_last_book_id(self, repo: SettingsRepository) -> None:
        repo.save_last_book_id(42)
        repo.save_last_book_id(None)
        assert repo.load_last_book_id() is None

    def test_load_last_book_id_handles_corrupt_data(self, db: Database) -> None:
        db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            ("last_book_id", "not_a_number"),
        )
        db.commit()
        repo = SettingsRepository(db)
        assert repo.load_last_book_id() is None
