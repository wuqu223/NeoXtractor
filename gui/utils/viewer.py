"""Viewer utility functions for viewers."""

from PySide6 import QtWidgets

from core.npk.types import NPKEntry
from gui.widgets.code_editor import CodeEditor
from gui.widgets.hex_viewer import HexViewer
from gui.widgets.texture_viewer import TextureViewer

def set_entry_for_viewer(viewer: QtWidgets.QWidget, data: NPKEntry | None):
    """
    Set the data for the viewer.
    
    :param viewer: The viewer to set the data for.
    :param data: The NPK entry data to set.
    """
    if isinstance(viewer, HexViewer):
        viewer.setData(bytearray(data.data) if data is not None else bytearray())
    elif isinstance(viewer, CodeEditor):
        if data is None:
            viewer.set_content("")
        else:
            viewer.set_content(data.data.decode("utf-8", errors="replace"), data.extension)
    elif isinstance(viewer, TextureViewer):
        if data is None:
            viewer.clear()
        else:
            # Raises ValueError if the image is not supported
            viewer.set_texture(data.data, data.extension)
