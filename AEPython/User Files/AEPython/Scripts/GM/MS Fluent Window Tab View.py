"""
Tabbed Fluent Window - AE style skeleton
"""

import sys
import os.path

import AEPython as ae
import qtae

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QSize, QUrl, QPoint
from PySide6.QtGui import QIcon, QDesktopServices, QColor
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QStackedWidget

from qfluentwidgets import (
    MSFluentWindow,
    MSFluentTitleBar,
    NavigationItemPosition,
    MessageBox,
    TabBar,
    SubtitleLabel,
    setFont,
    TabCloseButtonDisplayMode,
    IconWidget,
    TransparentDropDownToolButton,
    TransparentToolButton,
    setTheme,
    Theme,
    isDarkTheme,
)
from qfluentwidgets import FluentIcon as FIF

# make available globally (your pattern)
globals()['MSFluentWindow'] = MSFluentWindow
globals()['MSFluentTitleBar'] = MSFluentTitleBar
globals()['NavigationItemPosition'] = NavigationItemPosition
globals()['MessageBox'] = MessageBox
globals()['TabBar'] = TabBar
globals()['SubtitleLabel'] = SubtitleLabel
globals()['setFont'] = setFont
globals()['TabCloseButtonDisplayMode'] = TabCloseButtonDisplayMode
globals()['IconWidget'] = IconWidget
globals()['TransparentDropDownToolButton'] = TransparentDropDownToolButton
globals()['TransparentToolButton'] = TransparentToolButton
globals()['setTheme'] = setTheme
globals()['Theme'] = Theme
globals()['isDarkTheme'] = isDarkTheme
globals()['FIF'] = FIF

class Widget(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QtWidgets.QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, QtCore.Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class TabInterface(QWidget):
    """ Tab interface """

    def __init__(self, text: str, icon, objectName, parent=None):
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


class CustomTitleBar(MSFluentTitleBar):
    """ Title bar with icon and title """

    def __init__(self, parent):
        super().__init__(parent)

        # add buttons
        self.toolButtonLayout = QtWidgets.QHBoxLayout()
        color = QtGui.QColor(206, 206, 206) if isDarkTheme() else QtGui.QColor(96, 96, 96)
        self.searchButton = TransparentToolButton(FIF.SEARCH_MIRROR.icon(color=color), self)
        self.forwardButton = TransparentToolButton(FIF.RIGHT_ARROW.icon(color=color), self)
        self.backButton = TransparentToolButton(FIF.LEFT_ARROW.icon(color=color), self)

        self.forwardButton.setDisabled(True)
        self.toolButtonLayout.setContentsMargins(20, 0, 20, 0)
        self.toolButtonLayout.setSpacing(15)
        self.toolButtonLayout.addWidget(self.searchButton)
        self.toolButtonLayout.addWidget(self.backButton)
        self.toolButtonLayout.addWidget(self.forwardButton)
        self.hBoxLayout.insertLayout(4, self.toolButtonLayout)

        # add tab bar
        self.tabBar = TabBar(self)
        self.tabBar.setMovable(True)
        self.tabBar.setTabMaximumWidth(220)
        self.tabBar.setTabShadowEnabled(False)
        self.tabBar.setTabSelectedBackgroundColor(
            QtGui.QColor(255, 255, 255, 125),
            QtGui.QColor(255, 255, 255, 50)
        )

        # no tabCloseRequested connections
        self.tabBar.tabCloseRequested.connect(self.tabBar.removeTab)
        self.tabBar.currentChanged.connect(lambda i: print(self.tabBar.tabText(i)))

        self.hBoxLayout.insertWidget(5, self.tabBar, 1)
        self.hBoxLayout.setStretch(6, 0)

        # add avatar
        self.avatar = TransparentDropDownToolButton('resource/shoko.png', self)
        self.avatar.setIconSize(QtCore.QSize(26, 26))
        self.avatar.setFixedHeight(30)
        self.hBoxLayout.insertWidget(7, self.avatar, 0, QtCore.Qt.AlignRight)
        self.hBoxLayout.insertSpacing(8, 20)

        if sys.platform == "darwin":
            self.hBoxLayout.insertSpacing(8, 52)

    def canDrag(self, pos: QtCore.QPoint):
        if not super().canDrag(pos):
            return False

        pos.setX(pos.x() - self.tabBar.x())
        return not self.tabBar.tabRegion().contains(pos)


class TabbedWindow(MSFluentWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        setTheme(Theme.DARK)

        # AE-style floating palette, always on top
        flags = QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.isMicaEnabled = False

        self.setTitleBar(CustomTitleBar(self))
        self.tabBar = self.titleBar.tabBar  # type: TabBar
        self.tabCount = 1  # tab counter for unique routeKey

        # create sub interface
        self.homeInterface = QtWidgets.QStackedWidget(self, objectName='homeInterface')
        self.appInterface = Widget('Application Interface', self)
        self.videoInterface = Widget('Video Interface', self)
        self.libraryInterface = Widget('library Interface', self)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, '主页', FIF.HOME_FILL)
        self.addSubInterface(self.appInterface, FIF.APPLICATION, '应用')
        self.addSubInterface(self.videoInterface, FIF.VIDEO, '视频')

        self.addSubInterface(
            self.libraryInterface,
            FIF.BOOK_SHELF,
            '库',
            FIF.LIBRARY_FILL,
            NavigationItemPosition.BOTTOM
        )
        self.navigationInterface.addItem(
            routeKey='Help',
            icon=FIF.HELP,
            text='帮助',
            onClick=self.showMessageBox,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

        # add first tab
        self.addTab('Heart', 'As long as you love me', icon='resource/Heart.png')

        self.tabBar.currentChanged.connect(self.onTabChanged)
        self.tabBar.tabAddRequested.connect(self.onTabAddRequested)

    def initWindow(self):
        self.resize(1100, 750)
        self.setWindowIcon(QtGui.QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('PyQt-Fluent-Widgets Tabs')

        desktop = QtWidgets.QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def showMessageBox(self):
        w = MessageBox(
            '支持作者🥰',
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀',
            self
        )
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')

        if w.exec():
            QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://afdian.net/a/zhiyiYo"))

    def onTabChanged(self, index: int):
        objectName = self.tabBar.currentTab().routeKey()
        self.homeInterface.setCurrentWidget(self.findChild(TabInterface, objectName))
        self.stackedWidget.setCurrentWidget(self.homeInterface)

    def onTabAddRequested(self):
        text = f'硝子酱一级棒卡哇伊×{self.tabCount}'
        self.addTab(text, text, 'resource/Smiling_with_heart.png')
        self.tabCount += 1

    def addTab(self, routeKey, text, icon):
        self.tabBar.addTab(routeKey, text, icon)
        self.homeInterface.addWidget(TabInterface(text, icon, routeKey, self))

globals()['CustomTitleBar'] = CustomTitleBar
globals()['Widget'] = Widget
globals()['TabInterface'] = TabInterface

# run from AE Python console
win = TabbedWindow()
win.show()
