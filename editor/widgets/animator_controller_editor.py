"""Editor visual básico para assets ``.zanimator``."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QGraphicsItem, QGraphicsPathItem, QGraphicsPolygonItem, QGraphicsRectItem,
    QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView, QInputDialog, QLabel,
    QLineEdit, QMessageBox, QPushButton, QSplitter, QTabWidget, QTreeWidget,
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
        for transition in controller.get("transitions", []):
            self._draw_transition(str(transition.get("from", "")), str(transition.get("to", "")))
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

    def _draw_transition(self, origin: str, target: str) -> None:
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
        name = self.selected_state()
        if name:
            self.stateSelected.emit(name)


class AnimatorControllerEditorDialog(QDialog):
    """Edita estados, parâmetros e transições sem expor o JSON ao usuário."""

    def __init__(self, project_root: Path, path: Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self.project_root = Path(project_root).resolve()
        self.path = path.resolve() if path else None
        self.data = load_animator_controller(self.path) if self.path else default_animator_controller()
        self.saved_path: Path | None = None
        self._undo_stack: list[dict] = []
        self._redo_stack: list[dict] = []
        self._active_state = ""
        self._runtime_parameters: dict[str, object] = {}
        self._preview_state = str(self.data["initial_state"])
        self._preview_parameters = {
            name: parameter["default"] for name, parameter in self.data["parameters"].items()
        }
        self.setWindowTitle("Animator Controller")
        self.resize(1040, 650)
        self._build_ui()
        self._refresh_all()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QFormLayout()
        self.name_field = QLineEdit(str(self.data["name"]))
        self.initial_combo = QComboBox()
        header.addRow("Nome", self.name_field)
        header.addRow("Estado inicial", self.initial_combo)
        layout.addLayout(header)

        toolbar = QHBoxLayout()
        self.undo_button = QPushButton("Desfazer")
        self.redo_button = QPushButton("Refazer")
        self.rename_state_button = QPushButton("Renomear")
        self.duplicate_state_button = QPushButton("Duplicar")
        self.delete_state_button = QPushButton("Excluir")
        self.test_parameter_button = QPushButton("Testar parâmetro")
        self.evaluate_button = QPushButton("Avaliar transições")
        for button in (
            self.undo_button, self.redo_button, self.rename_state_button,
            self.duplicate_state_button, self.delete_state_button,
            self.test_parameter_button, self.evaluate_button,
        ):
            toolbar.addWidget(button)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        tabs = QTabWidget()
        self.states_tree = self._tree(("Estado", "Animação", "Velocidade"))
        self.states_tree.itemDoubleClicked.connect(self._edit_state)
        tabs.addTab(self._tab(self.states_tree, self._add_state, self._remove_state), "Estados")
        self.parameters_tree = self._tree(("Parâmetro", "Tipo", "Padrão", "Runtime/Teste"))
        self.parameters_tree.itemDoubleClicked.connect(self._edit_parameter)
        tabs.addTab(self._tab(self.parameters_tree, self._add_parameter, self._remove_parameter), "Parâmetros")
        self.transitions_tree = self._tree(("Origem", "Destino", "Condição"))
        tabs.addTab(self._tab(self.transitions_tree, self._add_transition, self._remove_transition), "Transições")
        self.graph = AnimatorGraphView()
        self.graph.setMinimumWidth(520)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.graph)
        splitter.addWidget(tabs)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        self.validation_label = QLabel()
        self.validation_label.setObjectName("PanelHint")
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.undo_button.clicked.connect(self._undo)
        self.redo_button.clicked.connect(self._redo)
        self.rename_state_button.clicked.connect(self._rename_selected_state)
        self.duplicate_state_button.clicked.connect(self._duplicate_selected_state)
        self.delete_state_button.clicked.connect(self._remove_state)
        self.test_parameter_button.clicked.connect(self._test_selected_parameter)
        self.evaluate_button.clicked.connect(self._evaluate_preview)
        self.graph.stateSelected.connect(self._select_state_in_tree)
        self.graph.positionsChanged.connect(self._apply_graph_positions)
        self.states_tree.itemSelectionChanged.connect(self._select_tree_state_in_graph)
        self.initial_combo.activated.connect(self._change_initial_state)

    @staticmethod
    def _tree(headers: tuple[str, ...]) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setHeaderLabels(list(headers))
        tree.setRootIsDecorated(False)
        tree.setAlternatingRowColors(True)
        return tree

    @staticmethod
    def _tab(tree: QTreeWidget, add_slot, remove_slot) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(tree, 1)
        row = QHBoxLayout()
        add_button = QPushButton("Adicionar")
        remove_button = QPushButton("Remover")
        add_button.clicked.connect(add_slot)
        remove_button.clicked.connect(remove_slot)
        row.addWidget(add_button)
        row.addWidget(remove_button)
        row.addStretch(1)
        layout.addLayout(row)
        return page

    def _animation_assets(self) -> list[str]:
        return sorted(
            path.relative_to(self.project_root).as_posix()
            for path in self.project_root.rglob("*.zanim")
            if path.is_file()
        )

    def _refresh_all(self) -> None:
        selected_state = self._selected_state_name()
        current_initial = str(self.data["initial_state"])
        self.initial_combo.clear()
        self.initial_combo.addItems(list(self.data["states"]))
        self.initial_combo.setCurrentText(current_initial)
        self.states_tree.clear()
        for name, state in self.data["states"].items():
            item = QTreeWidgetItem(self.states_tree, [name, state["animation"] or "Sem animação", f'{float(state.get("speed", 1.0)):.2f}'])
            if name == selected_state:
                self.states_tree.setCurrentItem(item)
        self.parameters_tree.clear()
        for name, parameter in self.data["parameters"].items():
            runtime_value = self._runtime_parameters.get(name, self._preview_parameters.get(name, "—"))
            QTreeWidgetItem(self.parameters_tree, [name, parameter["type"], str(parameter["default"]), str(runtime_value)])
        self.transitions_tree.clear()
        for transition in self.data["transitions"]:
            conditions = transition.get("conditions", [])
            text = "Sempre" if not conditions else " e ".join(
                f'{condition["parameter"]} {condition["operator"]} {condition.get("value", "")}' for condition in conditions
            )
            QTreeWidgetItem(self.transitions_tree, [transition["from"], transition["to"], text])
        issues = validate_animator_controller(self.data, self.project_root)
        invalid_states = {issue["state"] for issue in issues if issue.get("state")}
        active = self._active_state or self._preview_state
        self.graph.set_controller(self.data, active, invalid_states)
        if selected_state:
            self.graph.select_state(selected_state)
        if issues:
            errors = sum(issue["level"] == "error" for issue in issues)
            warnings = len(issues) - errors
            preview = " · ".join(issue["message"] for issue in issues[:3])
            self.validation_label.setText(f"Validação: {errors} erro(s), {warnings} aviso(s) — {preview}")
        else:
            self.validation_label.setText("Validação: controller pronto para uso.")
        self.undo_button.setEnabled(bool(self._undo_stack))
        self.redo_button.setEnabled(bool(self._redo_stack))

    def _selected_state_name(self) -> str:
        graph_name = self.graph.selected_state() if hasattr(self, "graph") else ""
        item = self.states_tree.currentItem() if hasattr(self, "states_tree") else None
        return graph_name or (item.text(0) if item is not None else "")

    def _remember(self) -> None:
        self._undo_stack.append(deepcopy(self.data))
        self._undo_stack = self._undo_stack[-100:]
        self._redo_stack.clear()

    def _undo(self) -> None:
        if not self._undo_stack:
            return
        self._redo_stack.append(deepcopy(self.data))
        self.data = self._undo_stack.pop()
        self._reset_preview()
        self._refresh_all()

    def _redo(self) -> None:
        if not self._redo_stack:
            return
        self._undo_stack.append(deepcopy(self.data))
        self.data = self._redo_stack.pop()
        self._reset_preview()
        self._refresh_all()

    def _reset_preview(self) -> None:
        self._preview_state = str(self.data["initial_state"])
        self._preview_parameters = {
            name: parameter["default"] for name, parameter in self.data["parameters"].items()
        }

    def _select_state_in_tree(self, name: str) -> None:
        matches = self.states_tree.findItems(name, Qt.MatchExactly, 0)
        if matches:
            self.states_tree.setCurrentItem(matches[0])

    def _select_tree_state_in_graph(self) -> None:
        item = self.states_tree.currentItem()
        if item is not None and self.graph.selected_state() != item.text(0):
            self.graph.select_state(item.text(0))

    def _apply_graph_positions(self, positions: dict, _previous: dict) -> None:
        self._remember()
        for name, position in positions.items():
            if name in self.data["states"]:
                self.data["states"][name]["position"] = [float(position[0]), float(position[1])]
        self._refresh_all()

    def _add_state(self) -> None:
        name, ok = QInputDialog.getText(self, "Novo estado", "Nome do estado:")
        name = name.strip()
        if not ok or not name:
            return
        if name in self.data["states"]:
            QMessageBox.warning(self, "Estado existente", "Já existe um estado com esse nome.")
            return
        animations = self._animation_assets()
        animation = ""
        if animations:
            animation, ok = QInputDialog.getItem(self, "Animação do estado", "Animação salva:", animations, 0, False)
            if not ok:
                return
        self._remember()
        index = len(self.data["states"])
        self.data["states"][name] = {
            "animation": animation, "speed": 1.0,
            "position": [40.0 + (index % 3) * 190.0, 40.0 + (index // 3) * 120.0],
        }
        self._refresh_all()

    def _remove_state(self) -> None:
        name = self._selected_state_name()
        if not name or len(self.data["states"]) <= 1:
            return
        self._remember()
        self.data["states"].pop(name, None)
        self.data["transitions"] = [t for t in self.data["transitions"] if t["from"] != name and t["to"] != name]
        if self.data["initial_state"] == name:
            self.data["initial_state"] = next(iter(self.data["states"]))
        self._refresh_all()

    def _edit_state(self, item: QTreeWidgetItem, _column: int = 0) -> None:
        name = item.text(0)
        state = self.data["states"].get(name)
        if state is None:
            return
        animations = self._animation_assets()
        choices = ["Sem animação"] + animations
        current = str(state.get("animation", ""))
        index = choices.index(current) if current in choices else 0
        animation, ok = QInputDialog.getItem(self, f"Estado {name}", "Animação salva:", choices, index, False)
        if not ok:
            return
        speed, ok = QInputDialog.getDouble(
            self, f"Estado {name}", "Velocidade:", float(state.get("speed", 1.0)), 0.0, 100.0, 2
        )
        if not ok:
            return
        self._remember()
        state["animation"] = "" if animation == "Sem animação" else animation
        state["speed"] = speed
        self._refresh_all()

    def _add_parameter(self) -> None:
        name, ok = QInputDialog.getText(self, "Novo parâmetro", "Nome do parâmetro:")
        name = name.strip()
        if not ok or not name or name in self.data["parameters"]:
            return
        kind, ok = QInputDialog.getItem(self, "Tipo", "Tipo do parâmetro:", ["bool", "float", "trigger"], 0, False)
        if not ok:
            return
        default = 0.0 if kind == "float" else False
        self._remember()
        self.data["parameters"][name] = {"type": kind, "default": default}
        self._refresh_all()

    def _remove_parameter(self) -> None:
        item = self.parameters_tree.currentItem()
        if item is None:
            return
        name = item.text(0)
        self._remember()
        self.data["parameters"].pop(name, None)
        for transition in self.data["transitions"]:
            transition["conditions"] = [c for c in transition["conditions"] if c["parameter"] != name]
        self._refresh_all()

    def _edit_parameter(self, item: QTreeWidgetItem, _column: int = 0) -> None:
        name = item.text(0)
        parameter = self.data["parameters"].get(name)
        if parameter is None or parameter["type"] == "trigger":
            return
        if parameter["type"] == "float":
            value, ok = QInputDialog.getDouble(
                self, f"Parâmetro {name}", "Valor padrão:", float(parameter["default"]), -1000000, 1000000, 3
            )
        else:
            text, ok = QInputDialog.getItem(
                self, f"Parâmetro {name}", "Valor padrão:", ["True", "False"],
                0 if parameter["default"] else 1, False,
            )
            value = text == "True"
        if ok:
            self._remember()
            parameter["default"] = value
            self._refresh_all()

    def _add_transition(self) -> None:
        states = list(self.data["states"])
        origin, ok = QInputDialog.getItem(self, "Origem", "Estado de origem:", ["*"] + states, 0, False)
        if not ok:
            return
        target, ok = QInputDialog.getItem(self, "Destino", "Estado de destino:", states, 0, False)
        if not ok:
            return
        conditions = []
        parameters = list(self.data["parameters"])
        if parameters:
            choices = ["Sem condição"] + parameters
            parameter, ok = QInputDialog.getItem(self, "Condição", "Parâmetro:", choices, 0, False)
            if not ok:
                return
            if parameter != "Sem condição":
                kind = self.data["parameters"][parameter]["type"]
                operators = ["trigger"] if kind == "trigger" else ([">", ">=", "<", "<=", "==", "!="] if kind == "float" else ["==", "!="])
                operator, ok = QInputDialog.getItem(self, "Operador", "Comparação:", operators, 0, False)
                if not ok:
                    return
                value = True
                if kind == "float":
                    value, ok = QInputDialog.getDouble(self, "Valor", "Valor:", 0.0, -1000000, 1000000, 3)
                    if not ok:
                        return
                elif kind == "bool":
                    text, ok = QInputDialog.getItem(self, "Valor", "Valor:", ["True", "False"], 0, False)
                    if not ok:
                        return
                    value = text == "True"
                conditions.append({"parameter": parameter, "operator": operator, "value": value})
        self._remember()
        self.data["transitions"].append({"from": origin, "to": target, "conditions": conditions})
        self._refresh_all()

    def _remove_transition(self) -> None:
        index = self.transitions_tree.indexOfTopLevelItem(self.transitions_tree.currentItem())
        if index >= 0:
            self._remember()
            self.data["transitions"].pop(index)
            self._refresh_all()

    def _change_initial_state(self, _index: int) -> None:
        name = self.initial_combo.currentText()
        if name and name != self.data["initial_state"]:
            self._remember()
            self.data["initial_state"] = name
            self._preview_state = name
            self._refresh_all()

    def _rename_selected_state(self) -> None:
        old_name = self._selected_state_name()
        if not old_name:
            return
        new_name, ok = QInputDialog.getText(self, "Renomear estado", "Novo nome:", text=old_name)
        new_name = new_name.strip()
        if not ok or not new_name or new_name == old_name:
            return
        if new_name in self.data["states"]:
            QMessageBox.warning(self, "Estado existente", "Já existe um estado com esse nome.")
            return
        self._remember()
        self.data["states"] = {
            (new_name if name == old_name else name): state for name, state in self.data["states"].items()
        }
        for transition in self.data["transitions"]:
            if transition["from"] == old_name:
                transition["from"] = new_name
            if transition["to"] == old_name:
                transition["to"] = new_name
        if self.data["initial_state"] == old_name:
            self.data["initial_state"] = new_name
        if self._preview_state == old_name:
            self._preview_state = new_name
        if self._active_state == old_name:
            self._active_state = new_name
        self._refresh_all()
        self.graph.select_state(new_name)

    def _duplicate_selected_state(self) -> None:
        source_name = self._selected_state_name()
        if not source_name:
            return
        suggested = f"{source_name}_Copy"
        name, ok = QInputDialog.getText(self, "Duplicar estado", "Nome da cópia:", text=suggested)
        name = name.strip()
        if not ok or not name or name in self.data["states"]:
            return
        self._remember()
        state = deepcopy(self.data["states"][source_name])
        position = state.get("position", [40.0, 40.0])
        state["position"] = [float(position[0]) + 35.0, float(position[1]) + 90.0]
        self.data["states"][name] = state
        self._refresh_all()
        self.graph.select_state(name)

    def _test_selected_parameter(self) -> None:
        item = self.parameters_tree.currentItem()
        if item is None:
            QMessageBox.information(self, "Testar parâmetro", "Selecione um parâmetro na lista.")
            return
        name = item.text(0)
        parameter = self.data["parameters"].get(name)
        if parameter is None:
            return
        kind = parameter["type"]
        current = self._preview_parameters.get(name, parameter["default"])
        if kind == "float":
            value, ok = QInputDialog.getDouble(self, "Testar parâmetro", f"{name}:", float(current), -1000000, 1000000, 3)
            if not ok:
                return
        elif kind == "bool":
            value = not bool(current)
        else:
            value = True
        self._preview_parameters[name] = value
        self._active_state = ""
        self._refresh_all()

    def _evaluate_preview(self) -> None:
        runtime = AnimatorControllerRuntime(self.data, self._preview_parameters)
        runtime.play(self._preview_state)
        runtime.update()
        self._preview_state = runtime.current_state
        self._preview_parameters = dict(runtime.parameters)
        self._active_state = ""
        self._refresh_all()
        self.graph.select_state(self._preview_state)

    def set_runtime_state(self, state: str | None, parameters: dict | None = None) -> None:
        """Atualiza o destaque sem modificar o asset salvo."""
        self._active_state = str(state or "")
        self._runtime_parameters = dict(parameters or {})
        self._refresh_all()

    def _save(self) -> None:
        name = self.name_field.text().strip()
        if not name:
            QMessageBox.warning(self, "Nome obrigatório", "Informe um nome para o controller.")
            return
        self.data["name"] = name
        self.data["initial_state"] = self.initial_combo.currentText()
        if self.path is None:
            safe_name = "".join(character if character.isalnum() or character in "-_" else "_" for character in name)
            self.path = self.project_root / "Assets" / "Animations" / f"{safe_name}.zanimator"
        save_animator_controller(self.path, self.data)
        self.saved_path = self.path
        self.accept()
