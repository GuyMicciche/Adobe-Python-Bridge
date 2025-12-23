"""
Batch Layer Renamer
Advanced renaming with patterns, numbering, prefix/suffix, find/replace
"""
import AEPython as ae
import qtae
from PySide6 import QtWidgets, QtCore

class BatchRenamer(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Import re and make it available
        import re
        self.re = re

        self.setWindowTitle("✏️ Batch Layer Renamer")
        self.setMinimumWidth(450)
        self.setMinimumHeight(500)
        
        layout = QtWidgets.QVBoxLayout()
        
        # Tab widget for different rename modes
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setMaximumHeight(220)
        
        # Tab 1: Prefix/Suffix
        prefix_tab = QtWidgets.QWidget()
        prefix_layout = QtWidgets.QFormLayout()
        self.prefix_input = QtWidgets.QLineEdit()
        self.suffix_input = QtWidgets.QLineEdit()
        prefix_layout.addRow("Prefix:", self.prefix_input)
        prefix_layout.addRow("Suffix:", self.suffix_input)
        prefix_btn = QtWidgets.QPushButton("Apply")
        prefix_btn.clicked.connect(self.apply_prefix_suffix)
        prefix_layout.addRow(prefix_btn)
        prefix_tab.setLayout(prefix_layout)
        
        # Tab 2: Number Sequence
        number_tab = QtWidgets.QWidget()
        number_layout = QtWidgets.QFormLayout()
        self.base_name = QtWidgets.QLineEdit("Layer")
        self.start_num = QtWidgets.QSpinBox()
        self.start_num.setMinimum(0)
        self.start_num.setMaximum(9999)
        self.padding = QtWidgets.QSpinBox()
        self.padding.setMinimum(1)
        self.padding.setMaximum(6)
        self.padding.setValue(2)
        number_layout.addRow("Base Name:", self.base_name)
        number_layout.addRow("Start Number:", self.start_num)
        number_layout.addRow("Padding:", self.padding)
        number_btn = QtWidgets.QPushButton("Apply Numbering")
        number_btn.clicked.connect(self.apply_numbering)
        number_layout.addRow(number_btn)
        number_tab.setLayout(number_layout)
        
        # Tab 3: Find/Replace
        find_tab = QtWidgets.QWidget()
        find_layout = QtWidgets.QFormLayout()
        self.find_text = QtWidgets.QLineEdit()
        self.replace_text = QtWidgets.QLineEdit()
        self.regex_check = QtWidgets.QCheckBox("Use Regex")
        self.case_check = QtWidgets.QCheckBox("Case Sensitive")
        find_layout.addRow("Find:", self.find_text)
        find_layout.addRow("Replace:", self.replace_text)
        find_layout.addRow(self.regex_check)
        find_layout.addRow(self.case_check)
        find_btn = QtWidgets.QPushButton("Find && Replace")
        find_btn.clicked.connect(self.apply_find_replace)
        find_layout.addRow(find_btn)
        find_tab.setLayout(find_layout)
        
        self.tabs.addTab(prefix_tab, "Prefix/Suffix")
        self.tabs.addTab(number_tab, "Numbering")
        self.tabs.addTab(find_tab, "Find/Replace")
        layout.addWidget(self.tabs, stretch=0)
        
        # Preview section (CREATE FIRST)
        preview_label = QtWidgets.QLabel("Preview:")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(preview_label)
        
        self.preview = QtWidgets.QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMinimumHeight(200)
        self.preview.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace; font-size: 9pt;")
        layout.addWidget(self.preview, stretch=1)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("🔄 Refresh Preview")
        refresh_btn.clicked.connect(self.update_preview)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
        
        # NOW connect signals AFTER preview exists
        self.tabs.currentChanged.connect(self.update_preview)
        self.prefix_input.textChanged.connect(self.update_preview)
        self.suffix_input.textChanged.connect(self.update_preview)
        self.base_name.textChanged.connect(self.update_preview)
        self.start_num.valueChanged.connect(self.update_preview)
        self.padding.valueChanged.connect(self.update_preview)
        self.find_text.textChanged.connect(self.update_preview)
        self.replace_text.textChanged.connect(self.update_preview)
        self.regex_check.stateChanged.connect(self.update_preview)
        self.case_check.stateChanged.connect(self.update_preview)
        
        # Initial preview
        self.update_preview()
    
    def get_selected_layers(self):
        comp = ae.app.project.activeItem
        if not comp or not isinstance(comp, ae.CompItem):
            return None
        
        layers = comp.selectedLayers
        if len(layers) == 0:
            return None
        
        return layers
    
    def update_preview(self):
        """Update the preview based on current tab and settings"""
        layers = self.get_selected_layers()
        
        if not layers:
            self.preview.setPlainText("⚠️ No layers selected\n\nSelect layers in the active composition to see preview.")
            return
        
        current_tab = self.tabs.currentIndex()
        preview_lines = []
        
        # Limit preview to first 10 layers
        preview_layers = layers[:10]
        show_more = len(layers) > 10
        
        if current_tab == 0:  # Prefix/Suffix
            prefix = self.prefix_input.text()
            suffix = self.suffix_input.text()
            
            for layer in preview_layers:
                old_name = layer.name
                new_name = f"{prefix}{old_name}{suffix}"
                preview_lines.append(f"{old_name} → {new_name}")
        
        elif current_tab == 1:  # Numbering
            base = self.base_name.text()
            start = self.start_num.value()
            pad = self.padding.value()
            
            for i, layer in enumerate(preview_layers):
                old_name = layer.name
                num = str(start + i).zfill(pad)
                new_name = f"{base}_{num}"
                preview_lines.append(f"{old_name} → {new_name}")
        
        elif current_tab == 2:  # Find/Replace
            find = self.find_text.text()
            replace = self.replace_text.text()
            
            if not find:
                self.preview.setPlainText("⚠️ Enter text to find")
                return
            
            for layer in preview_layers:
                old_name = layer.name
                try:
                    if self.regex_check.isChecked():
                        flags = 0 if self.case_check.isChecked() else self.re.IGNORECASE
                        new_name = self.re.sub(find, replace, old_name, flags=flags)
                    else:
                        if self.case_check.isChecked():
                            new_name = old_name.replace(find, replace)
                        else:
                            new_name = self.re.sub(self.re.escape(find), replace, old_name, flags=self.re.IGNORECASE)
                    
                    if new_name != old_name:
                        preview_lines.append(f"{old_name} → {new_name}")
                    else:
                        preview_lines.append(f"{old_name} (no change)")
                except Exception as e:
                    preview_lines.append(f"{old_name} ✗ Error: {str(e)}")
        
        # Build preview text
        preview_text = "\n".join(preview_lines)
        
        if show_more:
            preview_text += f"\n\n... and {len(layers) - 10} more layers"
        
        if not preview_lines:
            preview_text = "No changes will be made"
        
        self.preview.setPlainText(preview_text)
    
    def apply_prefix_suffix(self):
        layers = self.get_selected_layers()
        if not layers:
            ae.alert("Please select at least one layer!")
            return
        
        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        
        ae.app.beginUndoGroup("Prefix/Suffix Rename")
        for layer in layers:
            layer.name = f"{prefix}{layer.name}{suffix}"
        ae.app.endUndoGroup()
        
        print(f"✓ Renamed {len(layers)} layers with prefix/suffix")
        self.update_preview()
    
    def apply_numbering(self):
        layers = self.get_selected_layers()
        if not layers:
            ae.alert("Please select at least one layer!")
            return
        
        base = self.base_name.text()
        start = self.start_num.value()
        pad = self.padding.value()
        
        ae.app.beginUndoGroup("Number Sequence Rename")
        for i, layer in enumerate(layers):
            num = str(start + i).zfill(pad)
            layer.name = f"{base}_{num}"
        ae.app.endUndoGroup()
        
        print(f"✓ Renamed {len(layers)} layers with numbering")
        self.update_preview()
    
    def apply_find_replace(self):
        layers = self.get_selected_layers()
        if not layers:
            ae.alert("Please select at least one layer!")
            return
        
        find = self.find_text.text()
        replace = self.replace_text.text()
        
        if not find:
            ae.alert("Please enter text to find!")
            return
        
        ae.app.beginUndoGroup("Find/Replace Rename")
        count = 0
        for layer in layers:
            try:
                if self.regex_check.isChecked():
                    flags = 0 if self.case_check.isChecked() else self.re.IGNORECASE
                    new_name = self.re.sub(find, replace, layer.name, flags=flags)
                else:
                    if self.case_check.isChecked():
                        new_name = layer.name.replace(find, replace)
                    else:
                        new_name = self.re.sub(self.re.escape(find), replace, layer.name, flags=self.re.IGNORECASE)
                
                if new_name != layer.name:
                    layer.name = new_name
                    count += 1
            except Exception as e:
                print(f"✗ Error renaming {layer.name}: {e}")
        
        ae.app.endUndoGroup()
        print(f"✓ Renamed {count} layers")
        self.update_preview()

dialog = BatchRenamer(qtae.GetQtAEMainWindow())
dialog.show()