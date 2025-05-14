from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFontMetrics

from gui.widgets.hex_table_model import HexTableModel
from gui.widgets.hex_table_view import HexTableView

class HexViewerApp(QMainWindow):
    def __init__(self, data: bytes, filename: str | None, parent: QWidget | None):
        super().__init__(parent)
        self.setWindowTitle(f"{"" if filename == None else f"{filename} - "}Hex Viewer")
        self.setGeometry(100, 100, 670, 700)
        self.model = HexTableModel(data)

        # Main layout
        main_layout = QVBoxLayout()

        # Hex Viewer
        self.hex_view_table = HexTableView()
        self.hex_view_table.setModel(self.model)

        self.hex_view_table.setFont(self.model.mono_font)
        self.hex_view_table.verticalHeader().setVisible(False)
        h_header = self.hex_view_table.horizontalHeader()
        h_header.setDefaultAlignment(Qt.AlignLeft)

        self.hex_view_table.setColumnWidth(0, self.model.get_offset_width_hint())
        self.hex_view_table.setColumnWidth(1, self.model.get_hex_width_hint())
        self.hex_view_table.setColumnWidth(2, self.model.get_ascii_width_hint())
        h_header.setStretchLastSection(True)

        fm = QFontMetrics(self.model.mono_font)
        self.hex_view_table.verticalHeader().setDefaultSectionSize(fm.height() + 2)
        self.hex_view_table.setShowGrid(False)
        self.hex_view_table.setAlternatingRowColors(True)

        self.hex_view_table.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.hex_view_table.setWordWrap(False)
        self.hex_view_table.setCornerButtonEnabled(False)
        self.hex_view_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        main_layout.addWidget(self.hex_view_table)

        # Main widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
