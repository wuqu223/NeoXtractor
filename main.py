"""NeoXtractor entrypoint"""

import sys
from PySide6 import QtWidgets

from gui.windows.main_window import MainWindow
from logger import get_logger

def run_gui():
    """Run NeoXtractor as a GUI application."""

    get_logger().info("Starting NeoXtractor in GUI mode...")

    app = QtWidgets.QApplication(sys.argv)

    main_window = MainWindow()
    main_window.resize(600, 1000)
    main_window.show()

    sys.exit(app.exec())

def run_cli():
    """Run NeoXtractor as a CLI application."""
    raise NotImplementedError("CLI mode is not implemented yet.")

if __name__ == "__main__":
    run_gui()
