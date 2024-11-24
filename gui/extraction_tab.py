from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from utils.console_handler import *
from bin.read_nxfn import NxfnResultViewer

def create_extraction_tab(self):
    # Extraction Tab
    tab = QWidget()
    tab_layout = QHBoxLayout(tab)

    # Extraction widget
    extraction_widget = QWidget()
    extraction_layout = QVBoxLayout(extraction_widget)

    top_section_widget = QWidget()
    top_section_layout = QHBoxLayout(top_section_widget)

    # NPK File List
    self.read_npk_file_list_widget = QListWidget()
    self.read_npk_file_list_label = QLabel('NPK List: ')
    self.read_npk_file_list_widget.setFixedWidth(400)
    self.read_npk_file_list_widget.itemSelectionChanged.connect(self.on_file_selected)
    top_section_layout.addWidget(self.read_npk_file_list_widget)

    self.nxfn_viewer = NxfnResultViewer()
    self.nxfn_viewer_label = QLabel('   NXFN Content: ')
    top_section_layout.addWidget(self.nxfn_viewer)

    # Options and Controls
    button_layout = QVBoxLayout()

    # NPK content checkbox
    self.force_npk_unpack = QCheckBox('Force Unpack')
    self.force_npk_unpack.setCheckable(True)
    self.force_npk_unpack.setChecked(False)
    self.show_nxfn_content = QCheckBox('Show NXFN Info')
    self.show_nxfn_content.setCheckable(True)
    self.show_nxfn_content.setChecked(True)
    self.delete_compressed = QCheckBox('Delete Compressed Files')
    self.delete_compressed.setCheckable(True)
    self.delete_compressed.setChecked(False)
    self.unpack_entire_folder_checkbox = QCheckBox('Unpack Folder (NPKs)')
    self.unpack_entire_folder_checkbox.setCheckable(True)
    self.unpack_entire_folder_checkbox.setChecked(False)
    self.use_subfolders_checkbox = QCheckBox('Use subfolders for each NPK')
    self.use_subfolders_checkbox.setCheckable(True)
    self.use_subfolders_checkbox.setChecked(True)

    button_layout.addWidget(self.force_npk_unpack)
    button_layout.addWidget(self.show_nxfn_content)
    button_layout.addWidget(self.delete_compressed)
    button_layout.addWidget(self.unpack_entire_folder_checkbox)
    button_layout.addWidget(self.use_subfolders_checkbox)

    # Unpack NPK Button
    self.unpack_button = QPushButton("Unpack NPK")
    self.unpack_button.setFixedSize(180, 40)
    self.unpack_button.clicked.connect(self.start_unpack)
    button_layout.addWidget(self.unpack_button)

    self.extraction_console_label = QLabel('   Log: ')

    top_section_layout.addLayout(button_layout)
    extraction_layout.addLayout(button_layout)
    extraction_layout.addWidget(self.read_npk_file_list_label)
    extraction_layout.addWidget(self.read_npk_file_list_widget)
    extraction_layout.addWidget(self.nxfn_viewer_label)
    extraction_layout.addWidget(self.nxfn_viewer)
    extraction_layout.addWidget(self.extraction_console_label)

    # ------------------------------------------------------------------------------------------------------------
    # Console output
    self.extraction_console = ConsoleWidget(self.console_handler)
    extraction_layout.addWidget(self.extraction_console)
    # ------------------------------------------------------------------------------------------------------------

    # Add Widgets to Layout
    tab_layout.addWidget(top_section_widget)
    tab_layout.addWidget(extraction_widget)

    return tab