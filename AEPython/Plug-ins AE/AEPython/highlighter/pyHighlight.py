"""
https://wiki.python.org/moin/PyQt/Python%20syntax%20highlighting
"""

from PySide6 import QtCore, QtGui

def format(color, style=""):
    """Return a QTextCharFormat with the given attributes."""
    _color = QtGui.QColor()
    _color.setNamedColor(color)

    _format = QtGui.QTextCharFormat()
    _format.setForeground(_color)
    if "bold" in style:
        _format.setFontWeight(QtGui.QFont.Weight.Bold)
    if "italic" in style:
        _format.setFontItalic(True)
    return _format


STYLES = {
    # e.g. "def", "class", "import"
    "keyword":  format("#569CD6"),
    # e.g. =, +, -, *, /, ==, <=
    "operator": format("#D4D4D4"),
    # (), {}, []
    "brace":    format("#D4D4D4"),
    # function / class names after def / class
    "defclass": format("#DCDCAA", "bold"),
    # normal strings
    "string":   format("#CE9178"),
    # triple-quoted / multi-line strings
    "string2":  format("#CE9178"),
    # comments
    "comment":  format("#6A9955", "italic"),
    # "self"
    "self":     format("#9CDCFE", "italic"),
    # numbers
    "numbers":  format("#B5CEA8"),
}



class PythonHighlighter(QtGui.QSyntaxHighlighter):
    """Syntax highlighter for the Python language (Qt 6 / PySide6)."""

    keywords = [
        "and", "assert", "break", "class", "continue", "def",
        "del", "elif", "else", "except", "exec", "finally",
        "for", "from", "global", "if", "import", "in",
        "is", "lambda", "not", "or", "pass", "print",
        "raise", "return", "try", "while", "yield",
        "None", "True", "False",
    ]

    operators = [
        "=",
        "==", "!=", "<", "<=", ">", ">=",
        r"\+", "-", r"\*", "/", "//", r"\%", r"\*\*",
        r"\+=", "-=", r"\*=", "/=", r"\%=",
        r"\^", r"\|", r"\&", r"\~", ">>", "<<",
    ]

    braces = [
        r"\{", r"\}", r"\(", r"\)", r"\[", r"\]",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        # Triple-quoted strings
        self.tri_single = (QtCore.QRegularExpression("'''"), 1, STYLES["string2"])
        self.tri_double = (QtCore.QRegularExpression('"""'), 2, STYLES["string2"])

        rules = []

        # Keywords, operators, braces
        rules += [(rf"\b{w}\b", 0, STYLES["keyword"]) for w in PythonHighlighter.keywords]
        rules += [(o, 0, STYLES["operator"]) for o in PythonHighlighter.operators]
        rules += [(b, 0, STYLES["brace"]) for b in PythonHighlighter.braces]

        # Other rules
        rules += [
            (r"\bself\b", 0, STYLES["self"]),
            (r"\bdef\b\s*(\w+)", 1, STYLES["defclass"]),
            (r"\bclass\b\s*(\w+)", 1, STYLES["defclass"]),

            (r"\b[+-]?[0-9]+[lL]?\b", 0, STYLES["numbers"]),
            (r"\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b", 0, STYLES["numbers"]),
            (r"\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b", 0, STYLES["numbers"]),

            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES["string"]),
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES["string"]),

            (r"#[^\n]*", 0, STYLES["comment"]),
        ]

        # Compile patterns
        self.rules = [
            (QtCore.QRegularExpression(pat), index, fmt)
            for (pat, index, fmt) in rules
        ]

    # ---------- core highlighting ----------

    def highlightBlock(self, text: str) -> None:
        self.tripleQuotesWithinStrings = []

        # main token rules
        for expression, nth, fmt in self.rules:
            pattern = expression.pattern()
            is_string_rule = pattern in (
                r'"[^"\\]*(\\.[^"\\]*)*"',
                r"'[^'\\]*(\\.[^'\\]*)*'",
            )

            it = expression.globalMatch(text)
            while it.hasNext():
                m = it.next()
                index = m.capturedStart(nth)
                length = m.capturedLength(nth)
                if index < 0:
                    continue

                # collect inner triple quotes inside strings (so we can ignore them)
                if is_string_rule:
                    # search triple single
                    inner_m = self.tri_single[0].match(text, index + 1)
                    if inner_m.hasMatch():
                        self.tripleQuotesWithinStrings.extend(
                            range(inner_m.capturedStart(), inner_m.capturedStart() + 3)
                        )
                    # search triple double
                    inner_m = self.tri_double[0].match(text, index + 1)
                    if inner_m.hasMatch():
                        self.tripleQuotesWithinStrings.extend(
                            range(inner_m.capturedStart(), inner_m.capturedStart() + 3)
                        )

                # skip triple-quote characters themselves if they were counted above
                if index in self.tripleQuotesWithinStrings:
                    continue

                self.setFormat(index, length, fmt)

        self.setCurrentBlockState(0)

        # multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter: QtCore.QRegularExpression,
                        in_state: int, style: QtGui.QTextCharFormat) -> bool:
        """Handle multi-line triple-quoted strings."""
        # if we were already inside this string
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        else:
            m = delimiter.match(text)
            if not m.hasMatch():
                return False
            start = m.capturedStart()
            if start in getattr(self, "tripleQuotesWithinStrings", []):
                return False
            add = m.capturedLength()

        while start >= 0:
            m = delimiter.match(text, start + add)
            if m.hasMatch():
                end = m.capturedStart()
                length = (end - start) + m.capturedLength() + add
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start

            self.setFormat(start, length, style)

            m = delimiter.match(text, start + length)
            if m.hasMatch():
                start = m.capturedStart()
            else:
                start = -1

        return self.currentBlockState() == in_state