"""
Layer Timeline Visualizer
Visual representation of layer in/out points with EXACT AE label colors
"""
import AEPython as ae
import qtae
from PySide6 import QtWidgets, QtCore, QtGui

class TimelineVisualizer(QtWidgets.QDialog):
    
    # NESTED CLASS - TimelineCanvas defined INSIDE TimelineVisualizer
    class TimelineCanvas(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            self.setMinimumHeight(400)
            self.layers_data = []
            self.comp_duration = 1
        
        def update_timeline(self):
            comp = ae.app.project.activeItem
            if not comp or not isinstance(comp, ae.CompItem):
                self.layers_data = []
                self.update()
                return
            
            self.comp_duration = comp.duration
            self.layers_data = []
            
            for i in range(1, min(comp.numLayers + 1, 20)):  # Limit to 20 layers
                layer = comp.layer(i)
                self.layers_data.append({
                    "name": layer.name,
                    "in": layer.inPoint,
                    "out": layer.outPoint,
                    "color": layer.label
                })
            
            self.update()
        
        def paintEvent(self, event):
            if not self.layers_data:
                painter = QtGui.QPainter(self)
                painter.drawText(self.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "No composition active")
                return
            
            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            
            width = self.width() - 40
            height = self.height() - 40
            margin = 20
            
            # Draw timeline background
            painter.fillRect(margin, margin, width, height, QtGui.QColor(30, 30, 30))
            
            # DRAW TIME MARKERS FIRST (BEHIND everything)
            painter.setPen(QtGui.QColor(60, 60, 60))  # Subtle gray lines
            #painter.setFont(QtGui.QFont("Arial", 9))
            
            for i in range(0, int(self.comp_duration) + 1):
                x = margin + (i / self.comp_duration) * width
                # Draw vertical line
                painter.drawLine(int(x), margin, int(x), margin + height)
                # Draw time label at top
                painter.setPen(QtGui.QColor(180, 180, 180))
                painter.drawText(int(x - 10), margin - 5, f"{i}s")
                painter.setPen(QtGui.QColor(60, 60, 60))
            
            # Calculate layer height
            layer_height = height / len(self.layers_data) if self.layers_data else 20
            
            # EXACT After Effects label colors (from AE UI)
            label_colors = {
                0: QtGui.QColor(128, 128, 128),   # None (Gray)
                1: QtGui.QColor(204, 51, 51),     # Red
                2: QtGui.QColor(255, 204, 51),    # Yellow
                3: QtGui.QColor(153, 204, 204),   # Aqua
                4: QtGui.QColor(255, 153, 204),   # Pink
                5: QtGui.QColor(153, 153, 204),   # Lavender
                6: QtGui.QColor(255, 204, 153),   # Peach
                7: QtGui.QColor(153, 204, 153),   # Sea Foam
                8: QtGui.QColor(51, 102, 204),    # Blue
                9: QtGui.QColor(102, 204, 102),   # Green
                10: QtGui.QColor(153, 51, 153),   # Purple
                11: QtGui.QColor(255, 153, 51),   # Orange
                12: QtGui.QColor(153, 102, 51),   # Brown
                13: QtGui.QColor(255, 51, 204),   # Fuchsia
                14: QtGui.QColor(51, 204, 204),   # Cyan
                15: QtGui.QColor(204, 153, 102),  # Sandstone
                16: QtGui.QColor(51, 102, 51),    # Dark Green
            }
            
            # NOW DRAW LAYERS ON TOP
            for i, layer in enumerate(self.layers_data):
                y = margin + i * layer_height
                
                # Calculate positions
                start_x = margin + (layer["in"] / self.comp_duration) * width
                end_x = margin + (layer["out"] / self.comp_duration) * width
                bar_width = end_x - start_x
                
                # Draw layer bar with matching AE label color
                color = label_colors.get(layer["color"], QtGui.QColor(128, 128, 128))
                painter.fillRect(int(start_x), int(y + 2), int(bar_width), int(layer_height - 4), color)
                
                # Draw subtle border around bar
                painter.setPen(QtGui.QColor(0, 0, 0, 80))
                painter.drawRect(int(start_x), int(y + 2), int(bar_width), int(layer_height - 4))
                
                # Draw layer name with shadow for better visibility
                painter.setPen(QtGui.QColor(0, 0, 0))
                font = QtWidgets.QApplication.font()
                font.setBold(True)
                painter.setFont(font)
                text_rect = QtCore.QRect(int(start_x + 6), int(y + 1), int(bar_width - 10), int(layer_height))
                painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter, layer["name"][:20])
                
                # Draw layer name in white on top
                painter.setPen(QtGui.QColor(0, 0, 0))
                text_rect = QtCore.QRect(int(start_x + 5), int(y), int(bar_width - 10), int(layer_height))
                #painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter, layer["name"][:20])
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📈 Layer Timeline")
        self.setMinimumSize(800, 500)
        
        layout = QtWidgets.QVBoxLayout()
        
        # Header
        header = QtWidgets.QLabel("📈 Layer Timeline Visualizer")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Canvas for timeline - use self.TimelineCanvas
        self.canvas = self.TimelineCanvas()
        layout.addWidget(self.canvas)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("🔄 Refresh Timeline")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
        self.refresh()
    
    def refresh(self):
        self.canvas.update_timeline()


dialog = TimelineVisualizer(qtae.GetQtAEMainWindow())
dialog.show()