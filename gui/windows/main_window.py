"""Provides MainWindow class."""

import os
from typing import cast

from PySide6 import QtCore, QtWidgets, QtGui

from core.config import Config
from core.npk.enums import NPKEntryFileType, NPKFileType
from core.npk.npk_file import NPKFile
from gui.config_manager import ConfigManager
from gui.models.npk_file_model import NPKFileModel
from gui.npk_entry_filter import NPKEntryFilter
from gui.utils.config import save_config_manager_to_settings
from gui.widgets.npk_file_list import NPKFileList
from gui.widgets.preview_widget import PreviewWidget
from gui.windows.about_window import AboutWindow
from gui.windows.config_manager_window import ConfigManagerWindow

class MainWindow(QtWidgets.QMainWindow):
    """Main window class."""

    # Custom signals for thread-safe UI updates
    update_progress_signal = QtCore.Signal(int)
    update_model_signal = QtCore.Signal(int)
    loading_complete_signal = QtCore.Signal()

    _config_list_refreshing = False

    def __init__(self):
        super().__init__()

        self.app = cast(QtCore.QCoreApplication, QtWidgets.QApplication.instance())

        # Connect signals to slots
        self.update_progress_signal.connect(self._update_progress)
        self.update_model_signal.connect(self._update_model)
        self.loading_complete_signal.connect(self._loading_complete)

        self.setWindowTitle("NeoXtractor")

        self.config: Config | None = None

        self.config_manager: ConfigManager = self.app.property("config_manager")

        self.main_layout = QtWidgets.QHBoxLayout()

        self.control_layout = QtWidgets.QVBoxLayout()

        self.config_section = QtWidgets.QHBoxLayout()

        self.active_config_label = QtWidgets.QLabel("Active Config:")
        self.active_config_label.setStyleSheet("font-weight: bold;")
        self.active_config_label.setFixedWidth(100)
        self.config_section.addWidget(self.active_config_label)

        self.active_config = QtWidgets.QComboBox()
        self.active_config.setMinimumWidth(200)
        self.active_config.currentIndexChanged.connect(self.on_config_changed)
        self.config_section.addWidget(self.active_config)

        self.control_layout.addLayout(self.config_section)

        self.list_widget = NPKFileList(self)
        self.list_widget.preview_entry.connect(lambda _row, entry: self.preview_widget.set_file(entry))

        self.filter = NPKEntryFilter(self.list_widget)

        self.filter_section = QtWidgets.QVBoxLayout()

        self.filter_label = QtWidgets.QLabel("Filters")
        self.filter_label.setStyleSheet("font-weight: bold;")
        self.filter_section.addWidget(self.filter_label)

        self.name_filter_input = QtWidgets.QLineEdit()
        self.name_filter_input.setPlaceholderText("Search by filename...")
        def filter_text_changed():
            self.filter.filter_string = self.name_filter_input.text().lower()
            self.filter.apply_filter()
        self.name_filter_input.textChanged.connect(filter_text_changed)
        self.filter_section.addWidget(self.name_filter_input)

        self.file_type_filter_combobox = QtWidgets.QComboBox()
        self.file_type_filter_combobox.addItem("All", None)
        for i in NPKEntryFileType:
            self.file_type_filter_combobox.addItem(i.value, i)
        self.file_type_filter_combobox.setCurrentIndex(0)
        def filter_type_changed(index: int):
            self.filter.filter_type = self.file_type_filter_combobox.itemData(index)
            self.mesh_biped_head_filter_checkbox.setVisible(self.filter.filter_type == NPKEntryFileType.MESH)
            self.filter.apply_filter()
        self.file_type_filter_combobox.currentIndexChanged.connect(filter_type_changed)
        self.filter_section.addWidget(self.file_type_filter_combobox)

        self.mesh_biped_head_filter_checkbox = QtWidgets.QCheckBox("Only 'biped head' meshes")
        self.mesh_biped_head_filter_checkbox.setVisible(False)
        def filter_mesh_biped_head_changed(checked: bool):
            self.filter.mesh_biped_head = checked
            self.filter.apply_filter()
        self.mesh_biped_head_filter_checkbox.toggled.connect(filter_mesh_biped_head_changed)
        self.filter_section.addWidget(self.mesh_biped_head_filter_checkbox)

        self.control_layout.addLayout(self.filter_section)
        self.control_layout.addWidget(self.list_widget)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.control_layout.addWidget(self.progress_bar)

        def extract_all(visible_only: bool = False):
            model = self.list_widget.model()
            all_indexes = [model.index(i, 0) for i in range(model.rowCount())]

            if visible_only:
                indexes = [idx for idx in all_indexes if not self.list_widget.isRowHidden(idx.row())]
            else:
                indexes = all_indexes
            self.list_widget.extract_entries(indexes)

        self.extract_button_widget = QtWidgets.QWidget()
        self.extract_button_widget.setVisible(False)

        self.extract_buttons = QtWidgets.QHBoxLayout()
        self.extract_button_widget.setLayout(self.extract_buttons)

        self.extract_all = QtWidgets.QPushButton("Extract All")
        self.extract_all.setStatusTip("Extract all files in the NPK file.")
        self.extract_all.clicked.connect(lambda: extract_all(False))
        self.extract_buttons.addWidget(self.extract_all)

        self.extract_filtered = QtWidgets.QPushButton("Extract Filtered")
        self.extract_filtered.setStatusTip("Extract all files in the list.")
        self.extract_filtered.clicked.connect(lambda: extract_all(True))

        self.extract_buttons.addWidget(self.extract_filtered)

        self.control_layout.addWidget(self.extract_button_widget)

        self.main_layout.addLayout(self.control_layout, stretch=1)

        self.preview_widget = PreviewWidget(self)
        self.main_layout.addWidget(self.preview_widget, stretch=2)

        # Create a central widget and set the layout on it
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

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
                if self.config is None:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "No Config Selected",
                        "Please select a config before opening a file."
                    )
                    return
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
                save_config_manager_to_settings(self.config_manager, self.app.property("settings_manager"))
                self.refresh_config_list()

            config_manager.triggered.connect(open_config_manager)

            menu.addAction(config_manager)

            return menu

        self.menuBar().addMenu(file_menu())

        self.menuBar().addAction("About",
            lambda: AboutWindow(self).exec()
        )

        self.refresh_config_list()

    def unload_npk(self):
        """Unload the NPK file."""
        self.setWindowTitle("NeoXtractor")
        self.app.setProperty("npk_file", None)
        self.list_widget.refresh_npk_file()
        self.extract_button_widget.setVisible(False)
        self.preview_widget.clear()

    def refresh_config_list(self):
        """Refresh the config list from the config manager."""
        previous_config = self.config

        self._config_list_refreshing = True

        self.active_config.clear()
        for i, config in enumerate(self.config_manager.configs):
            self.active_config.addItem(config.name)
            if previous_config == config:
                self.active_config.setCurrentIndex(i)

        self._config_list_refreshing = False

        # Trigger the config change event
        self.on_config_changed(self.active_config.currentIndex())

    def on_config_changed(self, index: int):
        """Handle config change."""

        if self._config_list_refreshing:
            return

        previous_config = self.config

        if index == -1:
            self.config = None
        else:
            self.config = self.config_manager.configs[index]

        if previous_config != self.config:
            self.unload_npk()

            self.app.setProperty("game_config", self.config)

    def load_npk(self, path: str):
        """Load an NPK file and populate the list widget."""

        self.unload_npk()

        self.setWindowTitle(f"NeoXtractor - {os.path.basename(path)}")

        self.open_file_action.setEnabled(False)
        self.active_config.setEnabled(False)
        self.name_filter_input.setEnabled(False)
        self.file_type_filter_combobox.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.progress_bar.setFormat("Reading NPK file...")
        self.progress_bar.setRange(0, 0)

        # Make it look disabled but still allow scrolling
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.list_widget.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        # Apply disabled style while keeping the widget enabled for scrolling
        self.list_widget.setStyleSheet("QListView { color: #888; background-color: #f0f0f0; }")

        npk_file = NPKFile(path)

        if npk_file.file_type == NPKFileType.EXPK and cast(Config, self.config).decryption_key is None:
            if QtWidgets.QMessageBox.warning(
                self,
                "Check Decryption Key",
                "This is an EXPK file. Make sure to set the decryption key",
                buttons=QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel,
                defaultButton=QtWidgets.QMessageBox.StandardButton.Ok,
                ) == QtWidgets.QMessageBox.StandardButton.Cancel:
                self._loading_complete()
                return

        self.app.setProperty("npk_file", npk_file)

        self.list_widget.refresh_npk_file()

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
        idx = model.index(index)
        model.get_filename(idx, invalidate_cache=True)
        self.list_widget.update(idx)

    def _loading_complete(self):
        """Handle completion of loading from the signal."""
        # Restore normal selection behavior and style when loading is complete
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.list_widget.setStyleSheet("") # Remove the disabled styling
        self.open_file_action.setEnabled(True)
        self.active_config.setEnabled(True)
        self.name_filter_input.setEnabled(True)
        self.file_type_filter_combobox.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.extract_button_widget.setVisible(True)
        self.filter.apply_filter()
