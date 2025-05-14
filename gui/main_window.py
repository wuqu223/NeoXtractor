from functools import partial
import os, json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from gui.popups import AboutPopup
from gui.widgets.viewer_3d import ViewerWidget
from utils.npk_reader import NPKFile
from gui.extraction_tab import ExtractionViewer
from gui.windows.mesh_viewer import MeshViewer
from gui.windows.npk_metadata_dialog import NPKMetadataDialog
from gui.windows.plain_text_viewer import PlainTextViewer
from gui.windows.raw_hex_viewer import HexViewerApp
from gui.windows.texture_viewer import TextureViewer
from utils.config_manager import ConfigManager

from utils.console_handler import *
from logger import logger
from utils.util import mesh_from_path, ransack_agent

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('NeoXtractor')
        self.setGeometry(150, 50, 1600, 950)

        self.config_manager = ConfigManager() # Fetch Outputfolder from config manager
        # todo: don't set these attributes
        self.decryption_key = self.config_manager.get("decryption_key", 0)
        self.output_folder = self.config_manager.get("output_folder", "")
        self.project_folder = self.config_manager.get("project_folder", "")
        self.aes_key = self.config_manager.get("aes_key", 0)
        self.index_size = self.config_manager.get("index_size", 0)
        self.npk_type = self.config_manager.get("npk_type", 0)

        # Initialize the console output handler
        self.console_handler = ConsoleOutputHandler()
        redirect_output(self.console_handler)  # Redirect stdout and stderr

        self.main_console = ConsoleWidget(self.console_handler)
        self.console_handler.add_console(self.main_console.console_output)

        # Allowed extensions for respective window implementation
        self.allowed_texture_exts = ["bmp", "gif", "jpg", "jpeg", "png", "pbm", "pgm", "ppm", "xbm", "xpm", "tga", "ico", "tiff", "dds", "pvr","astc", "ktx", "cbk"]
        self.allowed_mesh_exts = [".mesh"]
        self.allowed_text_exts = [".mtl", ".json", ".xml", ".trackgroup", ".nfx", ".h",
                                 ".shader", ".animation"]  # Only for double-clicking, context menu will still work for other formats

        # Main widget and layout for the window
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)  # Horizontal layout to hold the main splitter

        # Right side setup (Main)
        left_column_widget = QWidget()
        left_column = QVBoxLayout(left_column_widget)

        self.create_file_menu()
        self.create_help_menu()
        self.create_edit_menu()
        self.create_extraction_menu()
        self.create_tools_menu()
    
        self.list = QListView()
        self.list.doubleClicked.connect(self.on_item_double_clicked)
        self.list_model = QStandardItemModel(self)
        self.list.setModel(self.list_model)

        # self.list.installEventFilter(self)

        # Status bar
        self.status_bar2 = QStatusBar()
        self.status_bar2.showMessage(f"Game Config: {self.config_manager.get('game_config', 'Unknown')}")

        self.filter_input = QLineEdit(self)
        self.filter_input.setPlaceholderText("Search...")
        self.filter_input.textChanged.connect(self.filter_list_items)

        self.filter_combobox = QComboBox(self)
        self.filter_combobox.setEditable(False)
        # self.filter_combobox.lineEdit().setPlaceholderText("Search...")
        combo_items = ["ALL", "MESH", "TEXTURE", "CHARACTER", "SKIN", "TEXT FORMAT"]
        self.filter_combobox.addItems(combo_items)
        self.filter_combobox.currentIndexChanged.connect(
            lambda: (
                self.filtered_mesh_checkbox.setVisible(self.filter_combobox.currentText() == "MESH"),
                self.filter_list_items()
            )
        )

        # Filtered mesh Checkbox
        self.filtered_mesh_checkbox = QCheckBox("Load 'biped head' mesh")
        self.filtered_mesh_checkbox.setVisible(False)
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
        self.extract_all_files.pressed.connect(self.extract_processed_npk_data)

        left_column.addWidget(self.status_bar2)
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

        main_layout.addWidget(left_column_widget)

        # Right side setup (Main)
        right_column_widget = QWidget()
        right_column = QVBoxLayout(right_column_widget)

        self.main_console = ConsoleWidget(self.console_handler)
        right_column.addWidget(self.main_console)

        main_layout.addWidget(right_column_widget)

        # Define all the Windows that can be opened
        self.window_mesh = MeshViewer(self)

        self.list.installEventFilter(self)

        # Connect double-click signal
        #self.list.clicked.connect(self.on_item_clicked) # not needed anymore

        # Set up master status bar
        self.mstatus_bar = self.statusBar()
        self.mstatus_bar.showMessage("Ready")

    def eventFilter(self, source, event):
        # Handle Right-Click Context Menu
        if event.type() == QEvent.ContextMenu and source is self.list:
            index = self.list.indexAt(event.pos())
            if not index.isValid():
                logger.warning("No item under cursor.")
                return True

            # Retrieve associated file index
            entry_index = self.list.model().data(index, Qt.UserRole)
            npk_entry = self.npk_file.read_entry(entry_index)
            if npk_entry is None:
                logger.debug("No valid file index associated with the item.")
                return True

            # Create Context Menu
            list_context_menu = QMenu(self)
            showdata_action = QAction("Show Data", self)
            showdata_action.triggered.connect(lambda: self.show_data(npk_entry))
            export_action = QAction("Export File", self)
            export_action.triggered.connect(lambda: self.extract_file(npk_entry))
            hex_action = QAction("Hex Viewer", self)
            hex_action.triggered.connect(lambda: self.show_hex_data(npk_entry.data, npk_entry.filename))
            text_action = QAction("Plaintext Viewer", self)
            text_action.triggered.connect(lambda: self.show_text(npk_entry.data, npk_entry.filename))
            texture_action = QAction("Texture Viewer", self)
            texture_action.triggered.connect(lambda: self.show_texture(npk_entry))
            mesh_action = QAction("Mesh Viewer", self)
            mesh_action.triggered.connect(lambda: self.show_mesh(npk_entry.filename, entry_index))

            # Add actions to the menu
            list_context_menu.addAction(showdata_action)
            list_context_menu.addAction(export_action)
            list_context_menu.addAction(hex_action)
            list_context_menu.addAction(text_action)
            list_context_menu.addAction(texture_action)
            list_context_menu.addAction(mesh_action)

            list_context_menu.exec_(event.globalPos())
            return True  # Block further processing

        # Handle Down Arrow Key and Skip Hidden Items
        elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_Down and source is self.list:
            selected_indexes = self.list.selectionModel().selectedIndexes()
            if not selected_indexes:
                return True  # No selection, stop processing

            current_index = selected_indexes[0]
            row_count = self.list.model().rowCount()

            # Find the next **visible** row
            next_row = current_index.row() + 1
            while next_row < row_count and self.list.isRowHidden(next_row):
                next_row += 1  # Skip hidden rows

            next_index = self.list.model().index(next_row, 0)

            if next_index.isValid():
                self.list.setCurrentIndex(next_index)  # Move selection down
                self.on_item_double_clicked(next_index)  # Simulate double-click

            return True  # Block default behavior
        return super().eventFilter(source, event)

    # Context Menu Options
    def show_data(self, npk_entry):
        """Displays metadata about the selected NPK entry."""
        try:
            dialog = NPKMetadataDialog(npk_entry, self)
            dialog.exec_()
        except Exception as e:
            print(f"Error displaying data: {e}")
            logger.critical(f"Error displaying data: {e}")
            QMessageBox.critical(self, "Error", f"Could not display file data:\n{e}")

    def show_hex_data(self, data: bytes, filename: str | None):
        wnd = HexViewerApp(data, filename, self)
        wnd.show()
        wnd.raise_()

    def show_text(self, npkentry, filename: str | None):
        wnd = PlainTextViewer(npkentry, filename, self)
        wnd.show()
        wnd.raise_()

    def show_mesh(self, data, filename, filepath):
        """Displays the selected mesh in the Mesh Viewer."""
        
        print(f"DEBUG: Selected Mesh - {filename}")
    
        if self.window_mesh.viewer.scene is None:
            print("Mesh Viewer is not ready, waiting for initialization.")
            self.window_mesh.viewer.on_init = lambda : self.show_mesh(data, filename, filepath)
            self.window_mesh.show()
            return
        
        self.window_mesh.viewer.filename = filename
        self.window_mesh.viewer.filepath = filepath

        if not any(filename.lower().endswith(ext) for ext in self.allowed_mesh_exts):
            print(f"'{filename}' is not a valid mesh file.")
            logger.debug("'%s' is not a valid mesh file.", filename)
            return
        
        try:
            # Parse the mesh data
            mesh = mesh_from_path(data)
            if not mesh:
                raise ValueError("Failed to parse the mesh file.")

            # Load the mesh into the viewer
            self.window_mesh.viewer.load_mesh(mesh, self.get_savefile_location())
            self.window_mesh.viewer.focus_on_selected_object()
            self.window_mesh.viewer.update_aspect_ratio()

            # Ensure the mesh viewer window is displayed and raised
            self.update()
            self.window_mesh.show()
            self.window_mesh.raise_()

        except Exception as e:
            logger.critical(f"An error occurred while loading the mesh '{filename}': {str(e)}")

    def show_texture(self, npk_entry):
        """Displays the selected texture file in the TextureViewer window."""

        if not npk_entry or not any(npk_entry.filename.lower().endswith(ext) for ext in self.allowed_texture_exts):
            print(f"'{npk_entry.filename}' is not a valid texture file.")
            logger.debug(f"'{npk_entry.filename}' is not a valid texture file.")
            return

        try:
            viewer = TextureViewer(npk_entry, npk_entry.filename, self)
            
            # Update the existing viewer with the new texture
            viewer.show()
            viewer.raise_()
        except Exception as e:
            logger.critical(f"An error occurred at location {e.__traceback__.tb_frame.f_code.co_name}; line {e.__traceback__.tb_lineno} while loading the texture: {str(e)}")


    # Main Toolbar
    # ----------------------------------------------------------------------------------------------------------
    def create_file_menu(self):
        # File Menu Button
        file_menu = self.menuBar().addMenu("File")

        # Choose New Config action
        new_config_action = QAction(self.style().standardIcon(QStyle.SP_FileIcon), "Choose New Config", self)
        new_config_action.setStatusTip("Select a new configuration file.")
        new_config_action.triggered.connect(partial(self.npk_config_data, force_new_file=True))
        file_menu.addAction(new_config_action)

        # Load Last Config action
        last_config_action = QAction(self.style().standardIcon(QStyle.SP_DialogSaveButton), "Load Last Config", self)
        last_config_action.setStatusTip("Load the last used configuration.")
        last_config_action.triggered.connect(partial(self.npk_config_data, force_new_file=False))
        file_menu.addAction(last_config_action)

        open_folder_action = QAction(self.style().standardIcon(QStyle.SP_DirOpenIcon), "Open File", self)
        open_folder_action.setStatusTip("Choose File")
        open_folder_action.setShortcut("Ctrl+O")
        open_folder_action.triggered.connect(partial(self.load_npk))
        file_menu.addAction(open_folder_action)

    def create_help_menu(self):
        # About Menu Button
        about_menu = self.menuBar().addMenu("Help *")

        d_crypt_action = QAction(self.style().standardIcon(QStyle.SP_VistaShield), "D-Key", self)
        d_crypt_action.setShortcut('Ctrl+D')
        d_crypt_action.setStatusTip("Open an decryction popup window")
        d_crypt_action.triggered.connect(self.show_decrypt)
        about_menu.addAction(d_crypt_action)

        about_action = QAction(self.style().standardIcon(QStyle.SP_VistaShield), "About", self)
        about_action.setShortcut('Ctrl+H')
        about_action.setStatusTip("Open an about popup window")
        about_action.triggered.connect(self.show_about)
        about_menu.addAction(about_action)

    def create_edit_menu(self):
        # Settings Menu Button
        settings_menu = self.menuBar().addMenu("Edit *")

        settings_action = QAction(self.style().standardIcon(QStyle.SP_VistaShield), "Preferences", self)
        settings_action.setShortcut('Ctrl+,')
        settings_action.setStatusTip("Open an about popup window")
        settings_action.triggered.connect(self.show_settings)
        settings_menu.addAction(settings_action)
    
    def create_extraction_menu(self):
        """Creates the batch extraction menu."""
        # Create extraction window instance
        self.extraction_window = ExtractionViewer(self)

        # Create the menu
        extraction_menu = self.menuBar().addMenu("Batch *")

        # Create extraction action
        extraction_action = QAction(self.style().standardIcon(QStyle.SP_VistaShield), "Extract NPK", self)
        extraction_action.setShortcut('Ctrl+,')
        extraction_action.setStatusTip("Open an extraction popup window")
        extraction_action.triggered.connect(self.show_extraction_window)  # Connect to a function
        extraction_menu.addAction(extraction_action)

    def show_extraction_window(self):
        """Displays the extraction window when triggered."""
        self.extraction_window.show()
        self.extraction_window.raise_()

    def create_tools_menu(self):
        tools_menu = self.menuBar().addMenu("Tools")

        mesh_viewer_action = QAction("Mesh Viewer", self)
        mesh_viewer_action.setStatusTip("Open Mesh Viewer")
        mesh_viewer_action.triggered.connect(self.show_mesh_viewer_window)
        tools_menu.addAction(mesh_viewer_action)

    def show_mesh_viewer_window(self):
        self.window_mesh.show()
        self.window_mesh.raise_()

    def show_decrypt(self):
        """Show the decryption popup window."""
        self.statusBar().showMessage("D-Key...")

        # Load message from a text file
        try:
            with open("info/decryption_manager_info.txt", 'r') as file:
                message = file.read()
        except FileNotFoundError:
            message = "Error: Message file not found."
        # Initialize the decryption window with the loaded message
        result, ok = QInputDialog().getInt(None, "Decryption Key", message, self.decryption_key, -1000,1000, 10)
        if ok:
            # Retrieve input text if the dialog was accepted
            self.decryption_key = result  # Store the input for future use
            self.config_manager.set("decryption_key", result)
            print(f"Decryption Key Entered: {self.decryption_key}")
            logger.debug(f"Decryption Key Entered: {self.decryption_key}")
        self.statusBar().showMessage(f"Decryption key set to {result}")

    def show_about(self):
        """Show the about popup window."""
        self.statusBar().showMessage("Preferences...")
        # Load message from a text file
        try:
            with open("info/about_info.txt", 'r') as file:
                message = file.read()
        except FileNotFoundError:
            message = "Error: Message file not found."

        # Initialize the popup with the loaded message
        popup = AboutPopup(message)
        popup.exec_()

    def show_settings(self):
        """Show the settings window.""" # Edit Tab
        self.statusBar().showMessage("Preferences...")
        # Load message from a text file
        try:
            with open("info/about_info.txt", 'r') as file:
                message = file.read()
        except FileNotFoundError:
            message = "Error: Message file not found."

        # Initialize the popup with the loaded message
        popup = AboutPopup(message)
        popup.exec_()


    # Functionality
    # ----------------------------------------------------------------------------------------------------------
    def get_savefile_location(self):
        try:
            # Get the currently selected indexes
            selected_indexes = self.list.selectionModel().selectedIndexes()
            
            if not selected_indexes:
                logger.warning("No valid NPK entry selected.")
                return None

            # Dynamically get the selected file index (from selection)
            selected_index = selected_indexes[0]
            entry_index = self.list.model().data(selected_index, Qt.UserRole)

            npk_entry = self.npk_file.read_entry(entry_index)

            if npk_entry is None:
                logger.warning(f"No valid file index ({entry_index}) found in NPK.")
                return None

            # Construct the output path dynamically based on the NPK entry attributes
            base_path = os.path.join(self.output_folder, os.path.basename(self.npk.path))

            if npk_entry.file_structure:
                filestructure = npk_entry.file_structure.decode("utf-8").replace("\\", "/")
                folder_path = os.path.join(base_path, os.path.dirname(filestructure))
                os.makedirs(folder_path, exist_ok=True)
                file_path = os.path.join(folder_path, os.path.basename(filestructure))
            else:
                # Fallback if file_structure is empty
                os.makedirs(base_path, exist_ok=True)
                file_path = os.path.join(base_path, f"{hex(npk_entry.file_sign)}.{npk_entry.ext}")

            logger.info(f"Generated file path: {file_path}")
            return file_path

        except Exception as e:
            logger.critical(f"Error generating save file location: {e}")
            return None

    def set_output(self):
        file_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if file_path:
            # self.output_folder = self.config_manager.set(f"output_folder", f"{os.path.basename(file_path)}")
            self.output_folder = self.config_manager.set(f"output_folder", f"{file_path}")
            self.status_bar.showMessage(f'Output Folder: {file_path}.')
            logger.info(f'Output Folder: {file_path}.')
        return self.output_folder

    def extract_file(self, npk_entry):
        """Extract the currently selected NPK entry to a user-specified location."""

        # Ensure there is data to extract
        if not npk_entry.data or npk_entry.file_original_length == 0:
            QMessageBox.warning(self, "Extraction Error", f"The selected file '{npk_entry.filename}' is empty.")
            logger.warning(f"Skipping extraction: {npk_entry.filename} (empty file).")
            return

        # Get save file location with default name
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save File As", npk_entry.filename, "All Files (*.*)"
        )
        if not save_path:
            self.status_bar.showMessage("Extraction canceled.")
            return

        # Write file to disk
        try:
            with open(save_path, "wb") as f:
                f.write(npk_entry.data)

            self.status_bar.showMessage(f"File extracted: {save_path}")
            QMessageBox.information(self, "Extraction Complete", f"Successfully extracted:\n{save_path}")
            logger.info(f"Extracted file: {save_path}")

        except Exception as e:
            QMessageBox.critical(self, "Extraction Failed", f"An error occurred:\n{str(e)}")
            logger.critical(f"Error extracting {npk_entry.filename}: {e}")


    def npk_config_data(self, config_file=None, force_new_file=False):
        """Load configuration data from a JSON file and save the last used config path."""
        # Check if a saved config path exists

        config_path_storage = "./utils/last_config.json"

        # Load last used config if available
        if not force_new_file and not config_file and os.path.exists(config_path_storage):
            try:
                with open(config_path_storage, "r") as storage_file:
                    saved_path = json.load(storage_file).get("last_used_config", None)
                    if saved_path and os.path.exists(saved_path):
                        config_file = saved_path
            except Exception as e:
                print(f"Error loading saved config path: {e}")
                logger.warning(f"Error loading saved config path: {e}")

        # If no valid config, ask user
        if not config_file or force_new_file:
            self.status_bar.showMessage('Choosing config file...')
            file_path = QFileDialog.getOpenFileName(self, "Choose file", filter="NPK Config (*.json)")[0]
            if not file_path:  # User canceled file dialog
                print("Config selection canceled.")
                return
            config_file = file_path

        # Validate config file extension
        if not config_file.endswith(".json"):
            print("Invalid File", "Please select a valid JSON configuration file.")
            logger.warning("Invalid File selected for NPK Config.")
            return
        
        try:
            # Load the JSON file
            with open(config_file, "r") as file:
                data = json.load(file)
                mapping = data.get("Data", {})

                # Debugging - Print mapping
                print(f"Mapping Loaded: {mapping}")

                # Retrieve specific configuration values
                game_config = mapping.get("game_config")
                npk_type = int(mapping.get("npk_type", 0)) # Ensure it's an integer
                decryption_key = int(mapping.get("decryption_key", 0))
                aes_key = int(mapping.get("aes_key", 0))
                index_size = int(mapping.get("index_size", 0))

                # Debugging - Print values
                print(f"Config Values Loaded: {game_config}, {npk_type}, {decryption_key}, {aes_key}, {index_size}")
                logger.debug(f"Config Values Loaded: {game_config}, {npk_type}, {decryption_key}, {aes_key}, {index_size}")

                #Update application state
                self.game_config = game_config
                self.npk_type = npk_type
                self.decryption_key = decryption_key
                self.aes_key = aes_key
                self.index_size = index_size
                self.compblks2png = compblks2png

                # Save the last used config path
                with open(config_path_storage, "w") as storage_file:
                    json.dump({"last_used_config": config_file}, storage_file)
                # print(f"Saved last used config path: {config_file}")
                logger.info(f"Saved last used config path: {config_file}")
                    
            # Update Config Manager
            if hasattr(self, "config_manager") and self.config_manager is not None:
                self.config_manager.set("game_config", game_config)
                self.config_manager.set("npk_type", npk_type)
                self.config_manager.set("decryption_key", decryption_key)
                self.config_manager.set("aes_key", aes_key)
                self.config_manager.set("index_size", index_size)
                self.config_manager.set("compblks2png", )
            else:
                print("ERROR: config_manager is not initialized!")
                logger.critical("ERROR: config_manager is not initialized!")
        
            self.status_bar2.showMessage(f"Game Config: {game_config}")

        except Exception as e:
            print(f"Error loading Config file: {e}")
            logger.critical(f"Error loading Config file: {e}")

    def update_config_data(self, json_file_path, outer_key, inner_key, value):
        """Update a nested JSON file structure."""
        # Check if the file exists
        if not os.path.exists(json_file_path):
            print(f"File {json_file_path} does not exist. Creating a new one.")
            logger.warning(f"File {json_file_path} does not exist. Creating a new one.")
            data = {outer_key: {}}  # Create a nested structure if the file doesn't exist
        else:
            # Read the existing JSON data
            try:
                with open(json_file_path, "r") as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                print(f"File {json_file_path} contains invalid JSON. Starting with an empty dictionary.")
                logger.warning(f"File {json_file_path} contains invalid JSON. Starting with an empty dictionary.")
                data = {outer_key: {}}

        # Ensure the outer key exists
        if outer_key not in data:
            data[outer_key] = {}

        # Update the nested dictionary
        data[outer_key][inner_key] = value

        # Write the updated data back to the file
        with open(json_file_path, "w") as file:
            json.dump(data, file, indent=4)

        print(f"Updated {json_file_path}: Set {outer_key}.{inner_key} to {value}")
        logger.info(f"Updated {json_file_path}: Set {outer_key}.{inner_key} to {value}")

    def load_npk(self):
        """Load an NPK file and populate the list."""
        self.npk_file = None
        self.status_bar.showMessage('Selecting file...')

        file_path, _ = QFileDialog.getOpenFileName(self, "Open file", filter="NPK Files (*.npk)")
        if not file_path or not file_path.endswith(".npk"):
            self.status_bar.showMessage("Select NPK to extract!")
            return
        
        self.filter_input.clear()
        self.list_model.clear()

        self.status_bar.showMessage(f'Loading NPK: {file_path}')

        # Read NPK File
        self.npk_file = NPKFile(file_path, self.config_manager)

        if self.npk_file.pkg_type == 1:
            checked = QMessageBox.question(self, "Check Decryption Key!", "Your decryption key is {}, program may fail if the key is wrong!\nAre you sure you want to continue?".format(self.decryption_key))
            if checked == QMessageBox.No:
                return
        
        if self.npk_file.read_index() == -1:
            self.status_bar.showMessage("Failed to read NPK index!")
            return

        # Populate List Model
        for index, file in enumerate(self.npk_file.index_table):
            filename = file[6].decode("utf-8") if file[6] else hex(file[0])

            widgetitem = QStandardItem(filename)
            widgetitem.setData(index, Qt.UserRole)  # Store file index as Qt.UserRole
            widgetitem.setIcon(self.style().standardIcon(QStyle.SP_DialogNoButton))

            self.list_model.appendRow(widgetitem)
            self.progress_bar.setValue((index + 1) * 100 // len(self.npk_file.index_table))  # Update progress bar

        self.status_bar.showMessage(f'Loading NPK: {file_path}')
        # todo: multithreaded, avoid blocking main UI thread.
        self.read_all_npk_data()  # Call the existing read_all_npk_data

        self.filter_list_items()

        if self.list_model.rowCount() > 0:
            self.list.setCurrentIndex(self.list_model.index(0, 0))  # Auto-select first item

    def read_all_npk_data(self):
        """Read all entries from the NPK file and update the list with filenames."""
        if not hasattr(self, "npk_file"):
            QMessageBox.information(self, "Open NPK!", "You must open an NPK file first!")
            logger.error("You must open an NPK file first!")
            return

        model: QStandardItemModel = self.list.model()

        # todo: is this needed?
        # Load JSON file for filename mapping
        hash_mapping = {}
        try:
            with open("./utils/filename.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                hash_mapping = data.get("characters", {})
                ViewerWidget.json_mapping = hash_mapping  # Store mapping globally
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            logger.debug(f"Error loading JSON file: {e}")

        # Iterate through the model's rows
        for x in range(model.rowCount()):
            try:
                item = model.item(x)
                if not item:
                    continue

                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Disable editing
                entry_index = item.data(Qt.UserRole)  # Retrieve file index

                if entry_index is None or not (0 <= entry_index < len(self.npk_file.index_table)):
                    continue  # Skip invalid indices

                # Read entry from NPK
                npkentry = self.npk_file.read_entry(entry_index)
                self.progress_bar.setValue((x + 1) * 100 // len(self.npk_file.index_table))  # Update progress bar

                if npkentry.file_original_length == 0:
                    print(f"Index {entry_index} is empty")
                    logger.debug(f"Index {entry_index} is empty")
                    continue

                # Update filename
                # todo: see if it can be moved to npk reader
                original_filename = item.text()
                updated_filename = hash_mapping.get(original_filename, original_filename)
                if not npkentry.file_structure:
                    updated_filename += f".{npkentry.ext or 'bin'}"

                item.setText(updated_filename)
                npkentry.filename = updated_filename  # Store updated name in npkentry

                # Set success icon
                if self.style():
                    item.setIcon(self.style().standardIcon(QStyle.SP_DialogYesButton))
                else:
                    item.setIcon(QIcon())  # Fallback if no style is available

            except Exception as e:
                print(f"Failed to process entry at row {x}: {e}")
                logger.debug(f"Failed to process entry at row {x}: {e}")
                if item and self.style():
                    item.setIcon(self.style().standardIcon(QStyle.SP_DialogNoButton))  # Failure icon

    def extract_processed_npk_data(self):
        """Extract all processed NPK entries into an output folder."""
        
        entries = self.npk_file.get_loaded_entries()

        total_files = len(self.entries)
        if total_files == 0:
            QMessageBox.warning(self, "Extraction Error", "No NPK data loaded. Load an NPK first!")
            return
        
        # Get output directory from config manager
        # output_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        output_dir = self.config_manager.get("output_folder", "")

        if not output_dir:
            self.status_bar.showMessage("Extraction canceled.")
            return
        
        extracted_files = 0

        # Extract each file
        for file_index, npkentry in entries.items():
            try:
                if npkentry.file_original_length == 0:
                    print(f"Skipping empty file: {npkentry.filename}")
                    logger.debug(f"Skipping empty file: {npkentry.filename}")
                    continue

                # Generate output path
                output_file_path = os.path.join(output_dir, npkentry.filename)

                # Write extracted file
                with open(output_file_path, "wb") as f:
                    f.write(npkentry.data)
                    self.status_bar.showMessage(f"Extracting: {npkentry}.")

                print(f"Extracted: {output_file_path}")
                logger.info(f"Extracted: {output_file_path}")
                extracted_files += 1

                # Update progress bar
                self.progress_bar.setValue((extracted_files * 100) // total_files)

            except Exception as e:
                print(f"Failed to extract {npkentry.filename}: {e}")
                logger.critical(f"Failed to extract {npkentry.filename}: {e}")

        # Show completion message
        if extracted_files > 0:
            self.status_bar.showMessage(f"Extraction complete! {extracted_files} files saved to {output_dir}")
            QMessageBox.information(self, "Extraction Complete", f"Successfully extracted {extracted_files} files.")
        else:
            self.status_bar.showMessage("No valid files were extracted.")
            QMessageBox.warning(self, "Extraction Warning", "No valid files found to extract.")

    def on_item_double_clicked(self, index: QModelIndex):
        """Handles double-click events to open the appropriate viewer."""
        
        # Ensure the index is valid
        if not index.isValid():
            print("Invalid index.")
            logger.warning("Invalid index.")
            return
        
        entry_index = index.data(Qt.UserRole)

        # Retrieve the corresponding NPK entry
        npk_entry = self.npk_file.read_entry(entry_index)
        if not npk_entry:
            print(f"No entry found for index {entry_index}.")
            logger.debug(f"No entry found for index {entry_index}.")
            return

        # Determine file type and open the correct viewer
        filename_lower = npk_entry.filename.lower()

        if filename_lower.endswith(tuple(self.allowed_mesh_exts)):
            self.show_mesh(npk_entry.data, npk_entry.filename, entry_index)
        elif filename_lower.endswith(tuple(self.allowed_texture_exts)):
            self.show_texture(npk_entry)
        elif filename_lower.endswith(tuple(self.allowed_text_exts)):
            self.show_text(npk_entry.data, npk_entry.filename)
        else:
            print(f"Unsupported file type: {npk_entry.filename}")
            logger.debug(f"Unsupported file type: {npk_entry.filename}")
    
    def filter_list_items(self):
        """Filter QListView items based on user input from QLineEdit and QComboBox."""
        model: QStandardItemModel = self.list.model()

        # Get filter parameters
        search_string = self.filter_input.text().strip().lower()  
        category = self.filter_combobox.currentText()  
        is_all_category = category == "ALL"
        check_biped_head = self.filtered_mesh_checkbox.isChecked() and category == "MESH"
        
        # Pre-compute extension tuple lookups for performance
        mesh_exts = tuple(self.allowed_mesh_exts)
        texture_exts = tuple(self.allowed_texture_exts)
        text_exts = tuple(self.allowed_text_exts)
        
        for row in range(model.rowCount()):
            item = model.item(row)
            entry_index = item.data(Qt.UserRole)

            npk_entry = self.npk_file.read_entry(entry_index)
            filename_lower = npk_entry.filename.lower()
            
            # Text filter - quick reject
            if search_string and search_string not in filename_lower:
                self.list.setRowHidden(row, True)
                continue
            
            # Category filtering
            if is_all_category:
                show_item = True
            elif category == "MESH" and filename_lower.endswith(mesh_exts):
                # Only do the expensive biped head check if needed
                show_item = not check_biped_head or ransack_agent(npk_entry.data, "biped head")
            elif category == "TEXTURE" and filename_lower.endswith(texture_exts):
                show_item = True
            elif category == "CHARACTER" and "character" in filename_lower:
                show_item = True
            elif category == "SKIN" and "skin" in filename_lower:
                show_item = True
            elif category == "TEXT FORMAT" and filename_lower.endswith(text_exts):
                show_item = True
            else:
                show_item = False
            
            # Apply visibility
            self.list.setRowHidden(row, not show_item)
