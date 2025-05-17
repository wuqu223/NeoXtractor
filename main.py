"""NeoXtractor entrypoint"""

from gui import run as run_gui

def run_cli():
    """Run NeoXtractor as a CLI application."""
    raise NotImplementedError("CLI mode is not implemented yet.")

if __name__ == "__main__":
    run_gui()
