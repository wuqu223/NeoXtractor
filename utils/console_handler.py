import sys, traceback
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
# from PyQt5.QtGui import *

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    print("Unhandled exception", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

class ConsoleOutputHandler(QObject):
    text_output = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.consoles = []  # Store all console widgets

    def add_console(self, console):
        """Add a new console QTextEdit widget to the handler."""
        self.consoles.append(console)
        self.text_output.connect(console.append)  # Connect the signal to the console's append method

    def write(self, text):
        if text.strip():  # Avoid emitting empty lines
            self.text_output.emit(text)
            sys.__stdout__.write(text)

    def handle_status_update(self, text: str):
        """Handle status updates from the thread."""
        self.text_output.emit(text)

    def flush(self):
        sys.__stdout__.flush()

def redirect_output(console_handler):
    sys.stdout = console_handler
    sys.stderr = console_handler

class ConsoleWidget(QWidget):
    def __init__(self, console_handler):
        super().__init__()
        
        # Set up layout for this widget
        layout = QVBoxLayout(self)

        # Create a QTextEdit for console output
        self.console_output = QTextEdit()
        self.console_output.setMinimumWidth(150)
        self.console_output.setReadOnly(True)

        # Connect the console handler to this console's append method
        console_handler.add_console(self.console_output)
        
        # Add to layout
        layout.addWidget(self.console_output)
