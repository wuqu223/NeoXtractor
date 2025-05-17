"""Font management module."""

from PySide6.QtGui import QFontDatabase

fonts: dict[str, int] = {}

def load_font(font: str, path: str) -> int:
    """Load a font from the given path and return its ID."""
    fonts[font] = QFontDatabase.addApplicationFont(path)
    return fonts[font]

def is_font_loaded(font: str) -> bool:
    """Check if a font is loaded."""
    fnt = fonts[font]
    return fnt is not None and font != -1
