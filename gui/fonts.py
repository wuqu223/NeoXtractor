from PyQt5.QtGui import QFontDatabase

fonts: dict[str, int] = {}

def loadFont(font: str, path: str) -> int:
    fonts[font] = QFontDatabase.addApplicationFont(path)
    return fonts[font]

def isFontLoaded(font: str) -> bool:
    fnt = fonts[font]
    return fnt is not None and font != -1