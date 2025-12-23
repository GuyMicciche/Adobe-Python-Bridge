"""
Expression Library
Browse and apply common expressions with live preview
"""
import AEPython as ae
import qtae
from PySide6 import QtWidgets, QtCore

class ExpressionLibrary(QtWidgets.QDialog):
    EXPRESSIONS = {
        "Wiggle Position": {
            "code": "wiggle(5, 50)",
            "desc": "Random wiggle movement",
            "property": "position"
        },
        "Bounce": {
            "code": "amp = .1;\nfreq = 2.0;\ndecay = 5.0;\nn = 0;\nif (numKeys > 0){\n  n = nearestKey(time).index;\n  if (key(n).time > time) n--;\n}\nif (n > 0){\n  t = time - key(n).time;\n  v = velocityAtTime(key(n).time - .001);\n  value + v*amp*Math.sin(freq*t*2*Math.PI)/Math.exp(decay*t);\n}else value",
            "desc": "Bouncy keyframe animation",
            "property": "position"
        },
        "Auto-Scale": {
            "code": "[value[0] * (thisComp.width / 1920), value[1] * (thisComp.height / 1080)]",
            "desc": "Scale based on comp size",
            "property": "position"
        },
        "Time Remap Loop": {
            "code": "loopOut('cycle')",
            "desc": "Loop animation continuously",
            "property": "timeRemapEnabled"
        },
        "Smooth Value": {
            "code": "smooth(5)",
            "desc": "Smooth out keyframe values",
            "property": "any"
        },
        "Random Rotation": {
            "code": "random(360)",
            "desc": "Random rotation value",
            "property": "rotation"
        },
        "Oscillate": {
            "code": "freq = 3;\namp = 30;\nvalue + Math.sin(time * freq) * amp",
            "desc": "Oscillate around current value",
            "property": "any"
        },
        "Scale with Audio": {
            "code": 'audio = thisComp.layer("Audio Layer").audio.audioLevels;\nlinear(audio, -60, -20, 0, 100)',
            "desc": "Scale based on audio levels (rename Audio Layer)",
            "property": "scale"
        }
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📚 Expression Library")
        self.setMinimumSize(600, 500)
        
        layout = QtWidgets.QVBoxLayout()
        
        # Header
        header = QtWidgets.QLabel("📚 Expression Library")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Expression list
        list_label = QtWidgets.QLabel("Select an expression:")
        layout.addWidget(list_label)
        
        self.expr_list = QtWidgets.QListWidget()
        for name, data in self.EXPRESSIONS.items():
            item = QtWidgets.QListWidgetItem(f"{name} - {data['desc']}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, name)
            self.expr_list.addItem(item)
        self.expr_list.currentItemChanged.connect(self.on_selection_changed)
        layout.addWidget(self.expr_list)
        
        # Code preview
        code_label = QtWidgets.QLabel("Expression Code:")
        layout.addWidget(code_label)
        
        self.code_display = QtWidgets.QTextEdit()
        self.code_display.setReadOnly(True)
        self.code_display.setStyleSheet("font-family: 'Consolas', monospace; background-color: #1e1e1e; color: #d4d4d4;")
        self.code_display.setMaximumHeight(150)
        layout.addWidget(self.code_display)
        
        # Apply button
        apply_btn = QtWidgets.QPushButton("✨ Apply to Selected Property")
        apply_btn.clicked.connect(self.apply_expression)
        layout.addWidget(apply_btn)
        
        # Instructions
        info = QtWidgets.QLabel("💡 Select a layer property in After Effects, then choose an expression above.")
        info.setStyleSheet("padding: 10px; background-color: #444; border-radius: 4px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        self.setLayout(layout)
        
        # Select first item
        self.expr_list.setCurrentRow(0)
    
    def on_selection_changed(self, current, previous):
        if current:
            expr_name = current.data(QtCore.Qt.ItemDataRole.UserRole)
            expr_data = self.EXPRESSIONS[expr_name]
            self.code_display.setPlainText(expr_data["code"])
    
    def apply_expression(self):
        current = self.expr_list.currentItem()
        if not current:
            return
        
        expr_name = current.data(QtCore.Qt.ItemDataRole.UserRole)
        expr_data = self.EXPRESSIONS[expr_name]
        
        comp = ae.app.project.activeItem
        if not comp or not isinstance(comp, ae.CompItem):
            ae.alert("Please select a composition first!")
            return
        
        layers = comp.selectedLayers
        if len(layers) == 0:
            ae.alert("Please select a layer first!")
            return
        
        # Get selected property
        selected_props = comp.selectedProperties
        if len(selected_props) == 0:
            ae.alert("Please select a property first!\n\nSelect the property (like Position, Scale, etc) in the timeline before applying.")
            return
        
        ae.app.beginUndoGroup(f"Apply Expression: {expr_name}")
        
        for prop in selected_props:
            try:
                prop.expression = expr_data["code"]
                print(f"✓ Applied '{expr_name}' to {layers[0].name}")
            except Exception as e:
                print(f"✗ Could not apply to this property: {e}")
        
        ae.app.endUndoGroup()

dialog = ExpressionLibrary(qtae.GetQtAEMainWindow())
dialog.show()