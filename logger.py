"""Logger module."""

import logging
import inspect
from PySide6.QtCore import QtMsgType, qInstallMessageHandler, QMessageLogContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Print logs to the console
    ]
)

def custom_logging_handler(mode: QtMsgType, _context: QMessageLogContext, message: str | None):
    """
    Custom logging handler for Qt to log messages to a file.

    :param mode: The type of message (debug, info, warning, critical, fatal).
    :param _context: The context of the message.
    :param message: The message to log.
    """
    # Get a logger with name "Qt" for all Qt messages
    qt_logger = logging.getLogger("Qt")

    if mode == QtMsgType.QtDebugMsg:
        qt_logger.debug(message)
    elif mode == QtMsgType.QtInfoMsg:
        qt_logger.info(message)
    elif mode == QtMsgType.QtWarningMsg:
        qt_logger.warning(message)
    elif mode == QtMsgType.QtCriticalMsg:
        qt_logger.critical(message)
    elif mode == QtMsgType.QtFatalMsg:
        qt_logger.fatal(message)

qInstallMessageHandler(custom_logging_handler)

def get_logger(module_name=None):
    """
    Get a logger with a specific module name.
    
    :param module_name: The name of the module. If None, uses the caller's module name.
    :return: A logger instance with the specified name.
    """
    if module_name is None:
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        module_name = module.__name__ if module else "unknown"

    if module_name == "__main__":
        return default_logger

    return logging.getLogger(module_name)

# Default logger with the main application name
default_logger = get_logger("NeoXtractor")
