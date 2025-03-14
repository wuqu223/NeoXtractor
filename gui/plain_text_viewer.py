from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class PlainTextViewer(QWidget):
    def __init__(self, npkdata):
        super().__init__()
        
        # Initialize text area
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        
        # Set font for the text area
        font = QFont()
        font.setPointSize(12)
        self.text_area.setFont(font)

        font_path = "../fonts/Roboto-Regular.ttf"
        if QFile.exists(font_path):
            QFontDatabase.addApplicationFont(font_path)
            font.setFamily("Roboto")
        else:
            font.setFamily("Arial")  # Fallback font

        try:
            decoded_text = npkdata.decode("utf-8")
        except UnicodeDecodeError:
            decoded_text = "Error: Unable to decode the data as UTF-8."

        self.text_area.setText(decoded_text)
        
        # Layout for the text area
        layout = QHBoxLayout(self)
        layout.addWidget(self.text_area)
        
        # Set layout
        self.setLayout(layout)