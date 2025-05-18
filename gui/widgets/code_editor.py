"""
Code highlighting functionality for the NeoXtractor GUI.
Provides a flexible syntax highlighting system with JSON-based rules.
"""

import json
import os

from PySide6.QtCore import QRegularExpression, Qt, QRect, QSize
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QTextDocument, QPainter
from PySide6.QtWidgets import QPlainTextEdit, QWidget

from utils import get_application_path

class LineNumberArea(QWidget):
    """
    Widget that displays line numbers for a QPlainTextEdit.
    
    This widget is displayed in the left margin of the CodeEditor and 
    shows the line numbers for the visible text.
    """

    def __init__(self, editor):
        """
        Initialize the line number area.
        
        Args:
            editor: The CodeEditor instance this line number area belongs to
        """
        super().__init__(editor)
        self.editor = editor

        # Set background color
        self.background_color = QColor("#2a2a2a")
        self.text_color = QColor("white")
        self.font_size = 10

    def sizeHint(self):
        """Calculate the appropriate width for the line number area."""
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        """Paint the line numbers."""
        painter = QPainter(self)
        painter.fillRect(event.rect(), self.background_color)

        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top())
        bottom = top + round(self.editor.blockBoundingRect(block).height())

        # Font for line numbers
        font = painter.font()
        font.setPointSize(self.font_size)
        font.setBold(True)
        painter.setFont(font)

        # Draw line numbers
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(self.text_color)
                painter.drawText(0, top, self.width() - 5,
                              self.editor.fontMetrics().height(),
                              Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.editor.blockBoundingRect(block).height())
            block_number += 1


class CodeHighlighter(QSyntaxHighlighter):
    """
    Flexible syntax highlighter that loads highlighting rules from JSON files.

    This highlighter supports loading rules for different programming languages
    from external JSON configuration files, making it easy to add support for
    new languages without modifying the code.
    """

    def __init__(self, document: QTextDocument, language: str = "text"):
        """
        Initialize the highlighter with a document and language.

        Args:
            document: The QTextDocument to highlight
            language: The language identifier (corresponds to JSON rule file)
        """
        super().__init__(document)
        self.highlighting_rules = []
        self.formats = {}

        # Set default language to plain text
        self.language = language

        # Load language rules
        self.load_language(language)

    def load_language(self, language: str) -> bool:
        """
        Load highlighting rules for the specified language from a JSON file.

        Args:
            language: The language identifier

        Returns:
            bool: True if rules were loaded successfully, False otherwise
        """
        self.highlighting_rules = []
        self.formats = {}
        self.language = language

        # Get the syntax file path using get_application_path
        rules_file = os.path.join(get_application_path(), "data", "hlsyntax", f"{language}.json")
        if not os.path.exists(rules_file):
            return False

        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)

            # Create formats first
            if 'formats' in rules_data:
                for format_name, format_data in rules_data['formats'].items():
                    text_format = QTextCharFormat()

                    # Set foreground color
                    if 'foreground' in format_data:
                        text_format.setForeground(QColor(format_data['foreground']))

                    # Set background color
                    if 'background' in format_data:
                        text_format.setBackground(QColor(format_data['background']))

                    # Set font weight
                    if 'bold' in format_data and format_data['bold']:
                        text_format.setFontWeight(QFont.Weight.Bold)

                    # Set font style
                    if 'italic' in format_data and format_data['italic']:
                        text_format.setFontItalic(True)

                    # Set underline
                    if 'underline' in format_data and format_data['underline']:
                        text_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)

                    self.formats[format_name] = text_format

            # Create highlighting rules
            if 'rules' in rules_data:
                for rule in rules_data['rules']:
                    if 'pattern' in rule and 'format' in rule and rule['format'] in self.formats:
                        pattern = QRegularExpression(rule['pattern'])
                        format_name = rule['format']
                        self.highlighting_rules.append((pattern, self.formats[format_name]))

            return True
        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"Error loading language rules for {language}: {str(e)}")
            return False

    def highlightBlock(self, text: str) -> None:
        """
        Highlight a block of text according to the loaded rules.

        Args:
            text: The text to highlight
        """
        for pattern, format_data in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format_data)


class CodeEditor(QPlainTextEdit):
    """
    A code editor widget with syntax highlighting support.
    
    This widget is a read-only code viewer by default but can be switched
    to edit mode if needed.
    """

    def __init__(self, parent=None, language: str = "text"):
        """
        Initialize the code editor.

        Args:
            parent: Parent widget
            language: The programming language to highlight
        """
        super().__init__(parent)

        self.setReadOnly(True)  # Read-only by default
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))

        # Set a monospace font
        font = QFont("Space Mono")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(12)
        self.setFont(font)

        # Create line number area
        self.line_number_area = LineNumberArea(self)

        # Connect signals for line numbers
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        # Initialize the line number area width
        self.update_line_number_area_width(0)

        # Highlight the current line
        self.highlight_current_line()

        # Create and apply the syntax highlighter
        self.highlighter = CodeHighlighter(self.document(), language)

    def set_language(self, language: str) -> bool:
        """
        Set the highlighting language.

        Args:
            language: The language identifier

        Returns:
            bool: True if language rules were loaded successfully
        """
        return self.highlighter.load_language(language)

    def set_read_only(self, read_only: bool = True) -> None:
        """
        Set whether the editor is read-only.

        Args:
            read_only: True for read-only mode, False for edit mode
        """
        self.setReadOnly(read_only)

    def line_number_area_width(self):
        """Calculate the width of the line number area."""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1

        space = 2 * 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        """Update the width of the editor to accommodate line numbers."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect: QRect, dy):
        """Update the line number area when the editor's viewport scrolls."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """Handle resize events to adjust the line number area."""
        super().resizeEvent(event)

        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        """Highlight the line where the cursor is currently positioned."""
        # TODO: Implement line highlighting
        pass
