import subprocess
import os, struct, io, math
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np
from logger import logger
from utils.image_converters import *

class TextureViewer(QMainWindow):
    def __init__(self, npk_entry, filename: str | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{"" if filename is None else f"{filename} - "}Texture Viewer")
        self.setGeometry(500, 50, 600, 600)  # Set window size

        self.npk = npk_entry

        # Create a central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout()

        # QLabel for displaying the texture
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Flip texture checkbox
        self.flip_tex = QCheckBox("Flip Vertically")
        self.flip_tex.stateChanged.connect(lambda: self.updateDisplay())

        # Channel checkboxes
        self.channel_R = QCheckBox("R")
        self.channel_G = QCheckBox("G")
        self.channel_B = QCheckBox("B")
        self.channel_A = QCheckBox("A")

        channels_layout = QHBoxLayout()

        for channel in [self.channel_R, self.channel_G, self.channel_B, self.channel_A]:
            channel.setChecked(True)
            channel.stateChanged.connect(lambda: self.updateDisplay())
            channels_layout.addWidget(channel)
        
        channels_layout.addStretch()

        # Save buttons
        save_raw_texture = QPushButton("Save original")
        save_raw_texture.setFixedSize(150, 30)
        save_raw_texture.clicked.connect(lambda: self.save_texture(self.textureRawData, self.textureName))

        save_png_texture = QPushButton("Save as PNG")
        save_png_texture.setFixedSize(150, 30)
        save_png_texture.clicked.connect(lambda: self.save_texture(self.texturePngData, os.path.splitext(self.textureName)[0] + ".png"))

        # Status label for feedback
        self.size_label = QLabel(f"Size: None", self)
        self.status_label = QLabel("Ready", self)

        # Layout setup
        save_btns_layout = QHBoxLayout()
        save_btns_layout.addWidget(save_raw_texture)
        save_btns_layout.addWidget(save_png_texture)

        layout.addWidget(self.label)
        layout.addWidget(self.flip_tex)
        layout.addLayout(channels_layout)
        layout.addLayout(save_btns_layout)
        layout.addWidget(self.size_label)
        layout.addWidget(self.status_label)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)  # Set central widget to QMainWindow

    def showEvent(self, a0):
        self.displayImage(self.npk)
        return super().showEvent(a0)
    
    def resizeEvent(self, a0):
        if hasattr(self, 'textureImage'):
            self.updateDisplay()
        return super().resizeEvent(a0)
    
    def updateDisplay(self):
        """Update the texture display."""

        image = self.textureImage.convertToFormat(QImage.Format_ARGB32).copy()

        a_modifier = int(self.channel_A.isChecked())
        r_modifier = int(self.channel_R.isChecked())
        g_modifier = int(self.channel_G.isChecked())
        b_modifier = int(self.channel_B.isChecked())

        ptr = image.bits()
        ptr.setsize(image.sizeInBytes())
        # For ARGB32, each pixel is 4 bytes (B, G, R, A)
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape(image.height(), image.width(), 4)

        # Perform vectorized operations on the NumPy array
        # Indices for BGRA: Blue=0, Green=1, Red=2, Alpha=3
        if a_modifier == 0:
            arr[:, :, 3] = 255  # Set Alpha channel to 255
        if r_modifier == 0:
            arr[:, :, 2] = 0  # Set Red channel to 0
        if g_modifier == 0:
            arr[:, :, 1] = 0  # Set Green channel to 0
        if b_modifier == 0:
            arr[:, :, 0] = 0  # Set Blue channel to 0

        if self.flip_tex.isChecked():
            arr[:] = np.flipud(arr)

        self.setImageOnLabel(image)
        
        self.status_label.setText(f"Loaded: {self.textureName}")
    
    #def compblks2png:
    
    def setImageOnLabel(self, image):
        self.label.setPixmap(QPixmap.fromImage(image).scaled(
            self.label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
            
        self.status_label.setText(f"Loaded: {self.textureName}")

    def displayImage(self, npk_entry):
        """Display the converted image inside the QLabel."""
        if not npk_entry or not npk_entry.data or not hasattr(npk_entry, "ext"):
            print("Error: No texture data to display.")
            logger.warning("No texture data to display.")
            return False
        
        if npk_entry.ext in ["bmp", "gif", "jpg", "jpeg", "png", "pbm", "pgm", "ppm", "xbm", "xpm"]:
            self.textureImage = QImage.fromData(npk_entry.data)

        elif not self.convert_to_png(npk_entry):
            return False
        
        if self.textureImage.isNull():
            print("Error: Failed to load image.")
            logger.warning("Failed to load texture image.")
            self.label.setText("Error: Unable to load texture.")
            return False
            
        self.size_label.setText(f"Size: {self.textureImage.width()} x {self.textureImage.height()}")
        self.textureName = hex(npk_entry.file_sign) + "." + npk_entry.ext
        self.textureRawData = npk_entry.data
        self.updateDisplay()
        return True


    def convert_to_png(self, npk_entry):
        """Converts using Tacent View CLI."""
        if not hasattr(npk_entry, "ext"):
            print("Error: Missing texture file extension.")
            self.status_label.setText("Error: Missing texture file extension.")
            return False
        
        try:
            img = convert_image(npk_entry.data, npk_entry.ext)
            
            if not img:
                raise ValueError("This extension is not yet detected")
            self.textureImage = QImage.fromData(img)
            self.texturePngData = img
            self.status_label.setText("Texture converted successfully")
        except Exception as e:
            print(f"Error converting texture: {e}")
            self.status_label.setText("Failed to convert texture")
            return False
        return True

    def save_texture(self, data, name):
        """Saves the currently displayed texture to a user-selected location."""
        options = QFileDialog.Options()
        # file_name, _ = QFileDialog.getSaveFileName(self, "Save Texture", "", "Image Files (*.png *.dds *.jpg *.bmp);;All Files (*)", options=options)

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not output_dir:
            self.status_label.showMessage("Saving canceled.")
            return
        
        output_file_path = os.path.join(output_dir, name)

        if not output_file_path:
            return  # User canceled

        try:
            with open(output_file_path, "wb") as f:
                f.write(data)  # Save the texture data
            self.status_label.setText(f"Saved: {output_file_path}")
            print(f"Texture saved successfully to: {output_file_path}")
        except Exception as e:
            self.status_label.setText("Failed to save texture!")
            print(f"Error saving texture: {e}")
