"""
AEPython Script Library Manager

A comprehensive script management UI for storing, organizing, and executing
custom Python scripts for After Effects.

Features:
- Folder-based categories
- JSON metadata for tags, favorites, descriptions
- Search and filter functionality
- Script execution and editing
- Dockable panel support
- Theme integration with main console
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from PySide6 import QtGui, QtWidgets, QtCore
import _AEPython as _ae
import AEPython as ae

from qtae import DotSplitter

from completer import HighlightedCompleter


__MainWindow = None
__ScriptLibraryWindow = None


class ScriptMetadata:
    """Represents metadata for a single script"""
    
    def __init__(self, script_id: str, data: Dict = None):
        self.script_id = script_id
        data = data or {}
        
        self.name = data.get('name', '')
        self.description = data.get('description', '')
        self.category = data.get('category', 'Uncategorized')
        self.tags = data.get('tags', [])
        self.favorite = data.get('favorite', False)
        self.author = data.get('author', '')
        self.created = data.get('created', '')
        self.modified = data.get('modified', '')
        self.file_path = data.get('file_path', '')
        
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'tags': self.tags,
            'favorite': self.favorite,
            'author': self.author,
            'created': self.created,
            'modified': self.modified,
            'file_path': self.file_path
        }


class ScriptLibraryManager:
    """Manages script metadata and file system operations"""
    
    def __init__(self, metadata_path: Path, scripts_root: Path):
        self.metadata_path = metadata_path
        self.scripts_root = scripts_root
        self.scripts: Dict[str, ScriptMetadata] = {}
        
        # Ensure directories exist
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self.scripts_root.mkdir(parents=True, exist_ok=True)
        
        self.load_metadata()
    
    def load_metadata(self):
        """Load metadata from JSON file"""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for script_id, metadata in data.items():
                        self.scripts[script_id] = ScriptMetadata(script_id, metadata)
            except Exception as e:
                print(f"Failed to load metadata: {e}", file=sys.stderr)
    
    def save_metadata(self):
        """Save metadata to JSON file"""
        try:
            data = {sid: meta.to_dict() for sid, meta in self.scripts.items()}
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save metadata: {e}", file=sys.stderr)
    
    def scan_scripts(self) -> List[ScriptMetadata]:
        """Scan ALL .py files, skip folders with __init__.py (modules/packages)"""
        found_scripts = {}
        
        self.load_metadata()
        
        # Scan all .py files recursively
        for py_file in self.scripts_root.rglob('*.py'):
            rel_path = py_file.relative_to(self.scripts_root)
            script_id = str(rel_path.as_posix())
            
            # ✅ Skip if parent folder has __init__.py (is a module/package)
            parent_folder = py_file.parent
            if (parent_folder / '__init__.py').exists():
                continue  # Skip modules
            
            # Get category from FIRST parent folder (or immediate parent)
            category_parts = rel_path.parent.parts
            category = category_parts[0] if category_parts else 'Uncategorized'
            
            # Check if we have metadata
            if script_id in self.scripts:
                metadata = self.scripts[script_id]
                metadata.file_path = str(py_file)
                metadata.category = category
            else:
                metadata = ScriptMetadata(script_id, {
                    'name': py_file.stem,
                    'category': category,
                    'file_path': str(py_file),
                    'created': datetime.now().isoformat(),
                    'modified': datetime.fromtimestamp(py_file.stat().st_mtime).isoformat()
                })
            
            found_scripts[script_id] = metadata
        
        # Remove stale metadata
        self.scripts = found_scripts
        self.save_metadata()
        
        return list(self.scripts.values())

    
    def get_categories(self) -> List[str]:
        """Get list of unique categories"""
        categories = set(meta.category for meta in self.scripts.values())
        return sorted(categories)
    
    def get_all_tags(self) -> List[str]:
        """Get list of all unique tags"""
        tags = set()
        for meta in self.scripts.values():
            tags.update(meta.tags)
        return sorted(tags)
    
    def update_script_metadata(self, script_id: str, **kwargs):
        """Update metadata for a script"""
        if script_id in self.scripts:
            metadata = self.scripts[script_id]
            for key, value in kwargs.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)
            metadata.modified = datetime.now().isoformat()
            self.save_metadata()
    
    def create_script(self, name: str, category: str, content: str = "") -> Optional[str]:
        """Create a new script file"""
        # Create category folder if needed
        category_path = self.scripts_root / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        # Create script file
        script_file = category_path / f"{name}.py"
        
        # Check if file already exists
        if script_file.exists():
            return None
        
        try:
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Create metadata
            script_id = str(script_file.relative_to(self.scripts_root).as_posix())
            self.scripts[script_id] = ScriptMetadata(script_id, {
                'name': name,
                'category': category,
                'file_path': str(script_file),
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat()
            })
            self.save_metadata()
            
            return script_id
        except Exception as e:
            print(f"Failed to create script: {e}", file=sys.stderr)
            return None
    
    def read_script(self, script_id: str) -> Optional[str]:
        """Read script content from file"""
        if script_id not in self.scripts:
            return None
        
        try:
            with open(self.scripts[script_id].file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Failed to read script: {e}", file=sys.stderr)
            return None


class ScriptListItem(QtWidgets.QWidget):
    """Custom widget for displaying a script in the list"""
    
    clicked = QtCore.Signal(str)
    double_clicked = QtCore.Signal(str)
    
    def __init__(self, metadata: ScriptMetadata):
        super().__init__()
        self.metadata = metadata
        self.selected = False
        
        # Get current theme colors from qtae
        from qtae import PythonWindowInstance
        self.theme_colors = PythonWindowInstance.themes.get_highlighter_colors(
            PythonWindowInstance.current_theme_key
        ) if PythonWindowInstance else {}
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Favorite icon - uses theme colors
        self.fav_label = QtWidgets.QLabel("★" if self.metadata.favorite else "☆")
        self.fav_label.setFixedWidth(20)
        fav_color = self.theme_colors.get('brace_color' if self.metadata.favorite else 'output_text', '#ffd700')
        self.fav_label.setStyleSheet(f"color: {fav_color}; font-weight: bold;")
        layout.addWidget(self.fav_label)
        
        # Script info
        info_layout = QtWidgets.QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Name - uses theme text color
        name_label = QtWidgets.QLabel(self.metadata.name)
        text_color = self.theme_colors.get('output_text', '#d4d4d4')
        name_label.setStyleSheet(f"color: {text_color}; font-weight: bold; font-size: 11px;")
        info_layout.addWidget(name_label)
        
        # Description - uses muted theme color
        if self.metadata.description:
            desc_label = QtWidgets.QLabel(self.metadata.description)
            muted_color = self.theme_colors.get('line_number', '#858585')
            desc_label.setStyleSheet(f"color: {muted_color}; font-size: 9px;")
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label)
        
        # Tags - uses theme accent colors
        if self.metadata.tags:
            tags_widget = QtWidgets.QWidget()
            tags_layout = QtWidgets.QHBoxLayout(tags_widget)
            tags_layout.setContentsMargins(0, 0, 0, 0)
            tags_layout.setSpacing(4)
            
            for tag in self.metadata.tags[:5]:  # Limit display
                tag_label = QtWidgets.QLabel(f"#{tag}")
                accent_color = self.theme_colors.get('keyword_color', '#569cd6')
                tag_label.setStyleSheet(f"""
                    background-color: {accent_color};
                    color: #ffffff;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 8px;
                    font-weight: 500;
                """)
                tags_layout.addWidget(tag_label)
            
            tags_layout.addStretch()
            info_layout.addWidget(tags_widget)
        
        layout.addLayout(info_layout, 1)
        
        # Category badge - uses theme background/button colors
        category_label = QtWidgets.QLabel(self.metadata.category)
        bg_color = self.theme_colors.get('background', '#1e1e1e')
        cat_text_color = self.theme_colors.get('output_text', '#d4d4d4')
        category_label.setStyleSheet(f"""
            background-color: {QtGui.QColor(bg_color).lighter(170).name()};
            color: {cat_text_color};
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 9px;
        """)
        category_label.setFixedHeight(24)
        layout.addWidget(category_label)
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit(self.metadata.script_id)
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.metadata.script_id)
    
    def set_selected(self, selected: bool):
        self.selected = selected
        if selected:
            # Use theme selection color
            sel_color = self.theme_colors.get('current_line', '#264f78')
            self.setStyleSheet(f"background-color: {sel_color}; border-radius: 2px;")
        else:
            self.setStyleSheet("background-color: transparent;")
    
    def update_favorite(self, is_favorite: bool):
        self.metadata.favorite = is_favorite
        self.fav_label.setText("★" if is_favorite else "☆")
        fav_color = self.theme_colors.get('brace_color' if is_favorite else 'output_text', '#ffd700')
        self.fav_label.setStyleSheet(f"color: {fav_color}; font-weight: bold;")



class ScriptEditorDialog(QtWidgets.QDialog):
    """Dialog for editing script metadata"""
    
    def __init__(self, metadata: ScriptMetadata, all_tags: List[str], parent=None):
        super().__init__(parent)
        self.metadata = metadata
        self.all_tags = all_tags
        self.setWindowTitle(f"Edit Script: {metadata.name}")
        self.setModal(True)
        self.resize(500, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Name
        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(QtWidgets.QLabel("Name:"))
        self.name_edit = QtWidgets.QLineEdit(self.metadata.name)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Description
        layout.addWidget(QtWidgets.QLabel("Description:"))
        self.desc_edit = QtWidgets.QTextEdit()
        self.desc_edit.setPlainText(self.metadata.description)
        self.desc_edit.setMaximumHeight(100)
        layout.addWidget(self.desc_edit)
        
        # Author
        author_layout = QtWidgets.QHBoxLayout()
        author_layout.addWidget(QtWidgets.QLabel("Author:"))
        self.author_edit = QtWidgets.QLineEdit(self.metadata.author)
        author_layout.addWidget(self.author_edit)
        layout.addLayout(author_layout)
        
        # Tags
        layout.addWidget(QtWidgets.QLabel("Tags (comma-separated):"))
        self.tags_edit = QtWidgets.QLineEdit(", ".join(self.metadata.tags))
        layout.addWidget(self.tags_edit)
        
        # Existing tags
        if self.all_tags:
            layout.addWidget(QtWidgets.QLabel("Available tags:"))
            tags_label = QtWidgets.QLabel(", ".join(self.all_tags))
            tags_label.setWordWrap(True)
            tags_label.setStyleSheet("color: #999999; font-size: 9px;")
            layout.addWidget(tags_label)
        
        # Favorite
        self.fav_check = QtWidgets.QCheckBox("Favorite")
        self.fav_check.setChecked(self.metadata.favorite)
        layout.addWidget(self.fav_check)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QtWidgets.QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def get_metadata_updates(self) -> Dict:
        """Get updated metadata"""
        tags = [t.strip() for t in self.tags_edit.text().split(',') if t.strip()]
        return {
            'name': self.name_edit.text(),
            'description': self.desc_edit.toPlainText(),
            'author': self.author_edit.text(),
            'tags': tags,
            'favorite': self.fav_check.isChecked()
        }


class ScriptLibraryWindow(QtWidgets.QMainWindow):
    """Main script library window"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, False)
        
        # Get user documents folder
        user_docs = Path.home() / "Documents" / "AEPython"
        
        # Initialize manager
        self.manager = ScriptLibraryManager(
            metadata_path=user_docs / "script_library.json",
            scripts_root=user_docs / "Scripts"
        )
        
        self.current_script_id: Optional[str] = None
        self.script_widgets: Dict[str, ScriptListItem] = {}
        
        self.setWindowTitle("AE Python Script Library")
        self.resize(800, 600)
        
        # SET WINDOW ICON
        # Option 1: Use a .ico or .png file
        icon_path = Path(__file__).parent / "icon.png"  # or "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))
        else:
            # Option 2: Create a simple colored icon programmatically
            pixmap = QtGui.QPixmap(64, 64)
            pixmap.fill(QtGui.QColor(0, 168, 120))  # Blue color
            painter = QtGui.QPainter(pixmap)
            painter.setPen(QtGui.QColor(255, 255, 255))
            painter.setFont(QtGui.QFont("Arial", 32, QtGui.QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "Py")
            painter.end()
            self.setWindowIcon(QtGui.QIcon(pixmap))

        self.setup_ui()
        
        self.setup_completer()
        
        self.refresh_scripts()
    
    def closeEvent(self, event):
        """Hide window instead of closing when user clicks X"""
        event.ignore()
        self.hide()
    
    def showEvent(self, event):
        """Auto-refresh when window shown/brought to front"""
        super().showEvent(event)
        self.reset_preview()
        QtCore.QTimer.singleShot(100, self.refresh_scripts)
    
    def setup_ui(self):
        """Setup the UI"""
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setSpacing(10)
        
        # Toolbar
        toolbar_layout = QtWidgets.QHBoxLayout()
        
        # Search
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search scripts...")
        self.search_input.textChanged.connect(self.filter_scripts)  #❌ Duplicate! # Completer handles it now
        toolbar_layout.addWidget(self.search_input, 1)
        
        # Category filter
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.currentTextChanged.connect(self.filter_scripts)
        toolbar_layout.addWidget(self.category_combo)
        
        # Filter buttons
        self.favorites_btn = QtWidgets.QPushButton("★ Favorites")
        self.favorites_btn.setCheckable(True)
        self.favorites_btn.clicked.connect(self.filter_scripts)
        toolbar_layout.addWidget(self.favorites_btn)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("⟳ Refresh")
        refresh_btn.clicked.connect(self.refresh_scripts)
        toolbar_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        # Splitter for list and preview
        splitter = DotSplitter(QtCore.Qt.Orientation.Horizontal)
        
        # LEFT: Script list
        list_widget = QtWidgets.QWidget()
        list_layout = QtWidgets.QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_layout.addWidget(QtWidgets.QLabel("Scripts"))
        
        # Scroll area for scripts
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.script_list_widget = QtWidgets.QWidget()
        self.script_list_widget.setObjectName("scriptListContainer")
        self.script_list_layout = QtWidgets.QVBoxLayout(self.script_list_widget)
        self.script_list_layout.setSpacing(0)
        self.script_list_layout.setContentsMargins(0, 0, 0, 0)
        self.script_list_layout.addStretch()
        
        scroll.setWidget(self.script_list_widget)
        list_layout.addWidget(scroll)
        
        splitter.addWidget(list_widget)
        
        # RIGHT: Preview/Actions
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_layout.addWidget(QtWidgets.QLabel("Script Preview"))
        
        # Script info
        self.info_label = QtWidgets.QLabel("Select a script to view details")
        self.info_label.setWordWrap(True)
        self.info_label.setObjectName("rightLabel")
        self.info_label.setStyleSheet("padding: 10px; border-radius: 4px;")
        right_layout.addWidget(self.info_label)
        
        # Code preview
        self.code_preview = QtWidgets.QTextEdit()
        self.code_preview.setReadOnly(True)
        right_layout.addWidget(self.code_preview)
        
        # Action buttons
        action_layout = QtWidgets.QHBoxLayout()
        
        self.run_btn = QtWidgets.QPushButton("▶ Run Script")
        self.run_btn.clicked.connect(lambda: self.run_script())
        self.run_btn.setEnabled(False)
        action_layout.addWidget(self.run_btn)

        self.edit_script_btn = QtWidgets.QPushButton("✏️ Edit Script")
        self.edit_script_btn.clicked.connect(self.edit_script_in_qtae)
        self.edit_script_btn.setEnabled(False)
        action_layout.addWidget(self.edit_script_btn)
        
        self.edit_meta_btn = QtWidgets.QPushButton("✎ Edit Info")
        self.edit_meta_btn.clicked.connect(self.edit_metadata)
        self.edit_meta_btn.setEnabled(False)
        action_layout.addWidget(self.edit_meta_btn)
        
        self.toggle_fav_btn = QtWidgets.QPushButton("☆ Favorite")
        self.toggle_fav_btn.clicked.connect(self.toggle_favorite)
        self.toggle_fav_btn.setEnabled(False)
        action_layout.addWidget(self.toggle_fav_btn)
        
        right_layout.addLayout(action_layout)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])
        
        main_layout.addWidget(splitter)
        
        # Bottom toolbar
        bottom_layout = QtWidgets.QHBoxLayout()
        
        new_script_btn = QtWidgets.QPushButton("+ New Script")
        new_script_btn.clicked.connect(self.create_new_script)
        bottom_layout.addWidget(new_script_btn)
        
        open_folder_btn = QtWidgets.QPushButton("📁 Open Scripts Folder")
        open_folder_btn.clicked.connect(self.open_scripts_folder)
        bottom_layout.addWidget(open_folder_btn)
        
        bottom_layout.addStretch()
        
        main_layout.addLayout(bottom_layout)
    
    def reset_preview(self):
        """Reset script preview to default state"""
        self.current_script_id = None
        
        # Clear preview
        self.info_label.setText("Select a script to view details")
        self.code_preview.setPlainText("")
        
        # Disable buttons
        self.run_btn.setEnabled(False)
        self.edit_script_btn.setEnabled(False)
        self.edit_meta_btn.setEnabled(False)
        self.toggle_fav_btn.setEnabled(False)
        self.toggle_fav_btn.setText("☆ Favorite")
        
        # Deselect all script items
        for widget in self.script_widgets.values():
            widget.set_selected(False)

    def setup_completer(self):
        """Setup Houdini-style search completer"""
        self.script_model = QtGui.QStandardItemModel()
        
        # Create completer
        self.completer = HighlightedCompleter(self.script_model, self.search_input)
        self.search_input.setCompleter(self.completer)
        
        # ✅ DISABLE POPUP COMPLETELY
        self.completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
    
        # ✅ SINGLE CONNECTION - handles BOTH completer AND list filtering
        self.search_input.textChanged.connect(self.on_search_changed)
        #self.completer.activated.connect(self.on_completer_activated)
        
        self.update_completer_model()

    def on_completer_activated(self, selected_text):
        """Handle completer item selection"""
        self.completer.popup().hide()
        self.search_input.clearFocus()
        
        # Find matching script_id by name
        for i in range(self.script_model.rowCount()):
            item = self.script_model.item(i)
            if item.text().lower() == selected_text.lower():
                script_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
                if script_id and script_id in self.script_widgets:
                    self.select_script(script_id)
                    self.search_input.clear()
                    break

    def update_completer_model(self):
        """Update completer model with current scripts"""
        self.script_model.clear()
        scripts = self.manager.scan_scripts()
        
        for metadata in scripts:
            item = QtGui.QStandardItem(metadata.name)
            item.setData(metadata.script_id, QtCore.Qt.ItemDataRole.UserRole)  # Store script_id
            self.script_model.appendRow(item)

    def on_search_changed(self, text):
        """Unified search handler - updates BOTH completer AND list"""
        # Update completer highlighting/filtering
        self.completer.delegate.set_search_text(text)
        self.completer.proxy_model.set_search_text(text)
        
        # Update main list (your existing logic)
        self.filter_scripts()
        
    def edit_script_in_qtae(self):
        """Open selected script in qtae new tab"""
        if not self.current_script_id:
            return
        
        filepath = self.manager.scripts[self.current_script_id].file_path
        content = self.manager.read_script(self.current_script_id)
        
        if not content:
            QtWidgets.QMessageBox.warning(self, "Error", "Could not read script file")
            return
        
        try:
            from qtae import PythonWindowInstance, ShowPythonWindow
            ShowPythonWindow()
            PythonWindowInstance._add_new_tab(filepath, content)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to open in qtae:\n{str(e)}")
    
    def refresh_scripts(self):
        """Refresh script list from disk"""
        # Scan and update
        scripts = self.manager.scan_scripts()
        
        # Update category filter
        categories = self.manager.get_categories()
        current = self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem("All Categories")
        self.category_combo.addItems(categories)
        if current in categories or current == "All Categories":
            self.category_combo.setCurrentText(current)
        
        # Clear existing list
        while self.script_list_layout.count() > 1:  # Keep stretch
            item = self.script_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.script_widgets.clear()
        
        # Add scripts to list
        for metadata in sorted(scripts, key=lambda m: (not m.favorite, m.category, m.name)):
            item = ScriptListItem(metadata)
            item.clicked.connect(self.select_script)
            item.double_clicked.connect(self.run_script)
            
            self.script_list_layout.insertWidget(self.script_list_layout.count() - 1, item)
            self.script_widgets[metadata.script_id] = item
        
        self.filter_scripts()
        self.update_completer_model()
    
    def filter_scripts(self):
        """Filter scripts based on search and filters"""
        # ✅ Use completer's cleaned search text
        search_text = self.search_input.text().lower()
        category = self.category_combo.currentText()
        favorites_only = self.favorites_btn.isChecked()
        
        for script_id, widget in self.script_widgets.items():
            metadata = widget.metadata
            
            # Enhanced search matching (like completer)
            matches_search = (
                not search_text or
                any(term in metadata.name.lower() or 
                    term in metadata.description.lower() or 
                    any(term in tag.lower() for tag in metadata.tags)
                    for term in search_text.split())
            )
            
            matches_category = category == "All Categories" or metadata.category == category
            matches_favorite = not favorites_only or metadata.favorite
            
            widget.setVisible(matches_search and matches_category and matches_favorite)

    
    def select_script(self, script_id: str):
        """Select a script and show preview"""
        # Deselect previous
        if self.current_script_id and self.current_script_id in self.script_widgets:
            self.script_widgets[self.current_script_id].set_selected(False)
        
        # Select new
        self.current_script_id = script_id
        if script_id in self.script_widgets:
            self.script_widgets[script_id].set_selected(True)
        
        # Load and display
        metadata = self.manager.scripts[script_id]
        content = self.manager.read_script(script_id)
        
        # Update info
        info_parts = [
            f"<b>{metadata.name}</b>",
            f"<i>{metadata.description}</i>" if metadata.description else "",
            f"Category: {metadata.category}",
            f"Tags: {', '.join(metadata.tags)}" if metadata.tags else "",
            f"Author: {metadata.author}" if metadata.author else "",
        ]
        self.info_label.setText("<br>".join(p for p in info_parts if p))
        
        # Update code preview
        self.code_preview.setPlainText(content or "# Could not load script")
        
        # Enable buttons
        self.run_btn.setEnabled(True)
        self.edit_script_btn.setEnabled(True)
        self.edit_meta_btn.setEnabled(True)
        self.toggle_fav_btn.setEnabled(True)
        self.toggle_fav_btn.setText("★ Unfavorite" if metadata.favorite else "☆ Favorite")
    
    def run_script(self, script_id: str = None):
        """Execute the selected script"""
        if script_id is None:
            script_id = self.current_script_id
        
        if not script_id:
            return
        
        content = self.manager.read_script(script_id)
        if not content:
            QtWidgets.QMessageBox.warning(self, "Error", "Could not read script file")
            return
        
        metadata = self.manager.scripts[script_id]
        script_path = metadata.file_path
        
        try:
            # Execute in main console context
            from qtae import PythonWindowInstance
            window = PythonWindowInstance
            colors = window.themes.get_highlighter_colors(window.current_theme_key)
            
            window.textedit_output.setTextColor(QtGui.QColor(colors["code_prefix"]))
            window.textedit_output.append(f"\n>>> Running: {metadata.name}")
            window.textedit_output.setTextColor(QtGui.QColor(colors["output_text"]))   
            
            # Create execution namespace with __file__ set correctly
            '''
            exec_globals = globals().copy()
            exec_globals['__file__'] = script_path
            '''
            
            ## OR # Create clean execution namespace
            _exec_namespace = {
                '__name__': '__main__',
                '__builtins__': __builtins__,
                'ae': ae,  # AEPython access
                '_ae': _ae  # Internal AEPython
            }
            
            if script_path:
                _exec_namespace['__file__'] = script_path
                module_dir = os.path.dirname(script_path)
                sys.path.insert(0, module_dir)
                exec(compile(content, script_path, 'exec'), _exec_namespace)
            elif '__file__' in _exec_namespace:
                del _exec_namespace['__file__']
                exec(code, _exec_namespace)    
            
            # Success message
            window.textedit_output.setTextColor(QtGui.QColor(colors["success_text"]))
            window.textedit_output.append(f"✓ Script '{metadata.name}' executed successfully!\n")
            window.textedit_output.setTextColor(QtGui.QColor(colors["output_text"]))

            '''
            QtWidgets.QMessageBox.information(
                self,
                "Success",
                f"Script '{metadata.name}' executed successfully!"
            )
            '''
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            
            window.textedit_output.setTextColor(QtGui.QColor(colors["error_text"]))
            window.textedit_output.append(f"\nError executing script:\n{error_msg}\n")
            window.textedit_output.setTextColor(QtGui.QColor(colors["output_text"]))

            QtWidgets.QMessageBox.critical(
                self,
                "Script Error",
                f"Error executing script:\n\n{error_msg}"
            )

    
    def edit_metadata(self):
        """Edit metadata for selected script"""
        if not self.current_script_id:
            return
        
        metadata = self.manager.scripts[self.current_script_id]
        all_tags = self.manager.get_all_tags()
        
        dialog = ScriptEditorDialog(metadata, all_tags, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            updates = dialog.get_metadata_updates()
            self.manager.update_script_metadata(self.current_script_id, **updates)
            self.refresh_scripts()
            self.select_script(self.current_script_id)
    
    def toggle_favorite(self):
        """Toggle favorite status of selected script"""
        if not self.current_script_id:
            return
        
        metadata = self.manager.scripts[self.current_script_id]
        new_favorite = not metadata.favorite
        
        self.manager.update_script_metadata(self.current_script_id, favorite=new_favorite)
        
        # Update UI
        if self.current_script_id in self.script_widgets:
            self.script_widgets[self.current_script_id].update_favorite(new_favorite)
        
        self.toggle_fav_btn.setText("★ Unfavorite" if new_favorite else "☆ Favorite")
    
    def create_new_script(self):
        """Create a new script"""
        # Dialog for name and category
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("New Script")
        dialog.setModal(True)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Name
        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(QtWidgets.QLabel("Script Name:"))
        name_edit = QtWidgets.QLineEdit()
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)
        
        # Category
        cat_layout = QtWidgets.QHBoxLayout()
        cat_layout.addWidget(QtWidgets.QLabel("Category:"))
        cat_combo = QtWidgets.QComboBox()
        cat_combo.setEditable(True)
        cat_combo.addItems(self.manager.get_categories())
        cat_layout.addWidget(cat_combo)
        layout.addLayout(cat_layout)
        
        # Template
        layout.addWidget(QtWidgets.QLabel("Template:"))
        template_edit = QtWidgets.QPlainTextEdit()
        template_edit.setPlaceholderText('''"""
Script description here
"""

import AEPython as ae

# Your code here
app = ae.app
''')
        layout.addWidget(template_edit)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        create_btn = QtWidgets.QPushButton("Create")
        create_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(create_btn)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            category = cat_combo.currentText().strip()
            template = template_edit.toPlainText()
            
            if not name:
                QtWidgets.QMessageBox.warning(self, "Error", "Script name is required")
                return
            
            script_id = self.manager.create_script(name, category or "Uncategorized", template)
            
            if script_id:
                self.refresh_scripts()
                self.select_script(script_id)
                QtWidgets.QMessageBox.information(
                    self,
                    "Success",
                    f"Script '{name}' created successfully!"
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to create script. File may already exist."
                )
    
    def open_scripts_folder(self):
        """Open scripts folder in file explorer"""
        import subprocess
        import platform
        
        path = str(self.manager.scripts_root)
        
        if platform.system() == 'Windows':
            subprocess.Popen(['explorer', path])
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])


def GetQtAEMainWindow():
    global __MainWindow
    if __MainWindow is None:
        import win32gui
        __MainWindow = QtWidgets.QWidget()
        win32gui.SetParent(int(__MainWindow.winId()), _ae.getMainHWND())
    return __MainWindow

def ShowScriptLibrary():
    """Show the script library window"""      
    __ScriptLibraryWindow.show()
    __ScriptLibraryWindow.raise_()
    __ScriptLibraryWindow.activateWindow()

# ADD THESE TWO FUNCTIONS:
def ToggleScriptLibrary():
    """Toggle the script library window visibility"""
    global __ScriptLibraryWindow
    if __ScriptLibraryWindow is None or not __ScriptLibraryWindow.isVisible():
        ShowScriptLibrary()
    else:
        __ScriptLibraryWindow.hide()

def IsScriptLibraryVisible():
    """Check if the script library window is visible"""
    global __ScriptLibraryWindow
    if __ScriptLibraryWindow is None:
        return False
    return __ScriptLibraryWindow.isVisible()

__ScriptLibraryWindow = ScriptLibraryWindow(GetQtAEMainWindow())


# ✅ Expose publicly for other modules
ScriptLibraryWindowInstance = __ScriptLibraryWindow