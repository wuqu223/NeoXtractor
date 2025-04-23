import subprocess
import os, struct, io, math
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from logger import logger
from utils.image_converters import *

class TextureViewer(QMainWindow):
    def __init__(self, npk_entry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Texture Preview")
        self.setGeometry(500, 50, 600, 600)  # Set window size

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

        for channel in [self.channel_R, self.channel_G, self.channel_B, self.channel_A]:
            channel.stateChanged.connect(lambda: self.updateDisplay())

        # Save button
        self.save_textures = QPushButton("Save")
        self.save_textures.setFixedSize(150, 30)
        self.save_textures.clicked.connect(self.save_texture)

        # Status label for feedback
        self.size_label = QLabel(f"Size: None", self)
        self.status_label = QLabel("Ready", self)

        # Layout setup
        channel_layout = QHBoxLayout()
        channel_layout.addWidget(self.channel_R)
        channel_layout.addWidget(self.channel_G)
        channel_layout.addWidget(self.channel_B)
        channel_layout.addWidget(self.channel_A)
        channel_layout.addStretch()

        layout.addWidget(self.label)
        layout.addWidget(self.flip_tex)
        layout.addLayout(channel_layout)
        layout.addWidget(self.save_textures)
        layout.addWidget(self.size_label)
        layout.addWidget(self.status_label)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)  # Set central widget to QMainWindow
        self.setWindowFlags(Qt.Window)  # Make it a separate window
         
    def updateDisplay(self):
        """Update the texture display when selecting a new file."""

        image = self.textureImage
        for i in range(0, image.width()):
            for j in range(0, image.height()):
                rgb = image.pixel(i, j)
                image.setPixelColor(i, j, QColor(qRgb(qRed(rgb) * int(not self.channel_R.isChecked()),
                                                 qGreen(rgb) * int(not self.channel_G.isChecked()),
                                                 qBlue(rgb) * int(not self.channel_B.isChecked()))))

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
        self.textureSaveData = npk_entry.data            
        self.setImageOnLabel(self.textureImage)
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
            self.status_label.setText("Texture converted successfully")
        except Exception as e:
            print(f"Error converting texture: {e}")
            self.status_label.setText("Failed to convert texture")
            return False
        return True

    def save_texture(self):
        """Saves the currently displayed texture to a user-selected location."""
        options = QFileDialog.Options()
        # file_name, _ = QFileDialog.getSaveFileName(self, "Save Texture", "", "Image Files (*.png *.dds *.jpg *.bmp);;All Files (*)", options=options)

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not output_dir:
            self.status_bar.showMessage("Saving canceled.")
            return
        
        output_file_path = os.path.join(output_dir, self.textureName)

        if not output_file_path:
            return  # User canceled

        try:
            with open(output_file_path, "wb") as f:
                f.write(self.textureSaveData)  # Save the texture data
            self.status_label.setText(f"Saved: {output_file_path}")
            print(f"Texture saved successfully to: {output_file_path}")
        except Exception as e:
            self.status_label.setText("Failed to save texture!")
            print(f"Error saving texture: {e}")
