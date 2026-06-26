from src.settings.settings import ReaderSettings, ThemeMode


class TestReaderSettings:
    """Tests for ReaderSettings."""

    def test_default_settings(self) -> None:
        settings = ReaderSettings()
        assert settings.font_family == "Serif"
        assert settings.font_size == 18
        assert settings.theme == ThemeMode.LIGHT
        assert settings.line_spacing == 1.8

    def test_get_bg_color_light(self) -> None:
        settings = ReaderSettings(theme=ThemeMode.LIGHT)
        assert settings.get_bg_color() == "#FFFFFF"

    def test_get_bg_color_dark(self) -> None:
        settings = ReaderSettings(theme=ThemeMode.DARK)
        assert settings.get_bg_color() == "#1E1E1E"

    def test_get_bg_color_sepia(self) -> None:
        settings = ReaderSettings(theme=ThemeMode.SEPIA)
        assert settings.get_bg_color() == "#F4ECD8"

    def test_get_bg_color_green(self) -> None:
        settings = ReaderSettings(theme=ThemeMode.GREEN)
        assert settings.get_bg_color() == "#C7EDCC"

    def test_get_text_color_dark(self) -> None:
        settings = ReaderSettings(theme=ThemeMode.DARK)
        assert settings.get_text_color() == "#D4D4D4"

    def test_to_dict(self) -> None:
        settings = ReaderSettings()
        d = settings.to_dict()
        assert d["font_family"] == "Serif"
        assert d["font_size"] == 18
        assert d["theme"] == "light"

    def test_from_dict(self) -> None:
        data = {"font_family": "Arial", "font_size": 24, "theme": "dark", "line_spacing": 2.0}
        settings = ReaderSettings.from_dict(data)
        assert settings.font_family == "Arial"
        assert settings.font_size == 24
        assert settings.theme == ThemeMode.DARK
        assert settings.line_spacing == 2.0

    def test_roundtrip(self) -> None:
        original = ReaderSettings(font_family="Monospace", font_size=22, theme=ThemeMode.SEPIA)
        restored = ReaderSettings.from_dict(original.to_dict())
        assert restored.font_family == original.font_family
        assert restored.font_size == original.font_size
        assert restored.theme == original.theme
