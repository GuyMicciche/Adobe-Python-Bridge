import sys
import os
import json
from pathlib import Path
from PySide6 import QtGui, QtWidgets, QtCore

import _AEPython as _ae
import AEPython as ae

import code_editor
from highlighter.pyHighlight import PythonHighlighter as PyHighlighter

__MainWindow = None
__PythonWindow = None


import json
import os
from PySide6 import QtGui

class Themes:
    def __init__(self, themes_dir: str):
        self.themes_dir = themes_dir
        self._themes = self._load_themes()

    def _load_themes(self):
        json_path = os.path.join(self.themes_dir, "themes.json")
        if not os.path.exists(json_path):
            return {}
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Load QSS content from files
        for theme_id, theme in data.items():
            qss_path = os.path.join(self.themes_dir, theme["qss_file"])
            if os.path.exists(qss_path):
                with open(qss_path, "r", encoding="utf-8") as f:
                    theme["style"] = f.read()
            else:
                theme["style"] = ""
        
        return data

    @classmethod
    def from_default_path(cls):
        #base_dir = os.path.dirname(os.path.abspath(__file__))
        #themes_dir = os.path.join(base_dir, "Themes")

        themes_dir = Path.home() / "Documents" / "AEPython" / "Themes"

        return cls(themes_dir)

    @classmethod
    def get_all_themes(cls, themes_dir: str):
        inst = cls(themes_dir)
        return inst.names()

    def names(self):
        return list(self._themes.keys())

    def get_qss(self, name: str) -> str:
        return self._themes.get(name, {}).get("style", "")

    def get_highlighter_colors(self, name: str) -> dict:
        colors = self._themes.get(name, {}).get("colors", {})
        
        # VS Code defaults as fallback
        defaults = {
            "welcome_border": "#4ec9b0", "welcome_title": "#dcdcaa",
            "welcome_subtitle": "#cccccc", "output_text": "#d4d4d4",
            "code_prefix": "#569cd6", "error_text": "#f48771",
            "success_text": "#608b4e", "keyword_color": "#569cd6",
            "builtin_color": "#dcdcaa", "constant_color": "#4ec9b0",
            "string_color": "#ce9178", "comment_color": "#6a9955",
            "number_color": "#b5cea8", "decorator_color": "#dcdcaa",
            "operator_color": "#d4d4d4", "brace_color": "#ffd700",
            "self_color": "#9cdcfe", "defclass_color": "#dcdcaa",
            "aepython_color": "#4fc1ff", "background": "#1e1e1e",
            "current_line": "#264f78", "line_number": "#858585"
        }
        
        for k, v in defaults.items():
            colors.setdefault(k, v)
        return colors


def __init_qt():
    app = QtWidgets.QApplication.instance()
    if app is not None:
        return
    app = QtWidgets.QApplication(sys.argv)


class CodeEditor(QtWidgets.QPlainTextEdit):
    """Custom code editor with file tracking and smart indentation"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        self.is_modified = False
        self.highlighter = None  # Track highlighter
        
        self.textChanged.connect(self._on_text_changed)
        self.setPlaceholderText("# Write your Python code here...\n# Press Ctrl+Enter to execute\n\nimport AEPython as ae\napp = ae.app\nprint(app.project.file)")
        
        # SET TAB WIDTH (4 spaces worth)
        font = self.font()
        metrics = QtGui.QFontMetrics(font)
        self.setTabStopDistance(metrics.horizontalAdvance(' ') * 8)  # 4 spaces
    
    def _on_text_changed(self):
        self.is_modified = True
    
    def set_file_path(self, path):
        self.file_path = path
        self.is_modified = False
    
    def set_highlighter(self, colors):
        """Re-apply syntax highlighter with new colors"""
        if self.highlighter:
            self.highlighter.setDocument(None)
        self.highlighter = PythonHighlighter(self.document(), colors)
        #self.highlighter = PyHighlighter(self.document())
    
    def mark_saved(self):
        self.is_modified = False
    
    def keyPressEvent(self, event):
        """Handle special key events for smart indentation"""
        cursor = self.textCursor()
        
        # TAB KEY - Indent selected lines or insert tab
        if event.key() == QtCore.Qt.Key.Key_Tab:
            if cursor.hasSelection():
                self._indent_selection(cursor)
                return
            else:
                # Insert tab at cursor
                super().keyPressEvent(event)
                return
        
        # SHIFT+TAB - Dedent selected lines
        elif event.key() == QtCore.Qt.Key.Key_Backtab:  # Shift+Tab
            if cursor.hasSelection():
                self._dedent_selection(cursor)
            else:
                self._dedent_current_line(cursor)
            return
        
        # Default behavior for all other keys
        super().keyPressEvent(event)
    
    def _indent_selection(self, cursor):
        """Indent all selected lines"""
        # Get selection bounds
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        # Move to start of first line
        cursor.setPosition(start)
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)
        
        # Move to end of last line
        end_cursor = QtGui.QTextCursor(cursor)
        end_cursor.setPosition(end)
        end_cursor.movePosition(QtGui.QTextCursor.MoveOperation.EndOfLine)
        
        cursor.beginEditBlock()
        
        # Indent each line
        while cursor.position() < end_cursor.position():
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)
            cursor.insertText("\t")
            
            # Move to next line
            if not cursor.movePosition(QtGui.QTextCursor.MoveOperation.Down):
                break
        
        cursor.endEditBlock()
    
    def _dedent_selection(self, cursor):
        """Dedent all selected lines"""
        # Get selection bounds
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        # Move to start of first line
        cursor.setPosition(start)
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)
        
        # Move to end of last line
        end_cursor = QtGui.QTextCursor(cursor)
        end_cursor.setPosition(end)
        end_cursor.movePosition(QtGui.QTextCursor.MoveOperation.EndOfLine)
        
        cursor.beginEditBlock()
        
        # Dedent each line
        while cursor.position() < end_cursor.position():
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)
            
            # Check if line starts with tab or spaces
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.Right, 
                              QtGui.QTextCursor.MoveMode.KeepAnchor)
            char = cursor.selectedText()
            
            if char == "\t":
                cursor.removeSelectedText()
            elif char == " ":
                # Remove up to 4 spaces
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)
                spaces_removed = 0
                for _ in range(4):
                    cursor.movePosition(QtGui.QTextCursor.MoveOperation.Right, 
                                      QtGui.QTextCursor.MoveMode.KeepAnchor)
                    if cursor.selectedText() == " ":
                        cursor.removeSelectedText()
                        spaces_removed += 1
                    else:
                        cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)
                        break
            
            # Move to next line
            if not cursor.movePosition(QtGui.QTextCursor.MoveOperation.Down):
                break
        
        cursor.endEditBlock()
    
    def _dedent_current_line(self, cursor):
        """Dedent the current line when Shift+Tab pressed without selection"""
        cursor.beginEditBlock()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)
        
        # Check if line starts with tab or spaces
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.Right, 
                          QtGui.QTextCursor.MoveMode.KeepAnchor)
        char = cursor.selectedText()
        
        if char == "\t":
            cursor.removeSelectedText()
        elif char == " ":
            # Remove up to 4 spaces
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)
            for _ in range(4):
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.Right, 
                                  QtGui.QTextCursor.MoveMode.KeepAnchor)
                if cursor.selectedText() == " ":
                    cursor.removeSelectedText()
                else:
                    break
        
        cursor.endEditBlock()


class PythonHighlighter(QtGui.QSyntaxHighlighter):
    """Enhanced Python syntax highlighter with comprehensive keyword support"""
    
    # ✨ COMPREHENSIVE PYTHON KEYWORDS
    keywords = [
        # Control flow
        'if', 'elif', 'else', 'for', 'while', 'break', 'continue', 'pass',
        'return', 'yield', 'raise', 'try', 'except', 'finally', 'with',
        
        # Definitions
        'def', 'class', 'lambda',
        
        # Import
        'import', 'from', 'as',
        
        # Operators
        'and', 'or', 'not', 'in', 'is',
        
        # Variables
        'global', 'nonlocal', 'del',
        
        # Async
        'async', 'await',
        
        # Assertions
        'assert',
    ]
    
    # ✨ BUILT-IN CONSTANTS
    constants = [
        'None', 'True', 'False', 'Ellipsis', 'NotImplemented',
        '__debug__',
    ]
    
    # ✨ BUILT-IN FUNCTIONS (commonly used)
    builtins = [
        # Type conversions
        'int', 'float', 'str', 'bool', 'list', 'tuple', 'dict', 'set',
        'frozenset', 'bytes', 'bytearray', 'complex',
        
        # I/O
        'print', 'input', 'open',
        
        # Iteration
        'range', 'enumerate', 'zip', 'map', 'filter', 'reversed', 'sorted',
        
        # Object inspection
        'len', 'type', 'isinstance', 'issubclass', 'hasattr', 'getattr',
        'setattr', 'delattr', 'dir', 'vars', 'id', 'hash',
        
        # Math
        'abs', 'min', 'max', 'sum', 'round', 'pow', 'divmod',
        
        # Functional
        'all', 'any', 'callable', 'eval', 'exec', 'compile',
        
        # Misc
        'help', 'super', 'property', 'staticmethod', 'classmethod',
        'iter', 'next', 'slice', 'format', 'chr', 'ord', 'hex', 'oct', 'bin',
    ]
    
    # ✨ AEPYTHON-SPECIFIC KEYWORDS
    aepython_keywords = [
        'ae', '_ae', 'app', 'project', 'comp', 'layer', 'property',
        'keyframe', 'effect', 'footage', 'item', 'render',
    ]
    
    # ✨ COMMON DECORATORS
    decorators = [
        'property', 'staticmethod', 'classmethod', 'abstractmethod',
        'dataclass', 'lru_cache', 'wraps', 'total_ordering',
    ]
    
    # Operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        r'\+', '-', r'\*', '/', '//', r'\%', r'\*\*',
        # In-place
        r'\+=', '-=', r'\*=', '/=', r'\%=', r'//=', r'\*\*=',
        # Bitwise
        r'\^', r'\|', r'\&', r'\~', '>>', '<<',
        # Logical
        '->',  # Type hints
    ]
    
    # Braces
    braces = [
        r'\{', r'\}', r'\(', r'\)', r'\[', r'\]',
    ]
    
    def __init__(self, document, theme_colors):
        super().__init__(document)
        
        
        function_name_color = QtGui.QColor(theme_colors.get("welcome_border", "#DCDCAA"))  # Yellow - function names
        class_name_color = QtGui.QColor("#4EC9B0")     # Cyan - class names  
        uppercase_color = QtGui.QColor("#4FC1FF")      # Light blue - CONSTANTS

        # Theme colors
        keyword_color = QtGui.QColor(theme_colors.get("code_prefix", "#569CD6"))
        builtin_color = QtGui.QColor(theme_colors.get("welcome_border", "#DCDCAA"))
        constant_color = QtGui.QColor("#4EC9B0")
        string_color = QtGui.QColor("#CE9178")
        comment_color = QtGui.QColor(theme_colors.get("success_text", "#6A9955"))
        number_color = QtGui.QColor("#B5CEA8")
        decorator_color = QtGui.QColor("#DCDCAA")
        operator_color = QtGui.QColor("#D4D4D4")
        brace_color = QtGui.QColor("#FFD700")
        self_color = QtGui.QColor("#9CDCFE")
        defclass_color = QtGui.QColor(theme_colors.get("welcome_title", "#DCDCAA"))
        aepython_color = QtGui.QColor("#4FC1FF")  # Special color for AEPython
        
        self._rules = []
        
        def add_rule(pattern, color, italic=False, bold=False):
            fmt = QtGui.QTextCharFormat()
            fmt.setForeground(color)
            if italic:
                fmt.setFontItalic(True)
            if bold:
                fmt.setFontWeight(QtGui.QFont.Weight.Bold)
            self._rules.append((QtCore.QRegularExpression(pattern), fmt))
        
        # ✨ KEYWORDS (bold)
        add_rule(r'\b(' + '|'.join(self.keywords) + r')\b', keyword_color, bold=True)
        
        # ✨ CONSTANTS (bold)
        add_rule(r'\b(' + '|'.join(self.constants) + r')\b', constant_color, bold=True)
        
        # ✨ BUILT-INS
        add_rule(r'\b(' + '|'.join(self.builtins) + r')\b', builtin_color)
        
        # ✨ AEPYTHON-SPECIFIC
        add_rule(r'\b(' + '|'.join(self.aepython_keywords) + r')\b', aepython_color, bold=True)
        
        # ✨ DECORATORS (@decorator)
        add_rule(r'@\w+', decorator_color, bold=True)
        
        # ✨ SELF
        add_rule(r'\bself\b', self_color, italic=True)
        
        # ✨ CLS
        add_rule(r'\bcls\b', self_color, italic=True)
        
        # ✨ DEF/CLASS NAMES
        # Function names (after def, before parenthesis)
        add_rule(r'(?<=def\s)\w+', defclass_color, bold=True)
        # Class names (after class, before colon/parenthesis)
        add_rule(r'(?<=class\s)\w+', defclass_color, bold=True)
                
        # ✨ UPPERCASE CONSTANTS/VARIABLES
        uppercase_color = QtGui.QColor("#4EC9B0")  # Teal/cyan for constants
        add_rule(r'\b[A-Z][A-Z0-9_]+\b', uppercase_color, bold=True)
        
        # ✨ OPERATORS
        for op in self.operators:
            add_rule(op, operator_color)
        
        # ✨ BRACES
        for brace in self.braces:
            add_rule(brace, brace_color)
        
        # ✨ NUMBERS (comprehensive)
        add_rule(r'\b[+-]?[0-9]+[lL]?\b', number_color)  # Integers
        add_rule(r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', number_color)  # Hex
        add_rule(r'\b[+-]?0[oO][0-7]+[lL]?\b', number_color)  # Octal
        add_rule(r'\b[+-]?0[bB][01]+[lL]?\b', number_color)  # Binary
        add_rule(r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', number_color)  # Floats
        
        # ✨ F-STRINGS
        add_rule(r'f["\'].*?["\']', string_color)
        add_rule(r'f""".*?"""', string_color)
        add_rule(r"f'''.*?'''", string_color)
        
        # ✨ RAW STRINGS
        add_rule(r'r["\'].*?["\']', string_color)
        
        # ✨ REGULAR STRINGS (but NOT triple quotes)
        add_rule(r'""".*?"""', string_color)  # Triple double on single line
        add_rule(r"'''.*?'''", string_color)  # Triple single on single line
        add_rule(r'"[^"\\]*(\\.[^"\\]*)*"', string_color)  # Regular double quotes
        add_rule(r"'[^'\\]*(\\.[^'\\]*)*'", string_color)  # Regular single quotes
        
        # ✨ COMMENTS (must come last to override)
        add_rule(r'#[^\n]*', comment_color, italic=True)
        
        # Triple-quoted strings (multi-line)
        self._triple_format = QtGui.QTextCharFormat()
        self._triple_format.setForeground(string_color)
        self._triple_single = QtCore.QRegularExpression(r"'''")
        self._triple_double = QtCore.QRegularExpression(r'"""')
    
    def _highlight_triple(self, text, expr, state_id):
        """Highlight multi-line triple-quoted strings"""
        start = 0
        
        if self.previousBlockState() == state_id:
            m = expr.match(text, 0)
            if m.hasMatch():
                end = m.capturedStart()
                length = end + 3
                self.setFormat(0, length, self._triple_format)
                self.setCurrentBlockState(0)
                m2 = expr.match(text, end + 3)
                if m2.hasMatch():
                    start = m2.capturedStart()
                else:
                    return False
            else:
                self.setFormat(0, len(text), self._triple_format)
                self.setCurrentBlockState(state_id)
                return True
        else:
            m = expr.match(text)
            if not m.hasMatch():
                return False
            start = m.capturedStart()
        
        while start >= 0:
            m = expr.match(text, start + 3)
            if m.hasMatch():
                end = m.capturedStart()
                length = (end + 3) - start
                self.setFormat(start, length, self._triple_format)
                m2 = expr.match(text, end + 3)
                if m2.hasMatch():
                    start = m2.capturedStart()
                else:
                    start = -1
            else:
                self.setFormat(start, len(text) - start, self._triple_format)
                self.setCurrentBlockState(state_id)
                return True
        
        return False
    
    def highlightBlock(self, text: str):
        """Apply syntax highlighting to the given block of text"""
        self.setCurrentBlockState(0)
        
        prev_state = self.previousBlockState()
        
        # Handle continuation of ''' blocks
        if prev_state == 1:
            if self._highlight_triple(text, self._triple_single, 1):
                return
        # Handle continuation of """ blocks
        elif prev_state == 2:
            if self._highlight_triple(text, self._triple_double, 2):
                return
        
        # Check for new triple-quoted strings
        if self._highlight_triple(text, self._triple_single, 1):
            return
        
        if self._highlight_triple(text, self._triple_double, 2):
            return
        
        # Apply normal single-line rules
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class DotSplitterHandle(QtWidgets.QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Transparent background
        painter.fillRect(self.rect(), QtCore.Qt.GlobalColor.transparent)

        color = QtGui.QColor(130, 130, 130)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(color)

        w = self.width()
        h = self.height()
        dot_diam = 2
        r = dot_diam / 2.0

        if self.orientation() == QtCore.Qt.Orientation.Vertical:
            # Vertical splitter → top/bottom → horizontal handle
            # Dots go LEFT→RIGHT in middle third of width
            start_x = w / 3.0
            end_x   = 2 * w / 3.0
            spacing = 5.0

            y = h / 2.0
            x = start_x
            while x <= end_x:
                painter.drawEllipse(QtCore.QPointF(x, y), r, r)
                x += spacing
        else:
            # Horizontal splitter → left/right → vertical handle
            # Dots go TOP→BOTTOM in middle third of height
            start_y = h / 3.0
            end_y   = 2 * h / 3.0
            spacing = 5.0

            x = w / 2.0
            y = start_y
            while y <= end_y:
                painter.drawEllipse(QtCore.QPointF(x, y), r, r)
                y += spacing


class DotSplitter(QtWidgets.QSplitter):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setHandleWidth(24)

    def createHandle(self):
        return DotSplitterHandle(self.orientation(), self)


class PythonWindow(QtWidgets.QMainWindow):
    STATE_FILE = Path.home() / "Documents" / "AEPython" / ".aepython_state.json"
    
    class Logger:
        def __init__(self, editor: QtWidgets.QTextEdit, color=None, show=None):
            self.editor = editor
            self.color = editor.textColor() if color is None else color
            self.show = show
        
        def write(self, message: str):
            self.editor.moveCursor(QtGui.QTextCursor.MoveOperation.End)
            self.editor.setTextColor(self.color)
            self.editor.insertPlainText(message)
            if self.show is not None:
                self.show()
        
        def flush(self):
            pass
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._exec_namespace = {
            '__name__': '__main__',
            '__builtins__': __builtins__,
            'ae': ae,  # AEPython access
            '_ae': _ae  # Internal AEPython
        }
        
        self.user_docs_dir = Path.home() / "Documents"
    
        self.setWindowTitle('AE Python Console')
        self.resize(900, 700)
        self.setAcceptDrops(True)
        
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, False)
        
        # SET WINDOW ICON
        # Option 1: Use a .ico or .png file
        icon_path = Path(__file__).parent / "icon.png"  # or "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))
        else:
            # Option 2: Create a simple colored icon programmatically
            pixmap = QtGui.QPixmap(64, 64)
            pixmap.fill(QtGui.QColor(14, 99, 156))  # Blue color
            painter = QtGui.QPainter(pixmap)
            painter.setPen(QtGui.QColor(255, 255, 255))
            painter.setFont(QtGui.QFont("Arial", 32, QtGui.QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "Py")
            painter.end()
            self.setWindowIcon(QtGui.QIcon(pixmap))
        
        # Current theme
        self.current_theme_key = "vscode_dark"
        themes_dir = Path.home() / "Documents" / "AEPython" / "themes" 
        self.themes = Themes(str(themes_dir))  # Now self.themes is a dict-accessible 
        
        # Central widget with margins
        self.centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralWidget)
        
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        self.centralWidget.setLayout(main_layout)
        
        # CREATE SPLITTER for resizable sections
        splitter = DotSplitter(QtCore.Qt.Orientation.Vertical)
        
        # TOP SECTION - Output
        output_widget = QtWidgets.QWidget()
        output_layout = QtWidgets.QVBoxLayout()
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(8)
        output_widget.setLayout(output_layout)
        
        label_output = QtWidgets.QLabel("OUTPUT")
        output_layout.addWidget(label_output)
        
        self.textedit_output = QtWidgets.QTextEdit()
        self.textedit_output.setReadOnly(True)
        self.textedit_output.setMinimumHeight(150)
        output_layout.addWidget(self.textedit_output)
        
        # BOTTOM SECTION - Code with tabs
        code_widget = QtWidgets.QWidget()
        code_layout = QtWidgets.QVBoxLayout()
        code_layout.setContentsMargins(0, 0, 0, 0)
        code_layout.setSpacing(8)
        code_widget.setLayout(code_layout)
        
        label_code = QtWidgets.QLabel("PYTHON CODE")
        code_layout.addWidget(label_code)
        
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.setMinimumHeight(200)
        code_layout.addWidget(self.tab_widget)
        
        # Add widgets to splitter
        splitter.addWidget(output_widget)
        splitter.addWidget(code_widget)
        
        # Set initial splitter sizes (40% output, 60% code)
        splitter.setSizes([280, 420])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Add initial tab
        self._add_new_tab()
        
        # Button row (stays at bottom, not in splitter)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.button_new_tab = QtWidgets.QPushButton("+ New Tab")
        self.button_new_tab.clicked.connect(self._add_new_tab)
        #self.button_new_tab.setStyleSheet("background-color: #3c3c3c;")
        button_layout.addWidget(self.button_new_tab)
        
        self.button_clear = QtWidgets.QPushButton("Clear Output")
        self.button_clear.clicked.connect(self._clear_output)
        #self.button_clear.setStyleSheet("background-color: #3c3c3c;")
        button_layout.addWidget(self.button_clear)
        
        button_layout.addStretch()
        
        self.button_execute = QtWidgets.QPushButton("▶ Execute Code")
        self.button_execute.setObjectName("executeButton")  # For #executeButton selector
        self.button_execute.clicked.connect(self._execute)
        button_layout.addWidget(self.button_execute)
        
        main_layout.addLayout(button_layout)
        
        # Setup menu bar
        self._setup_menu_bar()
        
        # Install event filter for all tabs
        self.tab_widget.installEventFilter(self)
        
        # Redirect stdout/stderr
        self._setup_loggers()
        
        # Restore previous session (includes theme)
        self._restore_state()
        
        # Apply theme
        self._apply_theme(self.current_theme_key)
        
        # Welcome message
        self._print_welcome()
    
    def exit_app(self):
        """Close the entire window/app."""
        self.close()
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.quit()
            
    def closeEvent(self, event):
        """Save state when closing"""
        self._save_state()
        #event.accept() # Actually close
        event.ignore()  # Don't actually close
        self.hide()     # Just hide instead

    def dragEnterEvent(self, event):
        """Accept drag events with .py files"""
        if event.mimeData().hasUrls():
            # Check if any URL is a .py file
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith('.py'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        """Open dropped .py files in new tabs"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.py'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if file with same NAME is already open (not full path)
                    new_filename = Path(file_path).name
                    already_open = False
                    for i in range(self.tab_widget.count()):
                        editor = self.tab_widget.widget(i)
                        if editor.file_path:
                            existing_filename = Path(editor.file_path).name
                            if existing_filename == new_filename:
                                self.tab_widget.setCurrentIndex(i)
                                already_open = True
                                break
                    
                    # Open in new tab if not already open
                    if not already_open:
                        self._add_new_tab(file_path, content)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")
        
        event.acceptProposedAction()

    def _setup_loggers(self):
        """Setup stdout/stderr loggers with current theme colors"""
        colors = self.themes.get_highlighter_colors(self.current_theme_key)

        sys.stdout = self.Logger(
            self.textedit_output,
            QtGui.QColor(colors["output_text"])
        )
        sys.stderr = self.Logger(
            self.textedit_output,
            QtGui.QColor(colors["error_text"]),
            self.show
        )
    
    def _setup_menu_bar(self):
        # File menu
        file_menu = self.menuBar().addMenu("File")
        
        new_action = QtGui.QAction("New Tab", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._add_new_tab)
        
        open_action = QtGui.QAction("Open File...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)

        # ADD THESE 3 LINES ↓
        close_tab_action = QtGui.QAction("Close Tab", self)
        close_tab_action.setShortcut("Ctrl+W")
        close_tab_action.triggered.connect(lambda: self._close_tab(self.tab_widget.currentIndex()))
        
        save_action = QtGui.QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_file)
        
        save_as_action = QtGui.QAction("Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_file_as)
        
        exec_file_action = QtGui.QAction("Execute Python File...", self)
        exec_file_action.setShortcut("Ctrl+Shift+O")
        exec_file_action.triggered.connect(self._execute_file)

        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.exit_app)
        
        file_menu.addAction(new_action)
        file_menu.addSeparator()
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(close_tab_action)
        file_menu.addSeparator()
        file_menu.addAction(exec_file_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = self.menuBar().addMenu("Edit")
        
        clear_action = QtGui.QAction("Clear Output", self)
        clear_action.setShortcut("Ctrl+L")
        clear_action.triggered.connect(self._clear_output)
        
        edit_menu.addAction(clear_action)
        
        # View menu (Themes)
        view_menu = self.menuBar().addMenu("View")
        
        # Create theme submenu
        theme_menu = view_menu.addMenu("Theme")
        self.theme_actions = {}  # Store actions for checkbox management
        
        # Window menu
        window_menu = self.menuBar().addMenu("Window")
        
        # Window menu → Script Library
        scriptlib_action = QtGui.QAction("📚 Script Library", self)
        scriptlib_action.triggered.connect(lambda: exec('import script_library;script_library.ShowScriptLibrary()'))
        '''
        scriptlib_action.triggered.connect(lambda: _ae.executeScript("""
            // Execute Python: import script_library; script_library.ShowScriptLibrary()
            __AEPython_executeScript("import script_library; script_library.ShowScriptLibrary()");
        """))
        '''

        window_menu.addAction(scriptlib_action)
        
        # Add theme actions
        for theme_key, theme_data in self.themes._themes.items():
            action = QtGui.QAction(theme_data["name"], self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, key=theme_key: self._on_theme_menu_selected(key))
            theme_menu.addAction(action)
            self.theme_actions[theme_key] = action
    
    def _change_theme(self, theme_key):
        """Change the UI theme"""
        self.current_theme_key = theme_key
        self._apply_theme(theme_key)
        self._setup_loggers()  # Update logger colors
        
        # Refresh welcome message with new colors
        if self.textedit_output.toPlainText():
            self._clear_output()  # Forces reprint with new colors
    
    def _apply_theme(self, theme_key):
        """Apply a theme to the application"""
        qss = self.themes.get_qss(theme_key)
        colors = self.themes.get_highlighter_colors(theme_key)

        app = QtWidgets.QApplication.instance()
        app.setStyleSheet(qss)
                
        # REFRESH ALL code editors + highlighters
        self._refresh_all_editors(colors)
        
        # Update loggers
        self._setup_loggers()

        self._update_theme_menu_checkboxes()

    def _update_theme_menu_checkboxes(self):
        """Update theme menu checkboxes (only current theme checked)"""
        for theme_key, action in self.theme_actions.items():
            action.setChecked(theme_key == self.current_theme_key)

    def _on_theme_menu_selected(self, theme_key):
        """Handle theme selection from menu - refreshes ScriptLibrary too"""
        sender_action = self.theme_actions[theme_key]
        
        # If unchecked (clicking already-checked), do nothing
        if not sender_action.isChecked():
            sender_action.setChecked(True)
            return
        
        # Change theme normally
        self._change_theme(theme_key)
        
        try:
            import script_library
            if(script_library.IsScriptLibraryVisible()):
                script_library.ToggleScriptLibrary()
                script_library.ShowScriptLibrary()
        except:
            pass  # Library not loaded yet
        
    def _refresh_all_editors(self, colors):
        """Re-apply syntax highlighting to ALL tabs"""
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if isinstance(editor, code_editor.CodeEditor):
                # Remove old highlighter
                old_highlighter = editor.document().findChild(QtGui.QSyntaxHighlighter)
                if old_highlighter:
                    old_highlighter.setDocument(None)
                
                # Add new highlighter with current colors
                editor.highlighter = PythonHighlighter(editor.document(), colors)
                #editor.highlighter = PyHighlighter(editor.document())

                # Force stylesheet refresh
                editor.setStyleSheet("")  # Clear
                app = QtWidgets.QApplication.instance()
                app.processEvents()      # Update immediately
    
    
    def _add_new_tab(self, file_path=None, content=""):
        # If opening a file, check if same filename is already open
        if file_path:
            new_filename = Path(file_path).name
            for i in range(self.tab_widget.count()):
                existing_editor = self.tab_widget.widget(i)
                if existing_editor.file_path:
                    existing_filename = Path(existing_editor.file_path).name
                    if existing_filename == new_filename:
                        self.tab_widget.setCurrentIndex(i)
                        return existing_editor  # Return existing editor instead of creating new
        
        editor = code_editor.CodeEditor()
        editor.installEventFilter(self)
        
        if content:
            editor.setPlainText(content)
        
        if file_path:
            editor.set_file_path(file_path)
            tab_name = Path(file_path).name
        else:
            # Find first missing number in Untitled-# sequence
            existing_numbers = set()
            for i in range(self.tab_widget.count()):
                existing_editor = self.tab_widget.widget(i)
                if existing_editor.file_path is None:
                    # Extract number from "Untitled-#" or "● Untitled-#"
                    title = self.tab_widget.tabText(i).replace("● ", "")
                    if title.startswith("Untitled-"):
                        try:
                            num = int(title.split("-")[1])
                            existing_numbers.add(num)
                        except (IndexError, ValueError):
                            pass
            
            # Find first missing number starting from 1
            untitled_number = 1
            while untitled_number in existing_numbers:
                untitled_number += 1
            
            tab_name = f"Untitled-{untitled_number}"
        
        # NEW: attach syntax highlighter using current theme colors
        colors = self.themes.get_highlighter_colors(self.current_theme_key)

        PythonHighlighter(editor.document(), colors)
        #PyHighlighter(editor.document())

        index = self.tab_widget.addTab(editor, tab_name)
        self.tab_widget.setCurrentIndex(index)
        self._update_tab_title(index)
        
        return editor
    
    def _close_tab(self, index: int) -> bool:
        """Close tab at index with unsaved-changes check.
           Returns True if the tab was closed, False if cancelled."""
        editor = self.tab_widget.widget(index)
        if editor is None:
            return True

        doc = editor.document()
        if doc.isModified():
            reply = QtWidgets.QMessageBox.question(
                self,
                "Unsaved Changes",
                "This tab has unsaved changes. Save before closing?",
                QtWidgets.QMessageBox.StandardButton.Save |
                QtWidgets.QMessageBox.StandardButton.Discard |
                QtWidgets.QMessageBox.StandardButton.Cancel,
                QtWidgets.QMessageBox.StandardButton.Save,
            )

            if reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                return False

            if reply == QtWidgets.QMessageBox.StandardButton.Save:
                if not self._save_file():   # or per-tab save helper
                    return False

        # At this point either not modified, or save/discard chosen
        self.tab_widget.removeTab(index)
        
        # ✅ ALWAYS KEEP ONE TAB: If we just closed the last tab, create a new empty one
        if self.tab_widget.count() == 0:
            self._add_new_tab()
        
        return True
    
    def _update_tab_title(self, index):
        editor = self.tab_widget.widget(index)
        if editor.file_path:
            title = Path(editor.file_path).name
        else:
            # Keep existing Untitled-# (don't recalculate)
            title = self.tab_widget.tabText(index).replace("● ", "")
        
        if editor.is_modified:
            title = "● " + title
        
        self.tab_widget.setTabText(index, title)
    
    def _get_current_editor(self):
        return self.tab_widget.currentWidget()
    
    def _open_file(self):
        default_dir = self.user_docs_dir / "AEPython" / "Scripts"
        os.makedirs(default_dir, exist_ok=True)
        
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open Python File",
            str(default_dir),
            "Python Files (*.py);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file with same NAME is already open (not full path)
            new_filename = Path(file_path).name
            for i in range(self.tab_widget.count()):
                editor = self.tab_widget.widget(i)
                if editor.file_path:
                    existing_filename = Path(editor.file_path).name
                    if existing_filename == new_filename:
                        self.tab_widget.setCurrentIndex(i)
                        return
            
            # Open in new tab
            self._add_new_tab(file_path, content)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")
        
    def _save_file(self):
        editor = self._get_current_editor()
        
        if not editor.file_path:
            return self._save_file_as()
        
        try:
            with open(editor.file_path, 'w', encoding='utf-8') as f:
                f.write(editor.toPlainText())
            
            editor.mark_saved()
            self._update_tab_title(self.tab_widget.currentIndex())
            
            colors = self.themes.get_highlighter_colors(self.current_theme_key)
            self.textedit_output.setTextColor(QtGui.QColor(colors["success_text"]))
            self.textedit_output.append(f"\n✓ Saved: {editor.file_path}")
            self.textedit_output.setTextColor(QtGui.QColor(colors["output_text"]))
            return True
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")
            return False
    
    def _save_file_as(self):
        editor = self._get_current_editor()

        # Default to Documents/AEPython/Scripts
        default_dir = self.user_docs_dir / "AEPython" / "Scripts"
        os.makedirs(default_dir, exist_ok=True)

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Python File",
            str(default_dir),  # <- default directory for first save
            "Python Files (*.py);;All Files (*.*)"
        )

        if not file_path:
            return False

        editor.set_file_path(file_path)
        return self._save_file()

    
    def _save_state(self):
        """Save current tabs and their states"""
        state = {
            "tabs": [],
            "current_index": self.tab_widget.currentIndex(),
            "theme": self.current_theme_key
        }
        
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            tab_state = {
                "file_path": editor.file_path,
                "content": editor.toPlainText() if not editor.file_path else None
            }
            state["tabs"].append(tab_state)
        
        try:
            with open(self.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Failed to save state: {e}", file=sys.stderr)
    
    def _restore_state(self):
        """Restore previous session tabs"""
        if not self.STATE_FILE.exists():
            return
        
        try:
            with open(self.STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Restore theme
            self.current_theme_key = state.get("theme", "vscode_dark")
            
            # Remove initial empty tab if we're restoring tabs
            if state.get("tabs") and self.tab_widget.count() == 1:
                editor = self.tab_widget.widget(0)
                if not editor.toPlainText() and not editor.file_path:
                    self.tab_widget.removeTab(0)
            
            for tab_state in state.get("tabs", []):
                file_path = tab_state.get("file_path")
                content = tab_state.get("content", "")
                
                if file_path and Path(file_path).exists():
                    # Load from file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self._add_new_tab(file_path, content)
                elif file_path is None:  # Changed: Restore untitled tabs even if empty
                    # Restore unsaved content (even if empty)
                    self._add_new_tab(None, content)
            
            # Restore active tab
            current_index = state.get("current_index", 0)
            if 0 <= current_index < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(current_index)
        
        except Exception as e:
            print(f"Failed to restore state: {e}", file=sys.stderr)
    
    def _print_welcome(self):
        colors = self.themes.get_highlighter_colors(self.current_theme_key)

        is_system_default = self.current_theme_key == "system_default"
        
        palette = self.textedit_output.palette()
        self.textedit_output.setTextColor(palette.color(QtGui.QPalette.ColorRole.WindowText))
        
        if not is_system_default:
            self.textedit_output.setTextColor(QtGui.QColor(colors["welcome_border"]))
        self.textedit_output.append("=" * 60)
        if not is_system_default:
            self.textedit_output.setTextColor(QtGui.QColor(colors["welcome_title"]))
        self.textedit_output.append("  🧪 AE Python Console v1.0.0")
        if not is_system_default:
            self.textedit_output.setTextColor(QtGui.QColor(colors["welcome_subtitle"]))
        self.textedit_output.append("  Python ↔ ExtendScript Bridge for After Effects")
        if not is_system_default:
            self.textedit_output.setTextColor(QtGui.QColor(colors["welcome_border"]))
        self.textedit_output.append("=" * 60)
        if not is_system_default:
            self.textedit_output.setTextColor(QtGui.QColor(colors["output_text"]))
        self.textedit_output.append("")
    
    def _clear_output(self):
        self.textedit_output.clear()
        self._print_welcome()
    
    def eventFilter(self, obj, event):
        # Ctrl+Enter to execute
        if isinstance(obj, code_editor.CodeEditor) and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() == QtCore.Qt.Key.Key_Return and event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
                self._execute()
                return True
            # Update tab title on text change
            elif event.type() == QtCore.QEvent.Type.KeyPress:
                QtCore.QTimer.singleShot(0, lambda: self._update_tab_title(self.tab_widget.currentIndex()))
        
        return super().eventFilter(obj, event)
    
    def _execute(self):
        editor = self._get_current_editor()
        code = editor.toPlainText()
        
        if not code.strip():
            return
        
        colors = self.themes.get_highlighter_colors(self.current_theme_key)
        
        # Print the executed code with >>> prefix
        self.textedit_output.setTextColor(QtGui.QColor(colors["code_prefix"]))
        self.textedit_output.append(f">>>")
        for line in code.split('\n'):
            self.textedit_output.append(f"{line}")
        self.textedit_output.append("")
        self.textedit_output.setTextColor(QtGui.QColor(colors["output_text"]))
        
        # CRITICAL: Force stdout/stderr redirection before each execution
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        try:
            # Re-redirect stdout/stderr to ensure capture
            sys.stdout = self.Logger(
                self.textedit_output,
                QtGui.QColor(colors["output_text"])
            )
            sys.stderr = self.Logger(
                self.textedit_output,
                QtGui.QColor(colors["error_text"]),
                self.show
            )
            
            # Set __file__ if editor has a file path
            if editor.file_path:
                self._exec_namespace['__file__'] = editor.file_path
            elif '__file__' in self._exec_namespace:
                del self._exec_namespace['__file__']
            
            exec(code, self._exec_namespace)
            
        except Exception as e:
            import traceback
            self.textedit_output.setTextColor(QtGui.QColor(colors["error_text"]))
            self.textedit_output.append("\nError:")
            traceback.print_exc()
            self.textedit_output.setTextColor(QtGui.QColor(colors["output_text"]))
        finally:
            # Don't restore old stdout/stderr - keep using our loggers
            pass
    
    def _execute_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Execute Python File",
            "",
            "Python Files (*.py)"
        )
        
        if not file_path:
            return
        
        colors = self.themes.get_highlighter_colors(self.current_theme_key)
        
        self.textedit_output.setTextColor(QtGui.QColor(colors["code_prefix"]))
        self.textedit_output.append(f"\n>>> Executing: {file_path}")
        self.textedit_output.setTextColor(QtGui.QColor(colors["output_text"]))
        
        dont_write_bytecode = sys.dont_write_bytecode
        module_dir = os.path.dirname(file_path)
        sys.path.insert(0, module_dir)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        
            # Fresh namespace for file execution
            exec_namespace = {
                '__file__': file_path,
                '__name__': '__main__',
                '__builtins__': __builtins__,
            }
            
            exec(compile(code, file_path, 'exec'), exec_namespace)
            
            '''
            # OLD METHOD
            import importlib.util
            spec = importlib.util.spec_from_file_location(file_path, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.dont_write_bytecode = True
            spec.loader.exec_module(module)
            '''
        except:
            import traceback
            traceback.print_exc()
        finally:
            sys.dont_write_bytecode = dont_write_bytecode
            if module_dir in sys.path:
                sys.path.remove(module_dir)


def GetQtAEMainWindow():
    global __MainWindow
    if __MainWindow is None:
        import win32gui
        __MainWindow = QtWidgets.QWidget()
        win32gui.SetParent(int(__MainWindow.winId()), _ae.getMainHWND())
    return __MainWindow


def ShowPythonWindow():
    __PythonWindow.show()
    __PythonWindow.raise_()
    __PythonWindow.activateWindow()


# ADD THESE TWO FUNCTIONS:
def TogglePythonWindow():
    """Toggle the Python window visibility"""
    global __PythonWindow
    if __PythonWindow is None or not __PythonWindow.isVisible():
        ShowPythonWindow()
    else:
        __PythonWindow.hide()

def IsPythonWindowVisible():
    """Check if the Python window is visible"""
    global __PythonWindow
    if __PythonWindow is None:
        return False
    return __PythonWindow.isVisible()

__init_qt()
__PythonWindow = PythonWindow(GetQtAEMainWindow())


# ✅ Expose publicly for other modules
PythonWindowInstance = __PythonWindow