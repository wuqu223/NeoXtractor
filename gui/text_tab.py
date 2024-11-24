from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from gui.plain_text_viewer import PlainTextViewer

def create_text_tab(self):
    # Text Tab
    tab = QMainWindow()
    tab.setWindowTitle("Plaintext Viewer")
    tab.setMinimumWidth(800)
    tab.setMinimumHeight(600)

    # Initialize the text viewer
    self.plain_text_viewer = PlainTextViewer(self.npkentries[self.selectednpkentry].data)
    self.plain_text_viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    # Set the layout for the tab
    tab.setCentralWidget(self.plain_text_viewer)

    return tab
