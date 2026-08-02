"""Generic Graph Canvas for the Zennity Engine.

Connection System (Item 1):
  - begin_connection / update_connection / finish_connection com bezier em tempo real
  - Validação de direção (output→input) e tipo de pino
  - Rota de conexão bloqueada por incompatibilidade de direção ou mesmo nó
  - Delete de conexão selecionada (tecla Delete / Backspace)
  - refresh_connections em cascata ao mover nó

Graph↔Inspector Sync (Item 3 hookup):
  - selectionChanged emite node_selected(GraphNodeItem | None)
  - selection_changed Signal permanece para retrocompatibilidade
"""
from __future__ import annotations
import uuid
from typing import Optional, Any
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPathItem
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QUndoStack, QPainter, QPen, QColor, QBrush, QPainterPath, QKeyEvent, QKeySequence, QShortcut

from .node_item import GraphNodeItem
from .edge_item import GraphEdgeItem
from .port_item import GraphPortItem
from .command_palette import CommandPaletteWidget


class GraphScene(QGraphicsScene):
    """Cena gráfica que gerencia conexões e nós genéricos."""

    # Emitido quando a seleção de nós muda (None se nada selecionado)
    node_selected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connection_origin: Optional[GraphPortItem] = None
        self._temp_connection: Optional[QGraphicsPathItem] = None
        self.nodes: dict[str, GraphNodeItem] = {}
        self.edges: dict[str, GraphEdgeItem] = {}

        # Wire-up selection changed
        self.selectionChanged.connect(self._on_selection_changed)

    # ── Node Management ───────────────────────────────────────────────────────
    def add_node(self, node_item: GraphNodeItem) -> None:
        self.nodes[node_item.node_id] = node_item
        self.addItem(node_item)

    def remove_node(self, node_id: str) -> None:
        """Remove um nó e todas as arestas conectadas a ele."""
        node = self.nodes.pop(node_id, None)
        if not node:
            return
        # Remove edges referencing this node
        to_remove = [eid for eid, e in list(self.edges.items())
                     if e.source_node == node_id or e.target_node == node_id]
        for eid in to_remove:
            self.remove_edge(eid)
        self.removeItem(node)

    # ── Edge Management ───────────────────────────────────────────────────────
    def add_edge(self, edge_item: GraphEdgeItem) -> None:
        self.edges[edge_item.edge_id] = edge_item
        self.addItem(edge_item)
        self.update_edge_path(edge_item)

    def remove_edge(self, edge_id: str) -> None:
        edge = self.edges.pop(edge_id, None)
        if edge and edge.scene():
            self.removeItem(edge)

    # ── Connection Drag ───────────────────────────────────────────────────────
    def begin_connection(self, port: GraphPortItem) -> None:
        self._connection_origin = port
        self._temp_connection = QGraphicsPathItem()
        self._temp_connection.setPen(QPen(port.base_color, 2.0, Qt.DashLine))
        self._temp_connection.setZValue(10)
        self.addItem(self._temp_connection)

    def update_connection(self, pos: QPointF) -> None:
        if not self._connection_origin or not self._temp_connection:
            return
        p1 = self._connection_origin.scene_position()
        p2 = pos
        # Flip control points depending on direction
        if self._connection_origin.direction == "output":
            dx = abs(p2.x() - p1.x()) * 0.5 + 40.0
            ctrl1 = QPointF(p1.x() + dx, p1.y())
            ctrl2 = QPointF(p2.x() - dx, p2.y())
        else:
            dx = abs(p2.x() - p1.x()) * 0.5 + 40.0
            ctrl1 = QPointF(p1.x() - dx, p1.y())
            ctrl2 = QPointF(p2.x() + dx, p2.y())
        path = QPainterPath(p1)
        path.cubicTo(ctrl1, ctrl2, p2)
        self._temp_connection.setPath(path)

    def finish_connection(self, pos: QPointF) -> None:
        if not self._connection_origin or not self._temp_connection:
            return

        if self._temp_connection.scene():
            self.removeItem(self._temp_connection)
        self._temp_connection = None

        # Busca o port sob o cursor
        items = self.items(pos)
        target_port = next(
            (item for item in items
             if isinstance(item, GraphPortItem) and item is not self._connection_origin),
            None,
        )

        if target_port:
            self._create_edge_between(self._connection_origin, target_port)

        self._connection_origin = None

    def cancel_connection(self) -> None:
        """Cancela o drag de conexão (tecla Escape)."""
        if self._temp_connection and self._temp_connection.scene():
            self.removeItem(self._temp_connection)
        self._temp_connection = None
        self._connection_origin = None

    def _create_edge_between(self, p1: GraphPortItem, p2: GraphPortItem) -> None:
        # Regra 1: direções opostas
        if p1.direction == p2.direction:
            return
        # Regra 2: nós diferentes
        if p1.node is p2.node:
            return

        source = p1 if p1.direction == "output" else p2
        target = p2 if p2.direction == "input" else p1

        # Regra 3: exec só conecta com exec
        if "exec" in (source.data_type, target.data_type):
            if source.data_type != target.data_type:
                return

        edge_id = str(uuid.uuid4())
        edge = GraphEdgeItem(
            edge_id=edge_id,
            source_port=source.name,
            target_port=target.name,
            source_node=source.node.node_id,
            target_node=target.node.node_id,
            data_type=source.data_type,
            target_data_type=target.data_type,
        )
        self.add_edge(edge)

    # ── Path Computation ──────────────────────────────────────────────────────
    def update_edge_path(self, edge: GraphEdgeItem) -> None:
        source_node = self.nodes.get(edge.source_node)
        target_node = self.nodes.get(edge.target_node)
        if not source_node or not target_node:
            return

        source_port = source_node.output_ports.get(edge.source_port)
        target_port = target_node.input_ports.get(edge.target_port)
        if not source_port or not target_port:
            return

        p1 = source_port.scene_position()
        p2 = target_port.scene_position()
        edge.update_path(p1, p2)

    def refresh_connections(self) -> None:
        """Recalcula todos os caminhos (chamado quando nós são movidos)."""
        for edge in self.edges.values():
            self.update_edge_path(edge)

    # ── Delete Key Handler ─────────────────────────────────────────────────────
    def delete_selected(self) -> None:
        """Remove todas as arestas e nós selecionados."""
        for item in list(self.selectedItems()):
            if isinstance(item, GraphEdgeItem):
                self.remove_edge(item.edge_id)
            elif isinstance(item, GraphNodeItem):
                self.remove_node(item.node_id)

    # ── Selection Sync ────────────────────────────────────────────────────────
    def _on_selection_changed(self) -> None:
        selected = self.selectedItems()
        node = next((i for i in selected if isinstance(i, GraphNodeItem)), None)
        self.node_selected.emit(node)


class GraphCanvas(QGraphicsView):
    selection_changed = Signal(list)
    node_selected = Signal(object)   # GraphNodeItem | None  → Inspector
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
        self.setFocusPolicy(Qt.StrongFocus)

        # A QGraphicsView nem sempre recebe keyPressEvent depois que um item
        # filho ganha foco. O atalho com escopo no canvas mantém Delete local
        # ao grafo e impede que a janela principal exclua o objeto da cena.
        self.delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self)
        self.delete_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.delete_shortcut.activated.connect(self.delete_selection)
        self.backspace_shortcut = QShortcut(QKeySequence(Qt.Key_Backspace), self)
        self.backspace_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.backspace_shortcut.activated.connect(self.delete_selection)

        self.palette = CommandPaletteWidget(self)
        self.palette.hide()
        self.palette.node_selected.connect(self._spawn_node)
        self._spawn_pos = QPointF(0, 0)

        # Relay node_selected from scene
        self.scene.node_selected.connect(self.node_selected)
        self.scene.selectionChanged.connect(self._on_scene_selection_changed)

        # --- GRAPH EDITORS POLISH: Minimapa & Comment Frames ---
        self.minimap_enabled: bool = True
        self.comment_frames: list = []

    # ── Comment Frames ─────────────────────────────────────────────────────────
    def add_comment_frame(self, title: str, rect: Any = None, color_hex: str = "#2C3E50") -> Any:
        """Adiciona uma caixa de comentários/grupo colorida ao grafo."""
        from PySide6.QtCore import QRectF
        from .comment_frame_item import CommentFrameItem
        r = rect or QRectF(0, 0, 300, 200)
        item = CommentFrameItem(title=title, rect=r, color_hex=color_hex)
        self.scene.addItem(item)
        self.comment_frames.append(item)
        return item

    # ── Mouse Events ───────────────────────────────────────────────────────────
    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        if event.button() == Qt.LeftButton:
            self._spawn_pos = self.mapToScene(event.pos())
            self.palette.show_at(event.globalPos())

    def contextMenuEvent(self, event):
        """Menu de Contexto 'Create Node' (Estilo Unreal Engine / Unity)."""
        super().contextMenuEvent(event)
        if not self.itemAt(event.pos()):
            self._spawn_pos = self.mapToScene(event.pos())
            self.palette.show_at(event.globalPos())

    # ── Keyboard Events ────────────────────────────────────────────────────────
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.delete_selection()
        elif event.key() == Qt.Key_Escape:
            self.scene.cancel_connection()
        else:
            super().keyPressEvent(event)

    def delete_selection(self) -> bool:
        """Delete selected graph items and report whether the graph changed."""
        if not self.scene.selectedItems():
            return False
        self.scene.delete_selected()
        self.asset_changed.emit()
        self.setFocus(Qt.ShortcutFocusReason)
        return True

    # ── Node Spawning ──────────────────────────────────────────────────────────
    @staticmethod
    def _node_definition(node_def_id: str):
        """Resolve nodes from the canonical metadata catalog with legacy fallback."""
        from engine.graphs.registry import GraphRegistry

        definition = GraphRegistry.get_node(node_def_id)
        if definition is not None:
            return definition
        from engine.core.context import EngineContext
        from engine.core.metadata import NodeDefinition
        from engine.metadata.manager import MetadataManager

        context = EngineContext.current()
        manager = (
            context.services.get_optional(MetadataManager)
            if context is not None else None
        )
        if manager is None:
            return None
        return next(
            (
                item for item in manager.get_all(NodeDefinition)
                if str(item.id) == str(node_def_id)
            ),
            None,
        )

    def _spawn_node(self, node_def_id: str) -> None:
        node_def = self._node_definition(node_def_id)
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

    # ── Compatibility API ──────────────────────────────────────────────────────
    @property
    def current_path(self):
        return getattr(self, "_current_path", None)

    @current_path.setter
    def current_path(self, value):
        self._current_path = value

    def graph_data(self) -> dict:
        nodes_data = [n.instance_data for n in self.scene.nodes.values()]
        edges_data = [
            {
                "id": e.edge_id,
                "source_node": e.source_node,
                "source_port": e.source_port,
                "target_node": e.target_node,
                "target_port": e.target_port,
                "type": e.data_type,
            }
            for e in self.scene.edges.values()
        ]
        return {"nodes": nodes_data, "edges": edges_data}

    def load_graph_data(self, data: dict) -> None:
        self.new_document()
        if not data:
            return

        for n_data in data.get("nodes", []):
            node_def = self._node_definition(n_data["type"])
            if node_def:
                item = GraphNodeItem(node_def, dict(n_data))
                self.scene.add_node(item)

        for e_data in data.get("edges", []):
            edge = GraphEdgeItem(
                edge_id=e_data["id"],
                source_port=e_data["source_port"],
                target_port=e_data["target_port"],
                source_node=e_data["source_node"],
                target_node=e_data["target_node"],
                data_type=e_data.get("type", "any"),
            )
            self.scene.add_edge(edge)

    def open_for_object(self, object_name, filepath=None) -> bool:
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

    def new_document(self) -> None:
        self.scene.clear()
        self.scene.nodes.clear()
        self.scene.edges.clear()
        self.current_path = None

    def set_play_state(self, playing: bool) -> None:
        pass

    def clear_runtime_trace(self) -> None:
        pass

    def apply_runtime_trace(self, trace_data) -> None:
        pass

    def _on_scene_selection_changed(self) -> None:
        self.selection_changed.emit(self.scene.selectedItems())

    # ── Drawing ────────────────────────────────────────────────────────────────
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        painter.fillRect(rect, QColor("#121418"))

        grid_small = 20
        grid_large = 100

        left = int(rect.left()) - (int(rect.left()) % grid_small)
        top = int(rect.top()) - (int(rect.top()) % grid_small)

        pen_small = QPen(QColor("#1a1d24"), 1)
        pen_large = QPen(QColor("#282c37"), 1.2)
        pen_axis = QPen(QColor("#4c9aff"), 1.5, Qt.DashLine)

        painter.setPen(pen_small)
        x = left
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += grid_small

        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += grid_small

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

        painter.setPen(pen_axis)
        painter.drawLine(0, int(rect.top()), 0, int(rect.bottom()))
        painter.drawLine(int(rect.left()), 0, int(rect.right()), 0)
