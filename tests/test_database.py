import os
import tempfile
from pathlib import Path

import pytest

from src.models.database import Database


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Provide a temporary database path."""
    return tmp_path / "test_ereader.db"


@pytest.fixture
def db(db_path: Path) -> Database:
    """Provide a connected database instance."""
    database = Database(db_path)
    database.connect()
    yield database
    database.close()


class TestDatabaseInit:
    """Tests for database initialization."""

    def test_connect_creates_database_file(self, db_path: Path) -> None:
        db = Database(db_path)
        db.connect()
        assert db_path.exists()
        db.close()

    def test_connect_creates_tables(self, db: Database) -> None:
        tables = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = {row["name"] for row in tables}
        assert "books" in table_names
        assert "annotations" in table_names
        assert "bookmarks" in table_names
        assert "settings" in table_names

    def test_context_manager(self, db_path: Path) -> None:
        with Database(db_path) as db:
            result = db.execute("SELECT 1").fetchone()
            assert result is not None

    def test_connection_raises_when_not_connected(self, db_path: Path) -> None:
        db = Database(db_path)
        with pytest.raises(RuntimeError, match="Database not connected"):
            _ = db.connection


class TestDatabaseOperations:
    """Tests for basic database operations."""

    def test_execute_and_commit(self, db: Database) -> None:
        db.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("test_key", "test_value"))
        db.commit()
        row = db.execute("SELECT value FROM settings WHERE key = ?", ("test_key",)).fetchone()
        assert row["value"] == "test_value"

    def test_foreign_keys_enabled(self, db: Database) -> None:
        result = db.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1
