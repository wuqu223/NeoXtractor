from PyQt5.QtGui import QPalette, QColor

class Theme:
    @staticmethod
    def palettes():
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor("#2b2b2b"))
        dark_palette.setColor(QPalette.WindowText, QColor("white"))
        dark_palette.setColor(QPalette.Base, QColor("#353535"))
        dark_palette.setColor(QPalette.AlternateBase, QColor("#2b2b2b"))
        dark_palette.setColor(QPalette.ToolTipBase, QColor("white"))
        dark_palette.setColor(QPalette.ToolTipText, QColor("white"))
        dark_palette.setColor(QPalette.Text, QColor("white"))
        dark_palette.setColor(QPalette.Button, QColor("#353535"))
        dark_palette.setColor(QPalette.ButtonText, QColor("white"))
        dark_palette.setColor(QPalette.Highlight, QColor("#2a82da"))
        dark_palette.setColor(QPalette.HighlightedText, QColor("white"))
        return {"dark": dark_palette}

    @staticmethod
    def style_modern():
        return """
        QPushButton {
            background-color: #353535;
            color: white;
            border: 1px solid #555555;
            border-radius: 5px;
            padding: 5px;
        }

        QPushButton:hover {
            background-color: #2a82da;
            border: 1px solid #2a82da;
        }

        QComboBox {
            background-color: #2b2b2b;
            color: white;
            border: 1px solid #555555;
            border-radius: 5px;
            padding: 5px;
        }

        QLineEdit {
            background-color: #2b2b2b;
            color: white;
            border: 1px solid #555555;
            border-radius: 5px;
            padding: 5px;
        }

        QLineEdit:focus {
            border: 1px solid #2a82da;
        }

        QLabel {
            color: white;
        }

        QMenuBar::item:selected {
            border: 1px solid #2a82da;
        }

        QMenuBar {
            background-color: #2b2b2b;
            color: white;
            border: 1px solid #444444;
        }

        QMenu::item:selected {
            background-color: #2a82da;
        }

        QMenu {
            background-color: #353535;
            color: white;
            border: 1px solid #444444;
        }

        QMessageBox {
            background-color: #353535;
        }

        QScrollBar:vertical {
            background: #2b2b2b;
            border: 1px solid #444444;
            width: 10px;
        }

        QScrollBar::handle:vertical {
            background: #555555;
            border-radius: 5px;
        }
        """

qt_theme = Theme()
