from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import subprocess
import os

class TextureViewer(QWidget):
    npkfile = None
    def __init__(self, _npkfile):
        super().__init__()
        self.npkfile = _npkfile
        self.initUI()
        # self.setGeometry(500, 50, 500, 500)

    def initUI(self):
        self.setWindowTitle("Texture Preview")
        
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        # self.label.setFixedSize(800, 800)

        layout = QVBoxLayout()
        layout.addWidget(self.label)

        # Status label for feedback instead of statusBar
        self.status_label = QLabel("Ready", self)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def convert_to_png(self, flip=False):
        """Converts a given file to .png format using Tacent View CLI."""
        input_file = f"output.{self.npkfile.ext}"
        output_file = "output"

        with open(input_file, "wb") as file:
            file.write(self.npkfile.data)

        if flip == True:
            flip_image = "--op flip[v]"
        elif flip == False:
            flip_image = ""

        # Path to Tacent View executable
        tacentview = r".\bin\tacentview.exe"

        # Define the conversion command for Tacent View CLI
        command_to_png = f'"{tacentview}" -cw {flip_image} --input "{input_file}" --output "{output_file}" -o png'

        # Run the command using subprocess
        process = subprocess.run(command_to_png, shell=True, capture_output=True, text=True)

        # Check if the process was successful
        if process.returncode != 0:
            error_message = process.stderr.strip()
            print(f"Error converting texture: {error_message}")
            QMessageBox.warning(self, "Error", f"Failed to convert texture: {error_message}")
            self.status_label.setText("Failed to convert texture")
            return False

        self.status_label.setText("Texture converted successfully")
        return True

    def displayImage(self, flip_check=False, scale_factor=0.66):
        flip = flip_check
        self.convert_to_png(flip)
        
        pixmap = QPixmap("output.png")
        
        if pixmap.isNull():
            QMessageBox.warning(self, "Error", "Failed to load image.")
            self.status_label.setText("Failed to load image")
            return False

        # Calculate the scaled width and height while maintaining the aspect ratio
        target_width = int(pixmap.width() * scale_factor)
        target_height = int(pixmap.height() * scale_factor)

        # Scale the pixmap with aspect ratio preserved
        scaled_pixmap = pixmap.scaled(
            target_width, target_height,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        # Set the scaled pixmap on the label
        self.label.setPixmap(scaled_pixmap)

        # Adjust the label size to fit the scaled pixmap
        self.label.setFixedSize(scaled_pixmap.size())

        self.status_label.setText(f"Texture Size: {pixmap.width()}x{pixmap.height()}")

        return True