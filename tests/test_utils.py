from src.utils import compute_file_hash, format_file_size, ensure_dir, get_app_data_dir


class TestComputeFileHash:
    """Tests for file hashing."""

    def test_hash_consistency(self, tmp_path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        h1 = compute_file_hash(test_file)
        h2 = compute_file_hash(test_file)
        assert h1 == h2

    def test_hash_different_content(self, tmp_path) -> None:
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("content a")
        f2.write_text("content b")
        assert compute_file_hash(f1) != compute_file_hash(f2)


class TestFormatFileSize:
    """Tests for file size formatting."""

    def test_bytes(self) -> None:
        assert "B" in format_file_size(500)

    def test_kilobytes(self) -> None:
        assert "KB" in format_file_size(2048)

    def test_megabytes(self) -> None:
        assert "MB" in format_file_size(5 * 1024 * 1024)


class TestEnsureDir:
    """Tests for directory creation."""

    def test_creates_new_dir(self, tmp_path) -> None:
        new_dir = tmp_path / "subdir" / "nested"
        result = ensure_dir(new_dir)
        assert result.exists()
        assert result.is_dir()

    def test_existing_dir(self, tmp_path) -> None:
        result = ensure_dir(tmp_path)
        assert result == tmp_path
