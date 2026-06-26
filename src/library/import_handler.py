import shutil
from pathlib import Path
from typing import Optional

from src.models.book import Book, BookRepository
from src.readers.epub_reader import EpubReader
from src.utils import compute_file_hash, get_covers_dir


class ImportHandler:
    """Handles importing EPUB files into the library."""

    def __init__(self, book_repo: BookRepository) -> None:
        self._book_repo = book_repo

    def import_epub(self, file_path: str | Path) -> Optional[int]:
        """Import an EPUB file into the library. Returns book ID or None on failure."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if file_path.suffix.lower() != ".epub":
            raise ValueError(f"Not an EPUB file: {file_path}")

        file_hash = compute_file_hash(file_path)
        existing = self._book_repo.get_by_file_path(str(file_path))
        if existing is not None:
            return existing.id

        reader = EpubReader(file_path)

        cover_path = self._save_cover(reader, file_hash)

        book = Book(
            title=reader.title,
            author=reader.author,
            file_path=str(file_path),
            cover_path=str(cover_path) if cover_path else "",
            file_hash=file_hash,
        )
        return self._book_repo.add(book)

    def _save_cover(self, reader: EpubReader, file_hash: str) -> Optional[Path]:
        """Extract and save cover image. Returns cover path or None."""
        cover_data = reader.get_cover_image()
        if cover_data is None:
            return None

        covers_dir = get_covers_dir()
        cover_path = covers_dir / f"{file_hash}.jpg"

        if not cover_path.exists():
            cover_path.write_bytes(cover_data)

        return cover_path

    def import_files(self, file_paths: list[str | Path]) -> list[int]:
        """Import multiple EPUB files. Returns list of book IDs."""
        book_ids: list[int] = []
        for fp in file_paths:
            try:
                book_id = self.import_epub(fp)
                if book_id is not None:
                    book_ids.append(book_id)
            except (FileNotFoundError, ValueError):
                continue
        return book_ids
