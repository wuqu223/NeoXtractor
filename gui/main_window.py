import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from utils.config_manager import ConfigManager

from utils.console_handler import *
from logger import logger

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
class IconSplitterHandle(QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.icon_label = QLabel(self)
        self.icon_label.setScaledContents(True)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(80, 80)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.icon_label.move((self.width() - self.icon_label.width()) // 2,
                             (self.height() - self.icon_label.height()) // 2)

class IconSplitter(QSplitter):
    def createHandle(self):
        return IconSplitterHandle(self.orientation(), self)


def create_main_viewer_tab(self):
    tab1 = QWidget()
    main_layout = QHBoxLayout(tab1)
    
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
  
    self.list = QListView()
    self.list.doubleClicked.connect(self.on_item_double_clicked)
    self.list.clicked.connect(self.on_item_double_clicked)
    self.list_model = QStandardItemModel(self)
    self.list.setModel(self.list_model)

    self.list.installEventFilter(self)

    self.filter_input = QLineEdit(self)
    self.filter_input.setPlaceholderText("Search...")
    self.filter_input.textChanged.connect(self.filter_list_items)

    self.filter_combobox = QComboBox(self)
    self.filter_combobox.setEditable(False)
    # self.filter_combobox.lineEdit().setPlaceholderText("Search...")
    combo_items = ["ALL", "MESH", "TEXTURE", "CHARACTER", "SKIN", "TEXT FORMAT"]
    self.filter_combobox.addItems(combo_items)
    self.filter_combobox.currentIndexChanged.connect(self.filter_list_items)

    # Filtered mesh Checkbox
    self.filtered_mesh_checkbox = QCheckBox("Load 'biped head' mesh")
    self.filtered_mesh_checkbox.setChecked(False)

    # Status bar
    self.status_bar = QStatusBar()
    self.status_bar.showMessage("Please choose a file to process.")

    self.progress_bar = QProgressBar()

    # Horizontal buttons
    horizontal_buttons_widget = QWidget()
    horizontal_buttons_layout = QHBoxLayout(horizontal_buttons_widget)

    self.set_output_button = QPushButton("SET OUTPUT")
    self.set_output_button.setFixedSize(100, 30)
    self.set_output_button.pressed.connect(self.set_output)

    self.extract_all_files = QPushButton("UNPACK NPK")
    self.extract_all_files.setFixedSize(100, 30)
    self.extract_all_files.pressed.connect(self.extract_selected_npk_data)

    left_column.addWidget(self.filter_input)
    left_column.addWidget(self.filter_combobox)
    left_column.addWidget(self.filtered_mesh_checkbox)
    left_column.addWidget(self.list)
    left_column.addWidget(self.status_bar)
    left_column.addWidget(self.progress_bar)
    left_column.addWidget(horizontal_buttons_widget)

    horizontal_buttons_layout.addStretch()
    horizontal_buttons_layout.addWidget(self.set_output_button)
    horizontal_buttons_layout.addWidget(self.extract_all_files)
    horizontal_buttons_layout.addStretch()
    # ------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------
    # Right side setup (Main)
    right_column_widget = QWidget()
    right_column = QVBoxLayout(right_column_widget)

    self.main_console = ConsoleWidget(self.console_handler)
    right_column.addWidget(self.main_console)
    # ------------------------------------------------------------------------------------------------------------

    class IconSplitterHandle(QSplitterHandle):
    """Custom Splitter Handle with an Icon."""
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)

        icon_path = os.path.join(os.path.dirname(__file__), "../icons/splitte.png")

        # Add a QLabel with an icon or text
        self.icon_label = QLabel(self)
        self.icon_label.setPixmap(QPixmap(icon_path))
        self.icon_label.setScaledContents(True)
        self.icon_label.setAlignment(Qt.AlignCenter)

        if os.path.exists(icon_path):
            self.icon_label.setPixmap(QPixmap(icon_path))
        else:
            self.icon_label.setText("|||")

        # Adjust size and position of the icon
        self.icon_label.setFixedSize(80, 80)
        self.icon_label.move(0, 0)

    def resizeEvent(self, event):
        """Ensure the icon stays centered when the splitter handle resizes."""
        super().resizeEvent(event)
        self.icon_label.move((self.width() - self.icon_label.width()) // 2,
                             (self.height() - self.icon_label.height()) // 2)

class IconSplitter(QSplitter):
    """Custom Splitter using the Icon Handle."""
    def createHandle(self):
        return IconSplitterHandle(self.orientation(), self)

def create_main_viewer_tab(self):
    self.config_manager = ConfigManager()
    self.output_folder = self.config_manager.get("output_folder", "")

    # ------------------------------------------------------------------------------------------------------------
    # Main Tab
    tab1 = QWidget()
    main_layout = QHBoxLayout(tab1)

    # Left side setup (Main)
    left_column_widget = QWidget()
    left_column = QVBoxLayout(left_column_widget)

    # Filter bar for QListWidget
    self.filter_input = QLineEdit()
    self.filter_input.setPlaceholderText("Search or filter items...")
    self.filter_input.textChanged.connect(self.filter_list_items)
    self.filter_input.setMinimumWidth(200)
    self.filter_input.setToolTip("Type to filter the file list.")
    left_column.addWidget(self.filter_input)

    # File list setup
    self.file_list_widget = QListWidget()
    self.file_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Enable multi-selection
    # self.file_list_widget.itemSelectionChanged.connect(self.on_selection_changed) # Custom handler for selection changes
    self.file_list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
    self.file_list_widget.itemPressed.connect(self.on_item_clicked)
    self.file_list_widget.installEventFilter(self)
    # self.file_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.file_list_widget.setToolTip("List of files in the loaded NPK.")
    left_column.addWidget(self.file_list_widget)
    # ------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------
    # Right side setup (Main)
    right_column_widget = QWidget()
    right_column = QVBoxLayout(right_column_widget)

    # Output folder selection status bar
    self.output_folder_label = QLabel(f"Welcome!")
    self.output_folder_label.setFixedHeight(20)
    right_column.addWidget(self.output_folder_label)

    self.main_view_console_label = QLabel("    Log: ")
    self.main_view_console_label.setFixedHeight(20)
    self.main_view_console_label.alignment=Qt.AlignCenter
    right_column.addWidget(self.main_view_console_label)

    # Console output in the Main tab
    self.main_console = ConsoleWidget(self.console_handler)
    right_column.addWidget(self.main_console)
    
    horizontal_buttons_widget = QWidget()
    horizontal_buttons_layout = QHBoxLayout(horizontal_buttons_widget)
    horizontal_buttons_layout.alignment=Qt.AlignLeft
    self.read_selected_files = QPushButton("Read Selected")
    self.read_selected_files.setFixedHeight(30)
    self.read_selected_files.pressed.connect(self.read_selected_npk_data)
    self.read_selected_files.setToolTip("Read Selected files from the loaded NPK.")
    horizontal_buttons_layout.addWidget(self.read_selected_files)
    
    self.read_all_files = QPushButton("Read all files")
    self.read_all_files.setFixedHeight(30)
    self.read_all_files.pressed.connect(self.read_all_npk_data)
    self.read_all_files.setToolTip("Read all files from the loaded NPK.")
    horizontal_buttons_layout.addWidget(self.read_all_files)
    
    self.extract_all_files = QPushButton("Extract loaded files")
    self.extract_all_files.setFixedHeight(30)
    self.extract_all_files.pressed.connect(self.extract_selected_npk_data)
    horizontal_buttons_layout.addWidget(self.extract_all_files)

    horizontal_buttons_layout.addSpacerItem(QSpacerItem(1,1,QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
    right_column.addWidget(horizontal_buttons_widget)

    # Status bar
    self.status_bar = QStatusBar()
    self.status_bar.showMessage("Please choose a NPK file to process.")
    self.status_bar.setFixedHeight(15)
    right_column.addWidget(self.status_bar)

    # Add progress bar for read_all and extract_all npk data
    self.progress_bar = QProgressBar()
    self.progress_bar.setToolTip("Progress for file operations.")
    right_column.addWidget(self.progress_bar)
    # ------------------------------------------------------------------------------------------------------------

    # Splitter setup
    splitter = IconSplitter(Qt.Horizontal)
    splitter.addWidget(left_column_widget)
    splitter.addWidget(right_column_widget)
    splitter.setStretchFactor(0, 2)  # File list widget gets 2/3 of space
    splitter.setStretchFactor(1, 1)  # Right panel gets 1/3 of space
    # ------------------------------------------------------------------------------------------------------------
    main_layout.addWidget(splitter)
    splitter.setSizes([800, 400])  # Example: Left column twice as wide as right

    return tab1

def load_data_into_list(self, external_data, json_file):
    try:
        # Load the JSON file
        if not os.path.exists(json_file):
            print(f"JSON file {json_file} not found. Aborting load.")
            logger.debug(f"JSON file {json_file} not found. Aborting load.")
            return

        with open(json_file, 'r') as file:
            data = json.load(file)
            hash_mapping = data.get("characters", {})  # Get hash-to-filename mapping
            print(f"Loaded JSON: {hash_mapping}")
            logger.debug(f"Loaded JSON: {hash_mapping}")

        # Clear the existing model data
        self.list_model.clear()

        # Populate the model with updated data
        for i, entry in enumerate(external_data):
            # Get the name from hash_mapping or use entry as a fallback
            display_name = hash_mapping.get(entry, entry)
            item = QStandardItem(display_name)
            item.setData(i, Qt.UserRole)  # Store the index in UserRole
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Prevent edit
            self.list_model.appendRow(item)

        self.list.setModel(self.list_model)

        print("List model updated successfully.")
        logger.debug("List model updated successfully.")

    except Exception as e:
        self.status_bar.showMessage(f"Error loading data into list: {str(e)}")
        print(f"Error details: {str(e)}")
        logger.debug(f"Error details: {str(e)}")
