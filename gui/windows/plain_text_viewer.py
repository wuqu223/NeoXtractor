from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from gui.fonts import isFontLoaded

from logger import logger

class PlainTextViewer(QMainWindow):
    def __init__(self, npkdata, filename: str | None, parent: QWidget | None):
        super().__init__(parent)

        self.setWindowTitle(f"{"" if filename == None else f"{filename} - "}Plaintext Viewer")
        self.setMinimumSize(800, 600)
        
        # Initialize text area
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        
        # Set font for the text area
        font = QFont()
        font.setPointSize(12)
        self.text_area.setFont(font)

        if isFontLoaded("Roboto"):
            font.setFamily("Roboto")
        else:
            font.setFamily("Arial")  # Fallback font

        self.text_area.setFont(font)

        # Decode text data safely
        if npkdata:
            try:
                decoded_text = npkdata.decode("utf-8", errors="replace")
            except Exception as e:
                decoded_text = f"Error: Unable to decode the data as UTF-8.\n{str(e)}"
        else:
            decoded_text = "No data available."

        self.text_area.setText(decoded_text)

        self.setCentralWidget(self.text_area)
