"""Generic Graph Canvas for the Zennity Engine."""
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QUndoStack, QPainter, QPen, QColor, QBrush

class GraphCanvas(QGraphicsView):
    selection_changed = Signal(list)
    message = Signal(str, str)
    asset_changed = Signal()
    debug_command = Signal(str)
    play_requested = Signal()
    stop_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        
    # --- Mocks para compatibilidade legada com LogicWorkspaceController ---
    @property
    def current_path(self): return None
    
    def graph_data(self): return None
    
    def open_for_object(self, object_name, filepath=None):
        print(f"GraphCanvas abriu para {object_name}")
        return True
        
    def new_document(self):
        pass
        
    def set_play_state(self, playing: bool):
        pass
        
    def clear_runtime_trace(self):
        pass
        
    def apply_runtime_trace(self, trace_data):
        pass
        
    def drawBackground(self, painter, rect):
        """Grade infinita genérica."""
        super().drawBackground(painter, rect)
        painter.fillRect(rect, QColor("#1e1e1e"))
        
        grid_size = 20
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        
        lines = []
        x = left
        while x < rect.right():
            lines.append((x, rect.top(), x, rect.bottom()))
            x += grid_size
            
        y = top
        while y < rect.bottom():
            lines.append((rect.left(), y, rect.right(), y))
            y += grid_size
            
        pen = QPen(QColor("#2a2a2a"), 1)
        painter.setPen(pen)
        for line in lines:
            painter.drawLine(*line)
            
    def _on_selection_changed(self):
        self.selection_changed.emit(self.scene.selectedItems())