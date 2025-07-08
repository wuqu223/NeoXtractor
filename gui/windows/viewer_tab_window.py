"""Provides a shared class for viewers to have a tabbed window."""

import os

from typing import Type, TypeVar
from PySide6 import QtWidgets, QtCore

from gui.utils.viewer import get_viewer_display_name, set_data_for_viewer

T = TypeVar("T", bound=QtWidgets.QWidget)

class ViewerTabWindow(QtWidgets.QMainWindow):
    """
    A window that manages viewer tabs for displaying files.
    This window provides a tabbed interface for viewing files with a specific viewer. It allows 
    opening multiple files, each in its own tab, and manages the visibility of tabs and a message
    when no files are open.
    Methods:
        load_file(data: bytes, filename: str): Loads file data into a new viewer tab.
    """
    def __init__(self, viewer: Type[T], parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._viewer_factory = viewer
        self._viewer_name = get_viewer_display_name(viewer)

        self.setWindowTitle(self._viewer_name)
        self.setMinimumSize(800, 600)

        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.central_layout = QtWidgets.QVBoxLayout(self.central_widget)

        self.no_tab_label = QtWidgets.QLabel("No file opened.")
        self.no_tab_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.no_tab_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        self.tab_widget = QtWidgets.QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setVisible(False)
        self.tab_widget.tabCloseRequested.connect(
            lambda index: (
                self.tab_widget.removeTab(index),
                (
                    self.setWindowTitle(self._viewer_name),
                    self.tab_widget.setVisible(False),
                    self.no_tab_label.setVisible(True)
                ) if self.tab_widget.count() == 0 else None
            )
        )
        self.tab_widget.currentChanged.connect(
            lambda index: (self.setWindowTitle(f"{self.tab_widget.tabText(index)} - {self._viewer_name}"),
                           self._load_lazy_data(index))
        )
        self.central_layout.addWidget(self.no_tab_label)
        self.central_layout.addWidget(self.tab_widget)

        def file_menu() -> QtWidgets.QMenu:
            menu = QtWidgets.QMenu("File", self)

            open_file_action = menu.addAction("Open File")
            open_file_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon))
            open_file_action.setShortcut("Ctrl+O")
            def open_file_dialog():
                file_filter = "All Files (*)"
                if hasattr(self._viewer_factory, "accepted_extensions"):
                    extensions = getattr(self._viewer_factory, "accepted_extensions")
                    file_filter = f"Supported Files (*.{' *.'.join(extensions)})"
                    if (hasattr(self._viewer_factory, "allow_unsupported_extensions") and \
                         getattr(self._viewer_factory, "allow_unsupported_extensions")):
                        file_filter += " ;; All Files (*)"
                file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
                    self,
                    "Open File",
                    "",
                    file_filter
                )
                for i, file_path in enumerate(file_paths):
                    if file_path:
                        with open(file_path, "rb") as file:
                            data = file.read()
                            filename = os.path.basename(file_path)
                            self.load_file(data, filename, i == 0, i != 0)
            open_file_action.triggered.connect(open_file_dialog)

            close_all_action = menu.addAction("Close All")
            close_all_action.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DockWidgetCloseButton))
            close_all_action.triggered.connect(
                lambda: (
                    self.tab_widget.clear(),
                    self.setWindowTitle(self._viewer_name),
                    self.tab_widget.setVisible(False),
                    self.no_tab_label.setVisible(True)
                )
            )

            return menu

        self.menuBar().addMenu(file_menu())

        if hasattr(self._viewer_factory, "setup_tab_window"):
            getattr(self._viewer_factory, "setup_tab_window")(self)

    def _load_lazy_data(self, index: int):
        """
        Load data for the viewer at the specified index if it has not been loaded yet.
        
        :param index: The index of the tab to load data for.
        """
        if self.tab_widget.count() == 0:
            return
        viewer = self.tab_widget.widget(index)
        if not hasattr(viewer, "_lazy_load_data"):
            return
        data, filename = getattr(viewer, "_lazy_load_data")
        setattr(viewer, "_lazy_load_data", None) # Clear lazy load data
        try:
            set_data_for_viewer(viewer, data, os.path.splitext(filename)[1][1:])
        except ValueError as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                str(e)
            )
            self.tab_widget.removeTab(index)

    def load_file(self, data: bytes, filename: str, take_focus = True, lazy_load = False):
        """
        Load a file.
        
        :param data: The file data to load.
        :param extension: The file extension.
        """
        viewer = self._viewer_factory()
        if lazy_load:
            setattr(viewer, "_lazy_load_data", (data, filename))
        else:
            try:
                set_data_for_viewer(viewer, data, os.path.splitext(filename)[1][1:])
            except ValueError as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    str(e)
                )
                return
        idx = self.tab_widget.addTab(viewer, filename)
        if take_focus:
            self.tab_widget.setCurrentIndex(idx)
        self.no_tab_label.setVisible(False)
        self.tab_widget.setVisible(True)
