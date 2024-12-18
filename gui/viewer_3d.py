import sys
import moderngl as mgl
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from pyrr import Matrix44
from gui.help import StaticTextRenderer
from utils.util import *
from gui.scene import Scene
from gui.camera import Camera
from converter import *


class ViewerWidget(QModernGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.location = ""
        self.scene = None
        self.ctx = None
        self.ctx_initialized = False  # Track if context has been set up
        self.mouse_middle_pressed = None
        self.mouse_right_pressed = None
        self.text_renderer = None

        # Initialize flags and properties
        self.last_x = None
        self.last_y = None
        self.mouse_left_pressed = False
        self.shift_pressed = False
        self.ctrl_pressed = False
        self.current_scale = 1.0
        self.viewport = (0, 0, 1200, 1200)  # Default viewport size
        self.camera = Camera()

        self.update_aspect_ratio()

    def initializeGL(self):
        print("Creating OpenGL context...")
        self.ctx = mgl.create_context()  # Create the OpenGL context

        if not self.ctx:
            print("Failed to initialize OpenGL context.")
            return

        # Initialize the Scene with the valid context
        self.scene = Scene(self.ctx, self)
        print("Scene initialized with OpenGL context.")

    def init(self):
        """Ensure the OpenGL context and scene are initialized."""

        if self.ctx is None:
            print("Error: OpenGL context is not initialized.")
            return

        # Set the viewport
        self.ctx.viewport = self.viewport
        print("Viewport set.")

        # Initialize TextRenderer with the current context
        self.text_renderer = StaticTextRenderer(self.ctx)
        print("TextRenderer initialized.")

    def render(self):
        self.ctx.viewport = self.viewport  # Ensure viewport matches window size
        self.screen.use()
        self.scene.draw()
        self.render_navigation_overlay(self.location)
        self.update_aspect_ratio()
        self.update()

    def ctx_init(self):
        self.ctx.enable(mgl.DEPTH_TEST)
        self.ctx.enable(mgl.CULL_FACE)
        self.update_aspect_ratio()
        self.update()

    def render_navigation_overlay(self, selected_file):

        if not self.text_renderer:
            print("TextRenderer not initialized, skipping navigation keys rendering.")
            return

        # Calculate triangle count dynamically for displaying count
        try:
            if self.scene and self.scene.ibo:  # Index buffer is present
                index_count = len(self.scene.ibo.read()) // 4
                face_count = index_count // 3
                vertex_count = index_count
            elif self.scene and self.scene.vbo:  # Vertex buffer is present, but no index buffer
                vertex_count = len(self.scene.vbo.read()) // (6 * 4)
                triangle_count = vertex_count // 3
            else:
                triangle_count = 0
                face_count = 0
                vertex_count = 0
        except Exception as e:
            print(f"Error counting triangles: {e}")
            triangle_count = "N/A"

        # Calculate bones count dynamically for displaying count
        try:
            if self.scene and hasattr(self.scene, 'bone_vbo') and self.scene.bone_vbo:  # Check for bone vertex buffer
                bone_count = len(self.scene.bone_vbo.read()) // (3 * 4)
            elif self.scene and hasattr(self.scene,
                                        'bone_lines') and self.scene.bone_lines:  # Fallback to bone lines list
                bone_count = len(self.scene.bone_lines) // 2  # Each bone line is defined by 2 points
            else:
                bone_count = 0
        except Exception as e:
            print(f"Error counting bones: {e}")
            bone_count = "N/A"

        # Extract the file name from the selected item
        try:
            if self.scene and self.scene.ibo:
                file_name = os.path.basename(selected_file)
                filename = f"{file_name}"
            else:
                filename = "Name"
        except Exception as e:
            print(f"Error getting filename: {e}")
            filename = "N/A"

        instructions = [
            ("'F' Key", "Focus Object"),
            ("M-Right", "Orbit"),
            ("M-Left", "Pan"),
            ("M-Middle", "Dolly"),
            ("Key 1", "Front View"),
            ("Key 3", "Right View"),
            ("Key 7", "Top View"),
        ]
        for i, (key, action) in enumerate(instructions):
            self.text_renderer.render_static_text(f"{key}:", x=20, y=20 + i * 20, scale=1.0, color=(0.5, 1.0, 1.0))
            self.text_renderer.render_static_text(f"{action}", x=90, y=20 + i * 20, scale=1.0, color=(1.0, 1.0, 1.0))

        model_info = [
            ("Bones", bone_count),
            ("Tris", vertex_count),
            ("Faces", face_count or triangle_count),
            ("Name", filename),
        ]
        for i, (key1, info) in enumerate(model_info):
            self.text_renderer.render_static_text(f"{key1}:", x=20, y=620 + i * 20, scale=1.0, color=(0.5, 1.0, 1.0))
            self.text_renderer.render_static_text(f"{info}", x=90, y=620 + i * 20, scale=1.0, color=(1.0, 1.0, 1.0))

    def resizeEvent(self, event):
        """Handle resizing and update the viewport if context is ready."""
        width, height = event.size().width(), event.size().height()
        self.viewport = (0, 0, width, height)

        if self.ctx_initialized and self.scene and hasattr(self.scene, 'camera'):
            self.scene.camera.aspect_ratio = width / height
        self.update()

    def mousePressEvent(self, event):
        self.last_x = event.x()
        self.last_y = event.y()
        if event.button() == Qt.LeftButton:
            self.mouse_left_pressed = True
        elif event.button() == Qt.RightButton:
            self.mouse_right_pressed = True
        elif event.button() == Qt.MiddleButton:
            self.mouse_middle_pressed = True
        self.update()

    def mouseReleaseEvent(self, event):
        self.last_x = None
        self.last_y = None
        if event.button() == Qt.LeftButton:
            self.mouse_left_pressed = False
        elif event.button() == Qt.RightButton:
            self.mouse_right_pressed = False
        elif event.button() == Qt.MiddleButton:
            self.mouse_middle_pressed = False
        self.update()

    def mouseMoveEvent(self, event):
        if self.last_x is None or self.last_y is None:
            return
        dx = event.x() - self.last_x
        dy = event.y() - self.last_y
        self.last_x = event.x()
        self.last_y = event.y()

        if self.mouse_left_pressed:
            self.scene.camera.orbit(dx, dy)
        elif self.mouse_right_pressed:
            self.scene.camera.pan(dx, dy)
            self.update()
        self.update()

    def wheelEvent(self, event):
        offset = event.angleDelta().y() / 100
        self.scene.camera.dolly(offset)
        self.update()

    def update_aspect_ratio(self):
        """Update camera aspect ratio based on current viewport size."""
        width, height = self.viewport[2], self.viewport[3]
        if self.scene is not None and hasattr(self.scene, 'camera'):
            self.scene.camera.aspect_ratio = width / height

        Camera.set_aspect_ratio(self, width, height)
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Shift:
            self.shift_pressed = True
        elif event.key() == Qt.Key_Control:
            self.ctrl_pressed = True
        elif event.key() in [Qt.Key_1, Qt.Key_3, Qt.Key_7]:
            view = {Qt.Key_1: 1, Qt.Key_3: 3, Qt.Key_7: 7}[event.key()]
            self.scene.camera.orthogonal(view, self.ctrl_pressed)
        elif event.key() == Qt.Key_F:
            self.focus_on_selected_object()
            self.scene.camera.orthogonal({Qt.Key_1: 1}, self.ctrl_pressed)

        self.update()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift:
            self.shift_pressed = False
        elif event.key() == Qt.Key_Control:
            self.ctrl_pressed = False
        self.update()

    def focus_on_selected_object(self):
        # Retrieve the center of the mesh from the scene
        selected_center = self.scene.get_selected_object_center()
        print("Object Centred")  # Debugging output
        # Set camera focus on the selected object center
        self.scene.camera.focus(selected_center)
        self.scene.camera.dist = 8.0  # Adjust as needed to frame the object
        self.update_aspect_ratio()
        self.update()

    def load_mesh(self, mesh, location):
        if self.ctx is None or self.scene is None:
            print("Scene or context not initialized.")
            return

        # Delegate mesh handling to the scene
        self.scene.load_mesh(mesh)
        self.location = location
        self.focus_on_selected_object()
        self.update_aspect_ratio()
        self.update()

    def load_armature(self, armature):
        """Load armature and ensure it displays in the viewport."""
        self.scene.load_armature(armature)
        self.ctx.enable(mgl.CULL_FACE)
        self.ctx.disable(mgl.DEPTH_TEST)
        self.update()

    def release_mesh(self):
        if hasattr(self, 'vbo'):
            Scene.vbo.release()
        if hasattr(self, 'ibo'):
            Scene.ibo.release()
        if hasattr(self, 'vao'):
            Scene.vao.release()
        del Scene.vbo, Scene.ibo, Scene.vao  # To ensure these are fully removed
        self.update()

    def scale_mesh(self, scale_factor):
        """Scale the loaded mesh and armature in the scene."""
        if self.scene:
            self.scene.scale_mesh(scale_factor)
            self.update()

    def toggle_bone_visibility(self, checked):
        # Update the scene's bone visibility based on the action's checked state
        self.scene.show_bones = checked
        self.update()

    def toggle_normals_visibility(self, checked):
        # Update the scene's bone visibility based on the action's checked state
        self.scene.show_normals = checked
        self.update()

    def toggle_wireframe_mode(self, checked):
        self.ctx.wireframe = checked
        self.update()

    def save_mesh_obj(self, checkedbox):
        ext = "OBJ"
        try:
            if hasattr(self.scene, "mesh"):
                saveobj(self.scene.mesh, self.location, flip_uv=checkedbox)
                QMessageBox.information(self, f'Save as {ext.upper()}',
                                        f'The mesh has been successfully saved as a {ext.upper()} file.')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save mesh as {ext.upper()}: {e}")

    def save_mesh_smd(self, checkedbox):
        ext = "SMD"
        try:
            if hasattr(self.scene, "mesh"):
                savesmd(self.scene.mesh, self.location, flip_uv=checkedbox)
                QMessageBox.information(self, f'Save as {ext.upper()}',
                                        f'The mesh has been successfully saved as a {ext.upper()} file.')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save mesh as {ext.upper()}: {e}")

    def save_mesh_ascii(self, checkedbox):
        ext = "ASCII"
        try:
            if hasattr(self.scene, "mesh"):
                saveascii(self.scene.mesh, self.location, flip_uv=checkedbox)
                QMessageBox.information(self, f'Save as {ext.upper()}',
                                        f'The mesh has been successfully saved as a {ext.upper()} file.')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save mesh as {ext.upper()}: {e}")

    def save_mesh_pmx(self):
        ext = "PMX"
        try:
            if hasattr(self.scene, "mesh"):
                savepmx(self.scene.mesh, self.location)
                QMessageBox.information(self, f'Save as {ext.upper()}',
                                        f'The mesh has been successfully saved as a {ext.upper()} file.')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save mesh as {ext.upper()}: {e}")

    def save_mesh_iqe(self):
        ext = "IQE"
        try:
            if hasattr(self.scene, "mesh"):
                saveiqe(self.scene.mesh, self.location)
                QMessageBox.information(self, f'Save as {ext.upper()}',
                                        f'The mesh has been successfully saved as a {ext.upper()} file.')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save mesh as {ext.upper()}: {e}")

    def save_mesh_gltf(self):
        ext = "GLTF2"
        try:
            if hasattr(self.scene, "mesh"):
                save_to_json(self.scene.mesh, self.location)
                QMessageBox.information(self, f'Save as {ext.upper()}',
                                        f'The mesh has been successfully saved as a {ext.upper()} file.')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save mesh as {ext.upper()}: {e}")

    def set_zoom_speed(self, speed):
        """
        Adjust the camera zoom speed based on the slider input.
        """
        self.camera.zoom_speed = speed / 1000.0  # Adjust divisor for sensitivity
        print(f"Zoom speed set to: {self.camera.zoom_speed}")
        self.update()
