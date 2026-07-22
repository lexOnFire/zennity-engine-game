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

class LogicGraphRuntimeViewMixin:
    def set_graph(self, graph: dict[str, Any], path: Path | None = None, *, reset_history: bool = True) -> None:
        self.clear_runtime_trace()
        self.cancel_connection()
        self._autosave_timer.stop()
        self.graph, consolidated_events = consolidate_logic_events(graph)
        self._sync_subgraph_call_interfaces(self.graph)
        for prefab_node in self.graph.get("nodes", []):
            self._sync_prefab_node_interface(prefab_node)
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

