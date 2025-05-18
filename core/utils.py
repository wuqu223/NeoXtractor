"""Shared utility functions for the application."""

import os
import sys

from core.config import Config
from core.npk.npk_file import NPKFile

def get_application_path():
    """
    Returns the base path of the application, works both in development
    and when packaged with PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temporary folder and stores path in _MEIPASS
        application_path = getattr(sys, '_MEIPASS')
    else:
        # Get the directory of the main script when running normally
        application_path = os.path.dirname(os.path.abspath(sys.argv[0]))

    return application_path

def get_filename_in_config(config: Config, index: int, file: NPKFile) -> str:
    """
    Get the filename for a given index in the config.
    
    :param config: The game config.
    :param index: The index of the file.
    :param file: The NPK file.
    :return: The filename.
    """
    entry_index = file.indices[index]
    if hex(entry_index.file_signature) in config.entry_signature_name_map:
        base_name = config.entry_signature_name_map[hex(entry_index.file_signature)]
        if file.is_entry_loaded(index):
            name = base_name + "." + file.entries[index].extension
            return name
        return base_name
    name = entry_index.filename if not file.is_entry_loaded(index) else file.entries[index].filename
    return name
