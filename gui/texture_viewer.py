from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import subprocess

class TextureViewer(QWidget):
    npkfile = None
    def __init__(self, _npkfile):
        super().__init__()
        self.npkfile = _npkfile
        self.initUI()
        self.setGeometry(500, 50, 500, 500)

    def initUI(self):
        self.setWindowTitle("Texture Preview")
        
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(800, 800)

        layout = QVBoxLayout()
        layout.addWidget(self.label)

        # Status label for feedback instead of statusBar
        self.status_label = QLabel("Ready", self)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)

    def convert_to_png(self):
        """Converts a given file to .png format, handling intermediate .dds conversion if necessary."""
        open(f"output.{self.npkfile.ext}", "wb").write(self.npkfile.data)
        if not self.npkfile.ext.endswith("png"):
            command_to_png = f"./bin/PVRTexToolCLI -i output.{self.npkfile.ext} -d output.png -o output.dds -f r8g8b8a8"
            subprocess.run(command_to_png, shell=True)

    def displayImage(self, scale_factor=0.66):
        self.convert_to_png()
        
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
        self.status_label.setText("Texture loaded correctly")

        return True