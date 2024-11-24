from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from gui.hex_viewer import HexViewer

def create_hex_tab(self):
    # Hex Viewer Tab
    tab = QWidget()
    tab.setWindowTitle("Hex Viewer")
    tab_layout = QVBoxLayout(tab)
    # Hex View widget with a background color for layout debugging
    hex_widget = QWidget()
    debug_layout = QHBoxLayout(hex_widget)

    palette = hex_widget.palette()
    palette.setColor(QPalette.Window, QColor("white"))  # Choose debug color
    hex_widget.setAutoFillBackground(True)
    hex_widget.setPalette(palette)

    # Hex Layout
    hex_layout_widget = QWidget()
    hex_layout = QVBoxLayout(hex_layout_widget)
    hex_viewer = HexViewer(self.npkentries[self.selectednpkentry].data)  # Placeholder for Hex viewer
    hex_layout.addWidget(hex_viewer)
    debug_layout.addWidget(hex_layout_widget)

    # Add the widget to the main layout
    tab_layout.addWidget(hex_widget)
    tab.setGeometry(50,50,1080,600)

    return tab