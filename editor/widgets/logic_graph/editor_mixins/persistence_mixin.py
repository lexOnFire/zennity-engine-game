"""Workspace visual para criar e editar assets ``.zlogic``."""

from __future__ import annotations

import json
import unicodedata
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from editor.widgets.logic_graph.items import (
    LogicPortItem, LogicEdgeItem, LogicGroupResizeHandle, LogicGroupItem,
    LogicCommentItem, LogicFlipControl, LogicCollapseControl, LogicResizeHandle,
    LogicNodeItem
)
from editor.widgets.logic_graph.views import LogicGraphView, LogicMiniMapView
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

from editor.widgets.logic_graph.definitions import (
    CATEGORY_COLORS,
    NODE_DESCRIPTIONS,
    NODE_PROPERTY_LABELS,
    PORT_COLORS,
    PROPERTY_LABELS,
)

class LogicGraphPersistenceMixin:
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
        directory = self.project_root / "Assets" / "Logic"
        directory.mkdir(parents=True, exist_ok=True)
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir Exemplo de Lógica",
            str(directory),
            "Zennity Logic Graph (*.zlogic)"
        )
        if filename:
            self.open_path(Path(filename))

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
