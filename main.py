import sys, signal
from PyQt5.QtWidgets import QApplication

from gui.fonts import loadFont
from gui.qt_theme import qt_theme
from gui.main_window import MainWindow

from logger import logger

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setPalette(qt_theme.palettes()["dark"]) # Set the dark palette
    app.setStyleSheet(qt_theme.style_modern()) # Apply the dark theme stylesheet

    loadFont("Roboto", "./fonts/Roboto-Regular.ttf")

    signal.signal(signal.SIGINT, lambda *a: app.quit())
    main_window = MainWindow()
    main_window.show()
    logger.info("Application started")
    sys.exit(app.exec_())
