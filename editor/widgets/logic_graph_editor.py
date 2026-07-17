"""Workspace visual para criar e editar assets ``.zlogic``."""

from __future__ import annotations

import json
import unicodedata
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPainterPathStroker, QPen, QBrush
from PySide6.QtWidgets import (
    QCheckBox,
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
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from editor.ui.icons import editor_icon
from editor.widgets.logic_asset_picker import LogicAssetPickerDialog
from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    UNIQUE_EVENT_TYPES,
    consolidate_logic_events,
    create_logic_node,
    default_logic_graph,
    load_logic_graph,
    merge_logic_fragment,
    normalize_logic_graph,
    node_port_definitions,
    save_logic_graph,
    subgraph_interface,
    validate_logic_graph,
)
from engine.logic.blackboard import coerce_variable_value, save_blackboard_asset
from engine.logic.code_preview import node_code_preview
from engine.logic.recipes import build_logic_recipe, find_logic_recipes, logic_recipe


CATEGORY_COLORS = {
    "Eventos": QColor("#d66ba0"),
    "Movimento": QColor("#4c9aff"),
    "Posição": QColor("#3fb6a8"),
    "Ação": QColor("#ae7df0"),
    "Lógica": QColor("#f0a64b"),
    "Condição": QColor("#50c878"),
    "Objetos": QColor("#47b8c8"),
    "Variáveis": QColor("#d5b84b"),
    "Subgrafos": QColor("#b48ead"),
    "Matemática": QColor("#e07a5f"),
    "Texto": QColor("#81b29a"),
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

NODE_DESCRIPTIONS = {
    "event_collision_enter": "Executa quando este objeto começa uma colisão física.",
    "event_collision_exit": "Executa quando os objetos deixam de colidir.",
    "event_trigger_enter": "Executa ao entrar em um collider marcado como área/trigger.",
    "event_trigger_exit": "Executa ao sair de uma área/trigger.",
    "event_timer": "Espera a quantidade de segundos e pode repetir automaticamente.",
    "event_key_pressed": "Executa uma única vez no instante em que a tecla é apertada.",
    "event_object_created": "Executa quando este grafo cria uma instância; o novo objeto vira o alvo implícito.",
    "create_object": "Cria uma cópia profunda e independente; ações conectadas depois recebem automaticamente o novo objeto.",
    "create_prefab": "Cria uma cópia completa de um Prefab com visual e componentes configurados.",
    "clone_object": "Duplica um objeto existente durante o Play Mode.",
    "destroy_after_time": "Agenda o descarte do alvo sem bloquear o restante do fluxo.",
    "add_component": "Adiciona e configura um componente no objeto alvo.",
    "remove_component": "Remove um componente opcional do objeto alvo.",
    "once": "Libera o fluxo somente na primeira execução.",
    "cooldown": "Libera o fluxo novamente após o intervalo configurado.",
    "restart_scene": "Restaura a cena ao estado capturado no início do Play Mode.",
    "get_position": "Lê as coordenadas X e Y atuais do objeto.",
    "move_by": "Move X e Y continuamente em unidades por segundo, sem exigir teclado.",
    "start_continuous_motion": "Inicia uma velocidade que continua ativa depois que a tecla é solta.",
    "stop_continuous_motion": "Interrompe todos os movimentos permanentes do objeto alvo.",
    "key_pressed": "Verdadeiro somente no primeiro frame em que a tecla é apertada.",
    "key_held": "Verdadeiro durante todo o tempo em que a tecla fica segurada.",
    "patrol_axis": "Move entre dois limites e inverte automaticamente a direção ao alcançá-los.",
    "set_sprite": "Troca a imagem principal do objeto durante o Play Mode.",
    "start_texture_scroll": "Repete e desloca a imagem dentro do plano sem mover collider ou Transform.",
    "stop_texture_scroll": "Interrompe o deslocamento da imagem do plano.",
    "play_animation_asset": "Carrega e toca diretamente um arquivo de animação .zanim.",
    "stop_animation": "Interrompe a animação atual do objeto.",
    "set_position": "Move imediatamente o objeto para uma posição X e Y.",
    "rotate": "Acrescenta graus à rotação atual do objeto.",
    "set_active": "Mostra/ativa ou oculta/desativa o objeto.",
    "destroy_object": "Desativa o objeto durante o Play Mode.",
    "log_message": "Escreve uma mensagem no console do editor.",
    "add_number": "Soma dois números.",
    "subtract_number": "Subtrai B de A.",
    "multiply_number": "Multiplica dois números.",
    "divide_number": "Divide A por B e avisa se B for zero.",
    "absolute_number": "Remove o sinal negativo de um número.",
    "clamp_number": "Mantém o número entre um mínimo e um máximo.",
    "random_number": "Gera um número aleatório dentro do intervalo.",
    "delta_time": "Tempo transcorrido desde o último frame.",
    "join_text": "Junta dois valores em um único texto.",
    "to_text": "Converte número, booleano ou objeto em texto.",
}

PROPERTY_LABELS = {
    "seconds": "Segundos", "repeat": "Repetir", "minimum": "Mínimo", "maximum": "Máximo",
    "degrees": "Graus", "active": "Ativo", "text": "Texto", "value": "Valor",
    "default": "Valor inicial", "type": "Tipo", "name": "Nome", "path": "Arquivo",
    "speed": "Velocidade", "force": "Força", "condition": "Condição",
    "width": "Largura", "height": "Altura", "color": "Cor", "texture": "Imagem",
    "tag": "Tag", "relative": "Posição relativa", "inherit_source": "Copiar objeto original",
    "inherit_logic": "Copiar Logic Graphs também",
    "lifetime": "Destruir após (s, 0 = nunca)",
    "max_instances": "Máximo de instâncias (0 = ilimitado)",
    "max_distance": "Distância máxima (0 = ilimitada)",
    "use_pool": "Reutilizar por pool",
    "speed_x": "Velocidade X", "speed_y": "Velocidade Y",
    "repeat_x": "Repetir no eixo X", "repeat_y": "Repetir no eixo Y",
    "parallax": "Intensidade do parallax", "reset": "Voltar à origem",
    "send_to_background": "Enviar para camada Background",
}

NODE_PROPERTY_LABELS = {
    "move_by": {"x": "Velocidade X", "y": "Velocidade Y"},
    "start_continuous_motion": {"x": "Velocidade permanente X", "y": "Velocidade permanente Y"},
    "set_position": {"x": "Posição X", "y": "Posição Y"},
    "patrol_axis": {"axis": "Eixo", "minimum": "Limite mínimo", "maximum": "Limite máximo", "speed": "Velocidade"},
    "create_object": {"x": "Posição X", "y": "Posição Y"},
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
        if event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier:
            if event.modifiers() & Qt.ShiftModifier:
                self.editor.redo()
            else:
                self.editor.undo()
            event.accept()
            return
        if event.key() == Qt.Key_Y and event.modifiers() & Qt.ControlModifier:
            self.editor.redo()
            event.accept()
            return
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
        x = -self.SIZE / 2 if direction == "input" else node.width - self.SIZE / 2
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
        self.data_type = str(data_type)
        self.base_color = PORT_COLORS.get(data_type, PORT_COLORS["any"])
        self._runtime_active = False
        self._validation_level = ""
        self.setPen(QPen(self.base_color, 2.2))
        self.setZValue(0)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setData(0, edge_id)
        self.setToolTip(
            "Referência de objeto • transporta qual instância será afetada"
            if self.data_type == "object"
            else "Fluxo de execução" if self.data_type == "flow" else f"Valor: {self.data_type}"
        )

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self._refresh_pen(bool(value))
        return result

    def set_runtime_active(self, active: bool) -> None:
        self._runtime_active = bool(active)
        self._refresh_pen(self.isSelected())

    def set_validation_state(self, level: str = "", message: str = "") -> None:
        self._validation_level = str(level)
        self.setToolTip(str(message))
        self._refresh_pen(self.isSelected())

    def _refresh_pen(self, selected: bool) -> None:
        if self._runtime_active:
            self.setPen(QPen(QColor("#7ee787"), 4.2))
        elif self._validation_level == "error":
            self.setPen(QPen(QColor("#ff5d62"), 3.4, Qt.DashLine))
        elif self._validation_level == "warning":
            self.setPen(QPen(QColor("#e6b85c"), 3.0, Qt.DashLine))
        else:
            style = Qt.DashLine if self.data_type == "object" else Qt.SolidLine
            self.setPen(QPen(
                QColor("#ffffff") if selected else self.base_color,
                3.4 if selected else (2.8 if self.data_type == "object" else 2.2),
                style,
            ))

    def shape(self) -> QPainterPath:
        stroker = QPainterPathStroker()
        stroker.setWidth(14.0)
        return stroker.createStroke(self.path())


class LogicGroupResizeHandle(QGraphicsRectItem):
    SIZE = 14.0

    def __init__(self, group: "LogicGroupItem") -> None:
        super().__init__(0.0, 0.0, self.SIZE, self.SIZE, group)
        self.group = group
        self._origin = QPointF()
        self._initial_size = (group.rect().width(), group.rect().height())
        self.setBrush(QBrush(QColor("#55789b")))
        self.setPen(Qt.NoPen)
        self.setCursor(Qt.SizeFDiagCursor)
        self.setZValue(3)

    def mousePressEvent(self, event) -> None:
        self._origin = event.scenePos()
        self._initial_size = (self.group.rect().width(), self.group.rect().height())
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        delta = event.scenePos() - self._origin
        self.group.resize_to(self._initial_size[0] + delta.x(), self._initial_size[1] + delta.y())
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self.group.editor.mark_dirty()
        event.accept()


class LogicGroupItem(QGraphicsRectItem):
    """Área visual persistente usada para organizar partes de um grafo."""

    def __init__(self, editor: "LogicGraphEditor", data: dict[str, Any]) -> None:
        size = data.get("size", [460.0, 280.0])
        super().__init__(0.0, 0.0, float(size[0]), float(size[1]))
        self.editor = editor
        self.data = data
        self.group_id = str(data["id"])
        self.setPos(*data.get("position", [0.0, 0.0]))
        self.setZValue(-4)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        color = QColor(str(data.get("color", "#35506b")))
        color.setAlpha(48)
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(str(data.get("color", "#35506b"))), 2.0, Qt.DashLine))
        self.title_item = QGraphicsTextItem(str(data.get("title", "Grupo")), self)
        self.title_item.setDefaultTextColor(QColor("#dbeafe"))
        font = self.title_item.font()
        font.setBold(True)
        self.title_item.setFont(font)
        self.title_item.setPos(8.0, 4.0)
        self.resize_handle = LogicGroupResizeHandle(self)
        self.resize_handle.setPos(self.rect().width() - 17.0, self.rect().height() - 17.0)
        self.setToolTip("Duplo clique renomeia o grupo")

    def resize_to(self, width: float, height: float) -> None:
        width = max(240.0, min(1600.0, float(width)))
        height = max(140.0, min(1200.0, float(height)))
        self.setRect(0.0, 0.0, width, height)
        self.resize_handle.setPos(width - 17.0, height - 17.0)
        self.data["size"] = [round(width, 2), round(height, 2)]

    def mouseDoubleClickEvent(self, event) -> None:
        title, accepted = QInputDialog.getText(None, "Renomear grupo", "Nome", text=str(self.data.get("title", "Grupo")))
        if accepted and title.strip():
            self.data["title"] = title.strip()
            self.title_item.setPlainText(title.strip())
            self.editor.mark_dirty()
        event.accept()

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemPositionHasChanged and hasattr(self, "editor"):
            position = value if isinstance(value, QPointF) else self.pos()
            self.data["position"] = [round(position.x(), 2), round(position.y(), 2)]
            self.editor.mark_dirty()
        return result


class LogicCommentItem(QGraphicsRectItem):
    """Nota persistente que explica uma região do grafo sem afetar o runtime."""

    def __init__(self, editor: "LogicGraphEditor", data: dict[str, Any]) -> None:
        width = float(data.get("width", 260.0))
        super().__init__(0.0, 0.0, width, 78.0)
        self.editor = editor
        self.data = data
        self.comment_id = str(data["id"])
        self.setPos(*data.get("position", [0.0, 0.0]))
        self.setZValue(1)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        color = QColor(str(data.get("color", "#6b5b2f")))
        color.setAlpha(190)
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor("#d9b85f"), 1.4))
        self.text_item = QGraphicsTextItem(str(data.get("text", "Comentário")), self)
        self.text_item.setDefaultTextColor(QColor("#fff3c4"))
        self.text_item.setTextWidth(width - 16.0)
        self.text_item.setPos(8.0, 7.0)
        self.setToolTip("Duplo clique edita o comentário")

    def mouseDoubleClickEvent(self, event) -> None:
        text_value, accepted = QInputDialog.getMultiLineText(
            None, "Editar comentário", "Texto", str(self.data.get("text", "Comentário"))
        )
        if accepted:
            self.data["text"] = text_value
            self.text_item.setPlainText(text_value)
            self.editor.mark_dirty()
        event.accept()

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemPositionHasChanged and hasattr(self, "editor"):
            position = value if isinstance(value, QPointF) else self.pos()
            self.data["position"] = [round(position.x(), 2), round(position.y(), 2)]
            self.editor.mark_dirty()
        return result


class LogicMiniMapView(QGraphicsView):
    """Visão geral compacta; clicar recentraliza o canvas principal."""

    def __init__(self, scene: QGraphicsScene, editor: "LogicGraphEditor") -> None:
        super().__init__(scene)
        self.editor = editor
        self.setObjectName("LogicMiniMap")
        self.setFixedSize(190, 120)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setInteractive(False)
        self.setStyleSheet("border: 1px solid #454a56; background: #111318;")

    def refresh(self) -> None:
        bounds = self.scene().itemsBoundingRect().adjusted(-60.0, -60.0, 60.0, 60.0)
        if not bounds.isEmpty():
            self.fitInView(bounds, Qt.KeepAspectRatio)

    def mousePressEvent(self, event) -> None:
        self.editor.view.centerOn(self.mapToScene(event.position().toPoint()))
        event.accept()


class LogicFlipControl(QGraphicsTextItem):
    """Controle pequeno que alterna frente e pseudocódigo do bloco."""

    def __init__(self, node: "LogicNodeItem") -> None:
        super().__init__("</>", node)
        self.node = node
        self.setDefaultTextColor(QColor("#dce6f2"))
        font = self.font()
        font.setBold(True)
        font.setPointSizeF(8.0)
        self.setFont(font)
        self.setPos(node.width - 52.0, 2.0)
        self.setToolTip("Virar bloco e mostrar o código equivalente")
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        self.node.toggle_code_preview()
        event.accept()


class LogicCollapseControl(QGraphicsTextItem):
    """Recolhe o corpo do bloco sem perder suas conexões."""

    def __init__(self, node: "LogicNodeItem") -> None:
        super().__init__("−", node)
        self.node = node
        self.setDefaultTextColor(QColor("#dce6f2"))
        font = self.font()
        font.setBold(True)
        font.setPointSizeF(10.0)
        self.setFont(font)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Recolher bloco")

    def refresh(self) -> None:
        self.setPlainText("+" if self.node.collapsed else "−")
        self.setToolTip("Expandir bloco" if self.node.collapsed else "Recolher bloco")
        self.setPos(self.node.width - 76.0, 1.0)

    def mousePressEvent(self, event) -> None:
        self.node.toggle_collapsed()
        event.accept()


class LogicResizeHandle(QGraphicsRectItem):
    """Alça inferior direita para redimensionar um bloco expandido."""

    SIZE = 14.0

    def __init__(self, node: "LogicNodeItem") -> None:
        super().__init__(0.0, 0.0, self.SIZE, self.SIZE, node)
        self.node = node
        self._origin = QPointF()
        self._initial_size = (node.width, node.height)
        self.setPen(QPen(QColor("#7f8796"), 1.0))
        self.setBrush(QBrush(QColor("#353943")))
        self.setCursor(Qt.SizeFDiagCursor)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setZValue(8)
        self.setToolTip("Arraste para redimensionar")

    def mousePressEvent(self, event) -> None:
        self._origin = event.scenePos()
        self._initial_size = (self.node.width, self.node.expanded_height)
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        delta = event.scenePos() - self._origin
        self.node.resize_to(self._initial_size[0] + delta.x(), self._initial_size[1] + delta.y())
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self.node.editor.mark_dirty()
        event.accept()


class LogicNodeItem(QGraphicsRectItem):
    WIDTH = 210.0
    MINIMUM_WIDTH = 170.0
    MAXIMUM_WIDTH = 520.0
    MINIMUM_HEIGHT = 116.0
    MAXIMUM_HEIGHT = 720.0
    COLLAPSED_HEIGHT = 32.0

    def __init__(self, editor: "LogicGraphEditor", node: dict[str, Any]) -> None:
        ports = node_port_definitions(node)
        self.input_definitions = ports["inputs"]
        self.output_definitions = ports["outputs"]
        self.natural_height = max(self.MINIMUM_HEIGHT + 18.0, 80.0 + max(len(self.input_definitions), len(self.output_definitions), 1) * 22.0)
        editor_state = node.setdefault("editor", {})
        self.width = max(self.MINIMUM_WIDTH, min(self.MAXIMUM_WIDTH, float(editor_state.get("width", self.WIDTH))))
        stored_height = float(editor_state.get("height", 0.0))
        self.expanded_height = max(self.natural_height, min(self.MAXIMUM_HEIGHT, stored_height or self.natural_height))
        self.collapsed = bool(editor_state.get("collapsed", False))
        self.height = self.COLLAPSED_HEIGHT if self.collapsed else self.expanded_height
        editor_state.update({"collapsed": self.collapsed, "width": self.width, "height": self.expanded_height})
        super().__init__(0.0, 0.0, self.width, self.height)
        self.editor = editor
        self.node = node
        self._show_code = False
        self._fanout_count = 0
        self._target_hint = ""
        self._target_is_implicit = False
        self._runtime_display: tuple[bool, dict[str, Any] | None, str, bool] = (False, None, "", False)
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
        self.header = QGraphicsRectItem(0.0, 0.0, self.width, 28.0, self)
        self.header.setPen(Qt.NoPen)
        self.header.setBrush(QBrush(color.darker(155)))
        self.breakpoint_item = QGraphicsEllipseItem(self.width - 20.0, 8.0, 10.0, 10.0, self)
        self.breakpoint_item.setPen(QPen(QColor("#ffd7d9"), 1.0))
        self.breakpoint_item.setBrush(QBrush(QColor("#ff4d55")))
        self.breakpoint_item.setToolTip("Breakpoint")
        self.breakpoint_item.setVisible(False)

        self.title_item = QGraphicsTextItem(str(node.get("title", "Nó")), self)
        self.title_item.setDefaultTextColor(QColor("#f2f4f8"))
        self.title_item.setPos(10.0, 3.0)
        font = self.title_item.font()
        font.setBold(True)
        font.setPointSizeF(9.5)
        self.title_item.setFont(font)
        self.flip_control = LogicFlipControl(self)
        self.collapse_control = LogicCollapseControl(self)

        self.summary_item = QGraphicsTextItem("", self)
        self.summary_item.setDefaultTextColor(QColor("#b8beca"))
        self.summary_item.setTextWidth(self.width - 22.0)
        self.summary_item.setPos(10.0, self.height - 25.0)
        summary_font = self.summary_item.font()
        summary_font.setPointSizeF(8.5)
        self.summary_item.setFont(summary_font)
        self.target_item = QGraphicsTextItem("", self)
        self.target_item.setDefaultTextColor(QColor("#75d5df"))
        self.target_item.setTextWidth(self.width - 22.0)
        self.target_item.setPos(10.0, self.height - 45.0)
        target_font = self.target_item.font()
        target_font.setBold(True)
        target_font.setPointSizeF(8.3)
        self.target_item.setFont(target_font)
        self.target_item.hide()
        self.debug_item = QGraphicsTextItem("", self)
        self.debug_item.setDefaultTextColor(QColor("#7ee787"))
        self.debug_item.setTextWidth(self.width - 22.0)
        self.debug_item.setPos(10.0, self.height - 25.0)
        self.debug_item.setVisible(False)
        self.code_item = QGraphicsTextItem("", self)
        self.code_item.setDefaultTextColor(QColor("#b9e3c6"))
        self.code_item.setTextWidth(self.width - 18.0)
        self.code_item.setPos(8.0, 32.0)
        code_font = self.code_item.font()
        code_font.setFamily("Consolas")
        code_font.setPointSizeF(7.8)
        self.code_item.setFont(code_font)
        self.code_item.setVisible(False)

        self.input_ports: dict[str, LogicPortItem] = {}
        self.output_ports: dict[str, LogicPortItem] = {}
        self.port_labels: list[QGraphicsTextItem] = []
        for index, (name, data_type) in enumerate(self.input_definitions):
            y = 43.0 + index * 22.0
            port = LogicPortItem(self, name, "input", data_type, y)
            self.input_ports[name] = port
            label = QGraphicsTextItem(name, self)
            label.setDefaultTextColor(QColor("#aeb6c5"))
            label.setPos(9.0, y - 12.0)
            self.port_labels.append(label)
        for index, (name, data_type) in enumerate(self.output_definitions):
            y = 43.0 + index * 22.0
            port = LogicPortItem(self, name, "output", data_type, y)
            self.output_ports[name] = port
            label = QGraphicsTextItem(name, self)
            label.setDefaultTextColor(QColor("#aeb6c5"))
            label.setTextWidth(76.0)
            label.setPos(self.width - 84.0, y - 12.0)
            self.port_labels.append(label)
        self.resize_handle = LogicResizeHandle(self)
        self.refresh_text()
        self._apply_geometry(notify=False)

    @property
    def node_id(self) -> str:
        return str(self.node["id"])

    def input_position(self, port_name: str = "in") -> QPointF:
        if self.collapsed:
            return self.mapToScene(QPointF(0.0, self.COLLAPSED_HEIGHT / 2.0))
        port = self.input_ports.get(port_name) or next(iter(self.input_ports.values()), None)
        return port.scene_position() if port is not None else self.mapToScene(QPointF(0.0, 43.0))

    def output_position(self, port_name: str = "next") -> QPointF:
        if self.collapsed:
            return self.mapToScene(QPointF(self.width, self.COLLAPSED_HEIGHT / 2.0))
        port = self.output_ports.get(port_name) or next(iter(self.output_ports.values()), None)
        return port.scene_position() if port is not None else self.mapToScene(QPointF(self.width, 43.0))

    def resize_to(self, width: float, height: float) -> None:
        self.width = max(self.MINIMUM_WIDTH, min(self.MAXIMUM_WIDTH, float(width)))
        self.expanded_height = max(self.natural_height, min(self.MAXIMUM_HEIGHT, float(height)))
        self.node.setdefault("editor", {}).update({
            "collapsed": self.collapsed,
            "width": round(self.width, 2),
            "height": round(self.expanded_height, 2),
        })
        self._apply_geometry()

    def toggle_collapsed(self) -> None:
        self.collapsed = not self.collapsed
        self.node.setdefault("editor", {}).update({
            "collapsed": self.collapsed,
            "width": round(self.width, 2),
            "height": round(self.expanded_height, 2),
        })
        self._apply_geometry()
        self.editor.mark_dirty()

    def _apply_geometry(self, notify: bool = True) -> None:
        self.height = self.COLLAPSED_HEIGHT if self.collapsed else self.expanded_height
        self.setRect(0.0, 0.0, self.width, self.height)
        self.header.setRect(0.0, 0.0, self.width, 28.0)
        self.breakpoint_item.setRect(self.width - 20.0, 8.0, 10.0, 10.0)
        self.flip_control.setPos(self.width - 52.0, 2.0)
        self.collapse_control.refresh()
        self.summary_item.setTextWidth(self.width - 22.0)
        self.summary_item.setPos(10.0, self.expanded_height - 25.0)
        self.target_item.setTextWidth(self.width - 22.0)
        self.target_item.setPos(10.0, self.expanded_height - 45.0)
        self.debug_item.setTextWidth(self.width - 22.0)
        self.debug_item.setPos(10.0, self.expanded_height - 25.0)
        self.code_item.setTextWidth(self.width - 18.0)
        self.resize_handle.setPos(
            self.width - self.resize_handle.SIZE - 3.0,
            self.expanded_height - self.resize_handle.SIZE - 3.0,
        )
        for index, (name, _data_type) in enumerate(self.input_definitions):
            y = 43.0 + index * 22.0
            port = self.input_ports[name]
            port.setRect(-LogicPortItem.SIZE / 2, y - LogicPortItem.SIZE / 2, LogicPortItem.SIZE, LogicPortItem.SIZE)
            port.setTransformOriginPoint(port.boundingRect().center())
            self.port_labels[index].setPos(9.0, y - 12.0)
        output_label_offset = len(self.input_definitions)
        for index, (name, _data_type) in enumerate(self.output_definitions):
            y = 43.0 + index * 22.0
            port = self.output_ports[name]
            port.setRect(self.width - LogicPortItem.SIZE / 2, y - LogicPortItem.SIZE / 2, LogicPortItem.SIZE, LogicPortItem.SIZE)
            port.setTransformOriginPoint(port.boundingRect().center())
            label = self.port_labels[output_label_offset + index]
            label.setTextWidth(min(110.0, self.width * 0.45))
            label.setPos(self.width - min(118.0, self.width * 0.48), y - 12.0)
        body_visible = not self.collapsed
        self.flip_control.setVisible(body_visible)
        self.resize_handle.setVisible(body_visible)
        for port in (*self.input_ports.values(), *self.output_ports.values()):
            port.setVisible(body_visible and not self._show_code)
        for label in self.port_labels:
            label.setVisible(body_visible and not self._show_code)
        self.code_item.setVisible(body_visible and self._show_code)
        if self.collapsed:
            self.summary_item.hide()
            self.target_item.hide()
            self.debug_item.hide()
        else:
            self.set_runtime_state(*self._runtime_display)
        if notify:
            self.editor.refresh_connections()
            self.update()

    def refresh_text(self) -> None:
        properties = self.node.get("properties", {})
        if str(self.node.get("type", "")).startswith("event_") and self._fanout_count:
            summary = f"{self._fanout_count} ação(ões) conectada(s) • arraste para adicionar"
        elif properties:
            summary = "  •  ".join(f"{key}: {value}" for key, value in list(properties.items())[:2])
        else:
            summary = str(self.node.get("category", ""))
        self.summary_item.setPlainText(summary)
        self.code_item.setPlainText(node_code_preview(self.node))

    def set_fanout_count(self, count: int) -> None:
        self._fanout_count = max(0, int(count))
        self.refresh_text()

    def set_target_hint(self, text: str = "", implicit: bool = False) -> None:
        self._target_hint = str(text)
        self._target_is_implicit = bool(implicit)
        self.target_item.setPlainText(self._target_hint)
        self.target_item.setDefaultTextColor(QColor("#e6b85c") if implicit else QColor("#75d5df"))
        self.target_item.setToolTip(
            "Este alvo veio automaticamente do fluxo de criação anterior. Conecte a porta target para substituí-lo."
            if implicit else "Objeto que este bloco afetará"
        )
        self.target_item.setVisible(bool(text) and not self.collapsed and not self._show_code)
        self.setToolTip(self.target_item.toolTip() if text else "")

    def toggle_code_preview(self) -> None:
        self._show_code = not self._show_code
        for port in (*self.input_ports.values(), *self.output_ports.values()):
            port.setVisible(not self._show_code and not self.collapsed)
        for label in self.port_labels:
            label.setVisible(not self._show_code and not self.collapsed)
        self.target_item.setVisible(bool(self._target_hint) and not self._show_code and not self.collapsed)
        self.code_item.setVisible(self._show_code and not self.collapsed)
        self.flip_control.setToolTip(
            "Voltar para as portas do bloco" if self._show_code else "Virar bloco e mostrar o código equivalente"
        )
        if self._show_code:
            self.refresh_text()
            self.summary_item.hide()
            self.target_item.hide()
            self.debug_item.hide()
            self.setBrush(QBrush(QColor("#17221c")))
        else:
            self.setBrush(QBrush(QColor("#22242a")))
            self.set_runtime_state(*self._runtime_display)

    def set_runtime_state(
        self,
        active: bool,
        values: dict[str, Any] | None = None,
        error: str = "",
        paused: bool = False,
    ) -> None:
        self._runtime_display = (bool(active), values, str(error), bool(paused))
        if self.collapsed:
            self.summary_item.hide()
            self.target_item.hide()
            self.debug_item.hide()
            return
        if self._show_code:
            self.summary_item.hide()
            self.debug_item.hide()
            return
        visible = bool(active or error or paused)
        self.summary_item.setVisible(not visible)
        self.target_item.setVisible(bool(self._target_hint) and not visible)
        self.debug_item.setVisible(visible)
        if not visible:
            self.debug_item.setPlainText("")
            self.setPen(QPen(QColor("#515662"), 1.2))
            return
        if error:
            self.debug_item.setDefaultTextColor(QColor("#ff6b70"))
            self.debug_item.setPlainText("ERRO • " + error[:54])
            self.setPen(QPen(QColor("#ff5d62"), 3.0))
            return
        if paused:
            self.debug_item.setDefaultTextColor(QColor("#e6b85c"))
            self.debug_item.setPlainText("PAUSADO ANTES DE EXECUTAR")
            self.setPen(QPen(QColor("#e6b85c"), 4.0))
            return
        self.debug_item.setDefaultTextColor(QColor("#7ee787"))
        pairs = list((values or {}).items())[:2]
        text = " • ".join(f"{name}={value}" for name, value in pairs) if pairs else "EXECUTANDO"
        self.debug_item.setPlainText(text)
        self.setPen(QPen(QColor("#7ee787"), 3.0))

    def set_breakpoint(self, enabled: bool) -> None:
        self.breakpoint_item.setVisible(bool(enabled))

    def mouseDoubleClickEvent(self, event) -> None:
        self.editor.toggle_breakpoint(self.node_id)
        event.accept()

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
    debug_command = Signal(str)
    play_requested = Signal()
    stop_requested = Signal()
    MAGNET_RADIUS_PIXELS = 42.0

    def __init__(self, project_root: str | Path | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LogicWorkspace")
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.current_path: Path | None = None
        self.graph = default_logic_graph()
        self.node_items: dict[str, LogicNodeItem] = {}
        self.edge_items: list[LogicEdgeItem] = []
        self.group_items: dict[str, LogicGroupItem] = {}
        self.comment_items: dict[str, LogicCommentItem] = {}
        self._connection_origin: LogicPortItem | None = None
        self._connection_candidate: LogicPortItem | None = None
        self._connection_preview: QGraphicsPathItem | None = None
        self._runtime_trace_active = False
        self._palette_category = "Movimento"
        self._blackboard_selected_name = ""
        self._dirty = False
        self._updating_properties = False
        self._history: list[dict[str, Any]] = []
        self._history_index = -1
        self._restoring_history = False
        self._history_timer = QTimer(self)
        self._history_timer.setSingleShot(True)
        self._history_timer.setInterval(180)
        self._history_timer.timeout.connect(self._capture_history)
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
        self.debug_status_label = QLabel("● DEBUG INATIVO")
        self.debug_status_label.setObjectName("WorkspaceContext")
        title_row.addWidget(self.debug_status_label)
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
        self.new_subgraph_button = QPushButton("Novo subgrafo")
        self.new_subgraph_button.setToolTip("Cria uma função visual reutilizável com entrada e retorno")
        toolbar.addWidget(self.new_subgraph_button)
        self.demo_button = QPushButton("Abrir exemplo Player")
        self.demo_button.setIcon(editor_icon("open"))
        self.demo_button.setProperty("uiRole", "primary")
        toolbar.addWidget(self.demo_button)
        toolbar.addSpacing(8)
        self.play_button = QPushButton("Play")
        self.play_button.setIcon(editor_icon("play"))
        self.play_button.setProperty("uiRole", "primary")
        self.play_button.setToolTip("Salva o grafo atual e inicia o Play Mode")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setIcon(editor_icon("stop"))
        self.stop_button.setProperty("uiRole", "danger")
        self.stop_button.setToolTip("Interrompe o Play Mode e restaura a cena")
        self.stop_button.setEnabled(False)
        toolbar.addWidget(self.play_button)
        toolbar.addWidget(self.stop_button)
        toolbar.addSpacing(12)
        self.graph_enabled_check = QCheckBox("Ativo no Play")
        self.graph_enabled_check.setChecked(True)
        self.graph_enabled_check.setToolTip("Desative para preservar o asset sem executá-lo")
        toolbar.addWidget(self.graph_enabled_check)
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
        self.undo_button = QPushButton("Desfazer")
        self.redo_button = QPushButton("Refazer")
        self.undo_button.setShortcut("Ctrl+Z")
        self.redo_button.setShortcut("Ctrl+Y")
        self.undo_button.setEnabled(False)
        self.redo_button.setEnabled(False)
        self.breakpoint_button = QPushButton("● Breakpoint")
        self.breakpoint_button.setToolTip("Alterna um breakpoint no nó selecionado (duplo clique também funciona)")
        self.continue_debug_button = QPushButton("Continuar")
        self.step_debug_button = QPushButton("Próximo nó")
        self.restart_debug_button = QPushButton("Reiniciar")
        self.continue_debug_button.setEnabled(False)
        self.step_debug_button.setEnabled(False)
        self.restart_debug_button.setEnabled(False)
        self.connect_button = QPushButton("Conectar selecionados")
        self.delete_button = QPushButton("Excluir selecionado")
        self.delete_button.setProperty("uiRole", "danger")
        toolbar.addWidget(self.fit_button)
        toolbar.addWidget(self.undo_button)
        toolbar.addWidget(self.redo_button)
        toolbar.addWidget(self.breakpoint_button)
        toolbar.addWidget(self.continue_debug_button)
        toolbar.addWidget(self.step_debug_button)
        toolbar.addWidget(self.restart_debug_button)
        toolbar.addWidget(self.connect_button)
        toolbar.addWidget(self.delete_button)
        root.addWidget(toolbar_widget)

        category_widget = QWidget()
        category_widget.setObjectName("LogicCategories")
        categories = QHBoxLayout(category_widget)
        categories.setContentsMargins(4, 4, 4, 4)
        categories.setSpacing(6)
        categories.addWidget(QLabel("Categoria"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(("Movimento", "Posição", "Ação", "Lógica", "Condição", "Eventos", "Objetos", "Variáveis", "Matemática", "Texto", "Subgrafos", "Todos"))
        self.category_combo.setMinimumWidth(150)
        self.category_combo.setToolTip("Filtra a biblioteca de blocos por categoria")
        categories.addWidget(self.category_combo)
        self.add_group_button = QPushButton("+ Grupo")
        self.add_comment_button = QPushButton("+ Comentário")
        self.organize_button = QPushButton("Organizar grafo")
        self.align_button = QPushButton("Alinhar")
        self.distribute_button = QPushButton("Distribuir")
        categories.addWidget(self.add_group_button)
        categories.addWidget(self.add_comment_button)
        categories.addWidget(self.organize_button)
        categories.addWidget(self.align_button)
        categories.addWidget(self.distribute_button)
        categories.addStretch(1)
        root.addWidget(category_widget)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("LogicContentSplitter")
        splitter.setChildrenCollapsible(False)

        palette_panel = QFrame()
        palette_panel.setObjectName("LogicPalettePanel")
        palette_layout = QVBoxLayout(palette_panel)
        palette_layout.setContentsMargins(8, 8, 8, 8)
        self.library_tabs = QTabWidget()
        self.library_tabs.setObjectName("LogicLibraryTabs")
        palette_layout.addWidget(self.library_tabs, 1)

        blocks_page = QWidget()
        blocks_layout = QVBoxLayout(blocks_page)
        blocks_layout.setContentsMargins(5, 6, 5, 6)
        blocks_layout.setSpacing(6)
        self.node_search = QLineEdit()
        self.node_search.setPlaceholderText("Pesquisar blocos...  ex.: colisão, som, somar")
        self.node_search.setClearButtonEnabled(True)
        blocks_layout.addWidget(self.node_search)
        self.palette = QListWidget()
        self.palette.setObjectName("LogicNodePalette")
        self.palette.setToolTip("Duplo clique para adicionar um nó")
        blocks_layout.addWidget(self.palette, 1)
        self.palette_count = QLabel()
        self.palette_count.setObjectName("PanelHint")
        blocks_layout.addWidget(self.palette_count)
        blocks_hint = QLabel("Duplo clique adiciona o bloco. Arraste uma porta para conectar.")
        blocks_hint.setObjectName("PanelHint")
        blocks_hint.setWordWrap(True)
        blocks_layout.addWidget(blocks_hint)
        self.library_tabs.addTab(blocks_page, "Blocos")

        recipes_page = QWidget()
        recipes_layout = QVBoxLayout(recipes_page)
        recipes_layout.setContentsMargins(5, 6, 5, 6)
        recipes_layout.setSpacing(6)
        self.recipe_topic_label = QLabel("Receitas de Movimento")
        self.recipe_topic_label.setObjectName("PanelSectionTitle")
        recipes_layout.addWidget(self.recipe_topic_label)
        self.recipe_search = QLineEdit()
        self.recipe_search.setPlaceholderText("O que você quer fazer? ex.: mover sozinho")
        self.recipe_search.setClearButtonEnabled(True)
        recipes_layout.addWidget(self.recipe_search)
        self.recipe_list = QListWidget()
        self.recipe_list.setToolTip("Escolha uma lógica pronta para aprender e inserir")
        recipes_layout.addWidget(self.recipe_list, 1)
        self.recipe_summary = QLabel("Escolha uma receita para ver como ela funciona.")
        self.recipe_summary.setObjectName("PanelHint")
        self.recipe_summary.setWordWrap(True)
        recipes_layout.addWidget(self.recipe_summary)
        self.recipe_apply_button = QPushButton("Inserir receita no grafo")
        self.recipe_apply_button.setProperty("uiRole", "primary")
        self.recipe_apply_button.setEnabled(False)
        recipes_layout.addWidget(self.recipe_apply_button)
        self.library_tabs.addTab(recipes_page, "Receitas")

        subgraphs_page = QWidget()
        subgraphs_layout = QVBoxLayout(subgraphs_page)
        subgraphs_layout.setContentsMargins(5, 6, 5, 6)
        subgraphs_layout.setSpacing(6)
        self.subgraph_list = QListWidget()
        self.subgraph_list.setToolTip("Duplo clique adiciona uma chamada ao subgrafo")
        subgraphs_layout.addWidget(self.subgraph_list, 1)
        subgraph_hint = QLabel("Funções visuais reutilizáveis salvas em Assets/Logic.")
        subgraph_hint.setObjectName("PanelHint")
        subgraph_hint.setWordWrap(True)
        subgraphs_layout.addWidget(subgraph_hint)
        self.library_tabs.addTab(subgraphs_page, "Subgrafos")

        data_page = QWidget()
        data_layout = QVBoxLayout(data_page)
        data_layout.setContentsMargins(5, 6, 5, 6)
        data_layout.setSpacing(6)
        self.blackboard_tree = QTreeWidget()
        self.blackboard_tree.setHeaderLabels(["Nome", "Tipo", "Escopo"])
        data_layout.addWidget(self.blackboard_tree, 1)
        self.blackboard_name_edit = QLineEdit()
        self.blackboard_name_edit.setPlaceholderText("nome_da_variável")
        data_layout.addWidget(self.blackboard_name_edit)
        blackboard_options = QHBoxLayout()
        self.blackboard_type_combo = QComboBox()
        for label, value in (("Número", "number"), ("Booleano", "bool"), ("Texto", "text"), ("Objeto", "object")):
            self.blackboard_type_combo.addItem(label, value)
        self.blackboard_scope_combo = QComboBox()
        for label, value in (("Objeto", "object"), ("Cena", "scene"), ("Projeto", "project")):
            self.blackboard_scope_combo.addItem(label, value)
        blackboard_options.addWidget(self.blackboard_type_combo)
        blackboard_options.addWidget(self.blackboard_scope_combo)
        data_layout.addLayout(blackboard_options)
        self.blackboard_default_edit = QLineEdit("0")
        self.blackboard_default_edit.setPlaceholderText("Valor inicial")
        data_layout.addWidget(self.blackboard_default_edit)
        blackboard_edit_actions = QHBoxLayout()
        self.blackboard_save_button = QPushButton("Adicionar")
        self.blackboard_remove_button = QPushButton("Excluir")
        blackboard_edit_actions.addWidget(self.blackboard_save_button)
        blackboard_edit_actions.addWidget(self.blackboard_remove_button)
        data_layout.addLayout(blackboard_edit_actions)
        blackboard_node_actions = QHBoxLayout()
        self.blackboard_get_button = QPushButton("Ler")
        self.blackboard_set_button = QPushButton("Definir")
        blackboard_node_actions.addWidget(self.blackboard_get_button)
        blackboard_node_actions.addWidget(self.blackboard_set_button)
        data_layout.addLayout(blackboard_node_actions)
        data_hint = QLabel("Variáveis organizadas por objeto, cena ou projeto.")
        data_hint.setObjectName("PanelHint")
        data_hint.setWordWrap(True)
        data_layout.addWidget(data_hint)
        self.library_tabs.addTab(data_page, "Dados")
        palette_panel.setMinimumWidth(230)
        splitter.addWidget(palette_panel)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-2000.0, -1400.0, 4000.0, 2800.0)
        canvas_panel = QWidget()
        canvas_layout = QVBoxLayout(canvas_panel)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(3)
        self.view = LogicGraphView(self.scene, self)
        canvas_layout.addWidget(self.view, 1)
        minimap_row = QHBoxLayout()
        minimap_row.addStretch(1)
        self.minimap = LogicMiniMapView(self.scene, self)
        minimap_row.addWidget(self.minimap)
        canvas_layout.addLayout(minimap_row)
        splitter.addWidget(canvas_panel)

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
        self.property_asset_button = QPushButton("Selecionar asset do projeto...")
        self.property_asset_button.setToolTip("Vincula uma imagem, animação ou som da pasta Assets")
        self.property_asset_button.hide()
        properties_layout.addWidget(self.property_asset_button)
        self.breakpoint_condition_label = QLabel("CONDIÇÃO DO BREAKPOINT")
        self.breakpoint_condition_label.setObjectName("PanelSectionTitle")
        properties_layout.addWidget(self.breakpoint_condition_label)
        self.breakpoint_condition_edit = QLineEdit()
        self.breakpoint_condition_edit.setPlaceholderText("Ex.: vida <= 0 ou estado == andando")
        self.breakpoint_condition_edit.setEnabled(False)
        properties_layout.addWidget(self.breakpoint_condition_edit)
        self.runtime_values_title = QLabel("VALORES EM EXECUÇÃO")
        self.runtime_values_title.setObjectName("PanelSectionTitle")
        self.runtime_values_title.hide()
        properties_layout.addWidget(self.runtime_values_title)
        self.runtime_values_tree = QTreeWidget()
        self.runtime_values_tree.setHeaderLabels(["Nó / variável", "Valor"])
        self.runtime_values_tree.setMaximumHeight(155)
        self.runtime_values_tree.hide()
        properties_layout.addWidget(self.runtime_values_tree)
        watch_title = QLabel("OBSERVADORES")
        watch_title.setObjectName("PanelSectionTitle")
        properties_layout.addWidget(watch_title)
        self.watch_values_tree = QTreeWidget()
        self.watch_values_tree.setHeaderLabels(["Expressão", "Valor"])
        self.watch_values_tree.setMaximumHeight(135)
        properties_layout.addWidget(self.watch_values_tree)
        watch_row = QHBoxLayout()
        self.watch_expression_edit = QLineEdit()
        self.watch_expression_edit.setPlaceholderText("vida, x, grounded...")
        self.add_watch_button = QPushButton("+")
        self.add_watch_button.setToolTip("Adicionar observador")
        self.remove_watch_button = QPushButton("−")
        self.remove_watch_button.setToolTip("Remover observador selecionado")
        watch_row.addWidget(self.watch_expression_edit, 1)
        watch_row.addWidget(self.add_watch_button)
        watch_row.addWidget(self.remove_watch_button)
        properties_layout.addLayout(watch_row)
        property_hint = QLabel(
            "Delete remove, Ctrl+D duplica e Esc cancela uma conexão. "
            "Use −/+ no bloco para recolher e a alça inferior para redimensionar."
        )
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
        self._refresh_recipes("")

    def _connect_ui(self) -> None:
        self.category_combo.currentTextChanged.connect(self._category_changed)
        self.node_search.textChanged.connect(lambda _text: self._refresh_palette())
        self.palette.itemDoubleClicked.connect(self._add_palette_item)
        self.recipe_search.textChanged.connect(lambda text: self._refresh_recipes(text))
        self.recipe_list.currentItemChanged.connect(self._recipe_selection_changed)
        self.recipe_list.itemDoubleClicked.connect(lambda _item: self._insert_selected_recipe())
        self.recipe_apply_button.clicked.connect(self._insert_selected_recipe)
        self.subgraph_list.itemDoubleClicked.connect(self._add_subgraph_asset)
        self.scene.selectionChanged.connect(self._selection_changed)
        self.property_tree.itemChanged.connect(self._property_changed)
        self.property_asset_button.clicked.connect(self._choose_selected_node_asset)
        self.new_button.clicked.connect(self.new_graph)
        self.new_subgraph_button.clicked.connect(self.new_subgraph)
        self.open_button.clicked.connect(self.open_dialog)
        self.save_button.clicked.connect(self.save)
        self.save_as_button.clicked.connect(lambda: self.save(save_as=True))
        self.demo_button.clicked.connect(self.open_demo)
        self.play_button.clicked.connect(self.request_play)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.fit_button.clicked.connect(self.fit_graph)
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)
        self.add_group_button.clicked.connect(self.add_group)
        self.add_comment_button.clicked.connect(self.add_comment)
        self.organize_button.clicked.connect(self.organize_graph)
        self.align_button.clicked.connect(self.align_selected)
        self.distribute_button.clicked.connect(self.distribute_selected)
        self.breakpoint_button.clicked.connect(self.toggle_selected_breakpoint)
        self.continue_debug_button.clicked.connect(lambda: self.debug_command.emit("continue"))
        self.step_debug_button.clicked.connect(lambda: self.debug_command.emit("step"))
        self.restart_debug_button.clicked.connect(lambda: self.debug_command.emit("restart"))
        self.breakpoint_condition_edit.editingFinished.connect(self._update_breakpoint_condition)
        self.add_watch_button.clicked.connect(self._add_watch)
        self.remove_watch_button.clicked.connect(self._remove_watch)
        self.watch_expression_edit.returnPressed.connect(self._add_watch)
        self.blackboard_tree.itemSelectionChanged.connect(self._select_blackboard_variable)
        self.blackboard_tree.itemDoubleClicked.connect(lambda _item, _column: self._add_blackboard_node("get_variable"))
        self.blackboard_save_button.clicked.connect(self._save_blackboard_variable)
        self.blackboard_remove_button.clicked.connect(self._remove_blackboard_variable)
        self.blackboard_get_button.clicked.connect(lambda: self._add_blackboard_node("get_variable"))
        self.blackboard_set_button.clicked.connect(lambda: self._add_blackboard_node("set_variable"))
        self.connect_button.clicked.connect(self.connect_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.target_type.currentIndexChanged.connect(lambda _index: (self.mark_dirty(), self._refresh_target_hints()))
        self.target_value.textChanged.connect(lambda _text: (self.mark_dirty(), self._refresh_target_hints()))
        self.graph_enabled_check.toggled.connect(lambda _checked: self.mark_dirty())

    @staticmethod
    def _search_key(value: Any) -> str:
        normalized = unicodedata.normalize("NFKD", str(value).casefold())
        return "".join(character for character in normalized if not unicodedata.combining(character))

    def _refresh_palette(self, category: str | None = None) -> None:
        if category is not None:
            self._palette_category = category
        query = self._search_key(self.node_search.text()).strip()
        self.palette.clear()
        for node_type, definition in NODE_DEFINITIONS.items():
            node_category = str(definition.get("category", "Personalizado"))
            searchable = self._search_key(
                f"{definition.get('title', '')} {node_category} {node_type} "
                f"{' '.join(str(key) for key in definition.get('properties', {}))} "
                f"{NODE_DESCRIPTIONS.get(node_type, '')}"
            )
            if query:
                if query not in searchable:
                    continue
            elif self._palette_category != "Todos" and node_category != self._palette_category:
                continue
            label = str(definition["title"])
            if query:
                label = f"{label}  —  {node_category}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, node_type)
            description = NODE_DESCRIPTIONS.get(node_type, "Arraste as portas para conectar este bloco ao fluxo.")
            item.setToolTip(f"{node_category} • {description}")
            self.palette.addItem(item)
        self.palette_count.setText(f"{self.palette.count()} bloco(s)" + (" encontrados" if query else " nesta categoria"))

    def _add_palette_item(self, item: QListWidgetItem) -> None:
        node_type = str(item.data(Qt.UserRole))
        if node_type in UNIQUE_EVENT_TYPES:
            existing = next(
                (node_item for node_item in self.node_items.values() if node_item.node.get("type") == node_type),
                None,
            )
            if existing is not None:
                self.scene.clearSelection()
                existing.setSelected(True)
                self.view.centerOn(existing)
                self.message.emit(
                    "INFO",
                    "Esse evento já existe; conecte outra ação usando a mesma saída",
                )
                return
        center = self.view.mapToScene(self.view.viewport().rect().center())
        offset = len(self.node_items) * 18.0
        node = create_logic_node(node_type, (center.x() + offset, center.y() + offset))
        self.graph["nodes"].append(node)
        self._create_node_item(node)
        self.mark_dirty()
        self._update_validation()

    def _category_changed(self, category: str) -> None:
        self._refresh_palette(category)
        self._refresh_recipes(self.recipe_search.text(), category)

    def _refresh_recipes(self, query: str = "", topic: str | None = None) -> None:
        selected_topic = str(topic or self.category_combo.currentText() or "Movimento")
        self.recipe_topic_label.setText(f"Receitas de {selected_topic}")
        self.recipe_list.clear()
        for recipe in find_logic_recipes(query, "" if selected_topic == "Todos" else selected_topic):
            item = QListWidgetItem(str(recipe["title"]))
            item.setData(Qt.UserRole, str(recipe["id"]))
            item.setToolTip(f"{recipe['category']} • {recipe['summary']}")
            self.recipe_list.addItem(item)
        if self.recipe_list.count():
            self.recipe_list.setCurrentRow(0)
        else:
            self.recipe_summary.setText(
                f"Nenhuma receita de {selected_topic} encontrada. Tente outra busca ou escolha outro tópico."
            )
            self.recipe_apply_button.setEnabled(False)

    def _recipe_selection_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        recipe_id = str(current.data(Qt.UserRole)) if current is not None else ""
        if not recipe_id:
            self.recipe_apply_button.setEnabled(False)
            return
        recipe = logic_recipe(recipe_id)
        steps = "\n".join(f"{index}. {step}" for index, step in enumerate(recipe["steps"], 1))
        self.recipe_summary.setText(f"{recipe['summary']}\n\n{steps}")
        self.recipe_apply_button.setEnabled(True)

    def _insert_selected_recipe(self) -> None:
        current = self.recipe_list.currentItem()
        recipe_id = str(current.data(Qt.UserRole)) if current is not None else ""
        if not recipe_id:
            return
        center = self.view.mapToScene(self.view.viewport().rect().center())
        fragment = build_logic_recipe(recipe_id, (center.x(), center.y()))
        merged, reused_events = merge_logic_fragment(self.graph_data(), fragment)
        current_path = self.current_path
        self.set_graph(merged, current_path)
        self.mark_dirty()
        recipe = logic_recipe(recipe_id)
        reused_message = f" • {reused_events} evento(s) reutilizado(s)" if reused_events else ""
        self.message.emit("INFO", f"Receita inserida: {recipe['title']}{reused_message}")

    def _refresh_subgraph_assets(self) -> None:
        self.subgraph_list.clear()
        directory = self.project_root / "Assets" / "Logic"
        if not directory.is_dir():
            return
        for path in sorted(directory.rglob("*.zlogic"), key=lambda entry: str(entry).casefold()):
            try:
                if self.current_path is not None and path.resolve() == self.current_path.resolve():
                    continue
                graph = load_logic_graph(path)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            if not any(node.get("type") == "subgraph_start" for node in graph.get("nodes", [])):
                continue
            interface = subgraph_interface(graph)
            item = QListWidgetItem(
                f"{graph.get('name', path.stem)}  ·  {len(interface['inputs'])} entrada(s) / {len(interface['outputs'])} saída(s)"
            )
            item.setData(Qt.UserRole, path.relative_to(self.project_root).as_posix())
            item.setData(Qt.UserRole + 1, interface)
            item.setToolTip(path.relative_to(self.project_root).as_posix())
            self.subgraph_list.addItem(item)

    def _add_subgraph_asset(self, item: QListWidgetItem) -> None:
        path = str(item.data(Qt.UserRole) or "").strip()
        interface = item.data(Qt.UserRole + 1)
        if not path or not isinstance(interface, dict):
            return
        center = self.view.mapToScene(self.view.viewport().rect().center())
        node = create_logic_node("call_subgraph", (center.x(), center.y()))
        node["title"] = f"Executar {Path(path).stem}"
        node["properties"] = {
            "path": path,
            "inputs": deepcopy(interface.get("inputs", [])),
            "outputs": deepcopy(interface.get("outputs", [])),
        }
        self.graph["nodes"].append(node)
        self.scene.clearSelection()
        self._create_node_item(node).setSelected(True)
        self.mark_dirty()
        self._update_validation()
        self.message.emit("INFO", f"Subgrafo adicionado: {Path(path).stem}")

    def _sync_subgraph_call_interfaces(self, graph: dict[str, Any]) -> None:
        """Mantém chamadas existentes alinhadas ao asset reutilizável salvo."""
        for node in graph.get("nodes", []):
            if node.get("type") != "call_subgraph":
                continue
            properties = node.setdefault("properties", {})
            path = Path(str(properties.get("path", "")))
            if not path.is_absolute():
                path = self.project_root / path
            try:
                resolved = path.resolve()
                if not resolved.is_relative_to(self.project_root) or not resolved.is_file():
                    continue
                interface = subgraph_interface(load_logic_graph(resolved))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            properties["inputs"] = deepcopy(interface["inputs"])
            properties["outputs"] = deepcopy(interface["outputs"])

    def _create_node_item(self, node: dict[str, Any]) -> LogicNodeItem:
        item = LogicNodeItem(self, node)
        self.scene.addItem(item)
        self.node_items[item.node_id] = item
        return item

    def _create_group_item(self, data: dict[str, Any]) -> LogicGroupItem:
        item = LogicGroupItem(self, data)
        self.scene.addItem(item)
        self.group_items[item.group_id] = item
        return item

    def _create_comment_item(self, data: dict[str, Any]) -> LogicCommentItem:
        item = LogicCommentItem(self, data)
        self.scene.addItem(item)
        self.comment_items[item.comment_id] = item
        return item

    def set_graph(self, graph: dict[str, Any], path: Path | None = None, *, reset_history: bool = True) -> None:
        self.clear_runtime_trace()
        self.cancel_connection()
        self._autosave_timer.stop()
        self.graph, consolidated_events = consolidate_logic_events(graph)
        self._sync_subgraph_call_interfaces(self.graph)
        self.graph_enabled_check.blockSignals(True)
        self.graph_enabled_check.setChecked(bool(self.graph.get("enabled", True)))
        self.graph_enabled_check.blockSignals(False)
        self._blackboard_selected_name = ""
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
        self.group_items.clear()
        self.comment_items.clear()
        editor_layout = self.graph.get("editor", {})
        for group in editor_layout.get("groups", []):
            self._create_group_item(group)
        for comment in editor_layout.get("comments", []):
            self._create_comment_item(comment)
        for node in self.graph["nodes"]:
            self._create_node_item(node)
        for node_id in self.graph.get("debug", {}).get("breakpoints", []):
            if node_id in self.node_items:
                self.node_items[node_id].set_breakpoint(True)
        self._refresh_watch_values()
        self._refresh_blackboard_variables()
        self._refresh_subgraph_assets()
        self.refresh_connections()
        self._dirty = bool(consolidated_events and path is not None)
        self._update_status()
        self._update_validation()
        self.fit_graph()
        self.minimap.refresh()
        if reset_history:
            self._reset_history()
        if consolidated_events:
            self.message.emit(
                "INFO",
                f"{consolidated_events} evento(s) duplicado(s) unificado(s); conexões preservadas",
            )

    def apply_runtime_trace(self, trace: dict[str, Any]) -> None:
        """Aplica um snapshot limitado enviado pelo processo da Viewport."""
        if self.current_path is None or not self.isVisible():
            return
        graph_value = str(trace.get("graph", ""))
        if not graph_value:
            return
        graph_path = Path(graph_value)
        if not graph_path.is_absolute():
            graph_path = self.project_root / graph_path
        try:
            if graph_path.resolve() != self.current_path.resolve():
                return
        except OSError:
            if graph_path.name != self.current_path.name:
                return

        active_node_list = [str(node_id) for node_id in trace.get("nodes", [])]
        active_nodes = set(active_node_list)
        active_edges = {str(edge_id) for edge_id in trace.get("edges", [])}
        values = trace.get("values", {}) if isinstance(trace.get("values"), dict) else {}
        variables = trace.get("variables", {}) if isinstance(trace.get("variables"), dict) else {}
        blackboard = trace.get("blackboard", {}) if isinstance(trace.get("blackboard"), dict) else {}
        events = trace.get("events", []) if isinstance(trace.get("events"), list) else []
        watches = trace.get("watches", {}) if isinstance(trace.get("watches"), dict) else {}
        paused = bool(trace.get("paused", False))
        pause_node = str(trace.get("pause_node", ""))
        breakpoints = {str(node_id) for node_id in trace.get("breakpoints", [])}
        error = str(trace.get("error", ""))
        error_node = active_node_list[-1] if error and active_node_list else ""
        self._runtime_trace_active = True
        self._update_validation()
        for node_id, item in self.node_items.items():
            item.set_breakpoint(node_id in breakpoints or node_id in self.graph.get("debug", {}).get("breakpoints", []))
            item.set_runtime_state(
                node_id in active_nodes,
                values.get(node_id) if isinstance(values.get(node_id), dict) else {},
                error if node_id == error_node else "",
                paused=node_id == pause_node and paused,
            )
        for edge in self.edge_items:
            edge.set_runtime_active(edge.edge_id in active_edges)

        object_name = str(trace.get("object", "Objeto"))
        if error:
            self.debug_status_label.setText(f"● ERRO • {object_name}")
            self.debug_status_label.setStyleSheet("color: #ff6b70; font-weight: 700;")
        elif paused:
            paused_item = self.node_items.get(pause_node)
            paused_title = str(paused_item.node.get("title", pause_node)) if paused_item is not None else pause_node
            condition_error = str(trace.get("condition_error", ""))
            if condition_error:
                self.debug_status_label.setText(f"● CONDIÇÃO INVÁLIDA • {condition_error}")
                self.debug_status_label.setStyleSheet("color: #ff6b70; font-weight: 700;")
            else:
                self.debug_status_label.setText(f"● PAUSADO • {object_name} • {paused_title}")
                self.debug_status_label.setStyleSheet("color: #e6b85c; font-weight: 700;")
        else:
            self.debug_status_label.setText(f"● PLAY • {object_name} • {len(active_nodes)} nó(s)")
            self.debug_status_label.setStyleSheet("color: #7ee787; font-weight: 700;")
        self.continue_debug_button.setEnabled(paused)
        self.step_debug_button.setEnabled(paused)
        self.restart_debug_button.setEnabled(paused)

        self.runtime_values_tree.clear()
        for node_id, port_values in values.items():
            node = self.node_items.get(str(node_id))
            title = str(node.node.get("title", node_id)) if node is not None else str(node_id)
            if not isinstance(port_values, dict):
                continue
            for port, value in port_values.items():
                self.runtime_values_tree.addTopLevelItem(QTreeWidgetItem([f"{title}.{port}", str(value)]))
        if blackboard:
            for scope, scope_values in blackboard.items():
                if not isinstance(scope_values, dict):
                    continue
                for name, value in scope_values.items():
                    self.runtime_values_tree.addTopLevelItem(QTreeWidgetItem([f"{scope}.{name}", str(value)]))
        else:
            for name, value in variables.items():
                self.runtime_values_tree.addTopLevelItem(QTreeWidgetItem([f"${name}", str(value)]))
        for event in events[-4:]:
            if isinstance(event, dict):
                source = str(event.get("source", ""))
                label = f"evento:{event.get('name', '')}" + (f" ({source})" if source else "")
                self.runtime_values_tree.addTopLevelItem(QTreeWidgetItem([label, str(event.get("payload"))]))
        has_values = self.runtime_values_tree.topLevelItemCount() > 0
        self.runtime_values_title.setVisible(has_values)
        self.runtime_values_tree.setVisible(has_values)
        self._refresh_watch_values(watches)

    def clear_runtime_trace(self) -> None:
        self._runtime_trace_active = False
        if hasattr(self, "debug_status_label"):
            self.debug_status_label.setText("● DEBUG INATIVO")
            self.debug_status_label.setStyleSheet("")
        if hasattr(self, "runtime_values_tree"):
            self.runtime_values_tree.clear()
            self.runtime_values_tree.hide()
            self.runtime_values_title.hide()
        if hasattr(self, "continue_debug_button"):
            self.continue_debug_button.setEnabled(False)
            self.step_debug_button.setEnabled(False)
            self.restart_debug_button.setEnabled(False)
        if hasattr(self, "watch_values_tree"):
            self._refresh_watch_values()
        for item in self.node_items.values():
            item.set_runtime_state(False)
        for edge in self.edge_items:
            edge.set_runtime_active(False)
        if hasattr(self, "validation_label"):
            self._update_validation()

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
        fanout_counts: dict[str, int] = {}
        port_counts: dict[tuple[str, str], int] = {}
        for edge in self.graph.get("edges", []):
            node_id = str(edge.get("from_node", ""))
            port_name = str(edge.get("from_port", "next"))
            port_counts[(node_id, port_name)] = port_counts.get((node_id, port_name), 0) + 1
            if str(edge.get("kind", "flow")) == "flow":
                fanout_counts[node_id] = fanout_counts.get(node_id, 0) + 1
        for node_id, item in self.node_items.items():
            item.set_fanout_count(fanout_counts.get(node_id, 0))
            for port_name, port in item.output_ports.items():
                count = port_counts.get((node_id, port_name), 0)
                if port.data_type == "flow":
                    port.setToolTip(
                        f"{count} conexão(ões) • arraste novamente para adicionar outra ação"
                        if count
                        else "Arraste para conectar uma ou várias ações"
                    )
        self._refresh_target_hints()
        if hasattr(self, "minimap"):
            self.minimap.refresh()

    def _refresh_target_hints(self) -> None:
        """Explica visualmente qual referência de objeto percorre cada fluxo."""
        creators = {"create_object", "create_prefab", "clone_object"}
        nodes = {str(node.get("id")): node for node in self.graph.get("nodes", [])}
        flow_next: dict[str, list[str]] = {}
        explicit_targets: set[str] = set()
        for edge in self.graph.get("edges", []):
            source_id = str(edge.get("from_node", ""))
            target_id = str(edge.get("to_node", ""))
            source_item = self.node_items.get(source_id)
            source_port = source_item.output_ports.get(str(edge.get("from_port", "next"))) if source_item else None
            kind = source_port.data_type if source_port is not None else str(edge.get("kind", "flow"))
            if kind == "flow":
                flow_next.setdefault(source_id, []).append(target_id)
            if kind == "object" and str(edge.get("to_port", "")) == "target":
                explicit_targets.add(target_id)

        implicit_sources: dict[str, set[str]] = {}

        def spread(source_id: str, label: str) -> None:
            pending = list(flow_next.get(source_id, []))
            visited: set[str] = set()
            while pending:
                node_id = pending.pop(0)
                if node_id in visited:
                    continue
                visited.add(node_id)
                implicit_sources.setdefault(node_id, set()).add(label)
                if str(nodes.get(node_id, {}).get("type", "")) in creators:
                    continue
                pending.extend(flow_next.get(node_id, []))

        for node_id, node in nodes.items():
            node_type = str(node.get("type", ""))
            properties = node.get("properties", {})
            if node_type == "create_object":
                label = str(properties.get("name", "NovoObjeto"))
                spread(node_id, label)
            elif node_type == "create_prefab":
                label = Path(str(properties.get("path", "Prefab"))).stem or "Prefab"
                spread(node_id, label)
            elif node_type == "clone_object":
                spread(node_id, str(properties.get("name", "Cópia")) or "Cópia")
            elif node_type == "event_object_created":
                spread(node_id, "objeto recém-criado")

        graph_target = str(self.graph.get("target", {}).get("value", "Player"))
        for node_id, item in self.node_items.items():
            node_type = str(nodes.get(node_id, {}).get("type", ""))
            if node_type in creators:
                properties = nodes[node_id].get("properties", {})
                created_name = (
                    Path(str(properties.get("path", ""))).stem
                    if node_type == "create_prefab"
                    else str(properties.get("name", ""))
                ) or ("Prefab" if node_type == "create_prefab" else "Nova instância")
                item.set_target_hint(f"NOVO ALVO → {created_name}", False)
                continue
            if "target" not in item.input_ports:
                item.set_target_hint()
                continue
            if node_id in explicit_targets:
                item.set_target_hint("ALVO → referência conectada", False)
                continue
            labels = implicit_sources.get(node_id, set())
            if len(labels) == 1:
                item.set_target_hint(f"ALVO IMPLÍCITO → {next(iter(labels))}", True)
            elif len(labels) > 1:
                item.set_target_hint("ALVO IMPLÍCITO → depende do fluxo", True)
            else:
                item.set_target_hint(f"ALVO ATUAL → {graph_target}", False)

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
        edge_ids = {str(item.data(0)) for item in self.scene.selectedItems() if isinstance(item, LogicEdgeItem)}
        group_ids = {item.group_id for item in self.scene.selectedItems() if isinstance(item, LogicGroupItem)}
        comment_ids = {item.comment_id for item in self.scene.selectedItems() if isinstance(item, LogicCommentItem)}
        if not node_ids and not edge_ids and not group_ids and not comment_ids:
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
        layout = self.graph.setdefault("editor", {"groups": [], "comments": []})
        layout["groups"] = [group for group in layout.get("groups", []) if str(group.get("id")) not in group_ids]
        layout["comments"] = [comment for comment in layout.get("comments", []) if str(comment.get("id")) not in comment_ids]
        for group_id in group_ids:
            item = self.group_items.pop(group_id, None)
            if item is not None:
                self.scene.removeItem(item)
        for comment_id in comment_ids:
            item = self.comment_items.pop(comment_id, None)
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

    def toggle_selected_breakpoint(self) -> None:
        selected = [item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        if len(selected) != 1:
            self.message.emit("WARNING", "Selecione um único nó para alternar o breakpoint")
            return
        self.toggle_breakpoint(selected[0].node_id)

    def toggle_breakpoint(self, node_id: str) -> None:
        item = self.node_items.get(str(node_id))
        if item is None:
            return
        ports = node_port_definitions(item.node)
        supports_flow = str(item.node.get("type", "")).startswith("event_") or any(
            data_type == "flow" for _name, data_type in ports["inputs"]
        )
        if not supports_flow:
            self.message.emit("WARNING", "Breakpoints são permitidos em nós do fluxo; valores aparecem no painel de execução")
            return
        debug = self.graph.setdefault("debug", {"breakpoints": []})
        breakpoints = [str(value) for value in debug.setdefault("breakpoints", [])]
        if item.node_id in breakpoints:
            breakpoints.remove(item.node_id)
            debug.setdefault("breakpoint_conditions", {}).pop(item.node_id, None)
            enabled = False
        else:
            breakpoints.append(item.node_id)
            enabled = True
        debug["breakpoints"] = breakpoints
        item.set_breakpoint(enabled)
        self.breakpoint_condition_edit.setEnabled(enabled)
        if not enabled:
            self.breakpoint_condition_edit.clear()
        self.mark_dirty()
        self._autosave()
        self.debug_command.emit("sync")
        self.message.emit("INFO", f"Breakpoint {'adicionado' if enabled else 'removido'}: {item.node.get('title', item.node_id)}")

    def _selection_changed(self) -> None:
        selected = [item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        self._updating_properties = True
        self.property_tree.clear()
        if len(selected) != 1:
            self.selected_label.setText("Selecione um nó para editar seus valores")
            self.property_asset_button.hide()
            self.breakpoint_condition_edit.clear()
            self.breakpoint_condition_edit.setEnabled(False)
            self._updating_properties = False
            return
        node = selected[0].node
        asset_kind = self._asset_kind_for_node(str(node.get("type", "")))
        self.property_asset_button.setVisible(asset_kind is not None)
        self.selected_label.setText(f"{node['title']}\n{node['category']} • {node['type']}")
        breakpoints = self.graph.get("debug", {}).get("breakpoints", [])
        has_breakpoint = str(node["id"]) in breakpoints
        condition = self.graph.get("debug", {}).get("breakpoint_conditions", {}).get(str(node["id"]), "")
        self.breakpoint_condition_edit.setEnabled(has_breakpoint)
        self.breakpoint_condition_edit.setText(str(condition))
        title_item = QTreeWidgetItem(["title", str(node["title"])])
        title_item.setData(0, Qt.UserRole, "title")
        title_item.setFlags(title_item.flags() | Qt.ItemIsEditable)
        self.property_tree.addTopLevelItem(title_item)
        for key, value in node.get("properties", {}).items():
            item = QTreeWidgetItem([
                NODE_PROPERTY_LABELS.get(str(node.get("type", "")), {}).get(
                    str(key), PROPERTY_LABELS.get(str(key), str(key))
                ),
                json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value,
            ])
            item.setData(0, Qt.UserRole, str(key))
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.property_tree.addTopLevelItem(item)
        self._updating_properties = False

    @staticmethod
    def _asset_kind_for_node(node_type: str) -> str | None:
        return {
            "set_sprite": "image",
            "start_texture_scroll": "image",
            "create_object": "image",
            "create_prefab": "prefab",
            "play_animation_asset": "animation",
            "play_sound": "audio",
        }.get(str(node_type))

    def _choose_selected_node_asset(self) -> None:
        selected = [item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        if len(selected) != 1:
            return
        node = selected[0].node
        kind = self._asset_kind_for_node(str(node.get("type", "")))
        if kind is None:
            return
        picker = LogicAssetPickerDialog(self.project_root, kind, self)
        if not picker.exec() or not picker.selected_path:
            return
        property_name = "texture" if str(node.get("type", "")) == "create_object" else "path"
        node.setdefault("properties", {})[property_name] = picker.selected_path
        selected[0].refresh_text()
        self._selection_changed()
        self.mark_dirty()
        self._update_validation()
        self.message.emit("INFO", f"Asset vinculado ao bloco: {picker.selected_path}")

    def _update_breakpoint_condition(self) -> None:
        selected = [item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        if len(selected) != 1 or not self.breakpoint_condition_edit.isEnabled():
            return
        node_id = selected[0].node_id
        conditions = self.graph.setdefault("debug", {}).setdefault("breakpoint_conditions", {})
        expression = self.breakpoint_condition_edit.text().strip()
        if expression:
            conditions[node_id] = expression
        else:
            conditions.pop(node_id, None)
        self.mark_dirty()
        self._autosave()
        self.debug_command.emit("sync")
        self.message.emit("INFO", f"Condição do breakpoint atualizada: {expression or 'sempre'}")

    def _add_watch(self) -> None:
        expression = self.watch_expression_edit.text().strip()
        if not expression:
            return
        watches = self.graph.setdefault("debug", {}).setdefault("watches", [])
        if expression not in watches:
            watches.append(expression)
        self.watch_expression_edit.clear()
        self._refresh_watch_values()
        self.mark_dirty()
        self._autosave()
        self.debug_command.emit("sync")

    def _remove_watch(self) -> None:
        item = self.watch_values_tree.currentItem()
        if item is None:
            return
        expression = item.text(0)
        watches = self.graph.setdefault("debug", {}).setdefault("watches", [])
        if expression in watches:
            watches.remove(expression)
        self._refresh_watch_values()
        self.mark_dirty()
        self._autosave()
        self.debug_command.emit("sync")

    def _refresh_watch_values(self, values: dict[str, Any] | None = None) -> None:
        if not hasattr(self, "watch_values_tree"):
            return
        values = values or {}
        self.watch_values_tree.clear()
        for expression in self.graph.get("debug", {}).get("watches", []):
            self.watch_values_tree.addTopLevelItem(
                QTreeWidgetItem([str(expression), str(values.get(str(expression), "—"))])
            )

    def _refresh_blackboard_variables(self) -> None:
        if not hasattr(self, "blackboard_tree"):
            return
        self.blackboard_tree.clear()
        labels = {"number": "Número", "bool": "Booleano", "text": "Texto", "object": "Objeto"}
        scopes = {"object": "Objeto", "scene": "Cena", "project": "Projeto"}
        for name, definition in self.graph.get("variables", {}).items():
            item = QTreeWidgetItem([
                str(name),
                labels.get(str(definition.get("type")), str(definition.get("type"))),
                scopes.get(str(definition.get("scope")), str(definition.get("scope"))),
            ])
            item.setData(0, Qt.UserRole, str(name))
            self.blackboard_tree.addTopLevelItem(item)

    def _select_blackboard_variable(self) -> None:
        item = self.blackboard_tree.currentItem()
        if item is None:
            return
        name = str(item.data(0, Qt.UserRole) or item.text(0))
        self._blackboard_selected_name = name
        definition = self.graph.get("variables", {}).get(name, {})
        self.blackboard_name_edit.setText(name)
        self.blackboard_type_combo.setCurrentIndex(max(0, self.blackboard_type_combo.findData(definition.get("type", "number"))))
        self.blackboard_scope_combo.setCurrentIndex(max(0, self.blackboard_scope_combo.findData(definition.get("scope", "object"))))
        default = definition.get("default")
        self.blackboard_default_edit.setText(json.dumps(default, ensure_ascii=False) if not isinstance(default, str) else default)
        self.blackboard_save_button.setText("Atualizar")

    def _save_blackboard_variable(self) -> None:
        name = self.blackboard_name_edit.text().strip()
        if not name:
            self.message.emit("WARNING", "Informe um nome para a variável")
            return
        raw_default = self.blackboard_default_edit.text().strip()
        try:
            default = json.loads(raw_default)
        except json.JSONDecodeError:
            default = raw_default
        variable_type = str(self.blackboard_type_combo.currentData() or "number")
        scope = str(self.blackboard_scope_combo.currentData() or "object")
        if self._blackboard_selected_name and self._blackboard_selected_name != name:
            self.graph.setdefault("variables", {}).pop(self._blackboard_selected_name, None)
        self.graph.setdefault("variables", {})[name] = {
            "type": variable_type,
            "scope": scope,
            "default": coerce_variable_value(default, variable_type),
        }
        self._refresh_blackboard_variables()
        self.blackboard_name_edit.clear()
        self.blackboard_default_edit.setText("0")
        self.blackboard_save_button.setText("Adicionar")
        self._blackboard_selected_name = ""
        self.mark_dirty()
        self._autosave()
        self.debug_command.emit("sync")
        self.message.emit("INFO", f"Variável criada: {scope}.{name}")

    def _remove_blackboard_variable(self) -> None:
        item = self.blackboard_tree.currentItem()
        if item is None:
            return
        name = str(item.data(0, Qt.UserRole) or item.text(0))
        self.graph.setdefault("variables", {}).pop(name, None)
        self._refresh_blackboard_variables()
        self.blackboard_name_edit.clear()
        self.blackboard_save_button.setText("Adicionar")
        self._blackboard_selected_name = ""
        self.mark_dirty()
        self._autosave()
        self.debug_command.emit("sync")
        self.message.emit("INFO", f"Variável excluída: {name}")

    def _add_blackboard_node(self, node_type: str) -> None:
        item = self.blackboard_tree.currentItem()
        if item is None:
            self.message.emit("WARNING", "Selecione uma variável do Blackboard")
            return
        name = str(item.data(0, Qt.UserRole) or item.text(0))
        definition = self.graph.get("variables", {}).get(name, {})
        center = self.view.mapToScene(self.view.viewport().rect().center())
        node = create_logic_node(node_type, (center.x(), center.y()))
        node.setdefault("properties", {}).update({"name": name, "scope": definition.get("scope", "object")})
        if node_type == "set_variable":
            node["properties"]["value"] = deepcopy(definition.get("default"))
        self.graph["nodes"].append(node)
        self.scene.clearSelection()
        self._create_node_item(node).setSelected(True)
        self.mark_dirty()
        self._update_validation()

    def _sync_project_blackboard(self) -> None:
        variables: dict[str, dict[str, Any]] = {}
        directory = self.project_root / "Assets" / "Logic"
        if directory.is_dir():
            for graph_path in sorted(directory.rglob("*.zlogic"), key=lambda item: str(item).casefold()):
                try:
                    graph = load_logic_graph(graph_path)
                except (OSError, ValueError, json.JSONDecodeError):
                    continue
                for name, definition in graph.get("variables", {}).items():
                    if isinstance(definition, dict) and definition.get("scope") == "project":
                        variables[str(name)] = deepcopy(definition)
        target = directory / "ProjectBlackboard.zblackboard"
        if variables or target.exists():
            save_blackboard_asset(target, {"variables": variables})

    def _property_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if self._updating_properties or column != 1:
            return
        selected = [entry for entry in self.scene.selectedItems() if isinstance(entry, LogicNodeItem)]
        if len(selected) != 1:
            return
        node_item = selected[0]
        key = str(item.data(0, Qt.UserRole) or item.text(0))
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
        if key == "type" and node_item.node.get("type") in {"subgraph_input", "subgraph_return"}:
            node = node_item.node
            self.scene.removeItem(node_item)
            self.node_items.pop(node_item.node_id, None)
            self.scene.clearSelection()
            self._create_node_item(node).setSelected(True)
            self.refresh_connections()
        else:
            node_item.refresh_text()
        self.mark_dirty()
        self._update_validation()

    def add_group(self) -> None:
        center = self.view.mapToScene(self.view.viewport().rect().center())
        data = {
            "id": uuid.uuid4().hex,
            "title": "Novo grupo",
            "position": [center.x() - 230.0, center.y() - 140.0],
            "size": [460.0, 280.0],
            "color": "#35506b",
        }
        self.graph.setdefault("editor", {}).setdefault("groups", []).append(data)
        self.scene.clearSelection()
        self._create_group_item(data).setSelected(True)
        self.mark_dirty()
        self.minimap.refresh()

    def add_comment(self) -> None:
        center = self.view.mapToScene(self.view.viewport().rect().center())
        text_value, accepted = QInputDialog.getMultiLineText(self, "Novo comentário", "Texto", "Explique esta parte do grafo")
        if not accepted:
            return
        data = {
            "id": uuid.uuid4().hex,
            "text": text_value,
            "position": [center.x() - 130.0, center.y() - 40.0],
            "width": 260.0,
            "color": "#6b5b2f",
        }
        self.graph.setdefault("editor", {}).setdefault("comments", []).append(data)
        self.scene.clearSelection()
        self._create_comment_item(data).setSelected(True)
        self.mark_dirty()
        self.minimap.refresh()

    def organize_graph(self) -> None:
        """Organiza o fluxo em colunas estáveis sem alterar a lógica."""
        if not self.graph.get("nodes"):
            return
        node_ids = [str(node["id"]) for node in self.graph["nodes"]]
        incoming = {node_id: 0 for node_id in node_ids}
        outgoing: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
        for edge in self.graph.get("edges", []):
            source = str(edge.get("from_node", ""))
            target = str(edge.get("to_node", ""))
            if source in outgoing and target in incoming:
                outgoing[source].append(target)
                incoming[target] += 1
        queue = [node_id for node_id in node_ids if incoming[node_id] == 0]
        levels = {node_id: 0 for node_id in queue}
        visited: list[str] = []
        while queue:
            node_id = queue.pop(0)
            visited.append(node_id)
            for target in outgoing[node_id]:
                levels[target] = max(levels.get(target, 0), levels[node_id] + 1)
                incoming[target] -= 1
                if incoming[target] == 0:
                    queue.append(target)
        for node_id in node_ids:
            if node_id not in visited:
                levels[node_id] = max(levels.values(), default=0) + 1
        rows: dict[int, list[str]] = {}
        for node_id in node_ids:
            rows.setdefault(levels.get(node_id, 0), []).append(node_id)
        for level, ids in sorted(rows.items()):
            for row, node_id in enumerate(ids):
                self.node_items[node_id].setPos(80.0 + level * 290.0, 80.0 + row * 170.0)
        self.refresh_connections()
        self.mark_dirty()
        self.fit_graph()
        self.message.emit("INFO", "Grafo organizado por ordem de execução")

    def align_selected(self) -> None:
        selected = [item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        if len(selected) < 2:
            self.message.emit("WARNING", "Selecione dois ou mais blocos para alinhar")
            return
        x = min(item.pos().x() for item in selected)
        for item in selected:
            item.setPos(x, item.pos().y())
        self.mark_dirty()

    def distribute_selected(self) -> None:
        selected = sorted(
            (item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)),
            key=lambda item: item.pos().y(),
        )
        if len(selected) < 3:
            self.message.emit("WARNING", "Selecione três ou mais blocos para distribuir")
            return
        top, bottom = selected[0].pos().y(), selected[-1].pos().y()
        spacing = (bottom - top) / (len(selected) - 1)
        for index, item in enumerate(selected):
            item.setPos(item.pos().x(), top + index * spacing)
        self.mark_dirty()

    def _reset_history(self) -> None:
        if self._restoring_history:
            return
        self._history_timer.stop()
        self._history = [self.graph_data()]
        self._history_index = 0
        self._update_history_actions()

    def _capture_history(self) -> None:
        if self._restoring_history:
            return
        snapshot = self.graph_data()
        if self._history and snapshot == self._history[self._history_index]:
            return
        self._history = self._history[: self._history_index + 1]
        self._history.append(snapshot)
        if len(self._history) > 80:
            self._history.pop(0)
        self._history_index = len(self._history) - 1
        self._update_history_actions()

    def _update_history_actions(self) -> None:
        if hasattr(self, "undo_button"):
            self.undo_button.setEnabled(self._history_index > 0)
            self.redo_button.setEnabled(0 <= self._history_index < len(self._history) - 1)

    def undo(self) -> None:
        self._capture_history()
        if self._history_index <= 0:
            return
        self._history_index -= 1
        self._restore_history_snapshot()

    def redo(self) -> None:
        self._capture_history()
        if self._history_index >= len(self._history) - 1:
            return
        self._history_index += 1
        self._restore_history_snapshot()

    def _restore_history_snapshot(self) -> None:
        snapshot = deepcopy(self._history[self._history_index])
        self._restoring_history = True
        try:
            self.set_graph(snapshot, self.current_path, reset_history=False)
            self._dirty = True
            self._update_status()
            self._autosave_timer.start()
        finally:
            self._restoring_history = False
        self._update_history_actions()
        self.message.emit("INFO", "Histórico do grafo restaurado")

    def graph_data(self) -> dict[str, Any]:
        for node_id, item in self.node_items.items():
            item.node["position"] = [round(item.pos().x(), 2), round(item.pos().y(), 2)]
        for item in self.group_items.values():
            item.data["position"] = [round(item.pos().x(), 2), round(item.pos().y(), 2)]
        for item in self.comment_items.values():
            item.data["position"] = [round(item.pos().x(), 2), round(item.pos().y(), 2)]
        data = deepcopy(self.graph)
        data["enabled"] = self.graph_enabled_check.isChecked()
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

    def new_subgraph(self) -> None:
        if not self._confirm_discard():
            return
        start = create_logic_node("subgraph_start", (80.0, 100.0))
        entry = create_logic_node("subgraph_input", (80.0, 260.0))
        result = create_logic_node("subgraph_return", (390.0, 100.0))
        graph = default_logic_graph("NovoSubgrafo")
        graph["nodes"] = [start, entry, result]
        graph["edges"] = [
            {
                "id": uuid.uuid4().hex,
                "from_node": start["id"], "from_port": "next",
                "to_node": result["id"], "to_port": "in", "kind": "flow",
            },
            {
                "id": uuid.uuid4().hex,
                "from_node": entry["id"], "from_port": "value",
                "to_node": result["id"], "to_port": "value", "kind": "number",
            },
        ]
        self.set_graph(graph)
        self.message.emit("INFO", "Subgrafo criado; edite a entrada, o retorno e salve em Assets/Logic")

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

    def open_asset(self, path: str | Path) -> bool:
        """Abre um asset respeitando alterações não salvas no grafo atual."""
        resolved = Path(path).resolve()
        if self.current_path is not None:
            try:
                if resolved == self.current_path.resolve():
                    return True
            except OSError:
                pass
        if not self._confirm_discard():
            return False
        self.open_path(resolved)
        return self.current_path is not None and self.current_path.resolve() == resolved

    def open_for_object(self, object_name: str, path: str | Path | None = None) -> bool:
        """Abre um asset existente ou prepara um rascunho para o objeto da Hierarchy."""
        target_name = str(object_name).strip()
        if not target_name:
            return False
        resolved = Path(path).resolve() if path is not None else None
        if resolved is not None:
            return self.open_asset(resolved)
        current_target = self.graph.get("target", {})
        already_contextual = (
            resolved is None
            and self.current_path is None
            and str(current_target.get("type", "name")) == "name"
            and str(current_target.get("value", "")).casefold() == target_name.casefold()
        )
        if already_contextual:
            return True
        if not self._confirm_discard():
            return False
        safe_name = "".join(character if character.isalnum() else "_" for character in target_name).strip("_") or "Object"
        graph = default_logic_graph(f"{safe_name}Logic")
        graph["target"] = {"type": "name", "value": target_name}
        graph["nodes"] = [create_logic_node("event_start", (80.0, 100.0))]
        self.set_graph(graph)
        self.message.emit("INFO", f"Novo Logic Graph preparado para: {target_name}")
        return True

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
            self._sync_project_blackboard()
            saved_path = Path(path).with_suffix(".zlogic")
            self.set_graph(saved, saved_path)
            self.asset_changed.emit()
            self.message.emit("INFO", f"Logic Graph salvo: {saved_path.name}")
        except (OSError, ValueError) as exc:
            self.message.emit("ERROR", f"Não foi possível salvar o Logic Graph: {exc}")

    def request_play(self) -> None:
        """Persiste o asset aberto antes de entregar o Play ao editor principal."""
        if self.current_path is None:
            self.save()
            if self.current_path is None:
                return
        elif self._dirty:
            self._autosave_timer.stop()
            self._autosave()
            if self._dirty:
                return
        self.play_requested.emit()

    def set_play_state(self, playing: bool) -> None:
        """Mantém os controles locais sincronizados com a Viewport isolada."""
        self.play_button.setEnabled(not playing)
        self.stop_button.setEnabled(playing)

    def fit_graph(self) -> None:
        if not self.node_items:
            self.view.resetTransform()
            self.view.centerOn(0.0, 0.0)
            return
        bounds = self.scene.itemsBoundingRect().adjusted(-80.0, -80.0, 80.0, 80.0)
        self.view.fitInView(bounds, Qt.KeepAspectRatio)

    def mark_dirty(self) -> None:
        if not self._restoring_history:
            self._history_timer.start()
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
            self._sync_project_blackboard()
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
        edge_issues: dict[str, list[dict[str, str]]] = {}
        for issue in issues:
            edge_id = str(issue.get("edge", ""))
            if edge_id:
                edge_issues.setdefault(edge_id, []).append(issue)
        for edge_item in self.edge_items:
            related = edge_issues.get(edge_item.edge_id, [])
            level = "error" if any(issue.get("level") == "error" for issue in related) else "warning" if related else ""
            edge_item.set_validation_state(level, "\n".join(str(issue.get("message", "")) for issue in related))
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
