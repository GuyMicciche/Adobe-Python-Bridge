from PySide6.QtCore import Qt, QSortFilterProxyModel, Signal
from PySide6.QtWidgets import QCompleter, QStyledItemDelegate, QListView, QApplication
from PySide6.QtGui import QColor, QPalette
import re

# Your existing classes (PyQt6 → PySide6)
class HighlightedItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, search_text=""):
        super().__init__(parent)
        self.search_text = search_text
        self.system_palette = QApplication.palette()

    def set_search_text(self, text):
        self.search_text = text

    def paint(self, painter, option, index):
        text = index.data()
        painter.save()

        bg_color = self.system_palette.window().color()
        text_color = self.system_palette.windowText().color()

        if self.search_text:
            search_terms = [term for term in self.search_text.lower().split() if term]
            text_lower = text.lower()
            highlighted_indexes = set()
            
            for term in search_terms:
                start = 0
                while start < len(text_lower):
                    found_pos = text_lower.find(term, start)
                    if found_pos == -1:
                        break
                    highlighted_indexes.update(range(found_pos, found_pos + len(term)))
                    start = found_pos + len(term)

            highlight_color = QColor("#FFFF00")
            x_offset = option.rect.x()

            for i, char in enumerate(text):
                part_width = option.fontMetrics.horizontalAdvance(char)
                if i in highlighted_indexes:
                    painter.fillRect(x_offset, option.rect.y(), part_width, option.rect.height(), highlight_color)
                    painter.setPen(Qt.GlobalColor.black)
                else:
                    painter.setPen(text_color)

                painter.drawText(x_offset, option.rect.y() + option.fontMetrics.ascent(), char)
                x_offset += part_width
        else:
            painter.setPen(text_color)
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

        painter.restore()

class FuzzyFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, search_text="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_text = search_text

    def set_search_text(self, text):
        self.search_text = text
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.search_text:
            return True

        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)
        text = index.data().lower()

        search_terms = self.search_text.lower().split()
        regex_pattern = r'.*'.join(map(re.escape, search_terms))
        return re.search(regex_pattern, text) is not None

class HighlightedCompleter(QCompleter):
    def __init__(self, model, *args, **kwargs):
        super().__init__(model, *args, **kwargs)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterMode(Qt.MatchFlag.MatchContains)
        
        self.delegate = HighlightedItemDelegate()
        self.popup().setItemDelegate(self.delegate)
        
        self.proxy_model = FuzzyFilterProxyModel()
        self.proxy_model.setSourceModel(model)
        super().setModel(self.proxy_model)
        
        # ✅ Auto-hide on selection
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

    def splitPath(self, path):
        clean_path = ' '.join(path.split())
        self.delegate.set_search_text(clean_path)
        self.proxy_model.set_search_text(clean_path)
        return []
