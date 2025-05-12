from PyQt5.QtWidgets import (QApplication, QTableView, QMenu, QAction)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import (Qt, QMimeData)

from .hex_table_model import BYTES_PER_LINE, HexTableModel

class HexTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def keyPressEvent(self, event):
        """Override Ctrl+C (Cmd+C) to copy formatted lines by default."""
        if event.matches(QKeySequence.Copy):
            self.copy_selection_formatted()
            event.accept()
        else:
            super().keyPressEvent(event) # Pass other key presses to base class

    def show_context_menu(self, pos):
        """Show custom context menu for copying."""
        menu = QMenu(self)
        selected_indexes = self.selectionModel().selectedIndexes()

        action_copy_formatted = QAction("Copy Formatted Lines", self)
        action_copy_formatted.triggered.connect(self.copy_selection_formatted)
        action_copy_formatted.setEnabled(bool(selected_indexes))
        menu.addAction(action_copy_formatted)

        action_copy_hex = QAction("Copy Hex Only", self)
        action_copy_hex.triggered.connect(self.copy_selection_hex)
        action_copy_hex.setEnabled(bool(selected_indexes))
        menu.addAction(action_copy_hex)

        action_copy_ascii = QAction("Copy ASCII Only", self)
        action_copy_ascii.triggered.connect(self.copy_selection_ascii)
        action_copy_ascii.setEnabled(bool(selected_indexes))
        menu.addAction(action_copy_ascii)

        action_copy_raw = QAction("Copy Raw Bytes", self)
        action_copy_raw.triggered.connect(self.copy_selection_raw)
        action_copy_raw.setEnabled(bool(selected_indexes))
        menu.addAction(action_copy_raw)

        # --- Add selection actions ---
        menu.addSeparator()
        action_select_all = QAction("Select All", self)
        action_select_all.triggered.connect(self.selectAll)
        menu.addAction(action_select_all)

        action_clear_selection = QAction("Clear Selection", self)
        action_clear_selection.triggered.connect(self.clearSelection)
        action_clear_selection.setEnabled(bool(selected_indexes))
        menu.addAction(action_clear_selection)


        # Display the menu
        menu.exec_(self.viewport().mapToGlobal(pos))

    # --- Helper to get selected rows/bytes ---

    def get_unique_selected_rows(self):
        """Returns a sorted list of unique selected row indices."""
        if not self.selectionModel():
            return []
        selected_indexes = self.selectionModel().selectedIndexes()
        return sorted(list(set(index.row() for index in selected_indexes)))

    def get_selected_byte_indices(self):
        """
        Gets a sorted list of unique (row, byte_index_in_row) tuples
        corresponding to the selected cells. More complex mapping.
        Returns None if model is not HexTableModel.
        """
        if not self.selectionModel() or not isinstance(self.model(), HexTableModel):
            return None

        selected_indexes = self.selectionModel().selectedIndexes()
        byte_indices = set()

        for index in selected_indexes:
            row = index.row()
            col = index.column()

            if col == 1: # Hex column
                # Map selection within the hex string back to byte index
                # This requires knowing selection start/end within the cell text,
                # which is not directly available from QModelIndex alone.
                # For simplicity, we'll treat selection in hex column as selecting
                # *all* bytes in that row for raw/hex/ascii copy purposes.
                # A more precise implementation would need mouse tracking or text cursor pos.
                for i in range(BYTES_PER_LINE):
                     # Check if byte actually exists at this position
                    if self.model().get_byte(row, i) is not None:
                        byte_indices.add((row, i))

            elif col == 2: # ASCII column
                # Treat selection in ASCII column as selecting *all* bytes in that row.
                 for i in range(BYTES_PER_LINE):
                    if self.model().get_byte(row, i) is not None:
                        byte_indices.add((row, i))
            # Ignore Offset column (col 0) for byte selection

        # Sort by row, then byte index within row
        return sorted(list(byte_indices), key=lambda x: (x[0], x[1]))


    # --- Copy Methods ---

    def copy_selection_formatted(self):
        """Copies full lines (Offset | Hex | ASCII) for selected rows."""
        if not self.model(): return
        model = self.model() # QAbstractTableModel
        selected_rows = self.get_unique_selected_rows()
        if not selected_rows: return

        lines = []
        for row in selected_rows:
            offset_data = model.data(model.index(row, 0), Qt.DisplayRole)
            hex_data = model.data(model.index(row, 1), Qt.DisplayRole)
            ascii_data = model.data(model.index(row, 2), Qt.DisplayRole)
            # Ensure consistent formatting even if data retrieval returns None/empty
            offset_str = offset_data if offset_data is not None else " " * 8
            hex_str = hex_data if hex_data is not None else " " * (BYTES_PER_LINE * 3 -1)
            ascii_str = ascii_data if ascii_data is not None else " " * BYTES_PER_LINE
            lines.append(f"{offset_str} | {hex_str} | {ascii_str}")

        QApplication.clipboard().setText("\n".join(lines))

    def copy_selection_hex(self):
        """Copies only the Hexadecimal representation of selected bytes."""
        if not isinstance(self.model(), HexTableModel): return
        model = self.model()
        byte_coords = self.get_selected_byte_indices() # Gets (row, byte_idx) list
        if not byte_coords: return

        hex_parts = []
        current_row = -1
        line_hex = []
        for row, byte_idx in byte_coords:
            byte_val = model.get_byte(row, byte_idx)
            if byte_val is not None:
                 hex_parts.append(f"{byte_val:02X}")

        # Simple space separation for now. Could add newlines per row.
        QApplication.clipboard().setText(" ".join(hex_parts))


    def copy_selection_ascii(self):
        """Copies only the ASCII representation of selected bytes."""
        if not isinstance(self.model(), HexTableModel): return
        model = self.model()
        byte_coords = self.get_selected_byte_indices()
        if not byte_coords: return

        ascii_chars = []
        for row, byte_idx in byte_coords:
             byte_val = model.get_byte(row, byte_idx)
             if byte_val is not None:
                ascii_chars.append(chr(byte_val) if 32 <= byte_val <= 126 else ".")

        QApplication.clipboard().setText("".join(ascii_chars))

    def copy_selection_raw(self):
        """Copies the raw bytes corresponding to the selection."""
        if not isinstance(self.model(), HexTableModel): return
        model = self.model()
        byte_coords = self.get_selected_byte_indices()
        if not byte_coords: return

        raw_bytes_list = []
        for row, byte_idx in byte_coords:
            byte_val = model.get_byte(row, byte_idx)
            if byte_val is not None:
                raw_bytes_list.append(byte_val)

        # Use QMimeData to put raw bytes onto the clipboard
        mime_data = QMimeData()
        mime_data.setData("application/octet-stream", bytes(raw_bytes_list))
        # Provide a text fallback for apps that don't handle octet-stream
        # (e.g., simple hex string)
        hex_fallback = " ".join(f"{b:02X}" for b in raw_bytes_list)
        mime_data.setText(hex_fallback) # Optional fallback

        QApplication.clipboard().setMimeData(mime_data)