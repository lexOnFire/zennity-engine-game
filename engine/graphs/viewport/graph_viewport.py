"""Universal Graph Viewport Component."""
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt
from engine.localization import tr

class GraphViewport(QGraphicsView):
    """A completely decoupled viewport that can be embedded anywhere."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHint(self.renderHints() | Qt.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Grid settings
        self.grid_size = 20
        self.zoom_level = 1.0
        
        self.setWindowTitle(tr("graph.title"))
        
    def wheelEvent(self, event):
        """Handle zoom."""
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        self.zoom_level *= zoom_factor
        self.scale(zoom_factor, zoom_factor)
        
    def load_graph(self, graph_data: dict):
        """Loads data from a .zgraph formatted dictionary."""
        self.scene.clear()
        # Implementation for node rendering goes here...
