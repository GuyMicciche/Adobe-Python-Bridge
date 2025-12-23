"""
Expression Library
Browse, create, edit, and apply expressions with full management features
"""
import AEPython as ae
import qtae
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtUiTools import QUiLoader
import json
from pathlib import Path


# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent


def load_ui(ui_filename, parent=None):
    """Load a .ui file and return the widget"""
    loader = QUiLoader()
    ui_path = SCRIPT_DIR / ui_filename
    ui_file = QtCore.QFile(str(ui_path))
    ui_file.open(QtCore.QFile.ReadOnly)
    widget = loader.load(ui_file, parent)
    ui_file.close()
    return widget

globals()['QUiLoader'] = QUiLoader
globals()['load_ui'] = load_ui
globals()['SCRIPT_DIR'] = SCRIPT_DIR

class AddExpressionDialog(QtWidgets.QDialog):
    """Dialog for adding/editing expressions"""
    def __init__(self, parent=None, edit_mode=False, item_data=None):
        super().__init__(parent)
        
        # Load UI
        self.ui = load_ui("add_expression_dialog.ui")
        
        # Copy properties from loaded widget
        self.setWindowTitle("Edit Expression" if edit_mode else "Add Expression")
        self.setMinimumSize(self.ui.minimumSize())
        
        # Create layout and add loaded widget
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)
        
        # Get widget references
        self.category_input = self.ui.findChild(QtWidgets.QLineEdit, "category_input")
        self.name_input = self.ui.findChild(QtWidgets.QLineEdit, "name_input")
        self.desc_input = self.ui.findChild(QtWidgets.QLineEdit, "desc_input")
        self.code_input = self.ui.findChild(QtWidgets.QPlainTextEdit, "code_input")
        
        # Connect buttons
        self.ui.findChild(QtWidgets.QPushButton, "save_btn").clicked.connect(self.accept)
        self.ui.findChild(QtWidgets.QPushButton, "cancel_btn").clicked.connect(self.reject)
        
        # Populate if editing
        if edit_mode and item_data:
            self.category_input.setText(item_data["category"])
            self.name_input.setText(item_data["name"])
            self.desc_input.setText(item_data["data"].get("desc", ""))
            self.code_input.setPlainText(item_data["data"]["code"])


class ExpressionLibrary(QtWidgets.QDialog):
    # Built-in expressions
    BUILTIN_EXPRESSIONS = {
        "Motion": {
            "Wiggle Position": {
                "code": "wiggle(5, 50)",
                "desc": "Random wiggle movement",
                "builtin": True
            },
            "Bounce": {
                "code": "amp = .1;\nfreq = 2.0;\ndecay = 5.0;\nn = 0;\nif (numKeys > 0){\n  n = nearestKey(time).index;\n  if (key(n).time > time) n--;\n}\nif (n > 0){\n  t = time - key(n).time;\n  v = velocityAtTime(key(n).time - .001);\n  value + v*amp*Math.sin(freq*t*2*Math.PI)/Math.exp(decay*t);\n}else value",
                "desc": "Bouncy keyframe animation",
                "builtin": True
            },
            "Smooth Value": {
                "code": "smooth(5)",
                "desc": "Smooth out keyframe values",
                "builtin": True
            },
            "Oscillate": {
                "code": "freq = 3;\namp = 30;\nvalue + Math.sin(time * freq) * amp",
                "desc": "Oscillate around current value",
                "builtin": True
            }
        },
        "Transform": {
            "Auto-Scale": {
                "code": "[value[0] * (thisComp.width / 1920), value[1] * (thisComp.height / 1080)]",
                "desc": "Scale based on comp size",
                "builtin": True
            },
            "Random Rotation": {
                "code": "random(360)",
                "desc": "Random rotation value",
                "builtin": True
            }
        },
        "Time": {
            "Time Remap Loop": {
                "code": "loopOut('cycle')",
                "desc": "Loop animation continuously",
                "builtin": True
            }
        },
        "Audio": {
            "Scale with Audio": {
                "code": 'audio = thisComp.layer("Audio Layer").audio.audioLevels;\nlinear(audio, -60, -20, 0, 100)',
                "desc": "Scale based on audio levels",
                "builtin": True
            }
        }
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Load UI
        self.ui = load_ui("expression_library.ui")
        
        # Copy properties from loaded widget
        self.setWindowTitle(self.ui.windowTitle())
        self.setMinimumSize(self.ui.minimumSize())
        
        # Create layout and add loaded widget
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)
        
        # Load custom expressions
        self.custom_file = Path.home() / ".aepython_expressions.json"
        self.custom_expressions = self.load_custom_expressions()
        
        # Get widget references from UI
        self.search_input = self.ui.findChild(QtWidgets.QLineEdit, "search_input")
        self.expr_tree = self.ui.findChild(QtWidgets.QTreeWidget, "expr_tree")
        self.expr_name_label = self.ui.findChild(QtWidgets.QLabel, "expr_name_label")
        self.expr_desc_label = self.ui.findChild(QtWidgets.QLabel, "expr_desc_label")
        self.code_display = self.ui.findChild(QtWidgets.QPlainTextEdit, "code_display")
        self.read_only_check = self.ui.findChild(QtWidgets.QCheckBox, "read_only_check")
        
        # Connect signals
        self.search_input.textChanged.connect(self.filter_expressions)
        self.ui.findChild(QtWidgets.QPushButton, "clear_search_btn").clicked.connect(
            lambda: self.search_input.clear()
        )
        self.expr_tree.currentItemChanged.connect(self.on_selection_changed)
        
        # Action buttons
        self.ui.findChild(QtWidgets.QPushButton, "add_btn").clicked.connect(self.add_expression)
        self.ui.findChild(QtWidgets.QPushButton, "edit_btn").clicked.connect(self.edit_expression)
        self.ui.findChild(QtWidgets.QPushButton, "delete_btn").clicked.connect(self.delete_expression)
        
        # Import/Export
        self.ui.findChild(QtWidgets.QPushButton, "import_btn").clicked.connect(self.import_expressions)
        self.ui.findChild(QtWidgets.QPushButton, "export_btn").clicked.connect(self.export_expressions)
        
        # Editor controls
        self.read_only_check.stateChanged.connect(self.toggle_read_only)
        self.ui.findChild(QtWidgets.QPushButton, "save_code_btn").clicked.connect(self.save_code_changes)
        
        # Apply button
        self.ui.findChild(QtWidgets.QPushButton, "apply_btn").clicked.connect(self.apply_expression)
        
        # Populate tree
        self.populate_tree()
        
        # Select first item
        if self.expr_tree.topLevelItemCount() > 0:
            first_category = self.expr_tree.topLevelItem(0)
            if first_category.childCount() > 0:
                self.expr_tree.setCurrentItem(first_category.child(0))
    
    def load_custom_expressions(self):
        """Load custom expressions from JSON file"""
        import json
        if not self.custom_file.exists():
            return {"Custom": {}}
        
        try:
            with open(self.custom_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"Custom": {}}
    
    def save_custom_expressions(self):
        """Save custom expressions to JSON file"""
        import json
        try:
            with open(self.custom_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_expressions, f, indent=2)
        except Exception as e:
            ae.alert(f"Failed to save expressions: {e}")
    
    def populate_tree(self):
        """Populate the expression tree"""
        import json
        self.expr_tree.clear()
        
        # Add built-in expressions
        for category, expressions in self.BUILTIN_EXPRESSIONS.items():
            category_item = QtWidgets.QTreeWidgetItem([f"📁 {category}"])
            category_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, {"type": "category", "name": category})
            
            for name, data in expressions.items():
                expr_item = QtWidgets.QTreeWidgetItem([name])
                expr_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, {
                    "type": "expression",
                    "category": category,
                    "name": name,
                    "data": data
                })
                category_item.addChild(expr_item)
            
            self.expr_tree.addTopLevelItem(category_item)
            category_item.setExpanded(True)
        
        # Add custom expressions
        for category, expressions in self.custom_expressions.items():
            category_item = QtWidgets.QTreeWidgetItem([f"⭐ {category}"])
            category_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, {"type": "category", "name": category, "custom": True})
            
            for name, data in expressions.items():
                expr_item = QtWidgets.QTreeWidgetItem([name])
                expr_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, {
                    "type": "expression",
                    "category": category,
                    "name": name,
                    "data": data,
                    "custom": True
                })
                category_item.addChild(expr_item)
            
            self.expr_tree.addTopLevelItem(category_item)
            category_item.setExpanded(True)
    
    def filter_expressions(self):
        """Filter expressions based on search text"""
        import json
        search_text = self.search_input.text().lower()
        
        for i in range(self.expr_tree.topLevelItemCount()):
            category = self.expr_tree.topLevelItem(i)
            category_visible = False
            
            for j in range(category.childCount()):
                child = category.child(j)
                item_data = child.data(0, QtCore.Qt.ItemDataRole.UserRole)
                
                name_match = search_text in item_data["name"].lower()
                desc_match = search_text in item_data["data"].get("desc", "").lower()
                
                visible = not search_text or name_match or desc_match
                child.setHidden(not visible)
                
                if visible:
                    category_visible = True
            
            category.setHidden(not category_visible)
    
    def on_selection_changed(self, current, previous):
        """Update code display when selection changes"""
        import json
        if not current:
            return
        
        item_data = current.data(0, QtCore.Qt.ItemDataRole.UserRole)
        
        if item_data.get("type") != "expression":
            self.code_display.clear()
            self.expr_name_label.setText("Select an expression")
            self.expr_desc_label.setText("")
            return
        
        expr_data = item_data["data"]
        self.expr_name_label.setText(item_data["name"])
        self.expr_desc_label.setText(expr_data.get("desc", "No description"))
        self.code_display.setPlainText(expr_data["code"])
        
        # Set read-only for built-in expressions
        is_builtin = expr_data.get("builtin", False)
        self.read_only_check.setChecked(is_builtin)
        self.code_display.setReadOnly(is_builtin)
    
    def toggle_read_only(self):
        """Toggle read-only mode"""
        import json
        self.code_display.setReadOnly(self.read_only_check.isChecked())
    
    def save_code_changes(self):
        """Save code changes to custom expression"""
        import json
        current = self.expr_tree.currentItem()
        if not current:
            return
        
        item_data = current.data(0, QtCore.Qt.ItemDataRole.UserRole)
        
        if item_data.get("type") != "expression":
            return
        
        if item_data["data"].get("builtin"):
            ae.alert("Cannot modify built-in expressions. Create a custom copy instead.")
            return
        
        # Update the expression code
        category = item_data["category"]
        name = item_data["name"]
        self.custom_expressions[category][name]["code"] = self.code_display.toPlainText()
        
        self.save_custom_expressions()
        print(f"✓ Saved changes to '{name}'")
    
    def add_expression(self):
        """Add a new custom expression"""
        import json
        dialog = AddExpressionDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            category = dialog.category_input.text()
            name = dialog.name_input.text()
            desc = dialog.desc_input.text()
            code = dialog.code_input.toPlainText()
            
            if not category or not name or not code:
                ae.alert("Please fill in all required fields!")
                return
            
            # Add to custom expressions
            if category not in self.custom_expressions:
                self.custom_expressions[category] = {}
            
            self.custom_expressions[category][name] = {
                "code": code,
                "desc": desc,
                "builtin": False
            }
            
            self.save_custom_expressions()
            self.populate_tree()
            print(f"✓ Added expression '{name}'")
    
    def edit_expression(self):
        """Edit current expression"""
        import json
        current = self.expr_tree.currentItem()
        if not current:
            return
        
        item_data = current.data(0, QtCore.Qt.ItemDataRole.UserRole)
        
        if item_data.get("type") != "expression":
            ae.alert("Please select an expression to edit.")
            return
        
        if item_data["data"].get("builtin"):
            ae.alert("Cannot edit built-in expressions. Create a custom copy instead.")
            return
        
        # Open edit dialog
        dialog = AddExpressionDialog(self, edit_mode=True, item_data=item_data)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            old_category = item_data["category"]
            old_name = item_data["name"]
            
            new_category = dialog.category_input.text()
            new_name = dialog.name_input.text()
            new_desc = dialog.desc_input.text()
            new_code = dialog.code_input.toPlainText()
            
            # Delete old entry
            del self.custom_expressions[old_category][old_name]
            if not self.custom_expressions[old_category]:
                del self.custom_expressions[old_category]
            
            # Add new entry
            if new_category not in self.custom_expressions:
                self.custom_expressions[new_category] = {}
            
            self.custom_expressions[new_category][new_name] = {
                "code": new_code,
                "desc": new_desc,
                "builtin": False
            }
            
            self.save_custom_expressions()
            self.populate_tree()
            print(f"✓ Updated expression '{new_name}'")
    
    def delete_expression(self):
        """Delete current custom expression"""
        import json
        current = self.expr_tree.currentItem()
        if not current:
            return
        
        item_data = current.data(0, QtCore.Qt.ItemDataRole.UserRole)
        
        if item_data.get("type") != "expression":
            ae.alert("Please select an expression to delete.")
            return
        
        if item_data["data"].get("builtin"):
            ae.alert("Cannot delete built-in expressions.")
            return
        
        reply = QtWidgets.QMessageBox.question(
            self,
            "Delete Expression",
            f"Delete '{item_data['name']}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            category = item_data["category"]
            name = item_data["name"]
            
            del self.custom_expressions[category][name]
            if not self.custom_expressions[category]:
                del self.custom_expressions[category]
            
            self.save_custom_expressions()
            self.populate_tree()
            print(f"✓ Deleted expression '{name}'")
    
    def import_expressions(self):
        """Import expressions from JSON file"""
        import json
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Import Expressions",
            "",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)
            
            # Merge with existing
            for category, expressions in imported.items():
                if category not in self.custom_expressions:
                    self.custom_expressions[category] = {}
                self.custom_expressions[category].update(expressions)
            
            self.save_custom_expressions()
            self.populate_tree()
            print(f"✓ Imported expressions from {Path(file_path).name}")
        except Exception as e:
            ae.alert(f"Failed to import: {e}")
    
    def export_expressions(self):
        """Export custom expressions to JSON file"""
        import json
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Expressions",
            "expressions.json",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.custom_expressions, f, indent=2)
            print(f"✓ Exported expressions to {Path(file_path).name}")
        except Exception as e:
            ae.alert(f"Failed to export: {e}")
    
    def apply_expression(self):
        """Apply selected expression to property"""
        import json
        current = self.expr_tree.currentItem()
        if not current:
            return
        
        item_data = current.data(0, QtCore.Qt.ItemDataRole.UserRole)
        
        if item_data.get("type") != "expression":
            ae.alert("Please select an expression to apply.")
            return
        
        expr_data = item_data["data"]
        expr_name = item_data["name"]
        
        comp = ae.app.project.activeItem
        if not comp or not isinstance(comp, ae.CompItem):
            ae.alert("Please select a composition first!")
            return
        
        layers = comp.selectedLayers
        if len(layers) == 0:
            ae.alert("Please select a layer first!")
            return
        
        selected_props = comp.selectedProperties
        if len(selected_props) == 0:
            ae.alert("Please select a property first!\n\nSelect the property (like Position, Scale, etc) in the timeline before applying.")
            return
        
        ae.app.beginUndoGroup(f"Apply Expression: {expr_name}")
        
        code = self.code_display.toPlainText()
        
        for prop in selected_props:
            try:
                prop.expression = code
                print(f"✓ Applied '{expr_name}' to {layers[0].name}")
            except Exception as e:
                print(f"✗ Could not apply to this property: {e}")
        
        ae.app.endUndoGroup()


dialog = ExpressionLibrary(qtae.GetQtAEMainWindow())
dialog.show()
