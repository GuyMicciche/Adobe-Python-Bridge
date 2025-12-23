"""
Script Demos - Fluent window palette (always on top)
"""

import sys
import os.path
import importlib.util

import AEPython as ae
import qtae

from PySide6 import QtCore, QtWidgets

from qfluentwidgets import (
    MSFluentWindow,
    NavigationItemPosition,
    setTheme,
    Theme,
    FluentIcon as FIF,
    PrimaryPushButton,
    PushButton,
    SubtitleLabel,
)

globals()['MSFluentWindow'] = MSFluentWindow  # Make available globally
globals()['NavigationItemPosition'] = NavigationItemPosition  # Make available globally
globals()['setTheme'] = setTheme  # Make available globally
globals()['Theme'] = Theme  # Make available globally
globals()['FIF'] = FIF  # Make available globally
globals()['PrimaryPushButton'] = PrimaryPushButton  # Make available globally
globals()['PushButton'] = PushButton  # Make available globally
globals()['SubtitleLabel'] = SubtitleLabel  # Make available globally

class ScriptDemosWindow(MSFluentWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # theme
        setTheme(Theme.DARK)

        # keep always-on-top, but avoid over‑tweaking flags
        flags = QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        # create a single "palette" page
        self.palettePage = QtWidgets.QWidget(self)
        self.palettePage.setObjectName("ScriptDemosPage")
        self._buildPalettePage(self.palettePage)

        # add page to navigation
        self.addSubInterface(self.palettePage, FIF.APPLICATION, "Script Demos")

        # window chrome
        self._initWindow()

    # ---------- UI building ----------

    def _buildPalettePage(self, page: QtWidgets.QWidget):
        layout = QtWidgets.QGridLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # header label
        title = SubtitleLabel("Script Demos", page)
        layout.addWidget(title, 0, 0, 1, 2)

        # row offset for buttons
        row0 = 1

        self._addScriptButton(layout, row0 + 0, 0,
                              "Find and Replace Text", "FindAndReplaceText.py")
        self._addScriptButton(layout, row0 + 1, 0,
                              "Scale Composition", "ScaleComposition.py")
        self._addScriptButton(layout, row0 + 2, 0,
                              "Scale Selected Layers", "ScaleSelectedLayers.py")
        self._addScriptButton(layout, row0 + 0, 1,
                              "Sort Layers by In Point", "SortLayersByInPoint.py")
        self._addScriptButton(layout, row0 + 1, 1,
                              "Render and Email", "RenderAndEmail.py")

        # help button (bottom right)
        helpButton = PushButton("?", page)
        helpButton.setFixedWidth(32)
        helpButton.clicked.connect(self.onHelpButtonClick)
        layout.addWidget(helpButton, row0 + 2, 1)

        layout.setRowStretch(row0 + 3, 1)

    def _addScriptButton(self, layout, row, column, label, scriptName):
        btn = PrimaryPushButton(label)
        btn.setMinimumWidth(180)
        btn.clicked.connect(lambda _, name=scriptName: self.onScriptButtonClick(name))
        layout.addWidget(btn, row, column)

    def _initWindow(self):
        self.setWindowTitle("Script Demos")
        self.resize(450, 260)

        # center relative to current screen
        screen = QtWidgets.QApplication.screens()[0].availableGeometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2,
        )

    # ---------- behavior ----------

    def onScriptButtonClick(self, pyFileName: str):
        import importlib.util

        moduleDirPath = os.path.dirname(__file__)
        pyFilePath = os.path.join(moduleDirPath, 'Samples', pyFileName)
        name = os.path.splitext(pyFileName)[0]

        spec = importlib.util.spec_from_file_location(name, pyFilePath)
        module = importlib.util.module_from_spec(spec)

        sys.path.insert(0, moduleDirPath)
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.remove(moduleDirPath)

    def onHelpButtonClick(self):
        ae.alert(
            "Click a button to run one of the following scripts:\n\n"
            "Find and Replace Text:\n"
            "Launches a UI to find and replace text values. Finds and replaces text within values and keyframe values of selected text layers of the active comp.\n"
            "\n"
            "Scale Composition:\n"
            "Launches a UI to scale the active comp. Scales all layers, including cameras, and also the comp dimensions.\n"
            "\n"
            "Scale Selected Layers:\n"
            "Launches a UI to scale the selected layers of the active comp. Scales all selected layers, including cameras.\n"
            "\n"
            "Sort Layers by In Point:\n"
            "Reorders all layers in the active comp by in-point.\n"
            "\n"
            "Render and Email:\n"
            "Renders all queued render items and then sends you an email message when the render batch is done. Refer to Help for more information on this script.\n",
            "Demo Palette",
        )
    def closeEvent(self, event):
        # make sure close is accepted so X actually closes the window
        event.accept()
        super().closeEvent(event)


# run from AE Python console
win = ScriptDemosWindow()
win.show()
