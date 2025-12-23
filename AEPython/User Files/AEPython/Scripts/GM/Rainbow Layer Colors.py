"""
Rainbow Layer Colors
Automatically assigns rainbow colors to selected layers in the active composition.
"""
import AEPython as ae
import qtae
from PySide6 import QtWidgets, QtCore, QtGui

class RainbowColors(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("🌈 Rainbow Layer Colors")
        self.setMinimumWidth(300)
        
        layout = QtWidgets.QVBoxLayout()
        
        # Header
        header = QtWidgets.QLabel("Assign Rainbow Colors to Selected Layers")
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Options
        self.reverse_check = QtWidgets.QCheckBox("Reverse Order")
        layout.addWidget(self.reverse_check)
        
        self.saturation = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.saturation.setMinimum(0)
        self.saturation.setMaximum(100)
        self.saturation.setValue(100)
        layout.addWidget(QtWidgets.QLabel("Saturation:"))
        layout.addWidget(self.saturation)
        
        self.brightness = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.brightness.setMinimum(0)
        self.brightness.setMaximum(100)
        self.brightness.setValue(100)
        layout.addWidget(QtWidgets.QLabel("Brightness:"))
        layout.addWidget(self.brightness)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        apply_btn = QtWidgets.QPushButton("Apply Rainbow 🌈")
        apply_btn.clicked.connect(self.apply_rainbow)
        reset_btn = QtWidgets.QPushButton("Reset Colors")
        reset_btn.clicked.connect(self.reset_colors)
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(reset_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def apply_rainbow(self):
        comp = ae.app.project.activeItem
        if not comp or not isinstance(comp, ae.CompItem):
            ae.alert("Please select a composition first!")
            return
        
        layers = comp.selectedLayers
        if len(layers) == 0:
            ae.alert("Please select at least one layer!")
            return
        
        ae.app.beginUndoGroup("Rainbow Colors")
        
        num_layers = len(layers)
        if self.reverse_check.isChecked():
            layers = list(reversed(layers))
        
        for i, layer in enumerate(layers):
            hue = i / num_layers
            sat = self.saturation.value() / 100.0
            val = self.brightness.value() / 100.0
            
            import colorsys
            r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
            
            # AE uses label colors 0-16
            label_map = {
                0: (1.0, 0.0, 0.0),   # Red
                1: (1.0, 1.0, 0.0),   # Yellow
                2: (0.4, 1.0, 0.4),   # Green
                3: (0.0, 1.0, 1.0),   # Cyan
                4: (0.0, 0.0, 1.0),   # Blue
                5: (1.0, 0.0, 1.0),   # Magenta
            }
            
            # Find closest label color
            best_label = 0
            min_dist = float('inf')
            for label_idx, (lr, lg, lb) in label_map.items():
                dist = (r - lr)**2 + (g - lg)**2 + (b - lb)**2
                if dist < min_dist:
                    min_dist = dist
                    best_label = label_idx
            
            layer.label = best_label + 1  # Labels are 1-indexed
        
        ae.app.endUndoGroup()
        print(f"✓ Applied rainbow colors to {num_layers} layers!")
    
    def reset_colors(self):
        comp = ae.app.project.activeItem
        if not comp or not isinstance(comp, ae.CompItem):
            return
        
        ae.app.beginUndoGroup("Reset Colors")
        for layer in comp.selectedLayers:
            layer.label = 0
        ae.app.endUndoGroup()
        print("✓ Reset layer colors")

dialog = RainbowColors(qtae.GetQtAEMainWindow())
dialog.show()