"""
Fluent window hosting a TabWidget (AE-safe, add + close tabs)
"""

import sys
import os.path

import AEPython as ae
import qtae

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from qfluentwidgets import (
    MSFluentWindow,
    NavigationItemPosition,
    MessageBox,
    SubtitleLabel,
    setFont,
    setTheme,
    Theme,
    TabWidget,
    IconWidget,
)
from qfluentwidgets import FluentIcon as FIF

# make available globally
globals()['MSFluentWindow'] = MSFluentWindow
globals()['NavigationItemPosition'] = NavigationItemPosition
globals()['MessageBox'] = MessageBox
globals()['SubtitleLabel'] = SubtitleLabel
globals()['setFont'] = setFont
globals()['setTheme'] = setTheme
globals()['Theme'] = Theme
globals()['TabWidget'] = TabWidget
globals()['IconWidget'] = IconWidget
globals()['FIF'] = FIF

class TabInterface(QtWidgets.QWidget):
    """Tab page widget"""

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

        self.setObjectName(objectName)


class TabbedFluentWindow(MSFluentWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        setTheme(Theme.DARK)

        # AE-style floating palette, always on top
        flags = QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.tabCount = 1

        # ---- main content: TabWidget inside a host widget ----
        self.homeInterface = QtWidgets.QWidget(objectName="homeInterface")
        homeLayout = QtWidgets.QVBoxLayout(self.homeInterface)
        homeLayout.setContentsMargins(8, 8, 8, 8)

        self.tabWidget = TabWidget(self.homeInterface)
        self.tabWidget.setMovable(True)
        homeLayout.addWidget(self.tabWidget)

        # first tab
        self.tabWidget.addPage(
            TabInterface("Heart", "resource/Heart.png", "HeartPage"),
            "As long as you love me",
            icon="resource/Heart.png",
        )

        # connections for add + close
        self.tabWidget.currentChanged.connect(
            lambda index: print("current index:", index)
        )
        self.tabWidget.tabCloseRequested.connect(self.tabWidget.removeTab)
        self.tabWidget.tabAddRequested.connect(self.addNewPage)

        # other navigation interfaces (optional)
        self.appInterface = TabInterface("Application Interface", "resource/Heart.png", "AppPage", self)
        self.videoInterface = TabInterface("Video Interface", "resource/Heart.png", "VideoPage", self)
        self.libraryInterface = TabInterface("Library Interface", "resource/Heart.png", "LibPage", self)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, "主页", FIF.HOME_FILL)
        self.addSubInterface(self.appInterface, FIF.APPLICATION, "应用")
        self.addSubInterface(self.videoInterface, FIF.VIDEO, "视频")

        self.addSubInterface(
            self.libraryInterface,
            FIF.BOOK_SHELF,
            "库",
            FIF.LIBRARY_FILL,
            NavigationItemPosition.BOTTOM,
        )
        self.navigationInterface.addItem(
            routeKey="Help",
            icon=FIF.HELP,
            text="帮助",
            onClick=self.showMessageBox,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

    def initWindow(self):
        self.resize(1100, 750)
        self.setWindowIcon(QtGui.QIcon(":/qfluentwidgets/images/logo.png"))
        self.setWindowTitle("Fluent Window with TabWidget")

        desktop = QtWidgets.QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def showMessageBox(self):
        w = MessageBox(
            "支持作者🥰",
            "个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。"
            "您的支持就是作者开发和维护项目的动力🚀",
            self,
        )
        w.yesButton.setText("来啦老弟")
        w.cancelButton.setText("下次一定")

        if w.exec():
            QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://afdian.net/a/zhiyiYo"))

    def addNewPage(self):
        text = f"硝子酱一级棒卡哇伊×{self.tabCount}"
        route_key = f"page_{self.tabCount}"

        self.tabWidget.addPage(
            TabInterface(text, "resource/Smiling_with_heart.png", route_key),
            text,
            "resource/Smiling_with_heart.png",
        )
        self.tabCount += 1

globals()['TabInterface'] = TabInterface

# run from AE Python console
win = TabbedFluentWindow()
win.show()
