from PySide6 import QtWidgets, QtCore, QtGui

class HexArea(QtWidgets.QWidget):
    """
    A widget that displays a hex view of the given data.
    """

    cursorPositionChanged = QtCore.Signal(int)  # Offset in bytes
    selectionChanged = QtCore.Signal(int, int)  # Start and end offsets

    # Data
    _data = bytearray()
    _addressing_base = 16
    _bytes_per_line = 16
    _bytes_per_group = 4
    _show_ascii = True

    # State
    _cursor_pos = 0
    _selection_start = -1
    _selection_end = -1
    _visible_lines = 0
    _total_width = 0

    # Colors
    _address_color = QtGui.QColor(80, 80, 80)
    _hex_color = QtGui.QColor(0, 0, 0)
    _ascii_color = QtGui.QColor(0, 0, 180)
    _highlight_bg_color = QtGui.QColor(220, 240, 255)
    _highlight_fg_color = QtGui.QColor(0, 0, 0)
    _selection_bg_color = QtGui.QColor(180, 220, 255)
    _selection_fg_color = QtGui.QColor(0, 0, 0)
    _alternate_row_color = QtGui.QColor(245, 245, 245)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._main_layout = QtWidgets.QGridLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._hex_widget = QtWidgets.QWidget(self)

        self._main_layout.addWidget(self._hex_widget, 0, 0)

        self._v_scrollbar = QtWidgets.QScrollBar(QtCore.Qt.Orientation.Vertical, self)
        self._h_scrollbar = QtWidgets.QScrollBar(QtCore.Qt.Orientation.Horizontal, self)
        self._v_scrollbar.setVisible(False)
        self._v_scrollbar.valueChanged.connect(self.update)
        self._h_scrollbar.setVisible(False)
        self._h_scrollbar.valueChanged.connect(self.update)
        self._main_layout.addWidget(self._v_scrollbar, 0, 1)
        self._main_layout.addWidget(self._h_scrollbar, 1, 0)

        self._corner_widget = QtWidgets.QWidget()
        self._corner_widget.setFixedSize(self._v_scrollbar.width(), self._h_scrollbar.height())
        self._corner_widget.setAutoFillBackground(True)
        self._main_layout.addWidget(self._corner_widget, 1, 1)

        self._measure_font_metrics()
        self._update_scrollbar()

    @property
    def data(self) -> bytearray:
        """Get the data being displayed."""
        return self._data

    @data.setter
    def data(self, value: bytearray):
        """Set the data to be displayed."""
        self._data = value
        self._cursor_pos = 0
        self._selection_start = -1
        self._selection_end = -1
        self._update_scrollbar()
        self.update()

    @property
    def addressing_base(self) -> int:
        """Get the addressing base."""
        return self._addressing_base

    @addressing_base.setter
    def addressing_base(self, value: int):
        """Set the addressing base."""
        if value == 0:
            self._addressing_base = 16
        elif value == 1:
            self._addressing_base = 10
        else:
            self._addressing_base = 8
        self.update()

    @property
    def bytes_per_line(self) -> int:
        """Get the number of bytes per line."""
        return self._bytes_per_line

    @bytes_per_line.setter
    def bytes_per_line(self, value: int):
        if value == 0:
            self._bytes_per_line = 8
        elif value == 1:
            self._bytes_per_line = 16
        elif value == 2:
            self._bytes_per_line = 32
        else:
            self._bytes_per_line = 64
        self._update_scrollbar()
        self.update()

    @property
    def bytes_per_group(self) -> int:
        """Get the number of bytes per group."""
        return self._bytes_per_group

    @bytes_per_group.setter
    def bytes_per_group(self, value: int):
        """Set the number of bytes per group."""
        self._bytes_per_group = value

    @property
    def show_ascii(self) -> bool:
        """Get whether to show ASCII representation."""
        return self._show_ascii

    @show_ascii.setter
    def show_ascii(self, value: bool):
        """Set whether to show ASCII representation."""
        self._show_ascii = value
        self._update_scrollbar()
        self.update()

    def _update_scrollbar(self):
        """Update the vertical and horizontal scrollbars based on data size and viewport."""
        if len(self._data) == 0:
            self._v_scrollbar.setVisible(False)
            self._h_scrollbar.setVisible(False)
            self._corner_widget.setVisible(False)
            return

        # Calculate how many lines can be displayed
        self._visible_lines = max(1, self._hex_widget.height() // self._char_height)

        # Calculate total lines needed to display all data
        total_lines = (len(self._data) + self._bytes_per_line - 1) // self._bytes_per_line

        # Vertical scrollbar visibility and range
        if total_lines <= self._visible_lines:
            # All data fits in view, no need for scrollbar
            self._v_scrollbar.setVisible(False)
            self._v_scrollbar.setValue(0)
        else:
            # Configure scrollbar for the data
            self._v_scrollbar.setRange(0, total_lines - self._visible_lines + 1)
            self._v_scrollbar.setPageStep(self._visible_lines)
            self._v_scrollbar.setSingleStep(1)
            self._v_scrollbar.setVisible(True)

            # Ensure current position is valid
            if self._v_scrollbar.value() > total_lines - self._visible_lines:
                self._v_scrollbar.setValue(total_lines - self._visible_lines)

        # Calculate the width needed for full display
        address_width = self._calculate_address_width()
        hex_width = (self._char_width * 4) * self._bytes_per_line  # Width for hex columns
        if self._bytes_per_group > 1:
            hex_width += (self._bytes_per_line // self._bytes_per_group - 1) * self._char_width

        ascii_width = 0
        if self._show_ascii:
            ascii_width = int(self._char_width * 1.5) * self._bytes_per_line

        # Total content width with padding
        self._total_width = total_width = address_width + hex_width + ascii_width + 40  # Add padding

        # Calculate available width accounting for the vertical scrollbar
        available_width = self._hex_widget.width()

        # Horizontal scrollbar visibility and range
        if total_width <= available_width:
            self._h_scrollbar.setVisible(False)
            self._h_scrollbar.setValue(0)
        else:
            self._h_scrollbar.setRange(0, total_width - available_width)
            self._h_scrollbar.setPageStep(available_width)
            self._h_scrollbar.setSingleStep(self._char_width * 4)  # Scroll by 4 character widths
            self._h_scrollbar.setVisible(True)

            # Ensure current position is valid
            if self._h_scrollbar.value() > total_width - available_width:
                self._h_scrollbar.setValue(total_width - available_width)

        if self._v_scrollbar.isVisible() and self._h_scrollbar.isVisible():
            self._corner_widget.setFixedSize(self._v_scrollbar.width(), self._h_scrollbar.height())
            self._corner_widget.setVisible(True)

    def _measure_font_metrics(self):
        """Measure font metrics for the current font."""
        self._font_metrics = QtGui.QFontMetrics(self.font())
        self._char_width = self._font_metrics.horizontalAdvance("0")
        self._char_height = self._font_metrics.height()

    def _calculate_address_width(self) -> int:
        """Calculate the width needed for address display."""
        if len(self._data) == 0:
            return 8 * self._char_width  # Minimum width

        # Calculate required width based on addressing mode and data size
        max_address = len(self._data) - 1
        min_width = len("Address") - 2

        if self._addressing_base == 16:  # Hex
            addr_chars = max(min_width, len(f"{max_address:X}"))
            return (addr_chars + 2) * self._char_width  # +2 for "0x"
        elif self._addressing_base == 8:  # Octal
            addr_chars = max(min_width, len(f"{max_address:o}"))
            return (addr_chars + 2) * self._char_width  # +2 for "0o"
        else:  # Decimal
            addr_chars = max(min_width, len(str(max_address)))
            return addr_chars * self._char_width

    def _draw_header(self, painter: QtGui.QPainter, rect: QtCore.QRect, addr_width: int,
                    hex_width: int, ascii_width: int):
        """Draw the header with column addresses."""
        header_rect = QtCore.QRect(rect.left(),
                                   rect.top(),
                                   max(self._total_width, rect.width()),
                                   self._char_height + 8# Increased height
                                   )

        # Draw header background
        header_bg = QtGui.QLinearGradient(header_rect.topLeft(), header_rect.bottomLeft())
        header_bg.setColorAt(0, QtGui.QColor(240, 240, 240))
        header_bg.setColorAt(1, QtGui.QColor(220, 220, 220))
        painter.fillRect(header_rect, header_bg)

        # Draw header separator line
        painter.setPen(QtGui.QColor(180, 180, 180))
        painter.drawLine(header_rect.left(), header_rect.bottom(),
                        header_rect.right(), header_rect.bottom())

        # Draw address column header
        painter.setPen(QtGui.QColor(80, 80, 80))
        addr_rect = QtCore.QRect(rect.left(), rect.top(), addr_width, self._char_height + 8)  # Increased height
        painter.drawText(addr_rect, QtCore.Qt.AlignmentFlag.AlignCenter, "Address")

        # Draw column separators
        painter.setPen(QtGui.QColor(180, 180, 180))
        painter.drawLine(addr_rect.right(), header_rect.top(),
                        addr_rect.right(), header_rect.bottom())

        # Draw hex column headers (00-0F)
        hex_start_x = addr_rect.right() + 10  # Increased spacing

        painter.setPen(QtGui.QColor(80, 80, 80))
        col_width = self._char_width * 4  # Increased width for hex columns

        for i in range(self._bytes_per_line):
            column_text = f"{i:02X}"
            col_rect = QtCore.QRect(hex_start_x + i * col_width, rect.top(),
                            col_width, self._char_height + 8)  # Increased height

            # Add extra space for group separator
            if i > 0 and i % self._bytes_per_group == 0:
                col_rect.moveLeft(col_rect.left() + self._char_width)

            painter.drawText(col_rect, QtCore.Qt.AlignmentFlag.AlignCenter, column_text)

        # Draw hex/ASCII separator
        if self._show_ascii:
            painter.setPen(QtGui.QColor(180, 180, 180))
            ascii_start_x = hex_start_x + hex_width + 5
            painter.drawLine(ascii_start_x - 5, header_rect.top(),
                            ascii_start_x - 5, header_rect.bottom())

            # Draw ASCII header
            ascii_header_rect = QtCore.QRect(ascii_start_x, rect.top(),
                                    ascii_width, self._char_height + 8)  # Increased height
            painter.setPen(QtGui.QColor(80, 80, 80))
            painter.drawText(ascii_header_rect, QtCore.Qt.AlignmentFlag.AlignCenter, "ASCII")

    def _draw_hex_content(self, painter: QtGui.QPainter, rect: QtCore.QRect, addr_width: int,
                         hex_width: int, ascii_width: int):
        """Draw the hex content and ASCII representation."""
        if len(self._data) == 0:
            return

        # Calculate positions
        addr_x = rect.left()
        hex_x = addr_x + addr_width + 10  # Increased spacing between address and hex
        ascii_x = hex_x + hex_width + 15  # Increased spacing between hex and ASCII

        row_height = self._char_height
        bytes_per_row = self._bytes_per_line

        # Calculate visible range
        first_row = self._v_scrollbar.value()
        visible_rows = min(self._visible_lines,
                          (len(self._data) + bytes_per_row - 1) // bytes_per_row - first_row)

        # For each visible row
        for row in range(visible_rows):
            y = rect.top() + row * row_height
            row_addr = (first_row + row) * bytes_per_row

            # Draw alternating row backgrounds
            if (first_row + row) % 2 == 1:
                painter.fillRect(QtCore.QRect(rect.left(), y, rect.width(), row_height),
                                self._alternate_row_color)

            # Draw address
            painter.setPen(self._address_color)
            addr_rect = QtCore.QRect(addr_x, y, addr_width, row_height)

            # Use minimum width of "Address" (7 chars)
            min_width = max(5, len("Address") - 2)  # -2 for the "0x" or "0o" prefix

            if self._addressing_base == 16:  # Hex
                addr_text = f"0x{row_addr:0{min_width}X}"
            elif self._addressing_base == 8:  # Octal
                addr_text = f"0o{row_addr:0{min_width}o}"
            else:  # Decimal
                addr_text = f"{row_addr:0{min_width+2}d}"  # +2 to account for missing prefix

            painter.drawText(addr_rect, QtCore.Qt.AlignmentFlag.AlignCenter, addr_text)

            # Draw bytes for this row
            max_bytes = min(bytes_per_row, len(self._data) - row_addr)

            for col in range(max_bytes):
                byte_addr = row_addr + col
                byte_val = self._data[byte_addr]

                # Calculate position for this byte
                col_width = self._char_width * 4  # Increased width for hex columns
                byte_x = hex_x + col * col_width

                # Add extra space for group separator
                if col > 0 and col % self._bytes_per_group == 0:
                    byte_x += self._char_width

                byte_rect = QtCore.QRect(byte_x, y, col_width - self._char_width, row_height)

                # Check if this byte is selected or cursor is here
                is_selected = (self._selection_start >= 0 and
                              byte_addr >= min(self._selection_start, self._selection_end) and
                              byte_addr <= max(self._selection_start, self._selection_end))
                is_cursor = byte_addr == self._cursor_pos

                # Draw background if selected or cursor is here
                if is_selected:
                    painter.fillRect(byte_rect, self._selection_bg_color)
                    painter.setPen(self._selection_fg_color)
                elif is_cursor:
                    painter.fillRect(byte_rect, self._highlight_bg_color)
                    painter.setPen(self._highlight_fg_color)
                else:
                    painter.setPen(self._hex_color)

                byte_text = f"{byte_val:02X}"
                painter.drawText(byte_rect, QtCore.Qt.AlignmentFlag.AlignCenter, byte_text)

            # Draw ASCII representation
            if self._show_ascii:
                for col in range(max_bytes):
                    byte_addr = row_addr + col
                    byte_val = self._data[byte_addr]

                    # Calculate position for this ASCII char
                    char_x = ascii_x + col * int(self._char_width * 1.5)
                    char_rect = QtCore.QRect(char_x, y, int(self._char_width * 1.5), row_height)

                    # Check if this byte is selected or cursor is here
                    is_selected = (self._selection_start >= 0 and
                                  byte_addr >= min(self._selection_start, self._selection_end) and
                                  byte_addr <= max(self._selection_start, self._selection_end))
                    is_cursor = byte_addr == self._cursor_pos

                    # Draw background if selected or cursor is here
                    if is_selected:
                        painter.fillRect(char_rect, self._selection_bg_color)
                        painter.setPen(self._selection_fg_color)
                    elif is_cursor:
                        painter.fillRect(char_rect, self._highlight_bg_color)
                        painter.setPen(self._highlight_fg_color)
                    else:
                        painter.setPen(self._ascii_color)

                    # Get printable character or dot for control chars
                    if 32 <= byte_val <= 126:  # Printable ASCII
                        char = chr(byte_val)
                    else:
                        char = '.'

                    painter.drawText(char_rect, QtCore.Qt.AlignmentFlag.AlignCenter, char)

    def setFont(self, font: QtGui.QFont | str):
        super().setFont(font)
        self._measure_font_metrics()

    def resizeEvent(self, event: QtGui.QResizeEvent):
        """Handle resize events to update the scrollbar and layout."""
        self._update_scrollbar()
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent):
        """Paint the hex viewer."""
        h_offset = self._h_scrollbar.value()

        painter = QtGui.QPainter(self)
        painter.setFont(self.font())

        # Calculate basic layout measurements - avoid drawing in scrollbar area
        rect = self._hex_widget.geometry()

        # Adjust for horizontal scrolling
        painter.translate(-h_offset, 0)

        # If no data, just display a message
        if len(self._data) == 0:
            painter.drawText(rect, QtCore.Qt.AlignmentFlag.AlignCenter, "No data")
            return

        # Calculate layout
        address_width = self._calculate_address_width()
        hex_width = (self._char_width * 4) * self._bytes_per_line  # Increased width for hex columns
        if self._bytes_per_group > 1:
            # Extra space between groups
            hex_width += (self._bytes_per_line // self._bytes_per_group - 1) * self._char_width

        ascii_width = 0
        if self._show_ascii:
            ascii_width = int(self._char_width * 1.5) * self._bytes_per_line  # Increased spacing for ASCII chars

        # Draw the header
        self._draw_header(painter, rect, address_width, hex_width, ascii_width)

        # Adjusted rect for content
        header_height = self._char_height + 8  # Increased header height
        rect.setTop(rect.top() + header_height)

        # Draw content rows
        self._draw_hex_content(painter, rect, address_width, hex_width, ascii_width)

# For standalone testing
if __name__ == "__main__":
    import sys
    import random

    app = QtWidgets.QApplication(sys.argv)

    # Create large random test data
    test_data = bytearray(random.randint(0, 255) for _ in range(10000))

    # Create the hex viewer
    hex_viewer = HexArea()
    hex_viewer.setWindowTitle("Hex Viewer Demo")
    hex_viewer.resize(1000, 800)
    hex_viewer.data = test_data
    hex_viewer.show()

    sys.exit(app.exec())
