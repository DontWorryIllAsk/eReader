import hashlib
import os
from pathlib import Path
from typing import Optional


def compute_file_hash(file_path: str | Path, algorithm: str = "sha256") -> str:
    """Compute hash of a file for deduplication."""
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def ensure_dir(path: str | Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_app_data_dir() -> Path:
    """Get the application data directory."""
    app_data = Path.home() / ".ereader"
    return ensure_dir(app_data)


def get_covers_dir() -> Path:
    """Get the directory for storing book covers."""
    return ensure_dir(get_app_data_dir() / "covers")


def format_file_size(size_bytes: float) -> str:
    """Format file size in human-readable form."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
