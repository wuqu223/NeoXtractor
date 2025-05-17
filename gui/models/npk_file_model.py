"""A custom model for displaying NPK files in a QListView."""

from typing import Any
from PySide6 import QtCore, QtGui, QtWidgets

from core.npk.npk_file import NPKFile

class NPKFileModel(QtCore.QAbstractListModel):
    """
    Custom model for displaying NPK files in a QListView.
    """

    def __init__(self, npk_file: NPKFile, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self._npk_file = npk_file

    def rowCount(self, _parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        return self._npk_file.file_count

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._npk_file.indices[index.row()].filename if not self._npk_file.is_entry_loaded(index.row()) else self._npk_file.entries[index.row()].filename
        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            parent = self.parent()
            if not isinstance(parent, QtWidgets.QWidget):
                return None
            return parent.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload if not self._npk_file.is_entry_loaded(index.row()) else QtWidgets.QStyle.StandardPixmap.SP_FileIcon)
        if role == QtCore.Qt.ItemDataRole.UserRole:
            return self._npk_file.indices[index.row()]
        return None
