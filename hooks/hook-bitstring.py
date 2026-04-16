from PyInstaller.utils.hooks import collect_submodules

hiddenimports = (
    collect_submodules("bitstring", on_error="warn once")
    + collect_submodules("tibs", on_error="warn once")
)
