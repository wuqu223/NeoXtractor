"""Provides MainWindow class."""

import os
from typing import cast

from PySide6 import QtCore, QtWidgets, QtGui

from core.config import Config
from core.npk.npk_file import NPKFile
from gui.config_manager import ConfigManager
from gui.models.npk_file_model import NPKFileModel
from gui.settings_manager import SettingsManager
from gui.utils.config import get_config_dict_list
from gui.widgets.npk_file_list import NPKFileList
from gui.windows.config_manager_window import ConfigManagerWindow
from utils import get_application_path

class MainWindow(QtWidgets.QMainWindow):
    """Main window class."""

    # Add a custom signal for thread-safe UI updates
    update_progress_signal = QtCore.Signal(int)
    update_model_signal = QtCore.Signal(int)
    loading_complete_signal = QtCore.Signal()

    def __init__(self):
        super().__init__()

        # Connect signals to slots
        self.update_progress_signal.connect(self._update_progress)
        self.update_model_signal.connect(self._update_model)
        self.loading_complete_signal.connect(self._loading_complete)

        self.setWindowTitle("NeoXtractor")

        # TODO: See if this required to be stored in here.
        self.npk_file: NPKFile | None = None

        first_run = not os.path.exists("settings.json")
        self.config_manager = ConfigManager()
        self.settings_manager = SettingsManager()

        # First run, setup default settings
        if first_run:
            self.config_manager.load_from_path(os.path.join(get_application_path(), "configs"))
            self.settings_manager.set("gameconfigs",
                                      get_config_dict_list(self.config_manager),
                                      True)
        else:
            self.config_manager.add_configs([Config.from_dict(config) for config in
                                             self.settings_manager.get("gameconfigs", [])])

        self.main_layout = QtWidgets.QVBoxLayout()

        # Create a central widget and set the layout on it
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        self.config_section = QtWidgets.QHBoxLayout()

        self.active_config_label = QtWidgets.QLabel("Active Config:")
        self.active_config_label.setStyleSheet("font-weight: bold;")
        self.active_config_label.setFixedWidth(100)
        self.config_section.addWidget(self.active_config_label)

        self.active_config = QtWidgets.QComboBox()
        self.active_config.setMinimumWidth(200)
        self.config_section.addWidget(self.active_config)

        self.main_layout.addLayout(self.config_section)

        self.list_widget = NPKFileList(self)
        self.main_layout.addWidget(self.list_widget)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)

        self.open_file_action: QtGui.QAction

        def file_menu() -> QtWidgets.QMenu:
            menu = QtWidgets.QMenu(title="File")

            open_file = QtGui.QAction(
                self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon),
                "Open File",
                self
            )
            open_file.setStatusTip("Open a NPK file.")
            open_file.setShortcut("Ctrl+O")
            menu.addAction(open_file)

            def open_file_dialog():
                file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                    self,
                    "Open NPK File",
                    "",
                    "NPK Files (*.npk);;All Files (*)"
                )
                if file_path:
                    self.load_npk(file_path)

            open_file.triggered.connect(open_file_dialog)
            self.open_file_action = open_file

            menu.addSeparator()

            config_manager = QtGui.QAction(
                self.style().standardIcon(
                    QtWidgets.QStyle.StandardPixmap.SP_FileDialogContentsView
                ),
                "Config Manager",
                self
            )
            config_manager.setStatusTip("Open the Config Manager.")
            config_manager.setShortcut("Ctrl+M")

            def open_config_manager():
                dialog = ConfigManagerWindow(self.config_manager)
                dialog.exec()
                self.refresh_config_list()

            config_manager.triggered.connect(open_config_manager)

            menu.addAction(config_manager)

            return menu

        self.menuBar().addMenu(file_menu())

        self.refresh_config_list()

    def refresh_config_list(self):
        """Refresh the config list from the config manager."""
        self.active_config.clear()
        for config in self.config_manager.configs:
            self.active_config.addItem(config.name)
        self.active_config.setCurrentIndex(0)

    def load_npk(self, path: str):
        """Load an NPK file and populate the list widget."""
        self.open_file_action.setEnabled(False)
        self.active_config.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.list_widget.unload()

        self.progress_bar.setFormat("Reading NPK file...")
        self.progress_bar.setRange(0, 0)

        # Make it look disabled but still allow scrolling
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.list_widget.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        # Apply disabled style while keeping the widget enabled for scrolling
        self.list_widget.setStyleSheet("QListView { color: #888; background-color: #f0f0f0; }")

        npk_file = self.npk_file = NPKFile(path)
        self.list_widget.set_npk_file(self.npk_file)

        self.progress_bar.setFormat("Loading entries... (%v/%m)")
        self.progress_bar.setRange(0, npk_file.file_count)
        self.progress_bar.setValue(0)

        def _load_entries():
            for i in range(npk_file.file_count):
                npk_file.read_entry(i)
                self.update_model_signal.emit(i)
                self.update_progress_signal.emit(i + 1)

            self.loading_complete_signal.emit()

        QtCore.QThreadPool.globalInstance().start(_load_entries)

    def _update_progress(self, value):
        """Update progress bar value from the signal."""
        self.progress_bar.setValue(value)

    def _update_model(self, index):
        """Update model from the signal."""
        model = cast(NPKFileModel, self.list_widget.model())
        self.list_widget.update(model.index(index))

    def _loading_complete(self):
        """Handle completion of loading from the signal."""
        # Restore normal selection behavior and style when loading is complete
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.list_widget.setStyleSheet("") # Remove the disabled styling
        self.open_file_action.setEnabled(True)
        self.active_config.setEnabled(True)
        self.progress_bar.setVisible(False)
