"""
Composition Stats Dashboard
Beautiful real-time stats about the active composition
"""
import AEPython as ae
import qtae
from PySide6 import QtWidgets, QtCore, QtGui

class CompDashboard(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Composition Dashboard")
        self.setMinimumSize(500, 600)
        
        layout = QtWidgets.QVBoxLayout()
        
        # Header
        header = QtWidgets.QLabel("📊 Composition Statistics")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Stats display
        self.stats_text = QtWidgets.QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("font-family: 'Consolas', monospace; font-size: 11pt;")
        layout.addWidget(self.stats_text)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("🔄 Refresh Stats")
        refresh_btn.clicked.connect(self.update_stats)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
        
        # Auto-refresh timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000)  # Update every 2 seconds
        
        self.update_stats()
    
    def closeEvent(self, event):
        self.timer.stop()
        event.accept()

    def update_stats(self):
        comp = ae.app.project.activeItem
        if not comp or not isinstance(comp, ae.CompItem):
            self.stats_text.setPlainText("⚠️ No active composition\n\nPlease select or open a composition to view stats.")
            return
        
        # Gather stats
        stats = []
        stats.append("=" * 60)
        stats.append(f"  COMPOSITION: {comp.name}")
        stats.append("=" * 60)
        stats.append("")
        
        # Basic info
        stats.append("📐 DIMENSIONS")
        stats.append(f"   Width:      {comp.width} px")
        stats.append(f"   Height:     {comp.height} px")
        stats.append(f"   Aspect:     {comp.width / comp.height:.2f}:1")
        stats.append(f"   PAR:        {comp.pixelAspect:.2f}")
        stats.append("")
        
        # Time info
        stats.append("⏱️  TIME")
        stats.append(f"   Duration:   {comp.duration:.2f} sec")
        stats.append(f"   Frame Rate: {comp.frameRate:.2f} fps")
        stats.append(f"   Frames:     {int(comp.duration * comp.frameRate)}")
        stats.append("")
        
        # Layer stats
        total_layers = comp.numLayers
        selected = len(comp.selectedLayers)
        
        # Count layer types
        video_layers = 0
        text_layers = 0
        shape_layers = 0
        null_layers = 0
        camera_layers = 0
        light_layers = 0
        
        for i in range(1, total_layers + 1):
            layer = comp.layer(i)
            match_name = layer.matchName
            
            if "Text" in match_name:
                text_layers += 1
            elif "Shape" in match_name:
                shape_layers += 1
            elif "Null" in match_name:
                null_layers += 1
            elif "Camera" in match_name:
                camera_layers += 1
            elif "Light" in match_name:
                light_layers += 1
            else:
                video_layers += 1
        
        stats.append("🎬 LAYERS")
        stats.append(f"   Total:      {total_layers}")
        stats.append(f"   Selected:   {selected}")
        stats.append(f"   Video:      {video_layers}")
        stats.append(f"   Text:       {text_layers}")
        stats.append(f"   Shape:      {shape_layers}")
        stats.append(f"   Null:       {null_layers}")
        stats.append(f"   Camera:     {camera_layers}")
        stats.append(f"   Light:      {light_layers}")
        stats.append("")
        
        # Memory estimate (rough)
        memory_mb = (comp.width * comp.height * 4 * comp.duration * comp.frameRate) / (1024 * 1024)
        stats.append("💾 ESTIMATES")
        stats.append(f"   Uncompressed: ~{memory_mb:.1f} MB")
        stats.append("")
        
        stats.append("=" * 60)
        stats.append(f"  Last Updated: {QtCore.QTime.currentTime().toString()}")
        stats.append("=" * 60)
        
        self.stats_text.setPlainText("\n".join(stats))

dialog = CompDashboard(qtae.GetQtAEMainWindow())
dialog.show()