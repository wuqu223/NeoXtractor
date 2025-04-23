import argparse
import os
import shutil
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from utils.config_manager import ConfigManager
from extractor import unpack

class NxfnResultViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.config_manager = ConfigManager()
        self.output_folder = self.config_manager.get("output_folder", "")
        self.last_decryption_key = self.config_manager.get("last_decryption_key", 0)
        
        # Initialize nxfn text area
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        
        # Set font for the nxfn text area
        font = QFont()
        font.setFamily("../fonts/DroidSansMono.ttf")
        self.text_area.setFont(font)
        
        # Layout for the nxfn text area
        layout = QVBoxLayout(self)
        layout.addWidget(self.text_area)
        self.text_area.setFixedWidth(1200)

        # Set layout
        self.setLayout(layout)

    def open_file_dialog(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open File", "", "All Files (*)")
        if file_path:
            if file_path.endswith('.npk'):
                result = self.extract_nxfn_result(file_path)
                self.loadTextFile(result)
            else:
                self.loadTextFile(file_path)

    def extract_nxfn_result(self, file_path: str, output_folder: str = None) -> str:
        """
        Extracts only the NXFN section of an NPK file without unpacking the entire file.
        Checks and removes any existing NXFN_result.txt before starting.
        """
        try:
            # Ensure output_folder is correctly set
            if output_folder is None:
                output_folder = self.output_folder or "../bin/nxfn_content"

            # Create the folder if it doesn't exist
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            key = self.last_decryption_key

            # Prepare arguments for unpacking
            args = argparse.Namespace(
                path=file_path,
                output=output_folder,
                nxfn_file=True,
                delete_compressed=False,
                info=None,
                key=key,
                credits=False,
                force=False,
                selectfile=None,
                no_nxfn=False,
                convert_images=False,
                include_empty=True,
                do_one=False,
                use_subfolders=True,
            )

            # Get path from output and filepath
            nxfn_path = os.path.join(output_folder, os.path.splitext(file_path)[0], "NXFN_result.txt")

            # Remove existing NXFN result if it exists
            if os.path.exists(nxfn_path):
                os.remove(nxfn_path)

            print(f"Starting extraction for {file_path}...")
            print(f"NXFN_result text path: {nxfn_path}")

            # Unpack the NPK file
            unpack(args)

            # Check if the NXFN result file was created
            if not os.path.exists(nxfn_path):
                QMessageBox.warning(self, "Warning", "No NXFN data found in the extracted files.")
                return None

            # Load NXFN content
            with open(nxfn_path, 'r', encoding="utf-8") as nxfn_file:
                nxfn_content = nxfn_file.read()

            # Display NXFN content in the text area
            self.text_area.setText(nxfn_content)

            return nxfn_path

        except Exception as e:
            QMessageBox.critical(self, "Extraction Error", f"Failed to extract NXFN: {str(e)}")
            return None

    def loadTextFile(self, file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                content = file.read()
                self.text_area.setText(content)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file: {e}")
            return False
