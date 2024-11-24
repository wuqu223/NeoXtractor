import sys
import moderngl as mgl
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from pyrr import Matrix44
from gui.help import TextRenderer
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
        

        # Initialize flags and properties
        self.last_x = None
        self.last_y = None
        self.mouse_left_pressed = False
        self.shift_pressed = False
        self.ctrl_pressed = False
        self.current_scale = 1.0
        self.viewport = (0, 0, 1200, 1200)  # Default viewport size

    def initializeGL(self):
        print("Creating OpenGL context...")
        self.ctx = mgl.create_context() # Create the OpenGL context
        
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
        self.text_renderer = TextRenderer(self.ctx)
        print("TextRenderer initialized.")

    def render(self):
        self.ctx.viewport = self.viewport  # Ensure viewport matches window size
        self.screen.use()
        self.scene.draw()

        if not self.text_renderer:
            print("TextRenderer not initialized, skipping text rendering.")
            return

        # Render overlay text using TextRenderer
        text_scale = 0.4
        x_pos = 10
        color1 = (0.5, 1.0, 1.0)
        color2 = (1.0, 1.0, 1.0)
        self.text_renderer.render_text("'F' Key: ", x=x_pos, y=20, scale=text_scale, color=color1)
        self.text_renderer.render_text("Mouse Right:", x=x_pos, y=50, scale=text_scale, color=color1)
        self.text_renderer.render_text("Mouse Left:", x=x_pos, y=80, scale=text_scale, color=color1)
        self.text_renderer.render_text("Mouse Middle:", x=x_pos, y=110, scale=text_scale, color=color1)
        self.text_renderer.render_text("Key 1: ", x=x_pos, y=140, scale=text_scale, color=color1)
        self.text_renderer.render_text("Key 3: ", x=x_pos, y=170, scale=text_scale, color=color1)
        self.text_renderer.render_text("Key 7: ", x=x_pos, y=200, scale=text_scale, color=color1)
        self.text_renderer.render_text("Focus Object", x=65, y=20, scale=text_scale, color=color2)
        self.text_renderer.render_text("Orbit", x=110, y=50, scale=text_scale, color=color2)
        self.text_renderer.render_text("Pan", x=105, y=80, scale=text_scale, color=color2)
        self.text_renderer.render_text("Dolly", x=120, y=110, scale=text_scale, color=color2)
        self.text_renderer.render_text("Front View", x=65, y=140, scale=text_scale, color=color2)
        self.text_renderer.render_text("Right View", x=65, y=170, scale=text_scale, color=color2)
        self.text_renderer.render_text("Top View", x=65, y=200, scale=text_scale, color=color2)
    
    def ctx_init(self):
        self.ctx.enable(mgl.DEPTH_TEST)
        self.ctx.enable(mgl.CULL_FACE)
        self.update_aspect_ratio()
        self.update()

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
        self.update()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift:
            self.shift_pressed = False
        elif event.key() == Qt.Key_Control:
            self.ctrl_pressed = False
    
    def focus_on_selected_object(self):
        # Retrieve the center of the mesh from the scene
        selected_center = self.scene.get_selected_object_center()
        print("Object Centred")  # Debugging output
        # Set camera focus on the selected object center
        self.scene.camera.focus(selected_center)
        self.scene.camera.dist = 4.0  # Adjust as needed to frame the object
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
        if hasattr(self.scene, "mesh"):
            saveobj(self.scene.mesh, self.location, flip_uv=checkedbox)

    def save_mesh_smd(self, checkedbox):
        if hasattr(self.scene, "mesh"):
            savesmd(self.scene.mesh, self.location, flip_uv=checkedbox)

    def save_mesh_ascii(self, checkedbox):
        if hasattr(self.scene, "mesh"):
            saveascii(self.scene.mesh, self.location, flip_uv=checkedbox)

    def save_mesh_pmx(self):
        if hasattr(self.scene, "mesh"):
            savepmx(self.scene.mesh, self.location)

    def save_mesh_iqe(self):
        if hasattr(self.scene, "mesh"):
            saveiqe(self.scene.mesh, self.location)
