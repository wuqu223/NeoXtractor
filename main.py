"""NeoXtractor entrypoint"""

from args import arguments
from gui import run as run_gui

def run_cli():
    """Run NeoXtractor as a CLI application."""
    raise NotImplementedError("CLI mode is not implemented yet.")

if __name__ == "__main__":
    if arguments.subcommand == "gui" or arguments.subcommand is None:
        run_gui()
