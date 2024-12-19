import sys, os, io, time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from utils.config_manager import ConfigManager
from utils.console_handler import *
from utils.util import *
from utils.extractor_utils import read_index, read_entry

from gui.viewer_3d import ViewerWidget
from gui.main_window import *
# from gui.main_window import create_main_viewer_tab
from gui.mesh_tab import create_mesh_viewer_tab
# from gui.extraction_tab import create_extraction_tab
from gui.texture_tab import create_texture_tab
from gui.text_tab import create_text_tab
from gui.raw_hex_viewer import HexViewerApp
from gui.popups import AboutPopup

# from bin.read_nxfn import NxfnResultViewer
from converter import * # saveobj, savesmd, saveascii, savepmx, saveiqe, parse_mesh_original, parse_mesh_helper, parse_mesh_adaptive


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('NeoXtractor')
        self.setGeometry(150, 50, 1600, 950)
        self.npkentries = dict()
        self.config_manager = ConfigManager() # Fetch Output folder from config manager
        self.decryption_key = self.config_manager.get("decryption_key", 150)
        self.output_folder = self.config_manager.get("output_folder", "out")
        self.project_folder = self.config_manager.get("project_folder", "")

        # Initialize the console output handler
        self.console_handler = ConsoleOutputHandler()
        redirect_output(self.console_handler)  # Redirect stdout and stderr

        self.main_console = ConsoleWidget(self.console_handler)
        self.console_handler.add_console(self.main_console.console_output)

        # Initialize the rest of the UI
        self.initUI()

    def closeEvent(self, a0):
        self.window_mesh.thread().quit()
        return super().closeEvent(a0)

    def eventFilter(self, source, event):
        if event.type() == QEvent.ContextMenu and source is self.file_list_widget:
            list_context_menu = QMenu()
            showdata_action = QAction("Show Data", self)
            showdata_action.triggered.connect(self.show_data)
            export_action = QAction("Export File", self)
            export_action.triggered.connect(self.extract_file)
            exp_texture_action = QAction("Export Only Texture", self)
            exp_texture_action.triggered.connect(self.extract_loaded_Textures)
            hex_action = QAction("Hex Viewer", self)
            hex_action.triggered.connect(self.show_hex)
            text_action = QAction("Plaintext Viewer", self)
            text_action.triggered.connect(self.show_text)
            texture_action = QAction("Texture Viewer", self)
            texture_action.triggered.connect(self.show_texture)
            mesh_action = QAction("Mesh Viewer", self)
            mesh_action.triggered.connect(self.show_mesh)
            list_context_menu.addAction(showdata_action)
            list_context_menu.addAction(export_action)
            list_context_menu.addAction(exp_texture_action)
            list_context_menu.addAction(hex_action)
            list_context_menu.addAction(text_action)
            list_context_menu.addAction(texture_action)
            list_context_menu.addAction(mesh_action)

            list_context_menu.exec_(event.globalPos())
        return True

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

        # Connect double-click signal
        self.file_list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

        # Create other menus and UI components
        self.create_file_menu()
        self.create_help_menu()

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

    def show_text(self):
        self.window_text = create_text_tab(self)
        self.window_text.show()
        self.window_text.raise_()

    def show_texture(self):
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No File Selected", "Please select a file to view in the Texture Viewer.")
            return

        # Extract the file name from the selected item
        selected_file = selected_items[0].text()

        # Define the set of allowed file extensions
        allowed_extensions = {".png", ".jpg", ".dds", ".ktx", ".pvr", ".astc", ".tga", "bmp"}

        if not any(selected_file.lower().endswith(ext) for ext in allowed_extensions):
            QMessageBox.warning(self, "Invalid File", f"'{selected_file}' is not supported in the Texture Viewer. \nAllowed types: {', '.join(allowed_extensions)}.")
            return

        try:
            # Create a new tab or window for the texture viewer
            self.window_texture = create_texture_tab(self)  # Assuming `create_texture_tab` returns the texture viewer.
            self.window_texture.show()
            self.window_texture.raise_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while loading the texture: {str(e)}")

    def show_mesh(self):
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No File Selected", "Please select a file to view in the Mesh Viewer.")
            return

        # Extract the file name from the selected item
        selected_file = selected_items[0].text()

        allowed_extensions = {".mesh"}

        if not any(selected_file.lower().endswith(ext) for ext in allowed_extensions):
            QMessageBox.warning(self, "Invalid File", f"'{selected_file}' is not supported in the Mesh Viewer. \nAllowed type: {', '.join(allowed_extensions)}.")
            return
        
        try:
            # Get mesh data from the selected .npk entry
            mesh_data = self.npkentries[self.selectednpkentry].data

            # Parse the mesh data
            mesh = mesh_from_path(mesh_data)

            if not mesh:
                raise ValueError("Failed to parse the mesh file.")

            # Load mesh into the viewer
            with io.BytesIO(mesh_data) as mesh_buffer:
                savefile_location = self.get_savefile_location()
                self.window_mesh.viewer.load_mesh(mesh, savefile_location)

            # Focus on the loaded mesh and update the viewer
            self.window_mesh.viewer.focus_on_selected_object()
            self.window_mesh.viewer.update_aspect_ratio()
            self.update()

            # Bring the viewer to the front
            self.window_mesh.raise_()

        except Exception as e:
            # Show error message for any exceptions
            QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")

    # Main Toolbar       
    # ----------------------------------------------------------------------------------------------------------
    def create_file_menu(self):
        # File Menu Button
        file_menu = self.menuBar().addMenu("File")

        # Using a standard Qt icon for the "Open Folder" action
        create_action = QAction(self.style().standardIcon(QStyle.SP_FileIcon), "Create Project", self)
        create_action.setStatusTip("Choose source directory")
        create_action.setShortcut('Ctrl+N')
        file_menu.addAction(create_action)

        open_folder_action = QAction(self.style().standardIcon(QStyle.SP_DirOpenIcon), "Open File", self)
        open_folder_action.setStatusTip("Choose File")
        open_folder_action.setShortcut("Ctrl+O")
        open_folder_action.triggered.connect(self.load_npk)
        file_menu.addAction(open_folder_action)

        dkey_action = QAction(self.style().standardIcon(QStyle.SP_VistaShield), "Decryption Key", self)
        dkey_action.setStatusTip("Open a decryption key popup")
        dkey_action.setShortcut("Ctrl+D")
        dkey_action.triggered.connect(self.show_decrypt_popup)  # Connect to the show popup function
        file_menu.addAction(dkey_action)

    def create_help_menu(self):
        # About Menu Button
        about_menu = self.menuBar().addMenu("Help *")

        about_action = QAction(self.style().standardIcon(QStyle.SP_VistaShield), "About", self)
        about_action.setShortcut('Ctrl+H')
        about_action.setStatusTip("Open an about popup window")
        about_action.triggered.connect(self.show_about_popup)
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

    def extract_file(self):
        currnpk = self.npkentries[self.selectednpkentry]
        # self.progress_bar.setValue((currnpk + 1) * 100 // len(self.npk.index_table)) # Update progress bar

        path = self.get_savefile_location()

        with open(path, "wb") as f:
            f.write(currnpk.data)

    def show_decrypt_popup(self):

        #"""Show the decryption manager popup window."""
        self.statusBar().showMessage("Entering Decryption Key...")

        # Load message from a text file
        try:
            with open("info/decryption_manager_info.txt", 'r') as file:
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

        # Load message from a text file
        try:
            with open("info/about_info.txt", 'r') as file:
                message = file.read()
        except FileNotFoundError:
            message = "Error: Message file not found."

        # Initialize the popup with the loaded message
        popup = AboutPopup(message)
        popup.exec_()

    def load_npk(self):
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

    def read_selected_npk_data(self):
        # Check if there are selected entries
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select files to read.")
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
                path = self.output_folder + "/" + os.path.basename(self.npk.path) + "/"
                if not currnpk.file_structure:
                    os.makedirs(path, exist_ok=True)
                    path = path  + hex(currnpk.file_sign) + "." + currnpk.ext

                else:
                    filestructure = currnpk.file_structure.decode("utf-8").replace("\\", "/")
                    path = path + os.path.dirname(filestructure)
                    os.makedirs(path, exist_ok=True)
                    path = path + "/" + os.path.basename(filestructure)

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
            allowed_extensions = {".dds", ".png"}  # Define allowed texture extensions
            saved_count = 0 

            # Iterate through all items in the file list widget
            for i in range(self.file_list_widget.count()):
                item = self.file_list_widget.item(i)
                
                # Retrieve the corresponding npk entry using the item's data
                index = item.data(3)
                currnpk = self.npkentries.get(index)

                if not currnpk:
                    continue

                if currnpk.ext.lower() not in allowed_extensions:
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
                QMessageBox.warning(self, "No Files Saved", "No valid texture files were saved.")
        else:
            QMessageBox.information(self, "Open NPK first", "You must open an NPK file before extracting it!")


    def clear_npk_data(self):
        self.file_list_widget.clear()
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
        """Open the mesh viewer when a .mesh file is double-clicked."""
        # Extract file name and check extension
        selected_file = item.text()

        allowed_extensions = {".mesh"}
        if not any(selected_file.lower().endswith(ext) for ext in allowed_extensions):
            QMessageBox.warning(self, "Invalid File", f"'{selected_file}' is not supported in the Mesh Viewer. \nAllowed type: {', '.join(allowed_extensions)}.")
            return

        try:
            # Simulate the user clicking the "Mesh Viewer" option
            self.show_mesh()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")


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


    def filter_list_items(self, text):
        """Filter items in the QListWidget based on input text."""
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
