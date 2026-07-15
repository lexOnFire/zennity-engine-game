"""Workspace visual para criar e editar assets ``.zlogic``."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPainterPathStroker, QPen, QBrush
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QComboBox,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from editor.ui.icons import editor_icon
from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    create_logic_node,
    default_logic_graph,
    load_logic_graph,
    normalize_logic_graph,
    node_port_definitions,
    save_logic_graph,
    validate_logic_graph,
)


CATEGORY_COLORS = {
    "Eventos": QColor("#d66ba0"),
    "Movimento": QColor("#4c9aff"),
    "Ação": QColor("#ae7df0"),
    "Lógica": QColor("#f0a64b"),
    "Condição": QColor("#50c878"),
    "Objetos": QColor("#47b8c8"),
    "Variáveis": QColor("#d5b84b"),
    "Personalizado": QColor("#7f8b9c"),
}

PORT_COLORS = {
    "flow": QColor("#d9dde7"),
    "number": QColor("#58a6ff"),
    "bool": QColor("#50c878"),
    "text": QColor("#e6b85c"),
    "object": QColor("#47b8c8"),
    "any": QColor("#ae7df0"),
}


class LogicGraphView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, editor: "LogicGraphEditor", parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.editor = editor
        self.setObjectName("LogicGraphView")
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor("#17191f"))
        spacing = 22
        left = int(rect.left()) - (int(rect.left()) % spacing)
        top = int(rect.top()) - (int(rect.top()) % spacing)
        painter.setPen(QPen(QColor("#2b2e37"), 1))
        for x in range(left, int(rect.right()) + spacing, spacing):
            for y in range(top, int(rect.bottom()) + spacing, spacing):
                painter.drawPoint(x, y)

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.12 if event.angleDelta().y() > 0 else 1 / 1.12
            self.scale(factor, factor)
            event.accept()
            return
        super().wheelEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_D and event.modifiers() & Qt.ControlModifier:
            self.editor.duplicate_selected()
            event.accept()
            return
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.editor.delete_selected()
            event.accept()
            return
        if event.key() == Qt.Key_Escape:
            self.editor.cancel_connection()
            event.accept()
            return
        super().keyPressEvent(event)


class LogicPortItem(QGraphicsEllipseItem):
    """Porta interativa que inicia e conclui uma conexão por arraste."""

    SIZE = 12.0

    def __init__(self, node: "LogicNodeItem", name: str, direction: str, data_type: str, y: float) -> None:
        x = -self.SIZE / 2 if direction == "input" else node.WIDTH - self.SIZE / 2
        super().__init__(x, y - self.SIZE / 2, self.SIZE, self.SIZE, node)
        self.node = node
        self.name = str(name)
        self.direction = str(direction)
        self.data_type = str(data_type)
        self.base_color = PORT_COLORS.get(self.data_type, PORT_COLORS["any"])
        self.setPen(QPen(QColor("#f3f5f9"), 1.0))
        self.setBrush(QBrush(self.base_color))
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setZValue(5)
        self.setToolTip(f"{self.name} • {self.data_type}")

    def scene_position(self) -> QPointF:
        return self.mapToScene(self.boundingRect().center())

    def set_connection_state(self, state: str = "normal") -> None:
        if state == "candidate":
            self.setBrush(QBrush(QColor("#7ee787")))
            self.setPen(QPen(QColor("#ffffff"), 1.8))
            self.setScale(1.5)
        elif state == "compatible":
            self.setBrush(QBrush(self.base_color.lighter(130)))
            self.setPen(QPen(QColor("#f3f5f9"), 1.2))
            self.setScale(1.16)
        elif state == "invalid":
            self.setBrush(QBrush(QColor("#5b606c")))
            self.setPen(QPen(QColor("#777d89"), 1.0))
            self.setScale(0.9)
        else:
            self.setBrush(QBrush(self.base_color))
            self.setPen(QPen(QColor("#f3f5f9"), 1.0))
            self.setScale(1.0)

    def hoverEnterEvent(self, event) -> None:
        if self.node.editor._connection_origin is None:
            self.setScale(1.22)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        if self.node.editor._connection_origin is None:
            self.setScale(1.0)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:
        self.node.editor.begin_connection(self)
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        self.node.editor.update_connection(event.scenePos())
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self.node.editor.finish_connection(event.scenePos())
        event.accept()


class LogicEdgeItem(QGraphicsPathItem):
    """Conexão selecionável com cor determinada pelo tipo da porta."""

    def __init__(self, path: QPainterPath, edge_id: str, data_type: str) -> None:
        super().__init__(path)
        self.edge_id = edge_id
        self.base_color = PORT_COLORS.get(data_type, PORT_COLORS["any"])
        self.setPen(QPen(self.base_color, 2.2))
        self.setZValue(0)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setData(0, edge_id)

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self.setPen(QPen(QColor("#ffffff") if bool(value) else self.base_color, 3.2 if bool(value) else 2.2))
        return result

    def shape(self) -> QPainterPath:
        stroker = QPainterPathStroker()
        stroker.setWidth(14.0)
        return stroker.createStroke(self.path())


class LogicNodeItem(QGraphicsRectItem):
    WIDTH = 210.0
    MINIMUM_HEIGHT = 94.0

    def __init__(self, editor: "LogicGraphEditor", node: dict[str, Any]) -> None:
        ports = node_port_definitions(str(node.get("type", "")))
        self.input_definitions = ports["inputs"]
        self.output_definitions = ports["outputs"]
        self.height = max(self.MINIMUM_HEIGHT, 62.0 + max(len(self.input_definitions), len(self.output_definitions), 1) * 22.0)
        super().__init__(0.0, 0.0, self.WIDTH, self.height)
        self.editor = editor
        self.node = node
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setPos(float(node["position"][0]), float(node["position"][1]))
        self.setZValue(2)
        self.setPen(QPen(QColor("#515662"), 1.2))
        self.setBrush(QBrush(QColor("#22242a")))

        color = CATEGORY_COLORS.get(str(node.get("category")), CATEGORY_COLORS["Personalizado"])
        self.header = QGraphicsRectItem(0.0, 0.0, self.WIDTH, 28.0, self)
        self.header.setPen(Qt.NoPen)
        self.header.setBrush(QBrush(color.darker(155)))

        self.title_item = QGraphicsTextItem(str(node.get("title", "Nó")), self)
        self.title_item.setDefaultTextColor(QColor("#f2f4f8"))
        self.title_item.setPos(10.0, 3.0)
        font = self.title_item.font()
        font.setBold(True)
        font.setPointSizeF(9.5)
        self.title_item.setFont(font)

        self.summary_item = QGraphicsTextItem("", self)
        self.summary_item.setDefaultTextColor(QColor("#b8beca"))
        self.summary_item.setTextWidth(self.WIDTH - 22.0)
        self.summary_item.setPos(10.0, self.height - 25.0)
        summary_font = self.summary_item.font()
        summary_font.setPointSizeF(8.5)
        self.summary_item.setFont(summary_font)

        self.input_ports: dict[str, LogicPortItem] = {}
        self.output_ports: dict[str, LogicPortItem] = {}
        for index, (name, data_type) in enumerate(self.input_definitions):
            y = 43.0 + index * 22.0
            port = LogicPortItem(self, name, "input", data_type, y)
            self.input_ports[name] = port
            label = QGraphicsTextItem(name, self)
            label.setDefaultTextColor(QColor("#aeb6c5"))
            label.setPos(9.0, y - 12.0)
        for index, (name, data_type) in enumerate(self.output_definitions):
            y = 43.0 + index * 22.0
            port = LogicPortItem(self, name, "output", data_type, y)
            self.output_ports[name] = port
            label = QGraphicsTextItem(name, self)
            label.setDefaultTextColor(QColor("#aeb6c5"))
            label.setTextWidth(76.0)
            label.setPos(self.WIDTH - 84.0, y - 12.0)
        self.refresh_text()

    @property
    def node_id(self) -> str:
        return str(self.node["id"])

    def input_position(self, port_name: str = "in") -> QPointF:
        port = self.input_ports.get(port_name) or next(iter(self.input_ports.values()), None)
        return port.scene_position() if port is not None else self.mapToScene(QPointF(0.0, 43.0))

    def output_position(self, port_name: str = "next") -> QPointF:
        port = self.output_ports.get(port_name) or next(iter(self.output_ports.values()), None)
        return port.scene_position() if port is not None else self.mapToScene(QPointF(self.WIDTH, 43.0))

    def refresh_text(self) -> None:
        properties = self.node.get("properties", {})
        if properties:
            summary = "  •  ".join(f"{key}: {value}" for key, value in list(properties.items())[:2])
        else:
            summary = str(self.node.get("category", ""))
        self.summary_item.setPlainText(summary)

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemPositionHasChanged and hasattr(self, "editor"):
            position = value if isinstance(value, QPointF) else self.pos()
            self.node["position"] = [round(position.x(), 2), round(position.y(), 2)]
            self.editor.refresh_connections()
            self.editor.mark_dirty()
        return result


class LogicGraphEditor(QWidget):
    message = Signal(str, str)
    asset_changed = Signal()
    MAGNET_RADIUS_PIXELS = 42.0

    def __init__(self, project_root: str | Path | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LogicWorkspace")
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.current_path: Path | None = None
        self.graph = default_logic_graph()
        self.node_items: dict[str, LogicNodeItem] = {}
        self.edge_items: list[LogicEdgeItem] = []
        self._connection_origin: LogicPortItem | None = None
        self._connection_candidate: LogicPortItem | None = None
        self._connection_preview: QGraphicsPathItem | None = None
        self._dirty = False
        self._updating_properties = False
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(700)
        self._autosave_timer.timeout.connect(self._autosave)
        self._build_ui()
        self._connect_ui()
        self.set_graph(self.graph)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        title_row = QHBoxLayout()
        title = QLabel("Editor de Lógica Visual")
        title.setObjectName("WorkspaceTitle")
        self.asset_label = QLabel("Novo Logic Graph — ainda não salvo")
        self.asset_label.setObjectName("WorkspaceStatus")
        self.validation_label = QLabel("Grafo vazio")
        self.validation_label.setObjectName("WorkspaceContext")
        title_row.addWidget(title)
        title_row.addWidget(self.asset_label)
        title_row.addStretch(1)
        title_row.addWidget(self.validation_label)
        root.addLayout(title_row)

        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("LogicToolbar")
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(6, 4, 6, 4)
        toolbar.setSpacing(4)
        self.new_button = QToolButton()
        self.open_button = QToolButton()
        self.save_button = QToolButton()
        self.save_as_button = QToolButton()
        for button, icon_name, tooltip in (
            (self.new_button, "new", "Novo Logic Graph"),
            (self.open_button, "open", "Abrir Logic Graph"),
            (self.save_button, "save", "Salvar"),
            (self.save_as_button, "save", "Salvar como..."),
        ):
            button.setIcon(editor_icon(icon_name))
            button.setToolTip(tooltip)
            button.setProperty("uiRole", "icon")
            toolbar.addWidget(button)
        toolbar.addSpacing(8)
        self.demo_button = QPushButton("Abrir exemplo Player")
        self.demo_button.setIcon(editor_icon("open"))
        self.demo_button.setProperty("uiRole", "primary")
        toolbar.addWidget(self.demo_button)
        toolbar.addSpacing(12)
        toolbar.addWidget(QLabel("OBJETO ALVO"))
        self.target_type = QComboBox()
        self.target_type.addItem("Nome", "name")
        self.target_type.addItem("Tag", "tag")
        self.target_type.setMaximumWidth(82)
        self.target_value = QLineEdit("Player")
        self.target_value.setPlaceholderText("Player")
        self.target_value.setMaximumWidth(150)
        toolbar.addWidget(self.target_type)
        toolbar.addWidget(self.target_value)
        toolbar.addStretch(1)
        self.fit_button = QPushButton("Enquadrar")
        self.connect_button = QPushButton("Conectar selecionados")
        self.delete_button = QPushButton("Excluir selecionado")
        self.delete_button.setProperty("uiRole", "danger")
        toolbar.addWidget(self.fit_button)
        toolbar.addWidget(self.connect_button)
        toolbar.addWidget(self.delete_button)
        root.addWidget(toolbar_widget)

        category_widget = QWidget()
        category_widget.setObjectName("LogicCategories")
        categories = QHBoxLayout(category_widget)
        categories.setContentsMargins(4, 4, 4, 4)
        categories.setSpacing(6)
        self.category_group = QButtonGroup(self)
        self.category_group.setExclusive(True)
        for index, category in enumerate(("Movimento", "Ação", "Lógica", "Condição", "Eventos", "Objetos", "Variáveis")):
            button = QPushButton(category)
            button.setCheckable(True)
            button.setProperty("logicCategory", category)
            self.category_group.addButton(button, index)
            categories.addWidget(button)
            if index == 0:
                button.setChecked(True)
        categories.addStretch(1)
        root.addWidget(category_widget)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("LogicContentSplitter")
        splitter.setChildrenCollapsible(False)

        palette_panel = QFrame()
        palette_panel.setObjectName("LogicPalettePanel")
        palette_layout = QVBoxLayout(palette_panel)
        palette_layout.setContentsMargins(8, 8, 8, 8)
        palette_title = QLabel("NÓS")
        palette_title.setObjectName("PanelSectionTitle")
        palette_layout.addWidget(palette_title)
        self.palette = QListWidget()
        self.palette.setObjectName("LogicNodePalette")
        self.palette.setToolTip("Duplo clique para adicionar um nó")
        palette_layout.addWidget(self.palette, 1)
        hint = QLabel("Duplo clique adiciona o nó. Ao arrastar, o ímã encaixa na porta compatível mais próxima.")
        hint.setObjectName("PanelHint")
        hint.setWordWrap(True)
        palette_layout.addWidget(hint)
        palette_panel.setMinimumWidth(180)
        splitter.addWidget(palette_panel)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-2000.0, -1400.0, 4000.0, 2800.0)
        self.view = LogicGraphView(self.scene, self)
        splitter.addWidget(self.view)

        properties_panel = QFrame()
        properties_panel.setObjectName("LogicPropertiesPanel")
        properties_layout = QVBoxLayout(properties_panel)
        properties_layout.setContentsMargins(8, 8, 8, 8)
        properties_title = QLabel("PROPRIEDADES DO NÓ")
        properties_title.setObjectName("PanelSectionTitle")
        properties_layout.addWidget(properties_title)
        self.selected_label = QLabel("Nenhum nó selecionado")
        self.selected_label.setObjectName("WorkspaceContext")
        self.selected_label.setWordWrap(True)
        properties_layout.addWidget(self.selected_label)
        self.property_tree = QTreeWidget()
        self.property_tree.setObjectName("LogicPropertyTree")
        self.property_tree.setHeaderLabels(["Propriedade", "Valor"])
        self.property_tree.setColumnWidth(0, 105)
        properties_layout.addWidget(self.property_tree, 1)
        property_hint = QLabel("Delete remove, Ctrl+D duplica e Esc cancela uma conexão. Ctrl + roda aproxima o grafo.")
        property_hint.setObjectName("PanelHint")
        property_hint.setWordWrap(True)
        properties_layout.addWidget(property_hint)
        properties_panel.setMinimumWidth(230)
        splitter.addWidget(properties_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([190, 700, 240])
        root.addWidget(splitter, 1)
        self._refresh_palette("Movimento")

    def _connect_ui(self) -> None:
        self.category_group.idClicked.connect(self._category_clicked)
        self.palette.itemDoubleClicked.connect(self._add_palette_item)
        self.scene.selectionChanged.connect(self._selection_changed)
        self.property_tree.itemChanged.connect(self._property_changed)
        self.new_button.clicked.connect(self.new_graph)
        self.open_button.clicked.connect(self.open_dialog)
        self.save_button.clicked.connect(self.save)
        self.save_as_button.clicked.connect(lambda: self.save(save_as=True))
        self.demo_button.clicked.connect(self.open_demo)
        self.fit_button.clicked.connect(self.fit_graph)
        self.connect_button.clicked.connect(self.connect_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.target_type.currentIndexChanged.connect(lambda _index: self.mark_dirty())
        self.target_value.textChanged.connect(lambda _text: self.mark_dirty())

    def _category_clicked(self, button_id: int) -> None:
        button = self.category_group.button(button_id)
        self._refresh_palette(str(button.property("logicCategory")) if button else "Movimento")

    def _refresh_palette(self, category: str) -> None:
        self.palette.clear()
        for node_type, definition in NODE_DEFINITIONS.items():
            if definition.get("category") != category:
                continue
            item = QListWidgetItem(str(definition["title"]))
            item.setData(Qt.UserRole, node_type)
            item.setToolTip(f"{category} • {node_type}")
            self.palette.addItem(item)

    def _add_palette_item(self, item: QListWidgetItem) -> None:
        node_type = str(item.data(Qt.UserRole))
        center = self.view.mapToScene(self.view.viewport().rect().center())
        offset = len(self.node_items) * 18.0
        node = create_logic_node(node_type, (center.x() + offset, center.y() + offset))
        self.graph["nodes"].append(node)
        self._create_node_item(node)
        self.mark_dirty()
        self._update_validation()

    def _create_node_item(self, node: dict[str, Any]) -> LogicNodeItem:
        item = LogicNodeItem(self, node)
        self.scene.addItem(item)
        self.node_items[item.node_id] = item
        return item

    def set_graph(self, graph: dict[str, Any], path: Path | None = None) -> None:
        self.cancel_connection()
        self._autosave_timer.stop()
        self.graph = normalize_logic_graph(graph)
        self.current_path = path
        target = self.graph.get("target", {"type": "name", "value": "Player"})
        self.target_type.blockSignals(True)
        self.target_value.blockSignals(True)
        self.target_type.setCurrentIndex(max(0, self.target_type.findData(str(target.get("type", "name")))))
        self.target_value.setText(str(target.get("value", "Player")))
        self.target_type.blockSignals(False)
        self.target_value.blockSignals(False)
        self.scene.clear()
        self.node_items.clear()
        self.edge_items.clear()
        for node in self.graph["nodes"]:
            self._create_node_item(node)
        self.refresh_connections()
        self._dirty = False
        self._update_status()
        self._update_validation()
        self.fit_graph()

    def refresh_connections(self) -> None:
        if not hasattr(self, "scene"):
            return
        for item in self.edge_items:
            self.scene.removeItem(item)
        self.edge_items.clear()
        for edge in self.graph.get("edges", []):
            source = self.node_items.get(str(edge.get("from_node")))
            target = self.node_items.get(str(edge.get("to_node")))
            if source is None or target is None:
                continue
            from_port = str(edge.get("from_port", "next"))
            to_port = str(edge.get("to_port", "in"))
            start = source.output_position(from_port)
            end = target.input_position(to_port)
            path = self._connection_path(start, end)
            source_port = source.output_ports.get(from_port)
            data_type = source_port.data_type if source_port is not None else str(edge.get("kind", "flow"))
            connection = LogicEdgeItem(path, str(edge.get("id")), data_type)
            self.scene.addItem(connection)
            self.edge_items.append(connection)

    @staticmethod
    def _connection_path(start: QPointF, end: QPointF) -> QPainterPath:
        distance = max(70.0, abs(end.x() - start.x()) * 0.48)
        path = QPainterPath(start)
        path.cubicTo(start + QPointF(distance, 0.0), end - QPointF(distance, 0.0), end)
        return path

    @staticmethod
    def _ports_compatible(first: LogicPortItem, second: LogicPortItem) -> bool:
        if first.node is second.node or first.direction == second.direction:
            return False
        source = first if first.direction == "output" else second
        target = second if second.direction == "input" else first
        return source.data_type == target.data_type or "any" in {source.data_type, target.data_type}

    def begin_connection(self, port: LogicPortItem) -> None:
        self.cancel_connection()
        self._connection_origin = port
        self._connection_candidate = None
        start = port.scene_position()
        preview = QGraphicsPathItem(self._connection_path(start, start))
        preview.setPen(QPen(port.base_color, 2.2, Qt.DashLine))
        preview.setZValue(1)
        self.scene.addItem(preview)
        self._connection_preview = preview
        self._update_port_highlights()

    def _update_port_highlights(self) -> None:
        origin = self._connection_origin
        for item in self.node_items.values():
            for candidate in (*item.input_ports.values(), *item.output_ports.values()):
                if candidate is origin or candidate is self._connection_candidate:
                    candidate.set_connection_state("candidate")
                else:
                    compatible = origin is not None and self._ports_compatible(origin, candidate)
                    candidate.set_connection_state("compatible" if compatible else "invalid")

    def _nearest_compatible_port(self, scene_position: QPointF) -> LogicPortItem | None:
        origin = self._connection_origin
        if origin is None:
            return None
        zoom = max(abs(float(self.view.transform().m11())), 0.05)
        radius = self.MAGNET_RADIUS_PIXELS / zoom
        radius_squared = radius * radius
        nearest: LogicPortItem | None = None
        nearest_distance = radius_squared
        for item in self.node_items.values():
            for candidate in (*item.input_ports.values(), *item.output_ports.values()):
                if not self._ports_compatible(origin, candidate):
                    continue
                delta = candidate.scene_position() - scene_position
                distance = delta.x() * delta.x() + delta.y() * delta.y()
                if distance <= nearest_distance:
                    nearest = candidate
                    nearest_distance = distance
        return nearest

    def update_connection(self, scene_position: QPointF) -> None:
        if self._connection_origin is None or self._connection_preview is None:
            return
        candidate = self._nearest_compatible_port(scene_position)
        if candidate is not self._connection_candidate:
            self._connection_candidate = candidate
            self._update_port_highlights()
        endpoint = candidate.scene_position() if candidate is not None else scene_position
        origin = self._connection_origin.scene_position()
        if self._connection_origin.direction == "output":
            self._connection_preview.setPath(self._connection_path(origin, endpoint))
        else:
            self._connection_preview.setPath(self._connection_path(endpoint, origin))

    def _port_at(self, scene_position: QPointF) -> LogicPortItem | None:
        for item in self.scene.items(scene_position):
            if isinstance(item, LogicPortItem):
                return item
        return None

    def finish_connection(self, scene_position: QPointF) -> None:
        origin = self._connection_origin
        target = self._connection_candidate or self._nearest_compatible_port(scene_position) or self._port_at(scene_position)
        if origin is None:
            return
        if target is None or target is origin:
            self.cancel_connection()
            return
        if not self._ports_compatible(origin, target):
            self.message.emit("WARNING", "Portas incompatíveis: conecte fluxo com fluxo e valores do mesmo tipo")
            self.cancel_connection()
            return
        source = origin if origin.direction == "output" else target
        destination = target if target.direction == "input" else origin
        if any(
            edge["from_node"] == source.node.node_id
            and edge.get("from_port", "next") == source.name
            and edge["to_node"] == destination.node.node_id
            and edge.get("to_port", "in") == destination.name
            for edge in self.graph["edges"]
        ):
            self.message.emit("WARNING", "Essa conexão já existe")
            self.cancel_connection()
            return
        # Uma entrada representa uma única origem. Ao reconectar, o fio antigo
        # é substituído, comportamento esperado em editores visuais.
        self.graph["edges"] = [
            edge for edge in self.graph["edges"]
            if not (edge["to_node"] == destination.node.node_id and edge.get("to_port", "in") == destination.name)
        ]
        self.graph["edges"].append({
            "id": uuid.uuid4().hex,
            "from_node": source.node.node_id,
            "from_port": source.name,
            "to_node": destination.node.node_id,
            "to_port": destination.name,
            "kind": source.data_type,
        })
        self.cancel_connection(refresh=False)
        self.refresh_connections()
        self.mark_dirty()
        self._update_validation()

    def cancel_connection(self, refresh: bool = True) -> None:
        if self._connection_preview is not None and self._connection_preview.scene() is self.scene:
            self.scene.removeItem(self._connection_preview)
        self._connection_preview = None
        self._connection_origin = None
        self._connection_candidate = None
        for item in self.node_items.values():
            for port in (*item.input_ports.values(), *item.output_ports.values()):
                port.set_connection_state()
        if refresh:
            self.view.viewport().update()

    def connect_selected(self) -> None:
        selected = [item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        if len(selected) != 2:
            self.message.emit("WARNING", "Selecione exatamente dois nós para conectar")
            return
        selected.sort(key=lambda item: item.scenePos().x())
        source, target = selected
        source_port = next((port for port in source.output_ports.values() if port.data_type == "flow"), None)
        target_port = next((port for port in target.input_ports.values() if port.data_type == "flow"), None)
        if source_port is None or target_port is None:
            self.message.emit("WARNING", "Esses nós não possuem portas de fluxo compatíveis; arraste as portas de valor")
            return
        if any(
            edge["from_node"] == source.node_id
            and edge.get("from_port", "next") == source_port.name
            and edge["to_node"] == target.node_id
            and edge.get("to_port", "in") == target_port.name
            for edge in self.graph["edges"]
        ):
            self.message.emit("WARNING", "Esses nós já estão conectados")
            return
        self.graph["edges"] = [
            edge for edge in self.graph["edges"]
            if not (edge["to_node"] == target.node_id and edge.get("to_port", "in") == target_port.name)
        ]
        self.graph["edges"].append({
            "id": uuid.uuid4().hex,
            "from_node": source.node_id,
            "from_port": source_port.name,
            "to_node": target.node_id,
            "to_port": target_port.name,
            "kind": "flow",
        })
        self.refresh_connections()
        self.mark_dirty()
        self._update_validation()

    def delete_selected(self) -> None:
        node_ids = {item.node_id for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)}
        edge_ids = {str(item.data(0)) for item in self.scene.selectedItems() if isinstance(item, QGraphicsPathItem)}
        if not node_ids and not edge_ids:
            return
        self.graph["nodes"] = [node for node in self.graph["nodes"] if node["id"] not in node_ids]
        self.graph["edges"] = [
            edge for edge in self.graph["edges"]
            if edge["id"] not in edge_ids and edge["from_node"] not in node_ids and edge["to_node"] not in node_ids
        ]
        for node_id in node_ids:
            item = self.node_items.pop(node_id, None)
            if item is not None:
                self.scene.removeItem(item)
        self.refresh_connections()
        self.mark_dirty()
        self._update_validation()

    def duplicate_selected(self) -> None:
        selected = [item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        if not selected:
            return
        old_ids = {item.node_id for item in selected}
        id_map: dict[str, str] = {}
        copies: list[dict[str, Any]] = []
        for item in selected:
            node = deepcopy(item.node)
            new_id = uuid.uuid4().hex
            id_map[item.node_id] = new_id
            node["id"] = new_id
            node["position"] = [float(item.pos().x()) + 32.0, float(item.pos().y()) + 32.0]
            copies.append(node)
        copied_edges = []
        for edge in self.graph["edges"]:
            if edge["from_node"] not in old_ids or edge["to_node"] not in old_ids:
                continue
            copied = deepcopy(edge)
            copied["id"] = uuid.uuid4().hex
            copied["from_node"] = id_map[edge["from_node"]]
            copied["to_node"] = id_map[edge["to_node"]]
            copied_edges.append(copied)
        self.scene.clearSelection()
        self.graph["nodes"].extend(copies)
        self.graph["edges"].extend(copied_edges)
        for node in copies:
            self._create_node_item(node).setSelected(True)
        self.refresh_connections()
        self.mark_dirty()
        self._update_validation()

    def _selection_changed(self) -> None:
        selected = [item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        self._updating_properties = True
        self.property_tree.clear()
        if len(selected) != 1:
            self.selected_label.setText("Selecione um nó para editar seus valores")
            self._updating_properties = False
            return
        node = selected[0].node
        self.selected_label.setText(f"{node['title']}\n{node['category']} • {node['type']}")
        title_item = QTreeWidgetItem(["title", str(node["title"])])
        title_item.setFlags(title_item.flags() | Qt.ItemIsEditable)
        self.property_tree.addTopLevelItem(title_item)
        for key, value in node.get("properties", {}).items():
            item = QTreeWidgetItem([str(key), json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value])
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.property_tree.addTopLevelItem(item)
        self._updating_properties = False

    def _property_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if self._updating_properties or column != 1:
            return
        selected = [entry for entry in self.scene.selectedItems() if isinstance(entry, LogicNodeItem)]
        if len(selected) != 1:
            return
        node_item = selected[0]
        key = item.text(0)
        text = item.text(1)
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            value = text
        if key == "title":
            node_item.node["title"] = str(value)
            node_item.title_item.setPlainText(str(value))
        else:
            node_item.node.setdefault("properties", {})[key] = value
        node_item.refresh_text()
        self.mark_dirty()
        self._update_validation()

    def graph_data(self) -> dict[str, Any]:
        for node_id, item in self.node_items.items():
            item.node["position"] = [round(item.pos().x(), 2), round(item.pos().y(), 2)]
        data = deepcopy(self.graph)
        data["target"] = {
            "type": str(self.target_type.currentData() or "name"),
            "value": self.target_value.text().strip() or "Player",
        }
        return normalize_logic_graph(data)

    def new_graph(self) -> None:
        if not self._confirm_discard():
            return
        self.set_graph(default_logic_graph())
        self.message.emit("INFO", "Novo Logic Graph criado")

    def open_dialog(self) -> None:
        if not self._confirm_discard():
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir Logic Graph", str(self.project_root / "Assets" / "Logic"), "Zennity Logic Graph (*.zlogic)"
        )
        if filename:
            self.open_path(Path(filename))

    def open_path(self, path: str | Path) -> None:
        try:
            resolved = Path(path).resolve()
            self.set_graph(load_logic_graph(resolved), resolved)
            self.message.emit("INFO", f"Logic Graph aberto: {resolved.name}")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.message.emit("ERROR", f"Não foi possível abrir o Logic Graph: {exc}")

    def open_demo(self) -> None:
        if not self._confirm_discard():
            return
        self.open_path(self.project_root / "Assets" / "Logic" / "PlayerMovement.zlogic")

    def save(self, _checked: bool = False, save_as: bool = False) -> None:
        path = self.current_path
        if save_as or path is None:
            directory = self.project_root / "Assets" / "Logic"
            directory.mkdir(parents=True, exist_ok=True)
            filename, _ = QFileDialog.getSaveFileName(self, "Salvar Logic Graph", str(directory / f"{self.graph['name']}.zlogic"), "Zennity Logic Graph (*.zlogic)")
            if not filename:
                return
            path = Path(filename)
        try:
            saved = save_logic_graph(path, self.graph_data())
            saved_path = Path(path).with_suffix(".zlogic")
            self.set_graph(saved, saved_path)
            self.asset_changed.emit()
            self.message.emit("INFO", f"Logic Graph salvo: {saved_path.name}")
        except (OSError, ValueError) as exc:
            self.message.emit("ERROR", f"Não foi possível salvar o Logic Graph: {exc}")

    def fit_graph(self) -> None:
        if not self.node_items:
            self.view.resetTransform()
            self.view.centerOn(0.0, 0.0)
            return
        bounds = self.scene.itemsBoundingRect().adjusted(-80.0, -80.0, 80.0, 80.0)
        self.view.fitInView(bounds, Qt.KeepAspectRatio)

    def mark_dirty(self) -> None:
        if not self._dirty:
            self._dirty = True
            self._update_status()
        if self.current_path is not None:
            self._autosave_timer.start()

    def _autosave(self) -> None:
        if not self._dirty or self.current_path is None:
            return
        try:
            save_logic_graph(self.current_path, self.graph_data())
            self._dirty = False
            self._update_status()
            self.asset_changed.emit()
            self.message.emit("INFO", f"Logic Graph salvo automaticamente: {self.current_path.name}")
        except (OSError, ValueError) as exc:
            self.message.emit("ERROR", f"Falha ao salvar automaticamente o Logic Graph: {exc}")

    def _update_status(self) -> None:
        name = self.current_path.name if self.current_path else str(self.graph.get("name", "NewLogic"))
        suffix = " • alterado" if self._dirty else (" • salvo" if self.current_path else " • ainda não salvo")
        self.asset_label.setText(name + suffix)
        self.asset_label.setProperty("uiState", "dirty" if self._dirty else "saved" if self.current_path else "")
        self.asset_label.style().unpolish(self.asset_label)
        self.asset_label.style().polish(self.asset_label)

    def _update_validation(self) -> None:
        issues = validate_logic_graph(self.graph_data())
        warnings = sum(issue.get("level") == "warning" for issue in issues)
        errors = sum(issue.get("level") == "error" for issue in issues)
        node_levels: dict[str, str] = {}
        for issue in issues:
            node_id = str(issue.get("node", ""))
            if not node_id:
                continue
            level = str(issue.get("level", "warning"))
            if node_levels.get(node_id) != "error":
                node_levels[node_id] = level
        for node_id, item in self.node_items.items():
            level = node_levels.get(node_id)
            color = QColor("#ff5d62") if level == "error" else QColor("#e6b85c") if level == "warning" else QColor("#515662")
            item.setPen(QPen(color, 2.2 if level else 1.2))
            messages = [str(issue.get("message", "")) for issue in issues if str(issue.get("node", "")) == node_id]
            item.setToolTip("\n".join(messages))
        self.validation_label.setText(
            f"{len(self.graph['nodes'])} nós • {len(self.graph['edges'])} conexões"
            + (f" • {errors} erro(s) • {warnings} aviso(s)" if errors else f" • {warnings} aviso(s)" if warnings else " • válido")
        )

    def _confirm_discard(self) -> bool:
        if not self._dirty:
            return True
        answer = QMessageBox.question(
            self,
            "Descartar alterações?",
            "O Logic Graph atual possui alterações não salvas. Deseja descartá-las?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return answer == QMessageBox.Yes
