"""Generic Graph Canvas for the Zennity Engine."""
import uuid
from typing import Optional, Any
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPathItem
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QUndoStack, QPainter, QPen, QColor, QBrush, QPainterPath

from .node_item import GraphNodeItem
from .edge_item import GraphEdgeItem
from .port_item import GraphPortItem
from .command_palette import CommandPaletteWidget

class GraphScene(QGraphicsScene):
    """Cena gráfica que gerencia conexões e nós genéricos."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._connection_origin: Optional[GraphPortItem] = None
        self._temp_connection: Optional[QGraphicsPathItem] = None
        self.nodes: dict[str, GraphNodeItem] = {}
        self.edges: dict[str, GraphEdgeItem] = {}
        
    def add_node(self, node_item: GraphNodeItem):
        self.nodes[node_item.node_id] = node_item
        self.addItem(node_item)
        
    def add_edge(self, edge_item: GraphEdgeItem):
        self.edges[edge_item.edge_id] = edge_item
        self.addItem(edge_item)
        self.update_edge_path(edge_item)
        
    def begin_connection(self, port: GraphPortItem):
        self._connection_origin = port
        self._temp_connection = QGraphicsPathItem()
        self._temp_connection.setPen(QPen(port.base_color, 2.2, Qt.DashLine))
        self.addItem(self._temp_connection)
        
    def update_connection(self, pos: QPointF):
        if not self._connection_origin or not self._temp_connection:
            return
            
        p1 = self._connection_origin.scene_position()
        p2 = pos
        path = QPainterPath(p1)
        
        # Desenha a curva bezier suave
        ctrl1 = QPointF(p1.x() + 50, p1.y()) if self._connection_origin.direction == "output" else QPointF(p1.x() - 50, p1.y())
        ctrl2 = QPointF(p2.x() - 50, p2.y()) if self._connection_origin.direction == "output" else QPointF(p2.x() + 50, p2.y())
        
        path.cubicTo(ctrl1, ctrl2, p2)
        self._temp_connection.setPath(path)
        
    def finish_connection(self, pos: QPointF):
        if not self._connection_origin or not self._temp_connection:
            return
            
        self.removeItem(self._temp_connection)
        self._temp_connection = None
        
        # Find target port under mouse
        items = self.items(pos)
        target_port = next((item for item in items if isinstance(item, GraphPortItem) and item != self._connection_origin), None)
        
        if target_port:
            self._create_edge_between(self._connection_origin, target_port)
            
        self._connection_origin = None
        
    def _create_edge_between(self, p1: GraphPortItem, p2: GraphPortItem):
        if p1.direction == p2.direction:
            return # Não conecta output com output ou input com input
            
        source = p1 if p1.direction == "output" else p2
        target = p2 if p2.direction == "input" else p1
        
        edge_id = str(uuid.uuid4())
        edge = GraphEdgeItem(
            edge_id=edge_id,
            source_port=source.name,
            target_port=target.name,
            source_node=source.node.node_id,
            target_node=target.node.node_id,
            data_type=source.data_type
        )
        self.add_edge(edge)
        
    def update_edge_path(self, edge: GraphEdgeItem):
        source_node = self.nodes.get(edge.source_node)
        target_node = self.nodes.get(edge.target_node)
        if not source_node or not target_node:
            return
            
        p1 = source_node.output_ports[edge.source_port].scene_position()
        p2 = target_node.input_ports[edge.target_port].scene_position()
        
        path = QPainterPath(p1)
        path.cubicTo(QPointF(p1.x() + 50, p1.y()), QPointF(p2.x() - 50, p2.y()), p2)
        edge.setPath(path)
        
    def refresh_connections(self):
        for edge in self.edges.values():
            self.update_edge_path(edge)


class GraphCanvas(QGraphicsView):
    selection_changed = Signal(list)
    message = Signal(str, str)
    asset_changed = Signal()
    debug_command = Signal(str)
    play_requested = Signal()
    stop_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = GraphScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        self.palette = CommandPaletteWidget(self)
        self.palette.hide()
        self.palette.node_selected.connect(self._spawn_node)
        self._spawn_pos = QPointF(0, 0)

        # --- GRAPH EDITORS POLISH: Minimapa & Comment Frames ---
        self.minimap_enabled: bool = True
        self.comment_frames: list = []

    def add_comment_frame(self, title: str, rect: Any = None, color_hex: str = "#2C3E50") -> Any:
        """Adiciona uma caixa de comentários/grupo colorida ao grafo."""
        from PySide6.QtCore import QRectF
        from .comment_frame_item import CommentFrameItem
        r = rect or QRectF(0, 0, 300, 200)
        item = CommentFrameItem(title=title, rect=r, color_hex=color_hex)
        self.scene.addItem(item)
        self.comment_frames.append(item)
        return item
        
    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        if event.button() == Qt.LeftButton:
            self._spawn_pos = self.mapToScene(event.pos())
            self.palette.show_at(event.globalPos())
            
    def _spawn_node(self, node_def_id: str):
        from engine.graphs.registry import GraphRegistry
        node_def = GraphRegistry.get_node(node_def_id)
        if not node_def:
            return
            
        instance_data = {
            "id": str(uuid.uuid4()),
            "type": node_def_id,
            "position": [self._spawn_pos.x(), self._spawn_pos.y()]
        }
        
        item = GraphNodeItem(node_def, instance_data)
        self.scene.add_node(item)
        self.asset_changed.emit()
        
    # --- Mocks para compatibilidade legada com LogicWorkspaceController ---
    @property
    def current_path(self):
        return getattr(self, "_current_path", None)
        
    @current_path.setter
    def current_path(self, value):
        self._current_path = value
        
    def graph_data(self):
        nodes_data = []
        for node in self.scene.nodes.values():
            nodes_data.append(node.instance_data)
            
        edges_data = []
        for edge in self.scene.edges.values():
            edges_data.append({
                "id": edge.edge_id,
                "source_node": edge.source_node,
                "source_port": edge.source_port,
                "target_node": edge.target_node,
                "target_port": edge.target_port,
                "type": edge.data_type
            })
            
        return {"nodes": nodes_data, "edges": edges_data}
        
    def load_graph_data(self, data: dict):
        self.new_document()
        if not data:
            return
            
        from engine.graphs.registry import GraphRegistry
        
        for n_data in data.get("nodes", []):
            node_def = GraphRegistry.get_node(n_data["type"])
            if node_def:
                item = GraphNodeItem(node_def, n_data)
                self.scene.add_node(item)
                
        for e_data in data.get("edges", []):
            edge = GraphEdgeItem(
                edge_id=e_data["id"],
                source_port=e_data["source_port"],
                target_port=e_data["target_port"],
                source_node=e_data["source_node"],
                target_node=e_data["target_node"],
                data_type=e_data.get("type", "any")
            )
            self.scene.add_edge(edge)
    
    def open_for_object(self, object_name, filepath=None):
        if filepath:
            import json
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.load_graph_data(data)
                    self.current_path = filepath
                    return True
            except Exception:
                pass
        return False
        
    def new_document(self):
        self.scene.clear()
        self.scene.nodes.clear()
        self.scene.edges.clear()
        self.current_path = None
        
    def set_play_state(self, playing: bool):
        pass
        
    def clear_runtime_trace(self):
        pass
        
    def apply_runtime_trace(self, trace_data):
        pass
        
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        painter.fillRect(rect, QColor("#121418"))

        # Grid primário (20px) e secundário (100px) adaptativo
        grid_small = 20
        grid_large = 100

        left = int(rect.left()) - (int(rect.left()) % grid_small)
        top = int(rect.top()) - (int(rect.top()) % grid_small)

        pen_small = QPen(QColor("#1a1d24"), 1)
        pen_large = QPen(QColor("#282c37"), 1.2)
        pen_axis = QPen(QColor("#4c9aff"), 1.5, Qt.DashLine)

        # 1. Grid secundário suave
        painter.setPen(pen_small)
        x = left
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += grid_small

        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += grid_small

        # 2. Grid principal em blocos de 100px
        painter.setPen(pen_large)
        left_large = int(rect.left()) - (int(rect.left()) % grid_large)
        top_large = int(rect.top()) - (int(rect.top()) % grid_large)

        x = left_large
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += grid_large

        y = top_large
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += grid_large

        # 3. Eixos de Origem do Mundo (0,0)
        painter.setPen(pen_axis)
        painter.drawLine(0, int(rect.top()), 0, int(rect.bottom()))
        painter.drawLine(int(rect.left()), 0, int(rect.right()), 0)
            
    def _on_selection_changed(self):
        self.selection_changed.emit(self.scene.selectedItems())