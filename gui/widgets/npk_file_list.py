"""Custom QListView to display NPK files."""

from typing import Optional, cast
from PySide6 import QtCore, QtWidgets

from core.npk.npk_file import NPKFile
from gui.models.npk_file_model import NPKFileModel

class NPKFileList(QtWidgets.QListView):
    """
    Custom QListView to display NPK files.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._npk_file: NPKFile | None = None

        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)

        # Connect double-click signal to handler
        self.doubleClicked.connect(self.on_item_double_clicked)

    def model(self) -> Optional[NPKFileModel]:
        """
        Get the current model of the list view.

        :return: The current model, or None if not set.
        """
        return cast(Optional[NPKFileModel], super().model())

    def set_npk_file(self, npk_file: NPKFile):
        """
        Set the NPK file to be displayed in the list.

        :param npk_file: The NPK file to display.
        """

        self._npk_file = npk_file
        self.setModel(NPKFileModel(npk_file, self))

    def unload(self):
        """Unloads the current NPK file."""
        self._npk_file = None
        self.setModel(None)

    def on_item_double_clicked(self, index: QtCore.QModelIndex):
        """
        Handle double-click on an item in the list.
        
        :param index: The model index that was double-clicked.
        """
        if not self.model() or self._npk_file is None:
            return

        # Get the row index from the model index
        row_index = index.row()

        entry_index = index.data(QtCore.Qt.ItemDataRole.UserRole)

        entry = self._npk_file.read_entry(row_index)
