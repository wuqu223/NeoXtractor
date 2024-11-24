from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from gui.viewer_3d import ViewerWidget
from utils.config_manager import ConfigManager
from utils.console_handler import *

def create_main_viewer_tab(self):
        self.config_manager = ConfigManager()
        self.output_folder = self.config_manager.get("output_folder", "")
        # -----------------------------------
        # Main Tab/ Mesh Viewer
        tab1 = QWidget()
        tab1_layout = QHBoxLayout(tab1)

        # File list setup
        self.file_list_widget = QListWidget()
        self.file_list_widget.itemPressed.connect(self.on_item_clicked)
        self.file_list_widget.installEventFilter(self)
        # --------------------------------------------------------------------------------------------

        # Right side setup (Viewer)
        right_column_widget = QWidget()
        right_column = QVBoxLayout(right_column_widget)

            # Output folder selection status bar
        self.output_folder_label = QLabel(f"Welcome!")
        self.output_folder_label.setFixedHeight(10)
        
        right_column.addWidget(self.output_folder_label)

        self.main_view_console_label = QLabel("    Log: ")
        self.main_view_console_label.setFixedHeight(20)
        self.main_view_console_label.alignment=Qt.AlignCenter
        right_column.addWidget(self.main_view_console_label)

        # ------------------------------------------------------------------------------------------------------------
        # Console output in the Mesh Viewer tab
        self.main_console = ConsoleWidget(self.console_handler)
        #self.main_console.setFixedHeight(1250)
        right_column.addWidget(self.main_console)
        # ------------------------------------------------------------------------------------------------------------
        
        horizontal_buttons_widget = QWidget()
        horizontal_buttons_layout = QHBoxLayout(horizontal_buttons_widget)
        horizontal_buttons_layout.alignment=Qt.AlignLeft
        self.read_all_files = QPushButton("Read all files")
        self.read_all_files.setFixedSize(100,20)
        self.read_all_files.pressed.connect(self.read_all_npk_data)
        horizontal_buttons_layout.addWidget(self.read_all_files)
        
        self.extract_all_files = QPushButton("Extract all files")
        self.extract_all_files.setFixedSize(100,20)
        self.extract_all_files.pressed.connect(self.extract_all_npk_data)
        horizontal_buttons_layout.addWidget(self.extract_all_files)
        horizontal_buttons_layout.addSpacerItem(QSpacerItem(1,1,QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        horizontal_buttons_widget.setLayout(horizontal_buttons_layout)
        right_column.addWidget(horizontal_buttons_widget)
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Please choose a file/folder to process.")
        right_column.addWidget(self.status_bar)
        self.status_bar.setFixedHeight(15)

        # Assemble Mesh Viewer Tab
        left_right_splitter = QSplitter(Qt.Horizontal)
        left_right_splitter.addWidget(self.file_list_widget)
        left_right_splitter.addWidget(right_column_widget)
        tab1_layout.addWidget(left_right_splitter)

        return tab1
