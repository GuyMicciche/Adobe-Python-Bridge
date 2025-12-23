"""
TabWidget demo - AE style skeleton (objectName compatible)
"""

import sys
import os.path

import AEPython as ae
import qtae

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from qfluentwidgets import TabWidget, SubtitleLabel, setFont, IconWidget

# make available globally
globals()['TabWidget'] = TabWidget
globals()['SubtitleLabel'] = SubtitleLabel
globals()['setFont'] = setFont
globals()['IconWidget'] = IconWidget

class TabInterface(QtWidgets.QWidget):
    """Tab interface"""

    def __init__(self, text: str, icon, objectName: str, parent=None):
        super().__init__(parent=parent)

        self.iconWidget = IconWidget(icon, self)
        self.label = SubtitleLabel(text, self)
        self.iconWidget.setFixedSize(120, 120)

        self.vBoxLayout = QtWidgets.QVBoxLayout(self)
        self.vBoxLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.vBoxLayout.setSpacing(30)
        self.vBoxLayout.addWidget(self.iconWidget, 0, QtCore.Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.label, 0, QtCore.Qt.AlignCenter)
        setFont(self.label, 24)

        # give each page a distinct object name
        self.setObjectName(objectName)

globals()['TabInterface'] = TabInterface

class Window(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.tabCount = 1
        self.tabWidget = TabWidget(self)
        self.hBoxLayout = QtWidgets.QVBoxLayout(self)

        self.tabWidget.setMovable(True)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.hBoxLayout.addWidget(self.tabWidget)

        # first tab
        self.tabWidget.addPage(
            TabInterface('Heart', 'resource/Heart.png', 'HeartPage'),
            'As long as you love me',
            icon='resource/Heart.png'
        )

        self.tabWidget.currentChanged.connect(
            lambda index: print("current index:", index)
        )
        self.tabWidget.tabCloseRequested.connect(self.tabWidget.removeTab)
        self.tabWidget.tabAddRequested.connect(self.addNewPage)

    def initWindow(self):
        self.resize(1100, 750)
        self.setWindowIcon(QtGui.QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('PyQt-Fluent-Widgets TabWidget')

    def addNewPage(self):
        text = f'硝子酱一级棒卡哇伊×{self.tabCount}'
        route_key = f"page_{self.tabCount}"

        self.tabWidget.addPage(
            TabInterface(text, 'resource/Smiling_with_heart.png', route_key),
            text,
            'resource/Smiling_with_heart.png'
        )
        self.tabCount += 1


# run from AE Python console
win = Window()
win.show()
