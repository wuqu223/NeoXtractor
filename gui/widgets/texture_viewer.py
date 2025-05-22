"""Provides Texture Viewer widget."""

from typing import cast
from PySide6 import QtCore, QtWidgets, QtGui
from PIL import Image, ImageFile
import numpy as np

from core.images import convert_image, image_to_png_data

QT_SUPPORTED_FORMATS = tuple(fmt.toStdString() for fmt in QtGui.QImageReader.supportedImageFormats())

class TextureViewer(QtWidgets.QWidget):
    """A widget that displays a texture."""

    # Viewer attributes
    name = "Texture Viewer"
    accepted_extensions = QT_SUPPORTED_FORMATS + ("tga", "ico",
                           "tiff", "dds", "pvr", "ktx", "astc", "cbk")

    _texture: QtGui.QImage | None = None
    _processed_texture: QtGui.QImage | None = None

    def __init__(self):
        super().__init__()

        main_layout = QtWidgets.QVBoxLayout(self)

        self._image_label = QtWidgets.QLabel(self)
        self._image_label.setAlignment(QtGui.Qt.AlignmentFlag.AlignCenter)
        self._image_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        size_layout = QtWidgets.QHBoxLayout()
        size_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.size_label = QtWidgets.QLabel(self)
        self.size_label.setAlignment(QtGui.Qt.AlignmentFlag.AlignCenter)
        size_layout.addWidget(self.size_label)

        self.rendered_size_label = QtWidgets.QLabel(self)
        self.rendered_size_label.setAlignment(QtGui.Qt.AlignmentFlag.AlignCenter)
        self.rendered_size_label.setVisible(False)
        size_layout.addWidget(self.rendered_size_label)

        self.flip_tex = QtWidgets.QCheckBox("Flip Vertically")
        self.flip_tex.stateChanged.connect(
            lambda: (
                self._apply_modifiers(),
                self._display_image()
            )
        )

        self.channel_r = QtWidgets.QCheckBox("R")
        self.channel_g = QtWidgets.QCheckBox("G")
        self.channel_b = QtWidgets.QCheckBox("B")
        self.channel_a = QtWidgets.QCheckBox("A")

        channels_layout = QtWidgets.QHBoxLayout()

        for channel in [self.channel_r, self.channel_g, self.channel_b, self.channel_a]:
            channel.setChecked(True)
            channel.stateChanged.connect(
                lambda: (
                    self._apply_modifiers(),
                    self._display_image()
                )
            )
            channels_layout.addWidget(channel)

        channels_layout.addStretch()

        main_layout.addWidget(self._image_label)
        main_layout.addLayout(size_layout)
        main_layout.addWidget(self.flip_tex)
        main_layout.addLayout(channels_layout)

    def _display_image(self):
        """Display the (processed) image in the label."""
        if self._texture is None and self._processed_texture is None:
            return

        pixmap = QtGui.QPixmap.fromImage(
                cast(QtGui.QImage, self._processed_texture if self._processed_texture else self._texture)
            ).scaled(
                self._image_label.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio
            )
        self._image_label.setPixmap(pixmap)
        if cast(QtGui.QImage, self._texture).size() != pixmap.size():
            self.rendered_size_label.setVisible(True)
            self.rendered_size_label.setText(f"(Rendered Size: {pixmap.width()} x {pixmap.height()})")
        else:
            self.rendered_size_label.setVisible(False)

    def _apply_modifiers(self):
        """Apply any necessary modifiers to the image."""

        if self._texture is None:
            return

        image = self._texture.convertToFormat(QtGui.QImage.Format.Format_ARGB32).copy()

        a_modifier = int(self.channel_a.isChecked())
        r_modifier = int(self.channel_r.isChecked())
        g_modifier = int(self.channel_g.isChecked())
        b_modifier = int(self.channel_b.isChecked())

        ptr = image.bits()
        # For ARGB32, each pixel is 4 bytes (B, G, R, A)
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape(image.height(), image.width(), 4)

        # Perform vectorized operations on the NumPy array
        # Indices for BGRA: Blue=0, Green=1, Red=2, Alpha=3
        if a_modifier == 0:
            arr[:, :, 3] = 255  # Set Alpha channel to 255
        if r_modifier == 0:
            arr[:, :, 2] = 0  # Set Red channel to 0
        if g_modifier == 0:
            arr[:, :, 1] = 0  # Set Green channel to 0
        if b_modifier == 0:
            arr[:, :, 0] = 0  # Set Blue channel to 0

        if self.flip_tex.isChecked():
            arr[:] = np.flipud(arr)

        self._processed_texture = image

        self._display_image()

    def resizeEvent(self, event: QtGui.QResizeEvent):
        """Handle resize events."""
        super().resizeEvent(event)
        if self._texture is not None:
            self._display_image()

    def set_texture(self, data: bytes, extension: str):
        """Set the texture data and extension."""
        if extension not in self.accepted_extensions:
            raise ValueError(f"Unsupported image format: {extension}")

        if extension in QT_SUPPORTED_FORMATS:
            # Use Qt's image reader for supported formats
            self._texture = QtGui.QImage.fromData(data)
        else:
            # Use custom conversion for unsupported formats
            self._texture = QtGui.QImage.fromData(image_to_png_data(
                cast(Image.Image | ImageFile.ImageFile,convert_image(data, extension))
                ))

        if self._texture.isNull():
            raise ValueError("Failed to load image data")

        self._apply_modifiers()
        self._display_image()

        self.size_label.setText(f"Size: {self._texture.width()} x {self._texture.height()}")

    def clear(self):
        """Clear the texture."""
        self._texture = None
        self._image_label.clear()
