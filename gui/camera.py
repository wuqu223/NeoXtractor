import math
import pyrr
from pyrr import Matrix44, Vector4

class Camera:
    def __init__(self):
        self._pos = Vector4([0, 1, 4, 1])
        self.pitch = 0.0
        self.yaw = 10.0
        self.roll = 0.0
        self.dist = 4.0
        self.fovY = 45
        self.aspect_ratio = 1
        self.perspective = True
        self.zoom_speed = 1.0  # Default zoom speed
        self.min_dist = 10
        self.max_dist = 100

    def pos(self):
        return self._pos

    def euler(self):
        roll = math.radians(self.roll)
        pitch = math.radians(self.pitch)
        yaw = math.radians(self.yaw)
        return pyrr.euler.create(pitch, roll, yaw)

    def rot(self):
        return Matrix44.from_eulers(self.euler())

    def view(self):
        view = Matrix44.from_translation(-self.pos())
        view = self.rot() * view
        view = Matrix44.from_translation([0.0, 0.0, -self.dist, 0.0]) * view
        return view

    def proj(self):
        if self.perspective:
            return Matrix44.perspective_projection(self.fovY, self.aspect_ratio, 0.1, 1000.0)
        else:
            length = math.tan(math.radians(self.fovY / 2)) * abs(self.dist)
            if self.aspect_ratio >= 1:
                return Matrix44.orthogonal_projection(-length * self.aspect_ratio, length * self.aspect_ratio, -length, length, 0.1, 1000.0)
            else:
                return Matrix44.orthogonal_projection(-length, length, -length / self.aspect_ratio, length / self.aspect_ratio, 0.1, 1000.0)
    
    def view_proj(self):
        return self.proj() * self.view()

    def dolly(self, amount):
        self.dist += amount * self.zoom_speed
        self.dist = max(self.min_dist, min(self.dist, self.max_dist))
        # print(f"Camera distance: {self.dist}")
        self.proj()

    def orbit(self, dx, dy):
        self.perspective = True
        self.yaw -= dx * 0.5
        self.pitch = max(-89.0, min(89.0, self.pitch - dy * 0.5))

    def pan(self, dx, dy):
        pan_speed = 0.01 * self.dist  # Scale pan speed by distance
        dv = Vector4([dx * -pan_speed, dy * pan_speed, 0.0, 0.0])
        dv = self.rot().inverse * dv

        self._pos = Vector4([
            self._pos.x + dv.x,
            self._pos.y + dv.y,
            self._pos.z + dv.z,
            1.0
        ])

    def orthogonal(self, direct, ctrl):
        self.perspective = False
        self.yaw, self.pitch, self.roll = 0.0, 0.0, 0.0
        if direct == 1:
            self.yaw = 0.0 if not ctrl else 180.0
        elif direct == 3:
            self.yaw = 90.0 if not ctrl else -90.0
        elif direct == 7:
            self.pitch = -90.0 if not ctrl else 90.0

    def focus(self, point):
        focus_point = Vector4([point[0], point[1], point[2], 1.0])
        self._pos = focus_point
        self.dist = math.sqrt((self._pos.x - focus_point.x)**2 +
                            (self._pos.y - focus_point.y)**2 +
                            (self._pos.z - focus_point.z)**2)

    def set_aspect_ratio(self, width, height):
        self.aspect_ratio = width / height if height != 0 else 1.0
