from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from gui.plain_text_viewer import PlainTextViewer

from logger import logger

def create_text_tab(self):
    if self.selectednpkentry not in self.npkentries:
        logger.warning("Invalid selected NPK entry.")
        QMessageBox.warning(None, "Invalid Selection", "No valid NPK entry selected.")
        return None
    
    npk_entry_data = self.npkentries[self.selectednpkentry].data

    # Text Tab
    tab = QMainWindow()
    tab.setWindowTitle("Plaintext Viewer")
    tab.setMinimumWidth(800)
    tab.setMinimumHeight(600)

    self.plain_text_viewer = PlainTextViewer(npk_entry_data)
    self.plain_text_viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    tab.setCentralWidget(self.plain_text_viewer)

    # # Initialize the text viewer
    # self.plain_text_viewer = PlainTextViewer(self.npkentries[self.selectednpkentry].data)
    # self.plain_text_viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    # # Set the layout for the tab
    # tab.setCentralWidget(self.plain_text_viewer)

    return tab
