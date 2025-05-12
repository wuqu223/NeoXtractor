import math
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant

BYTES_PER_LINE = 16

class HexTableModel(QAbstractTableModel):
    """
    A model to provide hex data to a QTableView on demand.
    """
    def __init__(self, data: bytes = b'', parent=None):
        super().__init__(parent)
        self._data = data
        self._rows = math.ceil(len(self._data) / BYTES_PER_LINE)

        # Pre-calculate font metrics for column width estimation
        # Use a typical monospace font
        self.mono_font = QFont("Courier", 10)
        fm = QFontMetrics(self.mono_font)

        # Estimate column widths
        # Offset: 8 hex chars + padding
        self._offset_width = fm.horizontalAdvance("00000000") + 20
        # Hex: (3 chars * BYTES_PER_LINE) + padding (e.g., "FF ")
        hex_sample = " ".join(["FF"] * BYTES_PER_LINE)
        self._hex_width = fm.horizontalAdvance(hex_sample) + 20
        # ASCII: BYTES_PER_LINE chars + padding
        ascii_sample = "W" * BYTES_PER_LINE # 'W' is often wide
        self._ascii_width = fm.horizontalAdvance(ascii_sample) + 20
    
    def get_data_chunk(self, row):
        start_offset = row * BYTES_PER_LINE
        end_offset = min(start_offset + BYTES_PER_LINE, len(self._data)) # Handle last partial line
        return self._data[start_offset:end_offset]

    def get_byte(self, row, byte_index_in_row):
        """Gets a single byte value if row/index is valid."""
        offset = row * BYTES_PER_LINE + byte_index_in_row
        if 0 <= byte_index_in_row < BYTES_PER_LINE and 0 <= offset < len(self._data):
            return self._data[offset]
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        # Return the number of 16-byte lines needed
        return self._rows

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        # Columns: Offset, Hex View, ASCII View
        return 3

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> QVariant:
        if not index.isValid():
            return QVariant()

        row = index.row()
        col = index.column()

        if role == Qt.DisplayRole:
            start_offset = row * BYTES_PER_LINE
            end_offset = start_offset + BYTES_PER_LINE
            chunk = self._data[start_offset:end_offset]

            if not chunk:
                return QVariant() # Should not happen if rowCount is correct

            if col == 0: # Offset column
                return f"{start_offset:08X}"
            elif col == 1: # Hex column
                hex_chunk = " ".join(f"{byte:02X}" for byte in chunk)
                # Pad partial lines
                return hex_chunk.ljust(BYTES_PER_LINE * 3 - 1)
            elif col == 2: # ASCII column
                # Replace non-printable chars with '.'
                # Use chr() but handle potential errors just in case (though bytes should be valid)
                try:
                    ascii_chunk = "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in chunk)
                except ValueError:
                    ascii_chunk = "." * len(chunk) # Fallback
                # Pad partial lines
                return ascii_chunk.ljust(BYTES_PER_LINE)

        elif role == Qt.FontRole:
             # Use a monospace font for alignment
            return self.mono_font

        elif role == Qt.TextAlignmentRole:
            if col == 0: # Offset
                return Qt.AlignRight | Qt.AlignVCenter
            else: # Hex and ASCII
                return Qt.AlignLeft | Qt.AlignVCenter

        return QVariant() # Default return empty QVariant

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> QVariant:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return "Offset"
            elif section == 1:
                # Construct the hex header dynamically based on BYTES_PER_LINE
                hex_header = " ".join(f"{i:02X}" for i in range(BYTES_PER_LINE))
                return hex_header
            elif section == 2:
                return "ASCII"
        return QVariant() # Default return empty QVariant

    def update_data(self, data: bytes):
        """Updates the model with new data."""
        self.beginResetModel()
        self._data = data
        self._rows = math.ceil(len(self._data) / BYTES_PER_LINE)
        self.endResetModel()

    # --- Methods for column width hints ---
    def get_offset_width_hint(self):
        return self._offset_width

    def get_hex_width_hint(self):
        return self._hex_width

    def get_ascii_width_hint(self):
        return self._ascii_width