"""GUI bootstrapper"""

import os
import sys

from PySide6 import QtWidgets
from gui.config_manager import ConfigManager
from gui.settings_manager import SettingsManager
from gui.utils.config import load_config_manager_from_settings, save_config_manager_to_settings
from gui.windows.main_window import MainWindow
from logger import get_logger
from utils import get_application_path

def run():
    """Run NeoXtractor as a GUI application."""

    get_logger().info("Starting NeoXtractor in GUI mode...")

    app = QtWidgets.QApplication(sys.argv)

    first_run = not os.path.exists("settings.json")

    config_manager = ConfigManager()
    settings_manager = SettingsManager()

    app.setProperty("settings_manager", settings_manager)
    app.setProperty("config_manager", config_manager)

    # First run, setup default settings
    if first_run:
        config_manager.load_from_path(os.path.join(get_application_path(), "configs"))
        save_config_manager_to_settings(config_manager, settings_manager)
    else:
        load_config_manager_from_settings(settings_manager, config_manager)

    main_window = MainWindow()
    main_window.resize(600, 1000)
    main_window.show()

    app.exec()
