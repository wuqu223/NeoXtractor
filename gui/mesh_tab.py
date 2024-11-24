from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from gui.viewer_3d import ViewerWidget
from utils.config_manager import ConfigManager
from utils.console_handler import *


def create_mesh_viewer_tab(self):
        # -----------------------------------
        # Main Tab/ Mesh Viewer
        tab1 = QMainWindow()
        tab1.setWindowTitle("ModernGL Mesh Viewer")
        tab1.closeEvent = on_closing_mesh_view
        _main = QWidget()
        tab1_layout = QVBoxLayout()
        
        full_widget = QWidget()
        full_layout = QVBoxLayout(full_widget)
        right_widget = QWidget()
        right_side = QVBoxLayout(right_widget)
        left_widget = QWidget()
        left_side = QVBoxLayout(left_widget)



        tab1.viewer = ViewerWidget(tab1)  # Placeholder for Mesh viewer
        tab1.viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tab1.viewer.setMinimumSize(QSize(400,400))
        right_side.addWidget(tab1.viewer)
        


        # Flip UV checkbox
        tab1.flip_uv_checkbox = QCheckBox('Flip UVs Y axis on Save')
        left_side.addWidget(tab1.flip_uv_checkbox)

        # Zoom slider
        tab1.zoom_speed_label = QLabel("Cam Speed:")
        tab1.zoom_speed_slider = QSlider(Qt.Horizontal)
        tab1.zoom_speed_slider.setMinimum(1)
        tab1.zoom_speed_slider.setMaximum(200)
        tab1.zoom_speed_slider.setValue(100)
        tab1.zoom_speed_slider.setFixedWidth(400)
        tab1.zoom_speed_slider.valueChanged.connect(update_zoom_speed)

        tab1.zoom_speed_label.setFixedHeight(15)
        tab1.zoom_speed_slider.setRange(1, 100)  # Convert from 0.01 to 1.0
        tab1.zoom_speed_slider.setValue(20)  # Set default zoom speed to 0.2
        full_layout.addWidget(right_widget)
        full_layout.addWidget(left_widget)
        tab1_layout.addWidget(full_widget)
        tab1_layout.addWidget(tab1.zoom_speed_label)
        tab1_layout.addWidget(tab1.zoom_speed_slider)
        _main.setLayout(tab1_layout)
        tab1.setCentralWidget(_main)
        #tab1.setGeometry(50,50,1000,800)
        
        create_view_menu(tab1)
        create_save_menu(tab1)
        
        return tab1

def on_closing_mesh_view(event):
    dialogbox = QDialog()
    dialogbox.setWindowTitle("ModernGL Mesh Viewer")

    # Layout and Widgets
    layout = QVBoxLayout()

    # Message Label
    label = QLabel("Are you sure you want to close the Mesh Viewer?\nIf you close it now, you wont be able to use it again until you reload the whole", )
    layout.addWidget(label, alignment=Qt.AlignCenter)  # Align the message to the center

    buttonslayout_widget = QWidget()
    buttonslayout = QHBoxLayout(buttonslayout_widget)

    # Close Button
    ok_button = QPushButton("Close Anyway")
    ok_button.setFixedSize(100, 30)
    ok_button.clicked.connect(dialogbox.reject)  # Use accept to close and return from dialog
    buttonslayout.addWidget(ok_button, alignment=Qt.AlignCenter)
    cancel_button = QPushButton("Leave Open")
    cancel_button.setFixedSize(100, 30)
    cancel_button.clicked.connect(dialogbox.accept)
    buttonslayout.addWidget(cancel_button, alignment=Qt.AlignCenter)
    layout.addWidget(buttonslayout_widget)
    dialogbox.setLayout(layout)

    result = dialogbox.exec_()

    if result:
        event.ignore()

def set_zoom_speed(self, speed):
    """Set the camera zoom speed."""
    if self.viewer.scene and hasattr(self.viewer.scene, 'camera'):
        self.viewer.scene.camera.zoom_speed = speed

def update_zoom_speed(self):
    if hasattr(self, 'viewer') and self.viewer.scene and hasattr(self.viewer.scene, 'camera'):
        zoom_speed = self.zoom_speed_slider.value() / 100.0
        self.viewer.scene.camera.zoom_speed = zoom_speed  # Set the zoom speed on the camera
        #self.statusBar().showMessage(f'Zoom speed set to {zoom_speed:.2f}')
    else:
        pass
        #self.statusBar().showMessage('No camera available to adjust zoom speed.')


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

    # Create the checkable action for "Show Bones"
    show_wireframe_action = QAction("Wireframe Mode", tab1)
    show_wireframe_action.setShortcut('Alt+W')
    show_wireframe_action.setCheckable(True)
    show_wireframe_action.setChecked(False)
    show_wireframe_action.triggered.connect(lambda checked: tab1.viewer.toggle_wireframe_mode(checked))
    view_menu.addAction(show_wireframe_action)

    # Create the checkable action for "Show Bones"
    show_norm_action = QAction("Show Normals", tab1)
    show_norm_action.setShortcut('Alt+N')
    show_norm_action.setCheckable(True)
    show_norm_action.setChecked(False)
    show_norm_action.triggered.connect(lambda checked: tab1.viewer.toggle_bone_visibility(checked))
    view_menu.addAction(show_norm_action)
    
def create_save_menu(tab1):
    # View Menu Button
    save_menu = tab1.menuBar().addMenu("Save")
    
    # Create the checkable action for "Show Bones"
    store_obj_action = QAction("Save as OBJ", tab1)
    store_obj_action.setShortcut('Alt+O')
    store_obj_action.setCheckable(False)
    store_obj_action.triggered.connect(lambda checked = tab1.flip_uv_checkbox.isChecked(): tab1.viewer.save_mesh_obj(checked))
    save_menu.addAction(store_obj_action)
    
    store_obj_action = QAction("Save as SMD", tab1)
    store_obj_action.setShortcut('Alt+O')
    store_obj_action.setCheckable(False)
    store_obj_action.triggered.connect(lambda checked = tab1.flip_uv_checkbox.isChecked(): tab1.viewer.save_mesh_smd(checked))
    save_menu.addAction(store_obj_action)
    
    store_obj_action = QAction("Save as ASCII", tab1)
    store_obj_action.setShortcut('Alt+O')
    store_obj_action.setCheckable(False)
    store_obj_action.triggered.connect(lambda checked = tab1.flip_uv_checkbox.isChecked(): tab1.viewer.save_mesh_ascii(checked))
    save_menu.addAction(store_obj_action)
    
    store_obj_action = QAction("Save as PMX", tab1)
    store_obj_action.setShortcut('Alt+O')
    store_obj_action.setCheckable(False)
    store_obj_action.triggered.connect(tab1.viewer.save_mesh_pmx)
    save_menu.addAction(store_obj_action)
    
    store_obj_action = QAction("Save as IQE", tab1)
    store_obj_action.setShortcut('Alt+O')
    store_obj_action.setCheckable(False)
    store_obj_action.triggered.connect(tab1.viewer.save_mesh_iqe)
    save_menu.addAction(store_obj_action)
    