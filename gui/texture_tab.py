from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from gui.texture_viewer import TextureViewer

def create_texture_tab(self):
    # Texture Viewer Tab
    tab = QWidget()
    tab.setWindowTitle("Texture Viewer")
    tab_layout = QHBoxLayout(tab)

    # Texture widget
    texture_widget = QWidget()
    texture_layout = QHBoxLayout(texture_widget)

    # Set a background color for the texture widget
    palette = texture_widget.palette()
    palette.setColor(QPalette.Window, QColor("lightblue"))  # Debug color
    texture_widget.setAutoFillBackground(True)
    texture_widget.setPalette(palette)

    # Main layout sections for texture viewer
    texture_viewer_layout = QVBoxLayout()
    texture_viewer_layout.setAlignment(Qt.AlignCenter)

    # Texture Viewer
    texture_view = TextureViewer(self.npkentries[self.selectednpkentry])  # Placeholder for TextureViewer
    texture_viewer_layout.addWidget(texture_view)

    # Create a QWidget to hold the texture viewer layout and add it to texture_layout
    texture_viewer_widget = QWidget()
    texture_viewer_widget.setLayout(texture_viewer_layout)
    texture_layout.addWidget(texture_viewer_widget)

    # Add texture layout to the tab    
    tab_layout.addWidget(texture_widget)  # Embed texture_widget within tab layout
    texture_view.displayImage()

    return tab