from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from gui.viewer_3d import ViewerWidget
from utils.config_manager import ConfigManager
from utils.console_handler import *
from utils.util import *
from converter import *


class FileSelector:
    @staticmethod
    def select_file():
        file_name, _ = QFileDialog.getOpenFileName(
            None, "Select File", "", "Mesh Files (*.mesh)"
        )
        return file_name


def show_input_dialog(title, text):
    dialogue_response, dialogue_complete = QInputDialog.getText(
        None, title, text, QLineEdit.Normal, ""
    )
    return dialogue_response if dialogue_complete else ""

def create_mesh_viewer_tab(self):
    # -----------------------------------
    # Mesh Viewer
    tab1 = QMainWindow()
    tab1.setGeometry(350, 150, 1400, 800)
    tab1.setWindowTitle("ModernGL Mesh Viewer")
    tab1.closeEvent = on_closing_mesh_view

    # Main Container
    _main = QWidget()
    main_layout = QHBoxLayout(_main)

    # Left Side: File List Setup
    tab1.mesh_list_widget = QListWidget()
    tab1.mesh_list_widget.setAcceptDrops(True)
    tab1.mesh_list_widget.setFixedSize(300, 800)
    tab1.mesh_list_widget.setToolTip("List of .mesh files in the loaded folder.")
    main_layout.addWidget(tab1.mesh_list_widget)

    # Define and attach signal handlers
    def on_mesh_item_clicked(item):
        """Handle single-click event for mesh items."""
        file_path = item.data(Qt.UserRole)
        print(f"Item clicked: {file_path}")

    def on_mesh_item_double_clicked(item):
        """Handle double-click event to load mesh into the viewer."""
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.isfile(file_path):
            try:
                load_mesh(tab1, file_path)
                print(f"Mesh loaded: {file_path}")
            except Exception as e:
                QMessageBox.critical(tab1, "Error", f"Failed to load mesh file: {str(e)}")

    tab1.on_mesh_item_clicked = on_mesh_item_clicked
    tab1.on_mesh_item_double_clicked = on_mesh_item_double_clicked

    # Connect the signals to the handlers
    tab1.mesh_list_widget.itemPressed.connect(tab1.on_mesh_item_clicked)
    tab1.mesh_list_widget.itemDoubleClicked.connect(tab1.on_mesh_item_double_clicked)

    # Right Side: Viewer and Controls
    right_side = QVBoxLayout()

    # Viewer Widget
    tab1.viewer = ViewerWidget(tab1)  # Placeholder for Mesh Viewer
    tab1.viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    tab1.viewer.setMinimumSize(QSize(400, 400))
    right_side.addWidget(tab1.viewer)

    # Viewport Navigation Label
    navigation_label = QLabel(
        "Key 7: Top View  |  Key 3: Right View  |  Key 1: Front View  |  Ctrl+Key: Flip View  |  "
        "Middle: Dolly  |  Left: Pan  |  Right: Orbit  |  'F' Key: Focus on Object"
    )
    navigation_label.setFixedHeight(20)
    right_side.addWidget(navigation_label)

    # Flip UV Checkbox
    tab1.flip_uv_checkbox = QCheckBox('Flip UVs V-axis on Save')
    tab1.flip_uv_checkbox.setChecked(False)
    right_side.addWidget(tab1.flip_uv_checkbox)

    # Zoom Speed Slider
    zoom_speed_label = QLabel("Camera Zoom Speed Control:")
    zoom_speed_label.setFixedHeight(15)
    right_side.addWidget(zoom_speed_label)

    zoom_speed_slider = QSlider(Qt.Horizontal)
    zoom_speed_slider.setRange(1, 100)  # Range: 1 to 100
    zoom_speed_slider.setValue(20)  # Default speed
    zoom_speed_slider.setFixedWidth(400)
    # zoom_speed_slider.valueChanged.connect(lambda: update_zoom_speed(tab1))
    zoom_speed_slider.valueChanged.connect(lambda value: tab1.viewer.set_zoom_speed(value))
    right_side.addWidget(zoom_speed_slider)

    # Add Right Side to Main Layout
    main_layout.addLayout(right_side)

    # Set Main Layout
    _main.setLayout(main_layout)
    tab1.setCentralWidget(_main)

    # Add Menus
    create_open_menu(tab1)
    create_view_menu(tab1)
    create_save_menu(tab1)

    # Attach load_mesh method
    setattr(tab1, "load_mesh", lambda file_path: load_mesh(tab1, file_path))

    return tab1

# class MeshListWidget(QListWidget):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.setAcceptDrops(True)

#     def dragEnterEvent(self, event):
#         if event.mimeData().hasUrls():
#             event.accept()
#         else:
#             event.ignore()

#     def dropEvent(self, event):
#         for url in event.mimeData().urls():
#             path = url.toLocalFile()
#             if os.path.isdir(path):
#                 self.add_mesh_files_from_folder(path)
#             elif os.path.isfile(path) and path.lower().endswith('.mesh'):
#                 self.add_mesh_to_list(path)

#     def add_mesh_files_from_folder(self, folder_path):
#         """Filter .mesh files in a folder and add them to the list."""
#         mesh_files = [
#             os.path.join(root, file)
#             for root, _, files in os.walk(folder_path)
#             for file in files if file.lower().endswith('.mesh')
#         ]
#         for mesh_file in mesh_files:
#             self.add_mesh_to_list(mesh_file)

#     def add_mesh_to_list(self, mesh_file):
#         """Add a single .mesh file to the list."""
#         item = QListWidgetItem(os.path.basename(mesh_file))
#         item.setData(Qt.UserRole, mesh_file)
#         self.addItem(item)


def on_closing_mesh_view(event):
    dialogbox = QDialog()
    dialogbox.setWindowTitle("Mesh Viewer")

    # Layout and Widgets
    layout = QVBoxLayout()

    # Message Label
    label = QLabel(
        "Are you sure you want to close the Mesh Viewer?\nIf you close it now, you wont be able to use it again until you restart the app.", )
    layout.addWidget(label, alignment=Qt.AlignCenter)  # Align the message to the center

    button_layout = QHBoxLayout()
    close_button = QPushButton("Close Anyway")
    close_button.clicked.connect(dialogbox.accept)
    button_layout.addWidget(close_button)

    cancel_button = QPushButton("Leave Open")
    cancel_button.clicked.connect(dialogbox.reject)
    button_layout.addWidget(cancel_button)

    layout.addLayout(button_layout)
    dialogbox.setLayout(layout)

    if dialogbox.exec_() == QDialog.Accepted:
        event.accept()
    else:
        event.ignore()


def update_zoom_speed(tab1):
    if hasattr(tab1.viewer.scene, "camera"):
        zoom_speed = tab1.zoom_speed_slider.value() / 30.0
        tab1.viewer.scene.camera.zoom_speed = zoom_speed
        tab1.statusBar().showMessage(f"Zoom Speed: {zoom_speed:.1f}")
    else:
        tab1.statusBar().showMessage("No camera available to adjust zoom speed.")


def create_view_menu(tab1):
    # View Menu Button
    view_menu = tab1.menuBar().addMenu("View")

    # Create the checkable action for "Show Bones"
    show_bones_action = QAction("Show Bones", tab1)
    show_bones_action.setShortcut('Alt+B')
    show_bones_action.setCheckable(True)
    show_bones_action.setChecked(True)
    show_bones_action.triggered.connect(lambda checked: tab1.viewer.toggle_bone_visibility(checked))
    view_menu.addAction(show_bones_action)

    # Create the checkable action for "Show Wireframe"
    show_wireframe_action = QAction("Wireframe Mode", tab1)
    show_wireframe_action.setShortcut('Alt+W')
    show_wireframe_action.setCheckable(True)
    show_wireframe_action.setChecked(False)
    show_wireframe_action.triggered.connect(lambda checked: tab1.viewer.toggle_wireframe_mode(checked))
    view_menu.addAction(show_wireframe_action)

    # Create the checkable action for "Show Normals"
    show_norm_action = QAction("Show Normals", tab1)
    show_norm_action.setShortcut('Alt+N')
    show_norm_action.setCheckable(True)
    show_norm_action.setChecked(False)
    show_norm_action.triggered.connect(lambda checked: tab1.viewer.toggle_normals_visibility(checked))
    view_menu.addAction(show_norm_action)


def create_save_menu(tab1):
    save_menu = tab1.menuBar().addMenu("Save")

    save_actions = [
        ("FBX - Coming Soon", "Ctrl+Shift+F",
         lambda: QMessageBox.information(tab1, "Coming Soon", "FBX support is not implemented yet.")),
        ("GLTF2", "Ctrl+Shift+G", tab1.viewer.save_mesh_gltf),
        ("OBJ", "Ctrl+Shift+O", tab1.viewer.save_mesh_obj),
        ("SMD", "Ctrl+Shift+S", tab1.viewer.save_mesh_smd),
        ("ASCII", "Ctrl+Shift+A", tab1.viewer.save_mesh_ascii),
        ("PMX", "Ctrl+Shift+P", tab1.viewer.save_mesh_pmx),
        ("IQE", "Ctrl+Shift+I", tab1.viewer.save_mesh_iqe),
    ]

    for label, shortcut, func in save_actions:
        action = QAction(f"Save as {label}", tab1)
        action.setShortcut(shortcut)
        action.triggered.connect(func)
        save_menu.addAction(action)


def create_open_menu(tab1):
    open_menu = tab1.menuBar().addMenu("Open")

    # Open .mesh file
    open_action = QAction("Open file (.mesh)", tab1)
    open_action.setShortcut("Ctrl+O")
    open_action.triggered.connect(lambda: openFile(tab1))
    open_menu.addAction(open_action)

    # Open folder and filter .mesh files
    open_folder_action = QAction("Open Folder (Filter .mesh)", tab1)
    open_folder_action.setShortcut("Ctrl+Shift+O")
    open_folder_action.triggered.connect(lambda: openFolder(tab1))
    open_menu.addAction(open_folder_action)


def openFile(tab1):
    file_name = FileSelector.select_file()
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


def load_mesh(tab1, file_path):
    try:
        # Attempt to parse the mesh directly from the file path
        mesh = mesh_from_path(file_path)
        if mesh:
            tab1.viewer.load_mesh(mesh, file_path)
            return

        # If fails, read the file as binary
        with open(file_path, "rb") as file:
            mesh_data = file.read()

        # Attempt to parse different type of mesh from binary data
        mesh = mesh_from_path(mesh_data)
        if mesh:
            tab1.viewer.load_mesh(mesh, file_path)
            return

        # If neither type could be loaded, show an error
        QMessageBox.warning(tab1, "Error", "Failed to parse the mesh file. Unsupported format.")
    except FileNotFoundError:
        QMessageBox.warning(tab1, "File Not Found", "The selected file could not be found.")
    except Exception as e:
        QMessageBox.critical(tab1, "Error", f"Failed to load mesh file: {e}\nFile Path: {file_path}")
