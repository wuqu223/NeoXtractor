"""Provides a preview widget for Main Window."""

from PySide6 import QtWidgets, QtCore

from core.npk.enums import NPKEntryFileType
from core.npk.types import NPKEntry
from gui.widgets.code_editor import CodeEditor

SELECT_ENTRY_TEXT = "Select an entry to preview."
SELECT_PREVIEWER_TEXT = "Unknown file type, select a previewer manually."

PREVIEW_CODE_VIEWER = "Code Viewer"

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

        self.code_editor = CodeEditor()
        self.previewer_selector.addItem(PREVIEW_CODE_VIEWER, self.code_editor)
        self._previewers.append(self.code_editor)

        for previewer in self._previewers:
            previewer.setVisible(False)
            self.widget_layout.addWidget(previewer)

        self.widget_layout.addWidget(self.message_label)

        self.set_control_bar_visible(False)

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
            p.setVisible(False)
        previewer.setVisible(True)

        if self._current_entry is None:
            return

        # Update the previewer with the current entry data
        if isinstance(previewer, CodeEditor):
            self.code_editor.set_content(self._current_entry.data.decode("utf-8", errors="replace"), self._current_entry.extension)

    def set_file(self, npk_entry: NPKEntry):
        """
        Set the file to be previewed and select the appropriate previewer.
        
        :param npk_entry: The NPK entry to preview.
        """
        self._current_entry = npk_entry

        self.status_label.setText(f"Signature: {hex(npk_entry.file_signature)} | Size: {npk_entry.file_original_length} bytes")

        self.set_control_bar_visible(True)

        if npk_entry.file_type == NPKEntryFileType.TEXT:
            self.previewer_selector.setCurrentText(PREVIEW_CODE_VIEWER)
            self.select_previewer(self.code_editor)
        else:
            self.previewer_selector.setCurrentIndex(-1)
            self.message_label.setText(SELECT_PREVIEWER_TEXT)
            self.message_label.setVisible(True)
            for previewer in self._previewers:
                previewer.setVisible(False)

    def clear(self):
        """
        Clear the preview.
        """
        for previewer in self._previewers:
            previewer.setVisible(False)
        self.set_control_bar_visible(False)
        self.message_label.setText("Select a file to preview.")
        self.message_label.setVisible(True)
        self._current_entry = None
