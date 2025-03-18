import subprocess
import os, struct, io, math
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from logger import logger

class TextureViewer(QMainWindow):
    def __init__(self, npk_entry, parent=None):
        super().__init__(parent)
        self.npkfile = npk_entry
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
        self.save_textures.clicked.connect(self.save_texture)

        # Status label for feedback
        self.size_label = QLabel(f"Size: {self.get_texture_size()}", self)
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
         
    def updateDisplay(self, npk_entry):
        """Update the texture display when selecting a new file."""
        self.npkfile = npk_entry  # Store the new file data
        self.size_label.setText(f"Size: {self.get_texture_size()}")
        self.status_label.setText(f"Loading: {npk_entry.updated_name}")

        if not self.npkfile or not self.npkfile.data:
            self.label.setText("Error: No texture data available.")
            logger.warning("No texture data available for display.")
            return

        # Convert and display the new texture
        success = self.displayImage(
            flip_check=self.flip_tex.isChecked(),
            channel_r=self.channel_R.isChecked(),
            channel_g=self.channel_G.isChecked(),
            channel_b=self.channel_B.isChecked(),
            channel_a=self.channel_A.isChecked(),
        )

        if success:
            self.size_label.setText(f"Size: {self.get_texture_size()}")
            self.status_label.setText(f"Loaded: {npk_entry.updated_name}")
        else:
            self.status_label.setText("Error: Failed to load texture.")

    def convert_to_png(self, flip_check=False, channel_r=False, channel_g=False, channel_b=False, channel_a=False):
        """Converts using Tacent View CLI."""
        if not hasattr(self.npkfile, "ext"):
            print("Error: Missing texture file extension.")
            self.status_label.setText("Error: Missing texture file extension.")
            return False
        
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
            
            # Determine blending modes
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
        """Display the converted image inside the QLabel."""
        if not self.npkfile or not self.npkfile.data:
            print("Error: No texture data to display.")
            logger.warning("No texture data to display.")
            return False

        if not self.convert_to_png(flip_check, channel_r, channel_g, channel_b, channel_a):
            return False

        pixmap = QPixmap("temp_texture.png")
        if pixmap.isNull():
            print("Error: Failed to load image.")
            logger.warning("Failed to load texture image.")
            self.label.setText("Error: Unable to load texture.")
            return False

        self.label.setPixmap(pixmap.scaled(
            self.label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

        return True

    def get_texture_size(self):
        """Extracts and returns the texture size from its binary data."""
        try:
            import struct
            with io.BytesIO(self.npkfile.data) as f:
                f.seek(12)  # Assuming size is stored at offset 12
                width = struct.unpack('<I', f.read(4))[0]  # 4 bytes for width
                height = struct.unpack('<I', f.read(4))[0]  # 4 bytes for height
            return f"{width} x {height}"
        except Exception:
            return "Unknown Size"

    def save_texture(self):
        """Saves the currently displayed texture to a user-selected location."""
        options = QFileDialog.Options()
        # file_name, _ = QFileDialog.getSaveFileName(self, "Save Texture", "", "Image Files (*.png *.dds *.jpg *.bmp);;All Files (*)", options=options)

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not output_dir:
            self.status_bar.showMessage("Saving canceled.")
            return
        
        output_file_path = os.path.join(output_dir, self.npkfile.updated_name)

        if not output_file_path:
            return  # User canceled

        try:
            with open(output_file_path, "wb") as f:
                f.write(self.npkfile.data)  # Save the texture data
            self.status_label.setText(f"Saved: {output_file_path}")
            print(f"Texture saved successfully to: {output_file_path}")
        except Exception as e:
            self.status_label.setText("Failed to save texture!")
            print(f"Error saving texture: {e}")
