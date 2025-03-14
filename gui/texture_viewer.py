from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import subprocess
import os
from logger import logger


class TextureViewer(QWidget):
    def __init__(self, npk_entry, parent=None):
        super().__init__(parent)
        self.npkfile = npk_entry
        self.initUI()
        self.setGeometry(500, 50, 500, 500)

    def initUI(self):
        self.setWindowTitle("Texture Preview")

        # QLabel for displaying the texture
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(800, 800)

        # Flip texture checkbox
        self.flip_tex = QCheckBox("Flip Vertically")
        self.flip_tex.stateChanged.connect(lambda: self.updateDisplay(self.npkfile))

        # Channel checkboxes
        self.channel_R = QCheckBox("R")
        self.channel_G = QCheckBox("G")
        self.channel_B = QCheckBox("B")
        self.channel_A = QCheckBox("A")
        for channel in [self.channel_R, self.channel_G, self.channel_B, self.channel_A]:
            channel.stateChanged.connect(lambda: self.updateDisplay(self.npkfile))

        # Save button
        self.save_textures = QPushButton("Save")
        self.save_textures.setFixedSize(150, 30)
        self.save_textures.clicked.connect(self.extract_file)

        # Status label for feedback
        self.status_label = QLabel("Ready", self)

        # Layout setup
        layout = QVBoxLayout()
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

    def convert_to_png(self):
        """Converts a given file to .png format, handling intermediate .dds conversion if necessary."""
        open(f"output.{self.npkfile.ext}", "wb").write(self.npkfile.data)
        if not self.npkfile.ext.endswith("png"):
            command_to_png = f"./bin/PVRTexToolCLI -i output.{self.npkfile.ext} -d output.png -o output.dds -f r8g8b8a8"
            subprocess.run(command_to_png, shell=True)
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
        
    def updateDisplay(self, npk_entry):
        """Update the texture display based on current options."""
        self.npkfile = npk_entry
        self.displayImage(
            flip_check=self.flip_tex.isChecked(),
            channel_r=self.channel_R.isChecked(),
            channel_g=self.channel_G.isChecked(),
            channel_b=self.channel_B.isChecked(),
            channel_a=self.channel_A.isChecked(),
        )

    def convert_to_png(self, flip_check=False, channel_r=False, channel_g=False, channel_b=False, channel_a=False):
        """Converts using Tacent View CLI."""
        input_file = f"temp_texture.{self.npkfile.ext}"
        output_file = "temp_texture.png"

        try:
            # Write the texture data to a temporary file
            with open(input_file, "wb") as file:
                file.write(self.npkfile.data)

            # Generate Tacent View CLI options
            flip_image = "--op flip[v]" if flip_check else ""
            channel_ops = []
            if channel_r:
                channel_ops.append("--op channel[spread,R]")
            if channel_g:
                channel_ops.append("--op channel[spread,G]")
            if channel_b:
                channel_ops.append("--op channel[spread,B]")
            if channel_a:
                channel_ops.append("--op channel[spread,A]")
            if channel_r and channel_g and channel_b:
                channel_ops.append("")
            if channel_r and channel_g:
                channel_ops.append("--op channel[blend,RG]")
            if channel_r and channel_b:
                channel_ops.append("--op channel[blend,RB]")
            if channel_g and channel_b:
                channel_ops.append("--op channel[blend,GB]")

            tacentview = r".\bin\tacentview.exe"
            command = f'"{tacentview}" -cw {flip_image} {" ".join(channel_ops)} --input "{input_file}" --output "{output_file}" -o png'

            # Run the command
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            if process.returncode != 0:
                error_message = process.stderr.strip()
                print(f"Error converting texture: {error_message}")
                logger.debug(f"Error converting texture: {error_message}")
                self.status_label.setText("Failed to convert texture")
                return False

            self.status_label.setText("Texture converted successfully")
            return True
        finally:
            # Clean up the temporary input file
            if os.path.exists(input_file):
                os.remove(input_file)

    def displayImage(self, flip_check=False, channel_r=False, channel_g=False, channel_b=False, channel_a=False, scale_factor=0.5):
        """Display the converted image."""
        if not self.npkfile or not self.npkfile.data:
            print("Error", "No texture data to display.")
            logger.warning("Error", "No texture data to display.")
            return False

        if not self.convert_to_png(flip_check, channel_r, channel_g, channel_b, channel_a):
            return False

        pixmap = QPixmap("temp_texture.png")

