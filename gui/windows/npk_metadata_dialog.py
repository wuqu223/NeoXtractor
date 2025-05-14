# filepath: /home/rain/NeoXtractor/gui/windows/npk_metadata_dialog.py
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QLabel, QSplitter, QWidget
from PyQt5.QtCore import Qt

from logger import logger

class NPKMetadataDialog(QDialog):
    """Dialog to display metadata about NPK entries."""
    
    def __init__(self, npk_entry, parent=None):
        """
        Initialize the NPK Metadata Dialog.
        
        Args:
            npk_entry: The NPK entry to display metadata for
            parent: The parent widget
        """
        super().__init__(parent)
        
        self.setWindowTitle("NPK Data")
        self.setFixedSize(600, 400)

        try:
            # Main layout
            main_layout = QHBoxLayout()

            # Left side labels
            labels = [
                "SIGN:", "NPK OFFSET:", "DATA LENGTH:", "ORIGINAL DATA LENGTH:",
                "COMPRESSED CRC:", "ORIGINAL CRC:", "COMPRESSION FLAG:", "FILE FLAG:"
            ]

            if npk_entry.file_structure:
                labels.append("FILE STRUCTURE:")
            labels.append("EXTENSION:")

            # Create left layout with labels
            left_layout = QVBoxLayout()
            for label in labels:
                left_layout.addWidget(QLabel(label))

            # Right side values
            right_layout = QVBoxLayout()
            right_layout.addWidget(QLabel(hex(npk_entry.file_sign)))
            right_layout.addWidget(QLabel(hex(npk_entry.file_offset)))
            right_layout.addWidget(QLabel(str(npk_entry.file_length)))
            right_layout.addWidget(QLabel(str(npk_entry.file_original_length)))
            right_layout.addWidget(QLabel(str(npk_entry.zcrc)))
            right_layout.addWidget(QLabel(str(npk_entry.crc)))
            right_layout.addWidget(QLabel(str(npk_entry.zflag)))
            right_layout.addWidget(QLabel(str(npk_entry.fileflag)))

            if npk_entry.file_structure:
                right_layout.addWidget(QLabel(npk_entry.file_structure.decode("utf-8")))
            right_layout.addWidget(QLabel(npk_entry.ext))

            # Create Splitter
            splitter = QSplitter(Qt.Horizontal)
            left_widget = QWidget()
            left_widget.setLayout(left_layout)
            right_widget = QWidget()
            right_widget.setLayout(right_layout)

            splitter.addWidget(left_widget)
            splitter.addWidget(right_widget)

            # Add to layout
            main_layout.addWidget(splitter)
            self.setLayout(main_layout)

        except Exception as e:
            print(f"Error displaying data: {e}")
            logger.critical(f"Error displaying data: {e}")