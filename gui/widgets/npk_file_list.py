"""Custom QListView to display NPK files."""

from typing import cast
from PySide6 import QtCore, QtWidgets

from core.config import Config
from core.npk.npk_file import NPKFile
from gui.models.npk_file_model import NPKFileModel
from gui.utils.config import save_config_manager_to_settings

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
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Connect double-click signal to handler
        self.doubleClicked.connect(self.on_item_double_clicked)

    def model(self) -> NPKFileModel:
        """
        Get the current model of the list view.

        :return: The current model, or None if not set.
        """
        return cast(NPKFileModel, super().model())

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

    def show_context_menu(self, position):
        """
        Show a context menu for selected items.
        
        :param position: Position where the context menu was requested.
        """
        if not self.model() or self._npk_file is None:
            return

        # Check if there are any selected items
        indexes = self.selectedIndexes()
        if not indexes:
            return

        menu = QtWidgets.QMenu(self)

        if len(indexes) == 1:
            rename = menu.addAction("Rename")
            rename.triggered.connect(lambda: self.show_rename_dialog(indexes[0]))

        # Show the context menu at the current position
        menu.exec(self.viewport().mapToGlobal(position))

    def show_rename_dialog(self, index: QtCore.QModelIndex):
        """
        Show a dialog to rename the selected file.
        
        :param index: The model index of the item to rename.
        """
        if not self.model() or self._npk_file is None:
            return

        entry_index = self._npk_file.indices[index.row()]

        # Show input dialog to get new name
        new_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Rename File",
            f"Enter new name for {index.data(QtCore.Qt.ItemDataRole.DisplayRole)}:",
            QtWidgets.QLineEdit.EchoMode.Normal,
            ""
        )

        if ok and new_name:
            app = cast(QtCore.QCoreApplication, QtWidgets.QApplication.instance())
            config: Config = app.property("game_config")
            config_manager = app.property("config_manager")
            settings_manager = app.property("settings_manager")
            config.entry_signature_name_map[hex(entry_index.file_signature)] = new_name
            save_config_manager_to_settings(config_manager, settings_manager)
            self.update(self.model().index(index.row()))
