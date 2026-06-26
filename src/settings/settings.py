from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ThemeMode(Enum):
    """Reading theme modes."""

    LIGHT = "light"
    DARK = "dark"
    SEPIA = "sepia"
    GREEN = "green"


THEME_COLORS = {
    ThemeMode.LIGHT: {"bg": "#FFFFFF", "text": "#000000"},
    ThemeMode.DARK: {"bg": "#1E1E1E", "text": "#D4D4D4"},
    ThemeMode.SEPIA: {"bg": "#F4ECD8", "text": "#000000"},
    ThemeMode.GREEN: {"bg": "#C7EDCC", "text": "#000000"},
}

DEFAULT_FONT_FAMILY = "Serif"
DEFAULT_FONT_SIZE = 18
DEFAULT_THEME = ThemeMode.LIGHT


@dataclass
class ReaderSettings:
    """Reader display settings."""

    font_family: str = DEFAULT_FONT_FAMILY
    font_size: int = DEFAULT_FONT_SIZE
    theme: ThemeMode = DEFAULT_THEME
    line_spacing: float = 1.8

    def get_bg_color(self) -> str:
        """Get background color for current theme."""
        return THEME_COLORS[self.theme]["bg"]

    def get_text_color(self) -> str:
        """Get text color for current theme."""
        return THEME_COLORS[self.theme]["text"]

    def to_dict(self) -> dict[str, object]:
        """Serialize settings to a dictionary."""
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "theme": self.theme.value,
            "line_spacing": self.line_spacing,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ReaderSettings":
        """Deserialize settings from a dictionary."""
        return cls(
            font_family=str(data.get("font_family", DEFAULT_FONT_FAMILY)),
            font_size=int(data.get("font_size", DEFAULT_FONT_SIZE)),
            theme=ThemeMode(str(data.get("theme", DEFAULT_THEME.value))),
            line_spacing=float(data.get("line_spacing", 1.8)),
        )
