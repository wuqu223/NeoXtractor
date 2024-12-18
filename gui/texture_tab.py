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

    # Button Widget
    self.button_layout = QVBoxLayout()

    channel_filter_label = QLabel("Channel Filter: ")
    channel_r = QCheckBox("R *")
    channel_g = QCheckBox("G *")
    channel_b = QCheckBox("B *")
    channel_a = QCheckBox("A *")

    flip_label = QLabel("_______________________")
    self.flip_tex = QCheckBox("Flip Vertically")
    # flip_tex.setFixedSize(150, 30)
    self.flip_tex.stateChanged.connect(lambda: texture_view.displayImage(flip_check=self.flip_tex.isChecked()))
    self.flip_tex.setToolTip("Flip texture on the V axis.")

    rotate_tex = QPushButton("Rotate 90*")
    rotate_tex.setFixedSize(150, 30)
    rotate_tex.pressed.connect(self.extract_file)
    rotate_tex.setToolTip("Rotate texture 90 degrees clock-wise.")

    self.save_textures = QPushButton("Save")
    self.save_textures.setFixedSize(150, 30)
    self.save_textures.pressed.connect(self.extract_file)
    self.save_textures.setToolTip("Save texture file from the Texture Preview.")

    self.save_all_textures = QPushButton("Save all loaded textures")
    self.save_all_textures.setFixedSize(150, 30)
    self.save_all_textures.pressed.connect(self.read_all_npk_data)
    self.save_all_textures.setToolTip("Save all texture files from the loaded NPK.")

    self.button_layout.addWidget(channel_filter_label)
    self.button_layout.addWidget(channel_r)
    self.button_layout.addWidget(channel_g)
    self.button_layout.addWidget(channel_b)
    self.button_layout.addWidget(channel_a)
    self.button_layout.addWidget(flip_label)
    self.button_layout.addWidget(self.flip_tex)
    self.button_layout.addWidget(rotate_tex)
    self.button_layout.addStretch()
    self.button_layout.addWidget(self.save_textures)
    self.button_layout.addWidget(self.save_all_textures)

    texture_layout.addLayout(self.button_layout)

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
    texture_view.displayImage(False)

    return tab

