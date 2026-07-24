"""Generic Graph Canvas for the Zennity Engine."""
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QUndoStack
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QBrush

class GraphCanvas(QGraphicsView):
    selection_changed = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Histórico embutido
        self.undo_stack = QUndoStack(self)
        
        self.scene.selectionChanged.connect(self._on_selection_changed)
        
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