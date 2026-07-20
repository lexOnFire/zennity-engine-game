"""Workspace visual para criar e editar assets ``.zlogic``."""

from __future__ import annotations

import json
import unicodedata
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from .logic_graph.items import (
    LogicPortItem, LogicEdgeItem, LogicGroupResizeHandle, LogicGroupItem,
    LogicCommentItem, LogicFlipControl, LogicCollapseControl, LogicResizeHandle,
    LogicNodeItem
)
from .logic_graph.views import LogicGraphView, LogicMiniMapView
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

from editor.widgets.logic_graph_editor import (
    CATEGORY_COLORS, PORT_COLORS, NODE_DESCRIPTIONS, PROPERTY_LABELS, NODE_PROPERTY_LABELS,
)

class LogicGraphCanvasMixin:
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

