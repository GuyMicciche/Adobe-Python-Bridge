"""
Expression Library
Browse, create, edit, and apply expressions with full management features
"""
import AEPython as ae
import qtae
from PySide6 import QtWidgets, QtCore, QtGui
import json
from pathlib import Path


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
    
    # NESTED CLASS - AddExpressionDialog defined INSIDE ExpressionLibrary
    class AddExpressionDialog(QtWidgets.QDialog):
        """Dialog for adding/editing expressions"""
        def __init__(self, parent=None, edit_mode=False, item_data=None):
            super().__init__(parent)
            self.setWindowTitle("Edit Expression" if edit_mode else "Add Expression")
            self.setMinimumSize(500, 400)
            
            layout = QtWidgets.QVBoxLayout()
            
            form_layout = QtWidgets.QFormLayout()
            
            self.category_input = QtWidgets.QLineEdit()
            form_layout.addRow("Category:", self.category_input)
            
            self.name_input = QtWidgets.QLineEdit()
            form_layout.addRow("Name:", self.name_input)
            
            self.desc_input = QtWidgets.QLineEdit()
            form_layout.addRow("Description:", self.desc_input)
            
            layout.addLayout(form_layout)
            
            code_label = QtWidgets.QLabel("Expression Code:")
            layout.addWidget(code_label)
            
            self.code_input = QtWidgets.QPlainTextEdit()
            self.code_input.setStyleSheet("""
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                background-color: #1e1e1e;
                color: #d4d4d4;
            """)
            layout.addWidget(self.code_input, stretch=1)
            
            # Buttons
            button_layout = QtWidgets.QHBoxLayout()
            
            save_btn = QtWidgets.QPushButton("Save")
            save_btn.clicked.connect(self.accept)
            button_layout.addWidget(save_btn)
            
            cancel_btn = QtWidgets.QPushButton("Cancel")
            cancel_btn.clicked.connect(self.reject)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            self.setLayout(layout)
            
            # Populate if editing
            if edit_mode and item_data:
                self.category_input.setText(item_data["category"])
                self.name_input.setText(item_data["name"])
                self.desc_input.setText(item_data["data"].get("desc", ""))
                self.code_input.setPlainText(item_data["data"]["code"])
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📚 Expression Library Pro")
        self.setMinimumSize(800, 600)
        
        # Load custom expressions
        self.custom_file = Path.home() / ".aepython_expressions.json"
        self.custom_expressions = self.load_custom_expressions()
        
        # Main layout
        main_layout = QtWidgets.QHBoxLayout()
        
        # Left panel - Expression browser
        left_panel = QtWidgets.QVBoxLayout()
        
        # Header
        header = QtWidgets.QLabel("📚 Expression Library Pro")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        left_panel.addWidget(header)
        
        # Search box
        search_layout = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search expressions...")
        self.search_input.textChanged.connect(self.filter_expressions)
        search_layout.addWidget(self.search_input)
        
        clear_search_btn = QtWidgets.QPushButton("✕")
        clear_search_btn.clicked.connect(lambda: self.search_input.clear())
        search_layout.addWidget(clear_search_btn)
        left_panel.addLayout(search_layout)
        
        # Category/Expression tree
        tree_label = QtWidgets.QLabel("Expressions:")
        left_panel.addWidget(tree_label)
        
        self.expr_tree = QtWidgets.QTreeWidget()
        self.expr_tree.setHeaderHidden(True)
        self.expr_tree.currentItemChanged.connect(self.on_selection_changed)
        left_panel.addWidget(self.expr_tree)
        
        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        add_btn = QtWidgets.QPushButton("➕ New")
        add_btn.clicked.connect(self.add_expression)
        button_layout.addWidget(add_btn)
        
        edit_btn = QtWidgets.QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self.edit_expression)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QtWidgets.QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self.delete_expression)
        button_layout.addWidget(delete_btn)
        
        left_panel.addLayout(button_layout)
        
        # Import/Export buttons
        io_layout = QtWidgets.QHBoxLayout()
        
        import_btn = QtWidgets.QPushButton("📥 Import")
        import_btn.clicked.connect(self.import_expressions)
        io_layout.addWidget(import_btn)
        
        export_btn = QtWidgets.QPushButton("📤 Export")
        export_btn.clicked.connect(self.export_expressions)
        io_layout.addWidget(export_btn)
        
        left_panel.addLayout(io_layout)
        
        # Right panel - Code editor and details
        right_panel = QtWidgets.QVBoxLayout()
        
        # Expression name and description
        self.expr_name_label = QtWidgets.QLabel("Expression Name")
        self.expr_name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        right_panel.addWidget(self.expr_name_label)
        
        self.expr_desc_label = QtWidgets.QLabel("Description")
        self.expr_desc_label.setWordWrap(True)
        self.expr_desc_label.setStyleSheet("color: #888; padding: 5px;")
        right_panel.addWidget(self.expr_desc_label)
        
        # Code editor
        code_label = QtWidgets.QLabel("Expression Code:")
        code_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        right_panel.addWidget(code_label)
        
        self.code_display = QtWidgets.QPlainTextEdit()
        self.code_display.setStyleSheet("""
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 10pt;
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            padding: 8px;
        """)
        self.code_display.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        right_panel.addWidget(self.code_display, stretch=1)  # Takes all available space
        
        # Editor controls
        editor_controls = QtWidgets.QHBoxLayout()
        
        self.read_only_check = QtWidgets.QCheckBox("Read-only")
        self.read_only_check.setChecked(True)
        self.read_only_check.stateChanged.connect(self.toggle_read_only)
        editor_controls.addWidget(self.read_only_check)
        
        editor_controls.addStretch()
        
        save_code_btn = QtWidgets.QPushButton("💾 Save Changes")
        save_code_btn.clicked.connect(self.save_code_changes)
        editor_controls.addWidget(save_code_btn)
        
        right_panel.addLayout(editor_controls)
        
        # Apply button
        apply_btn = QtWidgets.QPushButton("✨ Apply to Selected Property")
        apply_btn.setStyleSheet("font-weight: bold; padding: 10px;")
        apply_btn.clicked.connect(self.apply_expression)
        right_panel.addWidget(apply_btn)
        
        # Instructions
        info = QtWidgets.QLabel("💡 Select a property in After Effects timeline, then click Apply to add expression.")
        info.setStyleSheet("padding: 10px; background-color: #333; border-radius: 4px; color: #aaa;")
        info.setWordWrap(True)
        right_panel.addWidget(info)
        
        # Add panels to main layout
        left_widget = QtWidgets.QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(300)
        
        right_widget = QtWidgets.QWidget()
        right_widget.setLayout(right_panel)
        
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, stretch=1)
        
        self.setLayout(main_layout)
        
        # Populate tree
        self.populate_tree()
        
        # Select first item
        if self.expr_tree.topLevelItemCount() > 0:
            first_category = self.expr_tree.topLevelItem(0)
            if first_category.childCount() > 0:
                self.expr_tree.setCurrentItem(first_category.child(0))
    
    def load_custom_expressions(self):
        """Load custom expressions from JSON file"""
        if not self.custom_file.exists():
            return {"Custom": {}}
        
        try:
            with open(self.custom_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"Custom": {}}
    
    def save_custom_expressions(self):
        """Save custom expressions to JSON file"""
        try:
            with open(self.custom_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_expressions, f, indent=2)
        except Exception as e:
            ae.alert(f"Failed to save expressions: {e}")
    
    def populate_tree(self):
        """Populate the expression tree"""
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
        self.code_display.setReadOnly(self.read_only_check.isChecked())
    
    def save_code_changes(self):
        """Save code changes to custom expression"""
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
        # Use self.AddExpressionDialog to reference nested class
        dialog = self.AddExpressionDialog(self)
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
        
        # Open edit dialog - use self.AddExpressionDialog
        dialog = self.AddExpressionDialog(self, edit_mode=True, item_data=item_data)
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