from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
from logger import logger
from utils.console_handler import ConsoleWidget

class ExtractionViewer(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Extraction")
        self.setGeometry(500, 50, 800, 600)  # Adjusted window size

        self.init_ui()

    def init_ui(self):
        """Initialize the UI layout and widgets."""
        # Central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # ------------------- Top Section -------------------
        top_section = QWidget()
        top_section_layout = QHBoxLayout(top_section)

        # NPK File List
        self.npk_file_list_widget = QListWidget()
        self.npk_file_list_widget.setFixedWidth(350)
        # self.npk_file_list_label = QLabel('NPK List:')
        
        # top_section_layout.addWidget(self.npk_file_list_label)
        top_section_layout.addWidget(self.npk_file_list_widget)

        # ------------------- Options and Controls -------------------
        controls_layout = QVBoxLayout()

        # Checkboxes
        self.force_npk_unpack = QCheckBox('Force Unpack')
        self.show_nxfn_content = QCheckBox('Show NXFN Info')
        self.delete_compressed = QCheckBox('Delete Compressed Files')
        self.unpack_entire_folder_checkbox = QCheckBox('Unpack Folder (NPKs)')
        self.use_subfolders_checkbox = QCheckBox('Use Subfolders for Each NPK')

        # Default settings
        self.show_nxfn_content.setChecked(True)
        self.use_subfolders_checkbox.setChecked(True)

        # Add checkboxes to layout
        controls_layout.addWidget(self.force_npk_unpack)
        controls_layout.addWidget(self.show_nxfn_content)
        controls_layout.addWidget(self.delete_compressed)
        controls_layout.addWidget(self.unpack_entire_folder_checkbox)
        controls_layout.addWidget(self.use_subfolders_checkbox)

        # Unpack Button
        self.unpack_button = QPushButton("Unpack NPK")
        self.unpack_button.setFixedSize(180, 40)
        self.unpack_button.clicked.connect(self.start_unpack)
        controls_layout.addWidget(self.unpack_button)

        # Add controls layout to the top section
        top_section_layout.addLayout(controls_layout)

        # ------------------- Console Output -------------------
        # self.extraction_console_label = QLabel('Log:')
        # self.extraction_console = ConsoleWidget() 

        # ------------------- Layout Assembly -------------------
        main_layout.addWidget(top_section)
        # main_layout.addWidget(self.extraction_console_label)
        # main_layout.addWidget(self.extraction_console)

        self.create_open_menu()

        return(self)

    def create_open_menu(self):
        extraction_menu = self.menuBar().addMenu("Open")
        open_file_action = QAction("Open File", self)
        open_file_action.setShortcut("Ctrl+O")
        open_file_action.triggered.connect(self.open_file)  # Connect to a function
        extraction_menu.addAction(open_file_action)

        open_folder_action = QAction("Open Folder", self)
        open_folder_action.setShortcut("Ctrl+Shift+O")
        open_folder_action.triggered.connect(self.open_folder)  # Connect to a function
        extraction_menu.addAction(open_folder_action)


    def start_unpack(self):
        """Handles the extraction process."""
        selected_items = self.npk_file_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Extraction Error", "Please select an NPK file to extract.")
            return

        for item in selected_items:
            npk_file = item.text()
            output_folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")

            if not output_folder:
                self.extraction_console.append("Extraction cancelled.")
                return

            # Simulate unpacking (replace with actual extraction logic)
            self.extraction_console.append(f"Extracting: {npk_file} -> {output_folder}")

            # If force unpack is checked
            if self.force_npk_unpack.isChecked():
                self.extraction_console.append(f"Force Unpacking {npk_file}...")

            # If delete compressed is checked
            if self.delete_compressed.isChecked():
                self.extraction_console.append(f"Deleting compressed files after extraction...")

            # If unpack entire folder is checked
            if self.unpack_entire_folder_checkbox.isChecked():
                self.extraction_console.append("Extracting all NPK files in the selected folder...")

            # Simulate process completion
            QMessageBox.information(self, "Extraction Complete", f"Extraction completed for {npk_file}")

    def open_file(self):
        """Opens a file dialog to select a file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a File", "", "All Files (*)")
        if file_path:
            QMessageBox.information(self, "File Selected", f"Selected file:\n{file_path}")
            print(f"Selected File: {file_path}")  # Debugging output
            self.process_selected_file(file_path)
        else:
            QMessageBox.warning(self, "No File", "No file was selected.")

    def open_folder(self):
        """Opens a folder dialog to select a directory."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select a Folder")

        if not folder_path:
            return 

        self.npk_file_list_widget.clear()  # Clear the list before adding new items

        npk_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.npk'):
                    npk_files.append(os.path.join(root, file))
        
        if not npk_files:
            QMessageBox.information(self, "No NPK Files", "No .npk files found in the selected folder.")
            return

        for npk_file in npk_files:
            item = QListWidgetItem(os.path.basename(npk_file))  # Show only the file name
            item.setData(Qt.UserRole, npk_file)  # Store the full file path in UserRole
            self.npk_file_list_widget.addItem(item)

        logger.info(self, "Success", f"Loaded {len(npk_files)} .npk files.")


    def process_selected_file(self, file_path):
        """Process the selected file (Placeholder for future logic)."""
        print(f"Processing file: {file_path}")

    def process_selected_folder(self, folder_path):
        """Process the selected folder (Placeholder for future logic)."""
        print(f"Processing folder: {folder_path}")