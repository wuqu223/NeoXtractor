"""Provides a preview widget for Main Window."""

from PySide6 import QtWidgets, QtCore

from core.npk.types import NPKEntry, NPKEntryDataFlags
from core.utils import format_bytes
from gui.widgets.code_editor import CodeEditor
from gui.widgets.hex_viewer import HexViewer
from gui.widgets.texture_viewer import TextureViewer

SELECT_ENTRY_TEXT = "Select an entry to preview."
UNKNOWN_FILE_TYPE_TEXT = "Unknown file type. Using default viewer."

PREVIEW_HEX_VIEWER = "Hex Viewer"
PREVIEW_CODE_VIEWER = "Code Viewer"
PREVIEW_TEXTURE_VIEWER = "Texture Viewer"

class PreviewWidget(QtWidgets.QWidget):
    """
    A widget that provides a preview of the selected file in the NPK file list.
    """

    _current_entry: NPKEntry | None = None
    _previewers: list[QtWidgets.QWidget] = []

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self.message_label = QtWidgets.QLabel(SELECT_ENTRY_TEXT)
        self.message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.widget_layout = QtWidgets.QVBoxLayout(self)

        self.control_bar_layout = QtWidgets.QHBoxLayout()

        self.status_label = QtWidgets.QLabel()

        self.control_bar_layout.addWidget(self.status_label)

        self.control_bar_layout.addStretch()

        self.previewer_selector = QtWidgets.QComboBox(self)
        def on_previewer_selected(index: int):
            previewer = self.previewer_selector.currentData()
            if previewer is None:
                return
            self.select_previewer(previewer)
        self.previewer_selector.currentIndexChanged.connect(on_previewer_selected)

        self.control_bar_layout.addWidget(self.previewer_selector)

        self.widget_layout.addLayout(self.control_bar_layout)

        self.hex_viewer = HexViewer()
        self.previewer_selector.addItem(PREVIEW_HEX_VIEWER, self.hex_viewer)
        self._previewers.append(self.hex_viewer)

        self.code_editor = CodeEditor()
        self.previewer_selector.addItem(PREVIEW_CODE_VIEWER, self.code_editor)
        self._previewers.append(self.code_editor)

        self.texture_viewer = TextureViewer()
        self.previewer_selector.addItem(PREVIEW_TEXTURE_VIEWER, self.texture_viewer)
        self._previewers.append(self.texture_viewer)

        for previewer in self._previewers:
            previewer.setVisible(False)
            self.widget_layout.addWidget(previewer)

        self.widget_layout.addWidget(self.message_label)

        self.set_control_bar_visible(False)

    def _set_data_for_previewer(self, previewer: QtWidgets.QWidget, data: NPKEntry | None):
        """
        Set the data for the previewer.
        
        :param previewer: The previewer to set the data for.
        :param data: The NPK entry data to set.
        """
        if isinstance(previewer, HexViewer):
            previewer.setData(bytearray(data.data) if data is not None else bytearray())
        elif isinstance(previewer, CodeEditor):
            if data is None:
                previewer.set_content("")
            else:
                previewer.set_content(data.data.decode("utf-8", errors="replace"), data.extension)
        elif isinstance(previewer, TextureViewer):
            if data is None:
                previewer.clear()
            else:
                try:
                    previewer.set_texture(data.data, data.extension)
                except ValueError:
                    previewer.setVisible(False)
                    self.message_label.setText(f"Unsupported image format: {data.extension}")
                    self.message_label.setVisible(True)

    def set_control_bar_visible(self, visible: bool):
        """
        Set the visibility of the control bar.
        
        :param visible: Whether to show or hide the control bar.
        """
        self.status_label.setVisible(visible)
        self.previewer_selector.setVisible(visible)

    def select_previewer(self, previewer: QtWidgets.QWidget):
        """
        Select a previewer to display.
        
        :param previewer: The previewer to display.
        """
        self.message_label.setVisible(False)
        for p in self._previewers:
            # Memory cleanup
            self._set_data_for_previewer(p, None)
            p.setVisible(False)
        previewer.setVisible(True)

        if self._current_entry is None:
            return

        # Update the previewer with the current entry data
        self._set_data_for_previewer(previewer, self._current_entry)

    def set_file(self, npk_entry: NPKEntry):
        """
        Set the file to be previewed and select the appropriate previewer.
        
        :param npk_entry: The NPK entry to preview.
        """
        self.clear()

        self._current_entry = npk_entry

        self.status_label.setText(f"Signature: {hex(npk_entry.file_signature)} | " +
                                  f"Size: {format_bytes(npk_entry.file_original_length)}")

        self.set_control_bar_visible(True)

        for previewer in self._previewers:
            if hasattr(previewer, "accepted_extensions"):
                if npk_entry.extension in getattr(previewer, "accepted_extensions"):
                    self.select_previewer(previewer)
                    self.previewer_selector.setCurrentIndex(
                        self.previewer_selector.findData(previewer)
                    )
                    return

        if npk_entry.data_flags & NPKEntryDataFlags.TEXT:
            self.previewer_selector.setCurrentText(PREVIEW_CODE_VIEWER)
            self.select_previewer(self.code_editor)
        else:
            self.previewer_selector.setCurrentText(PREVIEW_HEX_VIEWER)
            self.select_previewer(self.hex_viewer)
        self.message_label.setText(UNKNOWN_FILE_TYPE_TEXT)
        self.message_label.setVisible(True)

    def clear(self):
        """
        Clear the preview.
        """
        for previewer in self._previewers:
            # Cleanup data in previewer to save memory
            self._set_data_for_previewer(previewer, None)
            previewer.setVisible(False)
        self.set_control_bar_visible(False)
        self.message_label.setText(SELECT_ENTRY_TEXT)
        self.message_label.setVisible(True)
        self._current_entry = None
