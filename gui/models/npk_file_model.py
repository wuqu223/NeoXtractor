"""A custom model for displaying NPK files in a QListView."""

from typing import Any, cast
from PySide6 import QtCore, QtWidgets

from core.config import Config
from core.npk.npk_file import NPKFile

class NPKFileModel(QtCore.QAbstractListModel):
    """
    Custom model for displaying NPK files in a QListView.
    """

    def __init__(self, npk_file: NPKFile, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self._npk_file = npk_file
        app = cast(QtCore.QCoreApplication, QtWidgets.QApplication.instance())
        self._game_config: Config = app.property("game_config")

    def rowCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex = QtCore.QModelIndex()) -> int:
        return self._npk_file.file_count

    def data(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            entry_index = self._npk_file.indices[index.row()]
            if hex(entry_index.file_signature) in self._game_config.entry_signature_name_map:
                base_name = self._game_config.entry_signature_name_map[hex(entry_index.file_signature)]
                if self._npk_file.is_entry_loaded(index.row()):
                    return base_name + "." + self._npk_file.entries[index.row()].extension
                return base_name
            return entry_index.filename if not self._npk_file.is_entry_loaded(index.row()) else self._npk_file.entries[index.row()].filename
        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            parent = self.parent()
            if not isinstance(parent, QtWidgets.QWidget):
                return None
            return parent.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload if not self._npk_file.is_entry_loaded(index.row()) else QtWidgets.QStyle.StandardPixmap.SP_FileIcon)
        if role == QtCore.Qt.ItemDataRole.UserRole:
            return self._npk_file.indices[index.row()]
        return None
