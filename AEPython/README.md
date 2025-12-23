# AE Python
Python scripting plugin for After Effects

## AE Python Console

<img width="725" height="518" alt="image" src="https://github.com/user-attachments/assets/c2435a60-89fa-41da-8cab-4d7e4dc72cc0" />

## Features
* Directly control After Effects with Python scripts
* Create Qt and Fluent UI elements
* Python script library and manager.
* Enabled to use classes and functions with the same names as After Effects default scripts (ExtendScript, JavaScript) 
  * Class and function reference: https://ae-scripting.docsforadobe.dev/introduction/overview.html
* Interoperation between Javascript and Python
* GUI development by Qt ([PySide6](https://pypi.org/project/PySide6/))
* GUI development by ([PyQt Fluent Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets/tree/PySide6))

## AE Script Library

<img width="721" height="514" alt="image" src="https://github.com/user-attachments/assets/398d6d09-a6a7-41f7-8983-8fa1c26d484e" />

## System Requirements
* Adobe After Effects 2025
* Windows 10 / 11
* [Python 3.14.2](https://www.python.org/downloads/release/python-3142/) (included in the distribution Zip)

## Installation
Copy each files and folders in the distribution Zip to the following locations.
* AEPython > AE > Plug-ins > AEPython -> C:\Program Files\Adobe\Adobe After Effects {version}\Support Files\Plug-ins\AEPython
* AEPython > AE > Scripts -> C:\Program Files\Adobe\Adobe After Effects {version}\Support Files\Scripts
* AEPython > User Documents > AEPython -> %USERPROFILE%\Documents\AEPython

## Scripting Guide

### Run Python scripts from the Python Window
Select menu: Window -> Python

```Python
comp = ae.app.project.items.addComp("Comp1", 1920, 1080, 1, 10, 24)
comp.bgColor = [1.0, 1.0, 1.0]

text_layer = comp.layers.addText("This is an AE Python sample.")

text_prop = text_layer.property("Source Text")
text_document = text_prop.value
text_document.fontSize = 50
text_prop.setValue(text_document)
```

### Run .py files from the Python Window
Select .py file from File -> "Execute Python File" in the AE Python Console window.

[sample.py]
```Python
import AEPython as ae
ae.alert(ae.app.project.file)
```

### Run Python scripts from ExtendScript
```JavaScript
Python.exec("ae.app.project.activeItem.name = 'New Name'");
```

### Run .py files from ExtendScript
```JavaScript
Python.execFile("D:/sample.py");
```

### GUI by Qt
```Python 
from PySide6 import QtWidgets

import AEPython as ae
import qtae

class MyDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout()

        self.text_input = QtWidgets.QLineEdit("")
        layout.addWidget(self.text_input)

        self.button = QtWidgets.QPushButton("Add Text Layer!")
        self.button.clicked.connect(self.onButtonClicked)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def onButtonClicked(self):
        text = self.text_input.text()
        layer = ae.app.project.activeItem.layers.addText(text)
        layer.position.setValue([100,100])

dialog = MyDialog(qtae.GetQtAEMainWindow())
dialog.show()
```
