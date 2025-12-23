# AE Python – Installation & First Flight 🚀

AE Python is a native-style Python scripting bridge for Adobe After Effects that lets you drive comps, layers, and even custom Qt/Fluent UIs with real Python code, not just ExtendScript. It ships with its own Python runtime plus a console and script library panel so you can treat AE like a programmable DCC app.

---

## 1. What You Get

- **AE Python Console**  
  After installation: `Window > Python` inside After Effects.  
  Use it like an in‑app REPL to poke at the AE API, run snippets, or execute `.py` files.

<img width="725" height="518" alt="AE Python Console" src="https://github.com/user-attachments/assets/c2435a60-89fa-41da-8cab-4d7e4dc72cc0" />

- **AE Python Script Library**  
  After installation: `Window > Python Script Library`.  
  A dockable browser for your scripts with favorites, tags, and metadata so you can build your own "tool shelf".

<img width="721" height="514" alt="AE Python Script Library" src="https://github.com/user-attachments/assets/398d6d09-a6a7-41f7-8983-8fa1c26d484e" />

- **Full AE Scripting API in Python**  
  Most classes and functions mirror the official ExtendScript/JavaScript API: things like `app.project`, `CompItem`, `TextLayer`, etc. behave the same, just with Python syntax.  
  See the AE scripting reference for concepts and names:  
  [https://ae-scripting.docsforadobe.dev/introduction/overview.html](https://ae-scripting.docsforadobe.dev/introduction/overview.html)

- **GUI Tooling**  
  - Qt via **PySide6** for custom dialogs and tools ([PySide6](https://pypi.org/project/PySide6/)).  
  - Fluent UI via **PyQt Fluent Widgets** for slick, modern panels ([PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets/tree/PySide6)).

---

## 2. Requirements (Before You Start)

Make sure this box is ticked off:

- **Adobe After Effects 2025** (64‑bit, Windows).
- **Windows 10 or Windows 11**.
- The AE Python **distribution ZIP**, which already contains a portable **Python 3.14.2** build configured for the plugin, so you don't need to install Python system‑wide ([Python 3.14.2](https://www.python.org/downloads/release/python-3142/)).

---

## 3. Installation – Step by Step

Think of the ZIP as a little "installer that you drag into place". There are **three destinations**: AE plug‑ins, AE scripts, and your user Documents.

### 3.1. Unpack the ZIP

1. Locate the AE Python ZIP you downloaded.  
2. Right‑click → **Extract All…** and unpack it somewhere convenient (e.g. your Downloads folder or a temp folder).  
3. Inside the extracted folder you'll see a top‑level **`AEPython`** directory with subfolders like:
   - `AE/Plug-ins/AEPython`
   - `AE/Scripts`
   - `User Documents/AEPython`

You'll copy each of these into specific places AE expects.

---

### 3.2. Install the Plug‑in (.aex, runtime, etc.) 🎛️

**This is the engine** that makes `Window > Python` appear.

1. Open the extracted folder path:  
   `AEPython\AE\Plug-ins\AEPython`
2. In another Explorer window, open your AE plug‑ins folder (adjust `{version}` to match your AE build, e.g. *Adobe After Effects 2025*):  

C:\Program Files\Adobe\Adobe After Effects {version}\Support Files\Plug-ins\

3. **Copy the `AEPython` folder** from the ZIP into that `Plug-ins` folder so you end up with:

C:\Program Files\Adobe\Adobe After Effects {version}\Support Files\Plug-ins\AEPython\

That folder should contain the `.aex` plus any bundled Python files and support DLLs.

> **⚠️ Pro Tip**: If AE is open, **close it before copying**, then reopen after you're done so it picks up the new plug‑in.

---

### 3.3. Install the AE Scripts 📜

These add menu items and ScriptUI integration that help launch and manage your tools.

1. From the extracted ZIP, open:  
`AEPython\AE\Scripts`
2. Open your AE Scripts folder (again adjust `{version}`):

`C:\Program Files\Adobe\Adobe After Effects {version}\Support Files\Scripts`

3. **Copy all files and subfolders** from `AEPython\AE\Scripts` into that `Scripts` folder.

After this, you'll see entries like **"Python Script Library.jsx"** under AE's `Window` menu.

---

### 3.4. Install User Documents (Config & Libraries) 🏠

This is the **writable home** for your script library, metadata, and user‑side Python scripts.

1. From the extracted ZIP, open:  
`AEPython\User Documents\AEPython`
2. **Copy the `AEPython` folder** into your Documents:

`%USERPROFILE%\Documents\AEPython`

In Explorer, that usually looks like:

`C:\Users\%USERNAME%\Documents\AEPython`

This folder is safe to customize: drop your own `.py` scripts in `Scripts` folder, tweak settings, back it up between machines, and create custom themes in the `Themes` folder.

---

## 4. Verifying the Install ✅

Once everything is copied, **start (or restart) After Effects**.

### 4.1. Check the Python Console

1. In AE, go to: **`Window > Python`**
2. You should see the **AE Python Console** dockable window.  
3. Try a quick sanity check:

```Python
import AEPython as ae
ae.alert("AE Python is alive! 🚀")
```

**If an alert pops up inside AE, the bridge is working!**

### 4.2. Check the Script Library

1. In AE, go to: **`Window > Python Script Library`**
2. The Script Library UI should appear with sample scripts and categories.

**To show the ScriptUI‑style launcher** (for classic panels):  
`Window > Python Script Library.jsx`

<img width="706" height="470" alt="Python Script Library JSX Panel" src="https://github.com/user-attachments/assets/29d49728-8799-485b-bd14-f61ed1141744" />

---

## 5. First Scripts – Quick Tour ⚡

### 5.1. Run Python directly in AE

In the **Python** window:

```Python
import AEPython as ae

comp = ae.app.project.items.addComp("Comp1", 1920, 1080, 1, 10, 24)
comp.bgColor = [1.0, 1.0, 1.0]

text_layer = comp.layers.addText("This is an AE Python sample.")
text_prop = text_layer.property("Source Text")
text_document = text_prop.value
text_document.fontSize = 50
text_prop.setValue(text_document)
```

**Result**: A new comp with a big white text layer!

### 5.2. Execute a `.py` file from the Console

1. Save this as `%USERPROFILE%\Documents\AEPython\Scripts\sample.py`:

```Python
import AEPython as ae
ae.alert(ae.app.project.file)
```

2. In the AE Python Console: **File → Execute Python File…** → Select `sample.py`.

### 5.3. Call Python from ExtendScript (JSX)

In a regular AE JSX script:

```Javascript
Python.exec("ae.app.project.activeItem.name = 'New Name'");
```

Or run a Python file:

```Javascript
Python.execFile("D:/sample.py");
```

### 5.4. Build a Qt GUI Tool 🎨

Drop this into the console:

```Python
from PySide6 import QtWidgets
import AEPython as ae
import qtae

class MyDialog(QtWidgets.QDialog):
def init(self, parent=None):
super().init(parent)
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
    layer.position.setValue()
dialog = MyDialog(qtae.GetQtAEMainWindow())
dialog.show()
```

**Type text, click button → layer appears in active comp!**

---

## 6. Uninstall / Clean Up 🧹

1. Delete: `C:\Program Files\Adobe\Adobe After Effects {version}\Support Files\Plug-ins\AEPython` folder
2. Remove `Python Script Library.jsx` file from: `C:\Program Files\Adobe\Adobe After Effects {version}\Support Files\Scripts\ScriptUI Panels`
3. Remove `AEPython.jsx` file from: `C:\Program Files\Adobe\Adobe After Effects {version}\Support Files\Scripts\Startup`
4. Optional: Delete user preferences `%USERPROFILE%\Documents\AEPython` folder

Restart AE – Python windows disappear.

---

## 7. Next Steps 🚀

- [AE Scripting Reference](https://ae-scripting.docsforadobe.dev/introduction/overview.html)
- Build your Script Library toolbox inside AE!
- Mix Python + JSX for gradual migration.

**You're now piloting After Effects with Python superpowers!** 🎉
