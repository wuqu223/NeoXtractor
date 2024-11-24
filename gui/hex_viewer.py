# hexqt.py -- HexQT a pretty QT hex editor.
# Author: queercat - original (https://github.com/queercat/HexQT/blob/master/hexqt.py)
#         KingJulz + MarcosVLl2 - Modified for integration in "NeoXtractor" tool

import os, enum
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt

class Mode(enum.Enum):
    READ = 0
    ADDITION = 1
    OVERRIDE = 2

class InputDialogue(QInputDialog):
    def __init__(self, title, text):
        super().__init__()
        self.dialogueTitle = title
        self.dialogueText = text
        self.initUI()

    def initUI(self):
        dialogueResponse, dialogueComplete = QInputDialog.getText(self, self.dialogueTitle, self.dialogueText, QLineEdit.Normal, '')
        self.dialogueReponse = dialogueResponse if dialogueComplete else ''

class HexViewer(QMainWindow):
    def __init__(self, npkdata):
        super().__init__()
        self.title = 'Hex Viewer'
        self.width, self.height = 1080, 840
        self.rowSpacing, self.rowLength, self.byteWidth = 1, 16, 2
        self.mode = Mode.READ
        self.npkdata = npkdata
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(50, 50, self.width, self.height)
        self.centerWindow()

        #self.createMenu()
        self.createMainView()
        self.generateView(self.npkdata)
        self.show()

    def centerWindow(self):
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        
    def createMenu(self):
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        editMenu = mainMenu.addMenu('Edit')

        openButton = QAction('Open', self)
        openButton.setShortcut('Ctrl+Shift+O')
        openButton.triggered.connect(self.openFile)
        fileMenu.addAction(openButton)

        offsetButton = QAction('Jump to Offset', self)
        offsetButton.setShortcut('Ctrl+J')
        offsetButton.triggered.connect(self.offsetJump)
        editMenu.addAction(offsetButton)

    def createMainView(self):
        qhBox = QHBoxLayout()
        self.setFixedWidth(1000)
        
        # Column Header for Byte Labels (0-F)
        self.columnHeader = QTextEdit()
        self.columnLSpace = QTextEdit()
        self.columnRSpace = QTextEdit()
        self.columnHeader.setReadOnly(True)
        self.columnLSpace.setReadOnly(True)
        self.columnRSpace.setReadOnly(True)
        self.columnHeader.setFixedHeight(30)
        self.columnLSpace.setFixedHeight(30)
        self.columnRSpace.setFixedHeight(30)
        self.columnHeader.setAlignment(Qt.AlignCenter)
        self.columnHeader.setText(self.generateColumnLabels())
        
        # Main Text Areas
        self.mainTextArea = QTextEdit()
        self.offsetTextArea = QTextEdit()
        self.asciiTextArea = QTextEdit()

        # Relative Path to font
        font_path = os.path.join(os.path.dirname(__file__), "../fonts/DroidSansMono.ttf")

        # Load font
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("Failed to load font.")
        else:
            # Retrieve the font family name from the loaded font
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            font = QFont(font_family, 12)
            
            # Confirm the actual loaded font
            font_info = QFontInfo(font)
            # print("Requested font:", font.family())
            print("Loaded font:", font_info.family())

            # Apply the font to each text area
            for area in [self.mainTextArea, self.asciiTextArea, self.offsetTextArea, self.columnHeader]:
                area.setReadOnly(True)
                area.setFont(font)

        syncScrolls(self.mainTextArea, self.asciiTextArea, self.offsetTextArea)

        # Add Column Header and Text Areas
        mainLayout = QVBoxLayout()

        columnLayout = QHBoxLayout()
        columnLayout.addWidget(self.columnLSpace, 1)
        columnLayout.addWidget(self.columnHeader, 6)
        columnLayout.addWidget(self.columnRSpace, 2)
        mainLayout.addLayout(columnLayout)
        
        # Add Text Areas for Hex and ASCII
        textAreasLayout = QHBoxLayout()
        textAreasLayout.addWidget(self.offsetTextArea, 1)
        textAreasLayout.addWidget(self.mainTextArea, 6)
        textAreasLayout.addWidget(self.asciiTextArea, 2)

        mainLayout.addLayout(textAreasLayout)

        centralWidget = QWidget()
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

    def generateColumnLabels(self):
        # Generates the column header labels (00 01 ... 0F) up to the row length
        labels = ""  # Leave space for offset column
        for i in range(self.rowLength):
            labels += f"{i:02X} " # Hex label with space
        return labels

    def generateView(self, text):
        space, bigSpace = '', ' '
        rowLength = self.rowLength
        offset, offsetText, mainText, asciiText = 0, '', '', ''
        
        for i, byte in enumerate(text):
            char = chr(byte) if 32 <= byte <= 126 else '.'
            asciiText += char
            mainText += format(byte, '02X') + space

            # End of Row
            if (i + 1) % rowLength == 0:
                offsetText += f"{offset:08X}\n"
                mainText += '\n'
                asciiText += '\n'
                offset += rowLength
            elif (i + 1) % self.rowSpacing == 0:
                mainText += bigSpace if (i + 1) % rowLength != 0 else space

        self.offsetTextArea.setText(offsetText)
        self.mainTextArea.setText(mainText)
        self.asciiTextArea.setText(asciiText)

    def offsetJump(self):
        jump_text = InputDialogue('Jump to Offset', 'Enter offset (in hex):').dialogueReponse
        try:
            jump_offset = int(jump_text, 16)
        except ValueError:
            self.statusBar().showMessage("Invalid offset entered.")
            return jump_text

        line = jump_offset // self.rowLength
        col = (jump_offset % self.rowLength) * (self.byteWidth + 1)
        cursor = self.mainTextArea.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line)
        cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, col)
        self.mainTextArea.setTextCursor(cursor)
        self.mainTextArea.ensureCursorVisible()
        #self.columnLSpace(f"{jump_text}")
        self.statusBar().showMessage(f"Jumped to offset: {jump_text}")

    def toggleEditMode(self, mode):
        if mode == Mode.ADDITION or mode == Mode.OVERRIDE:
            self.mainTextArea.setReadOnly(False)
            self.mode = mode
        else:
            self.mainTextArea.setReadOnly(True)
            self.mode = Mode.READ

def syncScrolls(qTextObj0, qTextObj1, qTextObj2):
    scroll0, scroll1, scroll2 = qTextObj0.verticalScrollBar(), qTextObj1.verticalScrollBar(), qTextObj2.verticalScrollBar()
    scroll0.valueChanged.connect(scroll1.setValue)
    scroll0.valueChanged.connect(scroll2.setValue)
    scroll1.valueChanged.connect(scroll0.setValue)
    scroll1.valueChanged.connect(scroll2.setValue)
    scroll2.valueChanged.connect(scroll1.setValue)
    scroll2.valueChanged.connect(scroll0.setValue)

def setStyle(qApp):
    qApp.setStyle("Fusion")
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    qApp.setPalette(dark_palette)
    qApp.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

