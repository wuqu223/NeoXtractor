from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from gui.widgets.viewer_3d import ViewerWidget
from utils.console_handler import *
from utils.util import *
from converter import *
import os

from logger import logger

class FileSelector:
    @staticmethod
    def select_file():
        file_name, _ = QFileDialog.getOpenFileName(
            None, "Select File", "", "Mesh Files (*.mesh)"
        )
        return file_name

class MeshListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        """Handles key events for navigation in the mesh list."""
        if event.key() == Qt.Key_Down:
            selected_indexes = self.selectedIndexes()

            if selected_indexes:
                current_index = selected_indexes[0]
                next_index = self.model().index(current_index.row() + 1, 0)

                if next_index.isValid():
                    self.setCurrentIndex(next_index)  # Move selection down
                    self.itemActivated.emit(self.item(next_index.row()))  # Simulate double-click

        elif event.key() == Qt.Key_Up:
            selected_indexes = self.selectedIndexes()

            if selected_indexes:
                current_index = selected_indexes[0]
                prev_index = self.model().index(current_index.row() - 1, 0)

                if prev_index.isValid():
                    self.setCurrentIndex(prev_index)  # Move selection up
                    self.itemActivated.emit(self.item(prev_index.row()))  # Simulate double-click

        else:
            super().keyPressEvent(event)  # Handle other key events normally


def show_input_dialog(title, text):
    dialogue_response, dialogue_complete = QInputDialog.getText(
        None, title, text, QLineEdit.Normal, ""
    )
    return dialogue_response if dialogue_complete else ""

class MeshViewer(QMainWindow):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setGeometry(350, 150, 1400, 800)
        self.setWindowTitle("Mesh Viewer")

        # Main Container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left Side: File List Setup
        self.mesh_list_widget = MeshListWidget()  # Use the subclassed list view
        self.mesh_list_widget.setAcceptDrops(True)
        self.mesh_list_widget.setFixedWidth(400)
        self.mesh_list_widget.setToolTip("List of .mesh files in the loaded folder.")
        main_layout.addWidget(self.mesh_list_widget)

        # Connect the signals to the handlers
        self.mesh_list_widget.itemDoubleClicked.connect(self.on_mesh_item_double_clicked)
        self.mesh_list_widget.itemActivated.connect(self.on_mesh_item_double_clicked)  # process index using up and down arrow

        # Right Side: Viewer and Controls
        right_side = QVBoxLayout()
        
        # Viewer Widget
        self.viewer = ViewerWidget(self)  # Placeholder for Mesh Viewer
        self.viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.viewer.setMinimumSize(QSize(400, 400))
        right_side.addWidget(self.viewer)

        # Viewport Navigation Label
        navigation_label = QLabel(
            "Fly mode:  W: Forward  |  A: Left  |  S: Backward  |  D: Right  |  Shift+Key: Sprint  |  Ctrl+'1,3,7': Flip View  |  'F' Key: Focus Object"
        )
        navigation_label.setFixedHeight(20)
        right_side.addWidget(navigation_label)

        # Flip UV Checkbox
        self.flip_uv_checkbox = QCheckBox('Flip UVs on Save (V-axis)')
        self.flip_uv_checkbox.setChecked(False)
        right_side.addWidget(self.flip_uv_checkbox)

        # Default value if the scene isn't initialized yet
        default_zoom_speed = 1.0  # Default value if scene is None

        if self.viewer and self.viewer.scene and self.viewer.scene.camera:
            default_zoom_speed = self.viewer.scene.camera.zoom_speed

        # Zoom Speed Slider
        self.zoom_speed_label = QLabel(f"Camera Zoom Speed Control: {default_zoom_speed:.2f}")
        self.zoom_speed_label.setFixedHeight(15)
        right_side.addWidget(self.zoom_speed_label)

        self.zoom_speed_slider = QSlider(Qt.Horizontal)
        self.zoom_speed_slider.setRange(1, 100)  # Range: 1 to 100
        self.zoom_speed_slider.setValue(20)  # Default speed
        self.zoom_speed_slider.setFixedWidth(300)
        right_side.addWidget(self.zoom_speed_slider)
        self.zoom_speed_slider.valueChanged.connect(lambda value: self.viewer.set_zoom_speed(value))
        self.zoom_speed_slider.valueChanged.connect(self.update_zoom_label)

        # Add Right Side to Main Layout
        main_layout.addLayout(right_side)

        # Create Menus
        self.create_open_menu()
        self.create_save_menu()
        self.create_view_menu()

    def on_mesh_item_double_clicked(self, item):
        """Handle double-click event to load mesh into the viewer."""
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.isfile(file_path):
            try:
                load_mesh(self, file_path)
                print(f"Mesh loaded: {file_path}")
                logger.debug(f"Mesh loaded: {file_path}")
            except Exception as e:
                logger.critical(self, "Error", f"Failed to load mesh file: {str(e)}")
    
    def update_zoom_label(self, value):
        """Update the zoom speed label dynamically."""
        zoom_speed = value / 10.0  # Normalize zoom speed
        if self.viewer and self.viewer.scene and self.viewer.scene.camera:
            self.viewer.scene.camera.set_zoom_speed(zoom_speed)  # Ensure camera is initialized
        self.zoom_speed_label.setText(f"Camera Zoom Speed Control: {zoom_speed:.2f}")
    
    def create_view_menu(self):
        view_menu = self.menuBar().addMenu("View")

        def add_menu_action(name, shortcut, callback, checkable=False, default_checked=False):
            action = QAction(name, self)
            action.setShortcut(shortcut)
            action.setCheckable(checkable)
            action.setChecked(default_checked)
            action.triggered.connect(callback)
            view_menu.addAction(action)

        add_menu_action("Show Bones", "Alt+B", lambda checked: self.viewer.toggle_bone_visibility(checked), True, True)
        add_menu_action("Wireframe Mode", "Alt+W", lambda checked: self.viewer.toggle_wireframe_mode(checked), True, False)
        add_menu_action("Show Normals", "Alt+N", lambda checked: self.viewer.toggle_normals_visibility(checked), True, False)
        add_menu_action("Enable Face Culling", "Alt+C", lambda checked: self.viewer.toggle_culling_mode(checked), True, False)
        add_menu_action("Show Overlay Text", "Alt+O", lambda checked: self.viewer.toggle_overlay_text(checked), True, True)

    def create_save_menu(self):
        save_menu = self.menuBar().addMenu("Save")
        
        ischecked = self.flip_uv_checkbox.isChecked()

        save_actions = [
            ("FBX - Coming Soon", "Ctrl+Shift+F",
            lambda: QMessageBox.information(self, "Coming Soon", "FBX support is not implemented yet.")),
            ("GLTF2", "Ctrl+Shift+G", self.viewer.save_mesh_gltf),
            ("OBJ", "Ctrl+Shift+O", lambda: self.viewer.save_mesh_obj(ischecked)),
            ("SMD", "Ctrl+Shift+S", lambda: self.viewer.save_mesh_smd(ischecked)),
            ("ASCII", "Ctrl+Shift+A", lambda: self.viewer.save_mesh_ascii(ischecked)),
            ("PMX", "Ctrl+Shift+P", self.viewer.save_mesh_pmx),
            ("IQE", "Ctrl+Shift+I", self.viewer.save_mesh_iqe),
        ]

        for label, shortcut, func in save_actions:
            action = QAction(f"Save as {label}", self)
            action.setShortcut(shortcut)
            action.triggered.connect(func)
            save_menu.addAction(action)

    def create_open_menu(self):
        open_menu = self.menuBar().addMenu("Open")
        open_action = QAction("Open file (.mesh)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(lambda: openFile(self))
        open_menu.addAction(open_action)

        # Open folder and filter .mesh files
        open_folder_action = QAction("Open Folder (Filter .mesh)", self)
        open_folder_action.setShortcut("Ctrl+Shift+O")
        open_folder_action.triggered.connect(lambda: openFolder(self))
        open_menu.addAction(open_folder_action)
    
    def update_zoom_speed(self):
        if hasattr(self.viewer.scene, "camera"):
            zoom_speed = self.zoom_speed_slider.value() / 30.0
            self.viewer.scene.camera.zoom_speed = zoom_speed
            self.statusBar().showMessage(f"Zoom Speed: {zoom_speed:.1f}")
        else:
            self.statusBar().showMessage("No camera available to adjust zoom speed.")

# For backward compatibility
def create_mesh_viewer_tab(self):
    if hasattr(self, "window_mesh") and self.window_mesh is not None:
        return self.window_mesh  # Reuse existing instance
    
    self.window_mesh = MeshViewer(self)
    return self.window_mesh

def openFile(tab1):
    file_name = FileSelector.select_file()
    if not file_name:
        return
    
    tab1.viewer.filename = os.path.realpath(os.path.basename(file_name)) # Filename for open mesh
    tab1.viewer.mesh_version = os.path.realpath(file_name)

    try:
        # Try to read the file as a string
        with open(file_name, 'r', encoding='utf-8') as f:
            file_content = f.read()
        print("File successfully read as string.")
        logger.debug("File successfully read as string within the Mesh Window List View.")
    except Exception as e:
        print(f"Failed to read as string: {e}")
        logger.debug(f"Failed to read as string: {e}")
        try:
            # If reading as a string fails, try reading as bytes
            with open(file_name, 'rb') as f:
                file_content = f.read()
            print("File successfully read as bytes.")
            logger.debug("File successfully read as bytes within the Mesh Window List View.")
        except Exception as e:
            print(f"Failed to read as bytes: {e}")
            logger.debug(f"Failed to read as bytes: {e}")
            return

    # Pass the file content to the mesh loader function
    load_mesh(tab1, file_content)
    if file_name:
        load_mesh(tab1, file_name)

def openFolder(tab1):
    """Open a folder, filter .mesh files, and display them in mesh_list_widget."""
    folder_path = QFileDialog.getExistingDirectory(None, "Select Folder")

    if not folder_path:
        return

    tab1.mesh_list_widget.clear()  # Clear the list before adding new items

    mesh_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.mesh'):
                mesh_files.append(os.path.join(root, file))

    if not mesh_files:
        QMessageBox.information(tab1, "No Mesh Files", "No .mesh files found in the selected folder.")
        return

    for mesh_file in mesh_files:
        item = QListWidgetItem(os.path.basename(mesh_file))  # Show only the file name
        item.setData(Qt.UserRole, mesh_file)  # Store the full file path in UserRole
        tab1.mesh_list_widget.addItem(item)

    QMessageBox.information(tab1, "Success", f"Loaded {len(mesh_files)} .mesh files.")
    logger.info(tab1, "Success", f"Loaded {len(mesh_files)} .mesh files.")

def load_mesh(tab1, file_path):
    try:
        # Attempt to parse the mesh directly from the file path
        mesh = mesh_from_path(file_path)
        if mesh:
            tab1.viewer.load_mesh(mesh, file_path)
            tab1.viewer.filename = os.path.basename(file_path) # Filename to mesh viewer
            tab1.viewer.filepath = os.path.abspath(file_path) # Filepath to mesh viewer

            return

        # If neither type could be loaded, show an error
        print(tab1, "Error", "Failed to parse the mesh file. Unsupported format.")
        logger.warning("Failed to parse the mesh file. Unsupported format.")
    except FileNotFoundError:
        print(tab1, "File Not Found", "The selected file could not be found.")
        logger.debug("File Not Found", "The selected file could not be found.")
    except Exception as e:
        print(tab1, "Error", f"Failed to load mesh file: {e} \n File Path: {file_path}")
        logger.critical("Error", f"Failed to load mesh file: {e} \n File Path: {file_path}")

