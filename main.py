import sys, os, io, time, json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from utils.config_manager import ConfigManager
from utils.console_handler import *
from utils.util import *
from utils.extractor_utils import read_index, read_entry, determine_info_size
# from utils import FileListModel

from functools import partial

from gui.main_window import create_main_viewer_tab
from gui.viewer_3d import ViewerWidget
from gui.main_window import *
# from gui.main_window import create_main_viewer_tab
from gui.mesh_tab import create_mesh_viewer_tab
# from gui.extraction_tab import create_extraction_tab
from gui.texture_tab import create_texture_tab
from gui.viewer_3d import ViewerWidget
from gui.main_window import *
from gui.qt_theme import qt_theme
# from gui.main_window import create_main_viewer_tab
from gui.mesh_tab import create_mesh_viewer_tab
# from gui.extraction_tab import create_extraction_tab
# from gui.texture_tab import create_texture_tab
from gui.texture_viewer import TextureViewer
from gui.text_tab import create_text_tab
from gui.raw_hex_viewer import HexViewerApp
from gui.popups import AboutPopup

# from bin.read_nxfn import NxfnResultViewer
from converter import * # saveobj, savesmd, saveascii, savepmx, saveiqe, parse_mesh_original, parse_mesh_helper, parse_mesh_adaptive
from qframelesswindow import FramelessWindow
from logger import logger

def custom_logging_handler(mode, context, message):
    with open("logfile.txt", "a") as log_file:
        if mode == QtDebugMsg:
            log_file.write(f"DEBUG: {message}\n")
        elif mode == QtInfoMsg:
            log_file.write(f"INFO: {message}\n")
        elif mode == QtWarningMsg:
            log_file.write(f"WARNING: {message}\n")
        elif mode == QtCriticalMsg:
            log_file.write(f"CRITICAL: {message}\n")
        elif mode == QtFatalMsg:
            log_file.write(f"FATAL: {message}\n")

qInstallMessageHandler(custom_logging_handler)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('NeoXtractor')
        self.setGeometry(150, 50, 1600, 950)
        self.npkentries = dict()

        self.config_manager = ConfigManager() # Fetch Outputfolder from config manager
        self.decryption_key = self.config_manager.get("decryption_key", 150)
        self.output_folder = self.config_manager.get("output_folder", "out")
        self.project_folder = self.config_manager.get("project_folder", "")
        
        self.config_manager = ConfigManager()  # Fetch config manager
        self.work_folder = self.config_manager.get("work_folder", "out")
        self.output_folder = self.config_manager.get("output_folder", "")
        self.decryption_key = 0 #self.config_manager.get("decryption_key", 150)

        self.aes_key = self.config_manager.get("aes_key", 0)
        self.index_size = self.config_manager.get("index_size", 0)
        self.npk_type = self.config_manager.get("npk_type", 0)

        self.update_config_data("./configs/IDV_config.json", "Data", "npk_type", 1) # update config entry (Testing)

        # Initialize the console output handler
        self.console_handler = ConsoleOutputHandler()
        redirect_output(self.console_handler)  # Redirect stdout and stderr

        self.main_console = ConsoleWidget(self.console_handler)
        self.console_handler.add_console(self.main_console.console_output)

        # Initialize the rest of the UI
        self.initUI()

        # Allowed extensions for respective window implementation
        self.allowed_texture_exts = [".png", ".jpg", ".dds", ".ktx", ".pvr", ".astc", ".tga", "bmp"]
        self.allowed_mesh_exts = [".mesh"]
        self.allowed_text_exts = [".mtl", ".json", ".xml", ".trackgroup", ".nfx", ".h",
                                 ".shader"]  # Only for double-clicking, context menu will still work for other formats

        # Initialize the rest of the UI
        self.initUI()

    def log_message(self):
        print("This is a print statement")
        qInstallMessageHandler(lambda mode, context, message: None) # Disable default output
        raise ValueError("This is an exception logged to file.") 

    def closeEvent(self, a0):
        self.window_mesh.thread().quit()
        logger.warning("Closed Mesh Window!")
        return super().closeEvent(a0)

    def eventFilter(self, source, event):
        if event.type() == QEvent.ContextMenu and source is self.list:
            index = self.list.indexAt(event.pos())
            if not index.isValid():
                # print("No item under cursor.")
                logger.warning("No item under cursor.")
                return True

            # Retrieve the associated data for the selected item
            file_index = self.list.model().data(index, Qt.UserRole)
            if file_index is None or file_index not in self.npkentries:
                print("No valid file index associated with the item.")
                logger.debug("No valid file index associated with the item.")
                return True

            # Create the context menu
            list_context_menu = QMenu(self)
            showdata_action = QAction("Show Data", self)
            showdata_action.triggered.connect(lambda: self.show_data(file_index))
            export_action = QAction("Export File", self)
            export_action.triggered.connect(self.extract_file)
            export_action.triggered.connect(lambda: self.extract_file())
            hex_action = QAction("Hex Viewer", self)
            hex_action.triggered.connect(lambda: self.show_hex_data())
            text_action = QAction("Plaintext Viewer", self)
            text_action.triggered.connect(lambda: self.show_text())
            texture_action = QAction("Texture Viewer", self)
            texture_action.triggered.connect(lambda: self.show_texture())
            mesh_action = QAction("Mesh Viewer", self)
            mesh_action.triggered.connect(lambda: self.show_mesh())

            # Add actions to the context menu
            list_context_menu.addAction(showdata_action)
            list_context_menu.addAction(export_action)
            list_context_menu.addAction(exp_texture_action)
            list_context_menu.addAction(hex_action)
            list_context_menu.addAction(text_action)
            list_context_menu.addAction(texture_action)
            list_context_menu.addAction(mesh_action)

            # Execute the context menu
            list_context_menu.exec_(event.globalPos())
        return True            
            return True

        # Pass other events to the default handler
        return super().eventFilter(source, event)

    def initUI(self):

        # Main widget and layout for the window
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)  # Horizontal layout to hold the main splitter

        # Define all the Windows that can be opened
        self.main_exploring = create_main_viewer_tab(self)
        self.window_mesh = create_mesh_viewer_tab(self)
        self.window_mesh.show()

        # Add widgets to the main layout
        main_layout.addWidget(self.main_exploring)

        # Define context menu for TreeView:
        # Connect double-click signal
        self.file_list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

        # Set up a status bar
        self.mstatus_bar = self.statusBar()
        self.mstatus_bar.showMessage("Ready")

    # Context Menu Options
    def show_data(self):
        file = self.npkentries[self.selectednpkentry]

        showdialog = QWidget()
        showdialog.setWindowTitle("NPK Data")
        showdialog_layout = QVBoxLayout(showdialog)

        right_side = QWidget()
        right_side_layout = QVBoxLayout(right_side)

        right_side_layout.addWidget(QLabel("SIGN:"))
        right_side_layout.addWidget(QLabel("NPK OFFSET:"))
        right_side_layout.addWidget(QLabel("DATA LENGTH:"))
        right_side_layout.addWidget(QLabel("ORIGINAL DATA LENGTH:"))
        right_side_layout.addWidget(QLabel("COMPRESSED CRC:"))
        right_side_layout.addWidget(QLabel("ORIGINAL CRC:"))
        right_side_layout.addWidget(QLabel("COMPRESSION FLAG:"))
        right_side_layout.addWidget(QLabel("FILE FLAG:"))
        if file.file_structure:
            right_side_layout.addWidget(QLabel("NXPK LOCATION: "))
        right_side_layout.addWidget(QLabel("DETECTED EXTENSION:"))

        left_side = QWidget()
        left_side_layout = QVBoxLayout(left_side)

        left_side_layout.addWidget(QLabel(hex(file.file_sign)))
        left_side_layout.addWidget(QLabel(hex(file.file_offset)))
        left_side_layout.addWidget(QLabel(str(file.file_length)))
        left_side_layout.addWidget(QLabel(str(file.file_original_length)))
        left_side_layout.addWidget(QLabel(str(file.crc)))
        left_side_layout.addWidget(QLabel(str(file.zcrc)))
        left_side_layout.addWidget(QLabel(str(file.zflag)))
        left_side_layout.addWidget(QLabel(str(file.fileflag)))
        if file.file_structure:
            left_side_layout.addWidget(QLabel(file.file_structure.decode("utf-8")))
        left_side_layout.addWidget(QLabel(file.ext))

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(right_side)
        splitter.addWidget(left_side)
        showdialog_layout.addWidget(splitter)
        showdialog_layout.addWidget(QLabel("Please report if DETECTED EXTENSION is not correct or shows .dat!"))

        self.showdialog = showdialog
        self.showdialog.show()

    def show_hex(self):
        self.window_hex = HexViewerApp(self.npkentries[self.selectednpkentry].data)
        self.window_hex.show()
        self.window_hex.raise_()

        # Set up a status bar
        self.mstatus_bar = self.statusBar()
        self.mstatus_bar.showMessage("Ready")

        # self.proxy_model.setSourceModel(self.list_model)
        self.list.setModel(self.list_model)

    # Context Menu Options
    def show_data(self, file_index):
        try:
            selected_indexes = self.list.selectionModel().selectedIndexes()
            if not selected_indexes:
                print("No valid selection.")
                logger.warning("No valid selection for Show Data.")
                return

            index = selected_indexes[0]
            selected_file_index = self.list.model().data(index, Qt.UserRole)
            
            file = self.npkentries.get(selected_file_index)
            if not file:
                print(f"Selected entry {selected_file_index} not found.")
                logger.debug(f"Selected entry {selected_file_index} not found.")
                return

            showdialog = QWidget()
            showdialog.setWindowTitle("NPK Data")
            showdialog_layout = QVBoxLayout(showdialog)

            right_side = QWidget()
            right_side_layout = QVBoxLayout(right_side)

            labels = [
                "SIGN:",
                "NPK OFFSET:",
                "DATA LENGTH:",
                "ORIGINAL DATA LENGTH:",
                "COMPRESSED CRC:",
                "ORIGINAL CRC:",
                "COMPRESSION FLAG:",
                "FILE FLAG:",
            ]
            
            if file.file_structure:
                labels.append("FILE STRUCTURE:")
            labels.append("EXTENSION:")

            for label in labels:
                right_side_layout.addWidget(QLabel(label))

            left_side = QWidget()
            left_side_layout = QVBoxLayout(left_side)

            left_side_layout.addWidget(QLabel(hex(file.file_sign)))
            left_side_layout.addWidget(QLabel(hex(file.file_offset)))
            left_side_layout.addWidget(QLabel(str(file.file_length)))
            left_side_layout.addWidget(QLabel(str(file.file_original_length)))
            left_side_layout.addWidget(QLabel(str(file.zcrc)))
            left_side_layout.addWidget(QLabel(str(file.crc)))
            left_side_layout.addWidget(QLabel(str(file.zflag)))
            left_side_layout.addWidget(QLabel(str(file.fileflag)))

            if file.file_structure:
                left_side_layout.addWidget(QLabel(file.file_structure.decode("utf-8")))
            left_side_layout.addWidget(QLabel(file.ext))

            splitter = QSplitter(Qt.Horizontal)
            splitter.addWidget(right_side)
            splitter.addWidget(left_side)

            showdialog = QWidget()
            showdialog_layout = QVBoxLayout(showdialog)
            showdialog.setWindowTitle("NPK Data")
            showdialog_layout.addWidget(splitter)

            notice_label = QLabel("Please report if there are any issues with the data displayed.")
            showdialog_layout.addWidget(notice_label)

            showdialog.setLayout(showdialog_layout)
            self.dialog = QDialog()
            self.dialog.setWindowTitle("File Information")
            self.dialog.setLayout(showdialog_layout)
            self.dialog.exec_()

        except Exception as e:
            print(f"Error displaying data: {e}")
            logger.critical(f"Error displaying data: {e}")
            QMessageBox.critical(self, "Error", f"Could not display file data:\n{e}")

    # def show_hex(self):
    #     self.window_hex = HexViewerApp(self.npkentries[self.selectednpkentry].data)
    #     self.window_hex.show()
    #     self.window_hex.raise_()

    def show_hex_data(self):
        try:
            selected_indexes = self.list.selectionModel().selectedIndexes()
            if not selected_indexes:
                print("No valid selection for hex data display.")
                logger.warning("No valid selection for hex data display.")
                return

            selected_index = selected_indexes[0]
            file_index = self.list.model().data(selected_index, Qt.UserRole)

            if file_index not in self.npkentries:
                print(f"Selected entry {file_index} not found for hex data.")
                logger.debug(f"Selected entry {selected_index} not found in npkentries.")
                return

            file = self.npkentries[file_index]

            hex_dialog = HexViewerApp(file.data)  # Adjust the class name if different
            hex_dialog.setWindowTitle(f"Hex Data - {hex(file.file_sign)}")
            hex_dialog.show()

        except Exception as e:
            print(f"Error displaying hex data: {e}")
            logger.critical(f"Error displaying hex data: {e}")
            QMessageBox.critical(self, "Error", f"Could not display hex data:\n{e}")

    def show_text(self):
        self.window_text = create_text_tab(self)
        # tab = create_text_tab(self)

        if not self.window_text:
            logger.warning("Text tab creation failed.")
            return
    
        # tab.show()
        self.window_text.show()
        # tab.raise_()
        self.window_text.raise_()

    def show_texture(self):
        selected_indexes = self.list.selectionModel().selectedIndexes()
        if not selected_indexes:
            print("No file selected for texture viewing.")
            logger.warning("No file selected for texture viewing.")
            return

        source_index = selected_indexes[0]
        file_index = self.list.model().data(source_index, Qt.UserRole)

        if file_index is None or not (0 <= file_index < len(self.npkentries)):
            print("Invalid file index for texture viewing.")
            logger.warning("Invalid file index for texture viewing.")
            return

        npk_entry = self.npkentries.get(file_index)
        if not npk_entry or not any(npk_entry.updated_name.lower().endswith(ext) for ext in self.allowed_texture_exts):
            print(f"'{npk_entry.updated_name}' is not a valid texture file.")
            logger.debug(f"'{npk_entry.updated_name}' is not a valid texture file.")
            return

        try:
            # Create a new TextureViewer instance if it doesn't already exist
            if not hasattr(self, "window_texture") or self.window_texture is None:
                self.window_texture = TextureViewer(npk_entry)  # Pass the NPK entry to the viewer
            else:
                # Update the existing instance with the new NPK entry
                self.window_texture.updateDisplay(npk_entry)

            # Display the texture
            self.window_texture.displayImage()  # Call the method to display the texture
            self.window_texture.show()
            self.window_texture.raise_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while loading the texture: {str(e)}")
            logger.critical(f"An error occurred while loading the texture: {str(e)}")


    def show_mesh(self):
        # Get all selected indexes from the QListView
        selected_indexes = self.list.selectionModel().selectedIndexes()
        if not selected_indexes:
            print("No file selected for mesh viewing.")
            logger.warning("No file selected for mesh viewing.")
            return

        for source_index in selected_indexes:
            # Retrieve the corresponding file index from the selected item
            file_index = self.list.model().data(source_index, Qt.UserRole)

            if file_index is None or not (0 <= file_index < len(self.npkentries)):
                print("Invalid file index for mesh viewing.")
                logger.debug("Invalid file index for mesh viewing.")
                continue

            # Get the NPK entry data
            npk_entry = self.npkentries.get(file_index)
            if not npk_entry or not any(npk_entry.updated_name.lower().endswith(ext) for ext in self.allowed_mesh_exts):
                print(f"'{npk_entry.updated_name}' is not a valid mesh file.")
                logger.debug(f"'{npk_entry.updated_name}' is not a valid mesh file.")
                continue
            # Focus on the loaded mesh and update the viewer
            self.window_mesh.viewer.focus_on_selected_object()
            self.window_mesh.viewer.update_aspect_ratio()
            self.update()

            # Bring the viewer to the front
            self.window_mesh.raise_()

        except Exception as e:
            # Show error message for any exceptions
            print(self, "Error", f"An error occurred: {str(e)}")
            try:
                # Parse the mesh data
                mesh = mesh_from_path(npk_entry.data)

                if not mesh:
                    raise ValueError("Failed to parse the mesh file.")

                # Load the mesh into the viewer
                self.window_mesh.viewer.load_mesh(mesh, self.get_savefile_location())
                self.window_mesh.viewer.focus_on_selected_object()
                self.window_mesh.viewer.update_aspect_ratio()

                # Ensure the mesh viewer window is displayed and raised
                self.update()
                self.window_mesh.raise_()

            except Exception as e:
                logger.critical(f"An error occurred while loading the mesh '{npk_entry.updated_name}': {str(e)}")

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
        open_folder_action.triggered.connect(partial(self.load_npk, "./utils/filename.json"))
        file_menu.addAction(open_folder_action)

    def create_help_menu(self):
        # About Menu Button
        about_menu = self.menuBar().addMenu("Help *")

        about_action = QAction(self.style().standardIcon(QStyle.SP_VistaShield), "About", self)
        about_action.setShortcut('Ctrl+H')
        about_action.setStatusTip("Open an about popup window")
        about_action.triggered.connect(self.show_about)
        about_menu.addAction(about_action)

    # Functionality
    # ----------------------------------------------------------------------------------------------------------
    def get_savefile_location(self):
        currnpk = self.npkentries[self.selectednpkentry]

        path = self.output_folder + "/" + os.path.basename(self.npk.path) + "/"
        if not currnpk.file_structure:
            os.makedirs(path, exist_ok=True)
            path = path  + hex(currnpk.file_sign) + "." + currnpk.ext

        else:
            filestructure = currnpk.file_structure.decode("utf-8").replace("\\", "/")
            path = path + os.path.dirname(filestructure)
            os.makedirs(path, exist_ok=True)
            path = path + "/" + os.path.basename(filestructure)

        return path

    def create_edit_menu(self):
        # Settings Menu Button
        settings_menu = self.menuBar().addMenu("Edit *")

        settings_action = QAction(self.style().standardIcon(QStyle.SP_VistaShield), "Preferences", self)
        settings_action.setShortcut('Ctrl+,')
        settings_action.setStatusTip("Open an about popup window")
        settings_action.triggered.connect(self.show_settings)
        settings_menu.addAction(settings_action)

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
            file_index = self.list.model().data(selected_index, Qt.UserRole)

            if file_index not in self.npkentries:
                logger.warning(f"No valid file index ({file_index}) found in npkentries.")
                return None

            currnpk = self.npkentries[file_index]

            # Construct the output path dynamically based on the NPK entry attributes
            base_path = os.path.join(self.output_folder, os.path.basename(self.npk.path))

            if currnpk.file_structure:
                filestructure = currnpk.file_structure.decode("utf-8").replace("\\", "/")
                folder_path = os.path.join(base_path, os.path.dirname(filestructure))
                os.makedirs(folder_path, exist_ok=True)
                file_path = os.path.join(folder_path, os.path.basename(filestructure))
            else:
                # Fallback if file_structure is empty
                os.makedirs(base_path, exist_ok=True)
                file_path = os.path.join(base_path, f"{hex(currnpk.file_sign)}.{currnpk.ext}")

            logger.info(f"Generated file path: {file_path}")
            return file_path

        except Exception as e:
            logger.critical(f"Error generating save file location: {e}")
            return None

    def extract_file(self):
        currnpk = self.npkentries[self.selectednpkentry]
        # self.progress_bar.setValue((currnpk + 1) * 100 // len(self.npk.index_table)) # Update progress bar

        path = self.get_savefile_location()

        with open(path, "wb") as f:
            f.write(currnpk.data)


    def set_output(self):
        file_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        self.output_folder = self.config_manager.set(f"output_folder", f"{os.path.basename(file_path)}")
        self.status_bar.showMessage(f'Output Folder: {file_path}.')
        logger.info(f'Output Folder: {file_path}.')


    def npk_config_data(self, config_file=None, force_new_file=False):
        """Load configuration data from a JSON file and save the last used config path."""
        # Check if a saved config path exists
        config_path_storage = "./utils/last_config.json"
        if not force_new_file and not config_file and os.path.exists(config_path_storage):
            try:
                with open(config_path_storage, "r") as storage_file:
                    saved_path = json.load(storage_file).get("last_used_config", None)
                    if saved_path and os.path.exists(saved_path):
                        config_file = saved_path
            except Exception as e:
                print(f"Error loading saved config path: {e}")
                logger.warning(f"Error loading saved config path: {e}")

        if not config_file or force_new_file:
            self.status_bar.showMessage('Choosing config file...')
            file_path = QFileDialog.getOpenFileName(self, "Choose file", filter="NPK Config (*.json)")[0]
            if file_path:
                config_file = file_path

        if config_file and config_file.endswith(".json"):
            try:
                # Load the JSON file
                with open(config_file, "r") as file:
                    data = json.load(file)
                    mapping = data.get("Data", {})

                    # Retrieve specific configuration values
                    game_config = mapping.get("game_config", None)
                    npk_type = mapping.get("npk_type", None)
                    decryption_key = mapping.get("decryption_key", None)
                    aes_key = mapping.get("aes_key", None)
                    index_size = mapping.get("index_size", None)

                    # Log the loaded configuration
                    print(f"Loaded Config: {game_config}\nNPK Type = {npk_type}\nDecryption key = {decryption_key}\n"
                        f"AES Key = {aes_key}\nIndex Size = {index_size}")
                    logger.info(f"Loaded Config: {game_config}\nNPK Type = {npk_type}\nDecryption Key = {decryption_key}\n"
                        f"AES Key = {aes_key}\nIndex Size = {index_size}")

                    #Update application state
                    self.game_config = game_config
                    self.decryption_key = decryption_key
                    self.npk_type = npk_type
                    self.aes_key = aes_key
                    self.index_size = index_size

                    # Save the last used config path
                    with open(config_path_storage, "w") as storage_file:
                        json.dump({"last_used_config": config_file}, storage_file)
                    # print(f"Saved last used config path: {config_file}")
                        
                # self.npk_type = self.config_manager.set("npk_type", {npk_type})
                # self.decryption_key = self.config_manager.set("npk_type", {decryption_key})
                # self.aes_key = self.config_manager.set("aes_key", {aes_key})
                # self.index_size = self.config_manager.set("npk_type", {index_size})

            except Exception as e:
                print(f"Error loading Config file: {e}")
                logger.critical(f"Error loading Config file: {e}")
        else:
            print("Invalid File", "Please select a valid JSON configuration file.")
            logger.warning("Please select a valid JSON configuration file.")


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


    def show_about(self):
        """Show the about popup window."""
        self.statusBar().showMessage("About...")

        # Load message from a text file
        try:
            with open("info/about_info.txt", 'r') as file:
                message = file.read()
        except FileNotFoundError:
            message = "Error: Message file not found."
        # Initialize the popup with the loaded message
        result, ok = QInputDialog().getInt(None, "Decryption Key", message, self.decryption_key, -1000,1000, 10)
        if ok:
            # Retrieve input text if the dialog was accepted
            self.decryption_key = result  # Store the input for future use
            self.config_manager.set("decryption_key", result)
            print(f"Decryption Key Entered: {self.decryption_key}")
        self.statusBar().showMessage(f"Decryption key set to {result}")

    def show_about_popup(self):
        """Show the about popup window."""
        self.statusBar().showMessage("About...")
            logger.debug(f"{message}\n Error: Message file not found.")

        # Initialize the popup with the loaded message
        popup = AboutPopup(message)
        popup.exec_()

    # Edit Tab
    def show_settings(self):
        """Show the settings window."""
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


    def load_npk(self, json_file):
        """Load an NPK file and populate the QListView."""
        self.clear_npk_data()
        self.status_bar.showMessage('Selecting file...')
        file_path = (QFileDialog.getOpenFileName(self, "Open file", filter="NPK Files (*.npk)")[0])
        if file_path and file_path[-4:] == ".npk":
            # self.status_bar.showMessage(f'Loading NPK: {file_path}')
            self.status_bar.showMessage(f'Loading NPK: {file_path}')
            print("Path is: {}".format(file_path))

            self.npk_file = io.BytesIO(open(file_path, 'rb').read())
            if read_index(self, file_path) != -1:

                currfile = 0
                for file in self.npk.index_table:
                    if not file[6]:
                        widgetitem = QListWidgetItem(hex(file[0]))
                    else:
                        widgetitem = QListWidgetItem(file[6].decode("utf-8"))
                    widgetitem.setData(3, currfile)
                    widgetitem.setData(4, False)
                    widgetitem.setIcon(self.style().standardIcon(QStyle.SP_DialogNoButton))
                    self.file_list_widget.addItem(widgetitem)
                    currfile += 1
                    self.progress_bar.setValue((currfile + 1) * 100 // len(self.npk.index_table)) # Update progress bar

                self.status_bar.showMessage(f'Finished loading NPK: {file_path}')
                self.file_list_widget.sortItems(Qt.AscendingOrder)
        else:
            self.status_bar.showMessage("Select NPK to extract!")
        self.file_list_widget.setCurrentRow(0)

    def read_all_npk_data(self):
        # Check viewer initialization
        if hasattr(self, "npk"):
            for x in range(self.file_list_widget.count()):
                item = self.file_list_widget.item(x)
                self.progress_bar.setValue((x + 1) * 100 // self.npk.files) # Update progress bar
                npkentry = read_entry(self, item.data(3))
                if npkentry.file_original_length == 0:
                    if npkentry.file_structure:
                        print(f"Index {npkentry.file_structure} is empty")
                    else:
                        print(f"Index {npkentry.file_sign} is empty")
                else:
                    if not bool(item.data(4)) and not npkentry.file_structure:
                        item.setText(item.text() + f".{npkentry.ext}")
                    item.setData(4, True)
                    self.npkentries[item.data(3)] = npkentry
                    item.setIcon(self.style().standardIcon(QStyle.SP_DialogYesButton))

            self.selectednpkentry = 0
            self.file_list_widget.setCurrentRow(0)

        else:
            QMessageBox.information(self, "Open NPK!", "You must open an NPK file before reading it!")
        
    def extract_all_npk_data(self):
        file_path = QFileDialog.getOpenFileName(self, "Open file", filter="NPK Files (*.npk)")[0]

        if file_path and file_path.endswith(".npk"):
            self.status_bar.showMessage(f'Loading NPK: {file_path}')
            try:
                self.npk_file = io.BytesIO(open(file_path, 'rb').read())
            except Exception as e:
                print(f"Failed to read NPK file: {str(e)}")
                logger.critical(f"Failed to read NPK file: {str(e)}")
                return

            if read_index(self, file_path) != -1:
                # print(f"NPK file parsed successfully with {len(self.npk.index_table)} entries.")
                
                model = QStandardItemModel()  # Create a new model for QListView

                for i, file in enumerate(self.npk.index_table):  # Assign sequential indices
                    try:
                        # Validate file entry
                        if not file or len(file) < 7:
                            print(f"Index {i}: Invalid or incomplete file data, skipping")
                            logger.warning(f"Index {i}: Invalid or incomplete file data, skipping")
                            continue

                        self.progress_bar.setValue((i + 1) * 100 // len(self.npk.index_table))  # Update progress bar

                        # Generate hash_value from file data
                        hash_value = hex(file[0]) if not file[6] else file[6].decode("utf-8")

                        # Create a new item for each entry
                        item = QStandardItem(hash_value)
                        item.setData(i, Qt.UserRole)  # Store file index in UserRole
                        item.setData(i, 3)  # Assign sequential index for compatibility
                        # item.setIcon(self.style().standardIcon(QStyle.SP_DialogNoButton))  # Default icon
                        item.setIcon(QIcon.fromTheme("dialog-no"))  # Use a theme-based icon
                        model.appendRow(item)

                    except Exception as e:
                        print(f"Index {i}: Failed to process entry - {str(e)}")
                        logger.critical(f"Index {i}: Failed to process entry - {str(e)}")
                        continue

                self.list.setModel(model)  # Assign the model to QListView

                self.read_all_npk_data(json_file)  # Process all NPK data

                logger.debug(f"Info Size: {determine_info_size(self)}") # Print out info_size

                #Temp. updating config info
                # ______________________________________________________
                # self.update_config_data(os.path.basename("./utils/npk_config.json"), "Data", "npk_type", 0) # update config entry - temp
                # self.npk_type = self.config_manager.set("npk_type", 0)
                # self.npk_type = self.config_manager.set("aes_key", 1)
                # self.npk_type = self.config_manager.set("index_size", 2)
                # _______________________________________________________

                # self.status_bar.showMessage(f'Finished loading NPK: {file_path}')
                self.setWindowTitle(f"NeoXtractor | {os.path.abspath(file_path)}")
            else:
                self.status_bar.showMessage("Failed to parse NPK file.")
        else:
            self.status_bar.showMessage("Select a valid NPK file!")


    def read_all_npk_data(self, json_file):
        if not hasattr(self, "npk"):
            QMessageBox.information(self, "Open NPK!", "You must open an NPK file first!")
            logger.info("Open NPK!", "You must open an NPK file first!")
            return

        model = self.list.model()
        if model is None:
            print("No list-model set for the list view.")
            logger.critical("No list-model set for the list view.")
            return
        
        # Load JSON file for filename mapping (IDV*)
        try:
            with open(json_file, "r") as file:
                data = json.load(file)
                hash_mapping = data.get("characters", {})
                ViewerWidget.json_mapping = hash_mapping
                # print(f"Loaded JSON: {hash_mapping}")
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            logger.debug(f"Error loading JSON file: {e}")
            return

        for x in range(model.rowCount()):
            try:
                item = model.item(x)
                if not item:
                    continue

                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Disable editing
                fileindex = item.data(3)  # Retrieve file index

                if fileindex is None or not (0 <= fileindex < len(self.npk.index_table)):
                    # print(f"Row {x}: Invalid file index {fileindex}, skipping")
                    continue

                npkentry = read_entry(self, fileindex)
                self.progress_bar.setValue((x + 1) * 100 // len(self.npk.index_table))  # Update progress bar

                if npkentry.file_original_length == 0:
                    print(f"Index {fileindex} is empty")
                    logger.debug(f"Index {fileindex} is empty")
                    continue

                # Update filename
                original_filename = item.text()
                updated_filename = hash_mapping.get(original_filename, original_filename)
                if not npkentry.file_structure:
                    updated_filename += f".{npkentry.ext or 'bin'}"

                item.setText(updated_filename)
                npkentry.updated_name = updated_filename  # Store updated name in npkentry
                self.npkentries[fileindex] = npkentry

                item.setIcon(self.style().standardIcon(QStyle.SP_DialogYesButton))  # Success icon
            except Exception as e:
                print(f"Failed to process entry at row {x}: {e}")
                logger.debug(f"Failed to process entry at row {x}: {e}")
                item.setIcon(self.style().standardIcon(QStyle.SP_DialogNoButton))  # Failure icon

    def read_selected_npk_data(self):
        # Check if there are selected entries
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            print(self, "No Selection", "Please select files to read.")
            return

        # Loop through the selected items
        for item in selected_items:
            index = int(item.data(3))

            # Check if the file is already processed
            if index in self.npkentries:
                print(f"File at index {index} is already processed.")
                continue

            # Read the entry
            npkentry = read_entry(self, index)

            # Check if the file is empty
            if npkentry.file_original_length == 0:
                print(f"Index {index} is empty.")
            else:
                # Update item text and icon if necessary
                if not bool(item.data(4)) and not npkentry.file_structure:
                    item.setText(item.text() + f".{npkentry.ext}")
                item.setData(4, True)
                self.npkentries[index] = npkentry
                # self.progress_bar.setValue((index + 1) * 100 // self.npk.files) # Update progress bar
                item.setIcon(self.style().standardIcon(QStyle.SP_DialogYesButton))

        # Optionally set the last processed entry as the selected one
        if selected_items:
            self.selectednpkentry = int(selected_items[-1].data(3))

        # Refresh List
        self.refresh_file_list()

        QMessageBox.information(self, "Success", f"Processed {len(selected_items)} selected files.")

    def extract_selected_npk_data(self):
        if hasattr(self, "npk"):
            for index in self.npkentries:
                currnpk = self.npkentries[index]
                path = f"{self.output_folder}" + "/" + os.path.basename(f"{self.npk.path}") + "/"
                if not currnpk.file_structure:
                    os.makedirs(path, exist_ok=True)
                    path = path + hex(currnpk.file_sign) + "." + currnpk.ext
                else:
                    filestructure = currnpk.file_structure.decode("utf-8").replace("\\", "/")
                    path = path + os.path.dirname(filestructure)
                    os.makedirs(path, exist_ok=True)
                    path = path + "/" + os.path.basename(filestructure)

                with open(path, "wb") as f:
                    f.write(currnpk.data)
                try:
                    with open(path, "wb") as f:
                        f.write(currnpk.data)

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
            QMessageBox.information(self, "Finished!", f"Saved {len(self.npkentries)} files to \"{self.output_folder}\" folder")
        else:
            QMessageBox.information(self, "Open NPK first", "You must open an NPK file before extracting it!")

    def extract_loaded_Textures(self):
        if hasattr(self, "npk"):
            # allowed_extensions = {".dds", ".png"}  # Define allowed texture extensions
            saved_count = 0 

            # Iterate through all items in the file list widget
            for i in range(self.file_list_widget.count()):
                item = self.file_list_widget.item(i)
                
                # Retrieve the corresponding npk entry using the item's data
                index = item.data(3)
                currnpk = self.npkentries.get(index)

                if not currnpk:
                    continue

                if currnpk.ext.lower() not in self.allowed_texture_exts:
                    continue

                # Build the output path
                base_path = os.path.join(self.output_folder, os.path.basename(self.npk.path))
                if not currnpk.file_structure:
                    os.makedirs(base_path, exist_ok=True)
                    output_path = os.path.join(base_path, f"{hex(currnpk.file_sign)}.{currnpk.ext}")
                else:
                    filestructure = currnpk.file_structure.decode("utf-8").replace("\\", "/")
                    output_dir = os.path.join(base_path, os.path.dirname(filestructure))
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(output_dir, os.path.basename(filestructure))

                # Save the file and handle errors
                try:
                    with open(output_path, "wb") as f:
                        f.write(currnpk.data)
                    saved_count += 1
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

            # Show a final message indicating the number of saved files
            if saved_count > 0:
                QMessageBox.information(self, "Finished!", f"Saved {saved_count} texture files to \"{self.output_folder}\" folder")
            else:
                print(self, "No Files Saved", "No valid texture files were saved.")
        else:
            QMessageBox.information(self, "Open NPK first", "You must open an NPK file before extracting it!")


    def clear_npk_data(self):
        self.file_list_widget.clear()
                try:
                    with open(path, "wb") as f:
                        f.write(currnpk.data)

                except Exception as e:
                    print(f"Failed to save file: {str(e)}")
                    logger.critical(f"Failed to save file: {str(e)}")
            QMessageBox.information(self, "Finished!",
                                    f"Saved {len(self.npkentries)} files to \"{self.output_folder}\" folder")
            logger.info(f"Finished!", f"Saved {len(self.npkentries)} files to \"{self.output_folder}\" folder")

        else:
            QMessageBox.information(self, "Open NPK first", "You must open an NPK file before extracting it!")
            logger.info("Open NPK first", "You must open an NPK file before extracting it!")


    def clear_npk_data(self):
        self.filter_input.clear()
        self.selectednpkentry = 0
        self.npkentries.clear()
        if hasattr(self, "npk"):
            self.npk.clear()
        self.npkentry = None

    def on_item_clicked(self, item):
        # Retrieve the index of the clicked item
        index = int(item.data(3))
        # Check if the item index is in the viewer's entries
        if index not in self.npkentries:
            # Read the entry corresponding to the index
            npkentry = read_entry(self, index)

            if npkentry.file_original_length == 0:
                print(f"This index is empty")
            else:
                # Update item text and data if necessary
                if not bool(item.data(4)) and not npkentry.file_structure:
                    item.setText(item.text() + f".{npkentry.ext}")
                item.setData(4, True)
                self.npkentries[index] = npkentry
                item.setIcon(self.style().standardIcon(QStyle.SP_DialogYesButton))
        self.update()
        self.selectednpkentry = index

        # Optional: Collect all selected items (if required)
        selected_items = [self.npkentries[i] for i in self.npkentries if i == index]
        # print(f"Selected Items: {index}")

    def on_item_double_clicked(self, item):
        """Open the mesh viewer when a mesh or texure file is double-clicked."""
        # Extract file name and check extension
        selected_file = item.text()

        # Combine allowed extensions
        allowed_extensions = tuple(self.allowed_texture_exts + self.allowed_mesh_exts + self.allowed_text_ext)
        if not selected_file.lower().endswith(allowed_extensions):
            QMessageBox.warning(
                self,
                "Invalid File",
                f"'{selected_file}' is not supported in the Mesh/Texture Viewer.\nAllowed types: {', '.join(allowed_extensions)}."
            )
            return
        try:
            # Determine the type of file and simulate user action
            if any(selected_file.lower().endswith(ext) for ext in self.allowed_mesh_exts):
                self.show_mesh()
            elif any(selected_file.lower().endswith(ext) for ext in self.allowed_texture_exts):
                self.show_texture()
            elif any(selected_file.lower().endswith(ext) for ext in self.allowed_text_ext):
                self.show_text()
        except Exception as e:
            # QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            print(self, "Error", f"An error occurred: {str(e)}")

    def on_selection_changed(self):
        # Get all selected items
        selected_items = self.file_list_widget.selectedItems()

        # Process selected items
        selected_indexes = [int(item.data(3)) for item in selected_items]  # Retrieve the indexes stored in role 3

        # Optionally process selected entries
        selected_entries = [self.npkentries.get(index) for index in selected_indexes if index in self.npkentries]

        self.selectednpkentry = selected_indexes[-1] if selected_indexes else None

    def refresh_file_list(self):
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            index = int(item.data(3))  # Retrieve the index stored in role 3

            # Check if the item is already processed
            if index in self.npkentries:
                npkentry = self.npkentries[index]
                # Update text and icon based on npkentry state
                if not bool(item.data(4)) and not npkentry.file_structure:
                    item.setText(item.text() + f".{npkentry.ext}")
                    self.progress_bar.setValue((index + 1) * 100 // self.npk.files) # Update progress bar

                item.setIcon(self.style().standardIcon(QStyle.SP_DialogYesButton))
                item.setData(4, True)  # Mark as processed
        else:
            self.update()

    def append_console_output(self, text: str):
        """Appends text to the console output."""
        if hasattr(self.console_handler, 'text_output'):
            self.console_handler.text_output.emit(text)
        else:
            print("Console handler is not properly initialized.")

    def on_item_double_clicked(self, index):
        if not index.isValid():
            print("Invalid index.")
            logger.warning("Invalid index.")
            return

        file_index = self.list.model().data(index, Qt.UserRole)
        if file_index is None or not (0 <= file_index < len(self.npkentries)):
            print("No file index data associated.")
            logger.warning("No file index data associated.")
            return

        npk_entry = self.npkentries.get(file_index)
        if not npk_entry:
            print(f"No entry found for index {file_index}.")
            logger.debug(f"No entry found for index {file_index}.")
            return

        # Action based on file type
        if any(npk_entry.updated_name.lower().endswith(ext) for ext in self.allowed_mesh_exts):
            self.show_mesh()
            self.window_mesh.viewer.filename = npk_entry.updated_name.lower() # Filename to mesh viewer
            self.window_mesh.viewer.filepath = self.list.selectionModel().selectedIndexes()
        elif any(npk_entry.updated_name.lower().endswith(ext) for ext in self.allowed_texture_exts):
            self.show_texture()
        elif any(npk_entry.updated_name.lower().endswith(ext) for ext in self.allowed_text_exts):
            self.show_text()
        else:
            print(f"Unsupported file type: {npk_entry.updated_name}")
            logger.debug(f"Unsupported file type: {npk_entry.updated_name}")

    def on_selection_changed(self):
        selected_indexes = self.list.selectionModel().selectedIndexes()
        for proxy_index in selected_indexes:
            source_index = self.proxy_model.mapToSource(proxy_index)
            if not source_index.isValid():
                continue

            file_index = self.list_model.data(source_index, Qt.ItemDataRole.UserRole)
            if file_index:
                print(f"Selected: {file_index['name']} (Index: {file_index['index']})")
                logger.debug(f"Selected: {file_index['name']} (Index: {file_index['index']})")

    def filter_list_items(self):
        """Filter QListView items based on user input from QLineEdit and QComboBox."""
        model = self.list.model()
        if model is None:
            logger.warning("No list-model set for filtering.")
            return

        search_string = self.filter_input.text().strip().lower()  # Get text input
        category = self.filter_combobox.currentText()  # Get selected category

        for row in range(model.rowCount()):
            item = model.item(row)
            file_index = item.data(Qt.UserRole)

            if file_index is None or file_index not in self.npkentries:
                self.list.setRowHidden(row, True)
                continue

            npk_entry = self.npkentries[file_index]

            # file_path = os.path.join(self.output_folder, npk_entry.updated_name)
            # file_path = os.path.join(self.npkentries, npk_entry.updated_name)

            # Apply text filtering
            text_match = not search_string or search_string in npk_entry.updated_name.lower()

            # Apply category filtering
            category_match = False
            if category == "ALL":
                category_match = True
            elif category == "MESH" and npk_entry.updated_name.lower().endswith(tuple(self.allowed_mesh_exts)):
                category_match = True
            elif category == "TEXTURE" and npk_entry.updated_name.lower().endswith(tuple(self.allowed_texture_exts)):
                category_match = True
            elif category == "CHARACTER" and "character" in npk_entry.updated_name.lower():
                category_match = True
            elif category == "SKIN" and "skin" in npk_entry.updated_name.lower():
                category_match = True
            elif category == "TEXT FORMAT" and npk_entry.updated_name.lower().endswith(tuple(self.allowed_text_exts)):
                category_match = True
            
            # If filtering for MESH, apply additional ransack filtering (from filepath)
            # if category == "MESH" and category_match:
            #     if not self.ransack_agent(file_path, "biped head"):
            #         category_match = False

            # If filtering for MESH and checkbox is enabled, apply additional ransack filtering (in-memory scan)
            if self.filtered_mesh_checkbox.isChecked():
                if category == "MESH" and category_match:
                    if not self.ransack_agent(npk_entry.data, "biped head"):  # Scan in-memory data
                        category_match = False

            # Hide or show based on filtering
            self.list.setRowHidden(row, not (text_match and category_match))

    # For file path
    # def ransack_agent(self, file_path, search_string):
    #     """Check if the given search_string is present in the specified file."""
    #     try:
    #         with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
    #             return search_string in file.read()
    #     except Exception as e:
    #         logger.warning(f"Error reading {file_path}: {e}")
    #         return False

    def ransack_agent(self, data, search_string):
        """Check if the given search_string is present in the in-memory NPK entry data."""
        try:
            if isinstance(data, bytes):  # Convert binary data to string for searching
                data = data.decode('utf-8', errors='ignore')

            return search_string in data.lower()
        except Exception as e:
            logger.warning(f"Error scanning in-memory data: {e}")
            return False

def main():
    app = QApplication(sys.argv)
    app.setPalette(qt_theme.palettes()["dark"]) # Set the dark palette
    app.setStyleSheet(qt_theme.style_modern()) # Apply the dark theme stylesheet
    main_window = MainWindow()
    main_window.show()
    logger.info("Application started")
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
