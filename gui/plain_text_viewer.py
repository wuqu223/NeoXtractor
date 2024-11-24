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
        font.setFamily("../fonts/Roboto-Regular.ttf")  # Ensure font exists in your system or set the path correctly
        font.setPointSize(12)
        self.text_area.setFont(font)
        self.text_area.setText(npkdata.decode("utf-8"))
        
        # Layout for the text area
        layout = QHBoxLayout(self)
        layout.addWidget(self.text_area)
        
        # Set layout
        self.setLayout(layout)