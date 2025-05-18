"""A custom model for displaying NPK files in a QListView."""

from typing import Any, cast
from PySide6 import QtCore, QtWidgets

from core.config import Config
from core.npk.npk_file import NPKFile

class NPKFileModel(QtCore.QAbstractListModel):
    """
    Custom model for displaying NPK files in a QListView.
    """

    _file_names_cache: dict[int, str] = {}

    def __init__(self, npk_file: NPKFile, parent: QtCore.QObject | None = None):
        super().__init__(parent)

        if isinstance(parent, QtWidgets.QWidget):
            self._loading_icon = parent.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload)
            self._file_icon = parent.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon)

        self._npk_file = npk_file
        app = cast(QtCore.QCoreApplication, QtWidgets.QApplication.instance())
        self._game_config: Config = app.property("game_config")

    def rowCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex = QtCore.QModelIndex()) -> int:
        return self._npk_file.file_count

    def data(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.get_filename(index)
        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            if not self._npk_file.is_entry_loaded(index.row()):
                return self._loading_icon

            return self._file_icon
        if role == QtCore.Qt.ItemDataRole.UserRole:
            return self._npk_file.indices[index.row()]
        return None

    def get_filename(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, invalidate_cache = False) -> str:
        """Get the filename for a given index."""
        if not index.isValid():
            return ""

        if index.row() in self._file_names_cache and not invalidate_cache:
            return self._file_names_cache[index.row()]

        entry_index = self._npk_file.indices[index.row()]
        if hex(entry_index.file_signature) in self._game_config.entry_signature_name_map:
            base_name = self._game_config.entry_signature_name_map[hex(entry_index.file_signature)]
            if self._npk_file.is_entry_loaded(index.row()):
                name = base_name + "." + self._npk_file.entries[index.row()].extension
                self._file_names_cache[index.row()] = name
                return name
            self._file_names_cache[index.row()] = base_name
            return base_name
        name = entry_index.filename if not self._npk_file.is_entry_loaded(index.row()) else self._npk_file.entries[index.row()].filename
        self._file_names_cache[index.row()] = name
        return name
