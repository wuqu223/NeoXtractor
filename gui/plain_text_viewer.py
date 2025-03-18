from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from logger import logger

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
        
        # Layout for the text area
        layout = QHBoxLayout(self)
        layout.addWidget(self.text_area)
        
        # Set layout
        self.setLayout(layout)


def create_text_tab(parent):
    """Creates a new tab with a plaintext viewer for the selected NPK entry."""
    
    # Ensure a valid selection exists
    selected_indexes = parent.list.selectionModel().selectedIndexes()
    if not selected_indexes:
        QMessageBox.warning(parent, "Invalid Selection", "No valid NPK entry selected.")
        return None

    # Retrieve the selected index
    index = selected_indexes[0]
    selected_file_index = parent.list.model().data(index, Qt.UserRole)

    # Retrieve the file entry
    npk_entry = parent.npkentries.get(selected_file_index)
    if not npk_entry:
        QMessageBox.warning(parent, "Invalid Selection", f"Selected entry {selected_file_index} not found.")
        return None
    
    # Extract data from NPK entry
    npk_entry_data = npk_entry.data

    # Create Main Window for Plaintext Viewer
    tab = QMainWindow()
    tab.setWindowTitle("Plaintext Viewer")
    # tab.setFixedSize(1000, 800)
    tab.setMinimumSize(800, 600)

    # Initialize the PlainTextViewer widget
    plain_text_viewer = PlainTextViewer(npk_entry_data)
    tab.setCentralWidget(plain_text_viewer)

    return tab