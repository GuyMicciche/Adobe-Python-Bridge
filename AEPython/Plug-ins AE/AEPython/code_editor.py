from PySide6 import QtCore, QtGui, QtWidgets

DARK_BLUE = QtGui.QColor(118, 150, 185)


class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self._code_editor = editor

    def sizeHint(self):
        return QtCore.QSize(self._code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._code_editor.lineNumberAreaPaintEvent(event)


class BaseCodeTextEdit(QtWidgets.QPlainTextEdit):
    """Base editor with line numbers, current-line highlight, and indent helpers."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Line numbers
        self.line_number_area = LineNumberArea(self)

        # Monospace font
        font = QtGui.QFont()
        font.setFamily("Consolas")
        font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
        font.setPointSize(10)
        self.setFont(font)

        # Tabs = 4 spaces
        tab_size = 4
        self.setTabStopDistance(tab_size * self.fontMetrics().horizontalAdvance(' '))

        # Signals
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    # ----- Line-number support -----

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 30 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def resizeEvent(self, e):
        super().resizeEvent(e)
        cr = self.contentsRect()
        width = self.line_number_area_width()
        rect = QtCore.QRect(cr.left(), cr.top(), width, cr.height())
        self.line_number_area.setGeometry(rect)

    def lineNumberAreaPaintEvent(self, event):
        painter = QtGui.QPainter(self.line_number_area)
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.contentOffset()
        top = self.blockBoundingGeometry(block).translated(offset).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(DARK_BLUE)
                width = self.line_number_area.width() - 10
                height = self.fontMetrics().height()
                painter.drawText(0, int(top), width, height,
                                 QtCore.Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def update_line_number_area_width(self, _new_block_count):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            width = self.line_number_area.width()
            self.line_number_area.update(0, rect.y(), width, rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            line_color = DARK_BLUE.lighter(160)
            line_color.setAlphaF(0.1)   # 10% opacity (0.0–1.0)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QtGui.QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)


class CodeEditor(BaseCodeTextEdit):
    """Custom code editor with file tracking, syntax highlighting, and smart indentation."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.file_path = None
        self.is_modified = False
        self.highlighter = None  # Track highlighter

        self.textChanged.connect(self._on_text_changed)
        self.setPlaceholderText(
            "# Write your Python code here...\n"
            "# Press Ctrl+Enter to execute\n\n"
            "import AEPython as ae\n"
            "app = ae.app\n"
            "print(app.project.file)"
        )

        # Recompute tab width using current font
        font = self.font()
        metrics = QtGui.QFontMetrics(font)
        self.setTabStopDistance(metrics.horizontalAdvance(' ') * 4)

    # ----- File / state -----

    def _on_text_changed(self):
        self.is_modified = True

    def set_file_path(self, path):
        self.file_path = path
        self.is_modified = False

    def set_highlighter(self, colors):
        """Re-apply syntax highlighter with new colors."""
        if self.highlighter:
            self.highlighter.setDocument(None)
        # PythonHighlighter is assumed to be your QSyntaxHighlighter subclass
        self.highlighter = PythonHighlighter(self.document(), colors)

    def mark_saved(self):
        self.is_modified = False

    # ----- Smart indentation -----

    def keyPressEvent(self, event):
        """Handle special key events for smart indentation."""
        cursor = self.textCursor()

        if event.key() == QtCore.Qt.Key.Key_Tab:
            if cursor.hasSelection():
                self._indent_selection(cursor)
                return
            else:
                super().keyPressEvent(event)
                return

        elif event.key() == QtCore.Qt.Key.Key_Backtab:  # Shift+Tab
            if cursor.hasSelection():
                self._dedent_selection(cursor)
            else:
                self._dedent_current_line(cursor)
            return

        super().keyPressEvent(event)

    def _indent_selection(self, cursor):
        """Indent all selected lines."""
        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        cursor.setPosition(start)
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)

        end_cursor = QtGui.QTextCursor(cursor)
        end_cursor.setPosition(end)
        end_cursor.movePosition(QtGui.QTextCursor.MoveOperation.EndOfLine)

        cursor.beginEditBlock()

        while cursor.position() <= end_cursor.position():
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)
            cursor.insertText("\t")
            if not cursor.movePosition(QtGui.QTextCursor.MoveOperation.Down):
                break

        cursor.endEditBlock()

    def _dedent_selection(self, cursor):
        """Dedent all selected lines."""
        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        cursor.setPosition(start)
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)

        end_cursor = QtGui.QTextCursor(cursor)
        end_cursor.setPosition(end)
        end_cursor.movePosition(QtGui.QTextCursor.MoveOperation.EndOfLine)

        cursor.beginEditBlock()

        while cursor.position() <= end_cursor.position():
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)

            # Check first char
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.Right,
                                QtGui.QTextCursor.MoveMode.KeepAnchor)
            char = cursor.selectedText()

            if char == "\t":
                cursor.removeSelectedText()
            elif char == " ":
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)
                for _ in range(4):
                    cursor.movePosition(QtGui.QTextCursor.MoveOperation.Right,
                                        QtGui.QTextCursor.MoveMode.KeepAnchor)
                    if cursor.selectedText() == " ":
                        cursor.removeSelectedText()
                    else:
                        break

            if not cursor.movePosition(QtGui.QTextCursor.MoveOperation.Down):
                break

        cursor.endEditBlock()

    def _dedent_current_line(self, cursor):
        """Dedent the current line when Shift+Tab is pressed without selection."""
        cursor.beginEditBlock()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)

        cursor.movePosition(QtGui.QTextCursor.MoveOperation.Right,
                            QtGui.QTextCursor.MoveMode.KeepAnchor)
        char = cursor.selectedText()

        if char == "\t":
            cursor.removeSelectedText()
        elif char == " ":
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)
            for _ in range(4):
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.Right,
                                    QtGui.QTextCursor.MoveMode.KeepAnchor)
                if cursor.selectedText() == " ":
                    cursor.removeSelectedText()
                else:
                    break

        cursor.endEditBlock()
