"""Editor visual básico para assets ``.zanimator``."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QCheckBox, QDoubleSpinBox, QGraphicsItem, QGraphicsPathItem, QGraphicsPolygonItem, QGraphicsRectItem,
    QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView, QInputDialog, QLabel,
    QLineEdit, QMessageBox, QPushButton, QSpinBox, QSplitter, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from engine.animation.controller_asset import (
    AnimatorControllerRuntime, default_animator_controller, load_animator_controller,
    save_animator_controller, validate_animator_controller,
)


class AnimatorGraphView(QGraphicsView):
    """Grafo leve de estados com posições persistentes e transições direcionais."""

    stateSelected = Signal(str)
    positionsChanged = Signal(dict, dict)
    transitionSelected = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setBackgroundBrush(QColor("#14171d"))
        self._nodes: dict[str, QGraphicsRectItem] = {}
        self._positions_before_drag: dict[str, list[float]] = {}
        self._active_state = ""
        self._invalid_states: set[str] = set()
        self.scene().selectionChanged.connect(self._emit_selection)

    def set_controller(self, controller: dict, active_state: str = "", invalid_states: set[str] | None = None) -> None:
        self.scene().clear()
        self._nodes.clear()
        self._active_state = active_state
        self._invalid_states = set(invalid_states or ())
        states = controller.get("states", {})
        for name, state in states.items():
            position = state.get("position", [40.0, 40.0])
            node = QGraphicsRectItem(0, 0, 150, 64)
            node.setPos(float(position[0]), float(position[1]))
            node.setData(0, name)
            node.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            node.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            node.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
            color = QColor("#287a48") if name == active_state else QColor("#2a303b")
            border = QColor("#f0b84b") if name == controller.get("initial_state") else QColor("#596579")
            if name in self._invalid_states:
                border = QColor("#df5b66")
            node.setBrush(QBrush(color))
            node.setPen(QPen(border, 3 if name == active_state else 2))
            title = QGraphicsSimpleTextItem(name, node)
            title.setBrush(QColor("#ffffff"))
            title.setPos(10, 8)
            animation_name = Path(str(state.get("animation", ""))).stem or "Sem animação"
            subtitle = QGraphicsSimpleTextItem(animation_name, node)
            subtitle.setBrush(QColor("#aeb7c5"))
            subtitle.setPos(10, 34)
            self.scene().addItem(node)
            self._nodes[name] = node
        for index, transition in enumerate(controller.get("transitions", [])):
            self._draw_transition(str(transition.get("from", "")), str(transition.get("to", "")), index)
        bounds = self.scene().itemsBoundingRect().adjusted(-80, -80, 80, 80)
        self.scene().setSceneRect(bounds if not bounds.isEmpty() else self.rect())

    def select_state(self, name: str) -> None:
        node = self._nodes.get(name)
        if node is not None:
            self.scene().clearSelection()
            node.setSelected(True)
            self.centerOn(node)

    def selected_state(self) -> str:
        selected = self.scene().selectedItems()
        return str(selected[0].data(0)) if selected and selected[0].data(0) else ""

    def _draw_transition(self, origin: str, target: str, index: int) -> None:
        target_node = self._nodes.get(target)
        if target_node is None:
            return
        target_center = target_node.sceneBoundingRect().center()
        origin_node = self._nodes.get(origin)
        if origin_node is target_node:
            bounds = target_node.sceneBoundingRect()
            start = QPointF(bounds.right() - 25, bounds.top())
            end = QPointF(bounds.right(), bounds.center().y())
            path = QPainterPath(start)
            path.cubicTo(bounds.right() + 75, bounds.top() - 55, bounds.right() + 85, bounds.bottom() + 30, end.x(), end.y())
        else:
            if origin == "*":
                start = QPointF(target_center.x() - 160, target_center.y() - 80)
            else:
                if origin_node is None:
                    return
                start = origin_node.sceneBoundingRect().center()
            dx, dy = target_center.x() - start.x(), target_center.y() - start.y()
            length = max(1.0, (dx ** 2 + dy ** 2) ** 0.5)
            ux, uy = dx / length, dy / length
            if origin != "*":
                start = QPointF(start.x() + ux * 78, start.y() + uy * 38)
            end = QPointF(target_center.x() - ux * 82, target_center.y() - uy * 40)
            path = QPainterPath(start)
            midpoint = (start.x() + end.x()) / 2.0
            path.cubicTo(midpoint, start.y(), midpoint, end.y(), end.x(), end.y())
        edge = QGraphicsPathItem(path)
        edge.setPen(QPen(QColor("#77849a"), 2))
        edge.setZValue(-2)
        edge.setData(1, index)
        edge.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.scene().addItem(edge)
        direction = end - path.pointAtPercent(0.92)
        length = max(1.0, (direction.x() ** 2 + direction.y() ** 2) ** 0.5)
        ux, uy = direction.x() / length, direction.y() / length
        tip = path.pointAtPercent(0.97)
        arrow = QPolygonF([
            tip,
            QPointF(tip.x() - ux * 12 - uy * 6, tip.y() - uy * 12 + ux * 6),
            QPointF(tip.x() - ux * 12 + uy * 6, tip.y() - uy * 12 - ux * 6),
        ])
        arrow_item = QGraphicsPolygonItem(arrow)
        arrow_item.setBrush(QColor("#77849a"))
        arrow_item.setPen(QPen(Qt.PenStyle.NoPen))
        arrow_item.setZValue(-1)
        self.scene().addItem(arrow_item)

    def mousePressEvent(self, event) -> None:
        self._positions_before_drag = {
            name: [float(node.pos().x()), float(node.pos().y())] for name, node in self._nodes.items()
        }
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        positions = {name: [float(node.pos().x()), float(node.pos().y())] for name, node in self._nodes.items()}
        if positions != self._positions_before_drag:
            self.positionsChanged.emit(positions, self._positions_before_drag)

    def _emit_selection(self) -> None:
        selected = self.scene().selectedItems()
        if not selected:
            return
        transition_index = selected[0].data(1)
        if transition_index is not None:
            self.transitionSelected.emit(int(transition_index))
            return
        name = self.selected_state()
        if name:
            self.stateSelected.emit(name)


class TransitionEditorDialog(QDialog):
    """Inspector de uma transição e de todas as suas condições."""

    def __init__(self, states: list[str], parameters: dict, transition: dict | None = None, parent=None) -> None:
        super().__init__(parent)
        self.parameters = parameters
        self.transition = deepcopy(transition or {"from": "*", "to": states[0], "conditions": []})
        self.setWindowTitle("Inspector da Transição")
        self.resize(520, 470)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.origin_combo = QComboBox(); self.origin_combo.addItems(["*"] + states)
        self.target_combo = QComboBox(); self.target_combo.addItems(states)
        self.priority_field = QSpinBox(); self.priority_field.setRange(-999, 999)
        self.exit_check = QCheckBox("Esperar o clip alcançar o Exit Time")
        self.exit_field = QDoubleSpinBox(); self.exit_field.setRange(0.0, 1.0); self.exit_field.setSingleStep(0.05)
        self.duration_field = QDoubleSpinBox(); self.duration_field.setRange(0.0, 10.0); self.duration_field.setSuffix(" s")
        self.interruptible_check = QCheckBox("Pode ser interrompida")
        form.addRow("Origem", self.origin_combo); form.addRow("Destino", self.target_combo)
        form.addRow("Prioridade", self.priority_field); form.addRow(self.exit_check)
        form.addRow("Exit Time", self.exit_field); form.addRow("Duração", self.duration_field)
        form.addRow(self.interruptible_check)
        layout.addLayout(form)
        layout.addWidget(QLabel("CONDIÇÕES (todas precisam ser verdadeiras)"))
        self.conditions_tree = QTreeWidget(); self.conditions_tree.setHeaderLabels(["Parâmetro", "Operador", "Valor"])
        layout.addWidget(self.conditions_tree, 1)
        row = QHBoxLayout(); add = QPushButton("Adicionar condição"); remove = QPushButton("Remover condição")
        row.addWidget(add); row.addWidget(remove); row.addStretch(1); layout.addLayout(row)
        add.clicked.connect(self._add_condition); remove.clicked.connect(self._remove_condition)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
        self._load()

    def _load(self) -> None:
        self.origin_combo.setCurrentText(str(self.transition.get("from", "*")))
        self.target_combo.setCurrentText(str(self.transition.get("to", "")))
        self.priority_field.setValue(int(self.transition.get("priority", 0)))
        self.exit_check.setChecked(bool(self.transition.get("has_exit_time", False)))
        self.exit_field.setValue(float(self.transition.get("exit_time", 1.0)))
        self.duration_field.setValue(float(self.transition.get("duration", 0.0)))
        self.interruptible_check.setChecked(bool(self.transition.get("interruptible", True)))
        self._refresh_conditions()

    def _refresh_conditions(self) -> None:
        self.conditions_tree.clear()
        for condition in self.transition.get("conditions", []):
            QTreeWidgetItem(self.conditions_tree, [str(condition["parameter"]), str(condition["operator"]), str(condition.get("value", True))])

    def _add_condition(self) -> None:
        if not self.parameters:
            QMessageBox.information(self, "Condição", "Crie um parâmetro antes de adicionar condições.")
            return
        name, ok = QInputDialog.getItem(self, "Condição", "Parâmetro:", list(self.parameters), 0, False)
        if not ok: return
        kind = self.parameters[name]["type"]
        operators = ["trigger"] if kind == "trigger" else ([">", ">=", "<", "<=", "==", "!="] if kind == "float" else ["==", "!="])
        operator, ok = QInputDialog.getItem(self, "Condição", "Operador:", operators, 0, False)
        if not ok: return
        value: object = True
        if kind == "float":
            value, ok = QInputDialog.getDouble(self, "Condição", "Valor:", 0.0, -1000000, 1000000, 3)
            if not ok: return
        elif kind == "bool":
            text, ok = QInputDialog.getItem(self, "Condição", "Valor:", ["True", "False"], 0, False)
            if not ok: return
            value = text == "True"
        self.transition.setdefault("conditions", []).append({"parameter": name, "operator": operator, "value": value})
        self._refresh_conditions()

    def _remove_condition(self) -> None:
        index = self.conditions_tree.indexOfTopLevelItem(self.conditions_tree.currentItem())
        if index >= 0:
            self.transition["conditions"].pop(index); self._refresh_conditions()

    def _accept(self) -> None:
        self.transition.update({
            "from": self.origin_combo.currentText(), "to": self.target_combo.currentText(),
            "priority": self.priority_field.value(), "has_exit_time": self.exit_check.isChecked(),
            "exit_time": self.exit_field.value(), "duration": self.duration_field.value(),
            "interruptible": self.interruptible_check.isChecked(),
        })
        self.accept()


