import logging
from PyQt5.QtCore import QtMsgType, qInstallMessageHandler, QMessageLogContext

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logfile.txt", mode="a"),  # Write logs to a file
        logging.StreamHandler()  # Optional: Print logs to the console
    ]
)

def custom_logging_handler(mode: QtMsgType, _context: QMessageLogContext, message: str | None):
    """
    Custom logging handler for PyQt5 to log messages to a file.

    :param mode: The type of message (debug, info, warning, critical, fatal).
    :param _context: The context of the message.
    :param message: The message to log.
    """
    if mode == QtMsgType.QtDebugMsg:
        logger.debug(message)
    elif mode == QtMsgType.QtInfoMsg:
        logger.info(message)
    elif mode == QtMsgType.QtWarningMsg:
        logger.warning(message)
    elif mode == QtMsgType.QtCriticalMsg:
        logger.critical(message)
    elif mode == QtMsgType.QtFatalMsg:
        logger.fatal(message)

qInstallMessageHandler(custom_logging_handler)

# Get the logger instance
logger = logging.getLogger("PyQtAppLogger")
