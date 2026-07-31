"""Workspace visual para criar e editar assets ``.zlogic``."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
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
    QApplication,
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
from editor.widgets.logic_graph.target_hints import refresh_target_hints

class LogicGraphCanvasMixin:
    _clipboard_mime = "application/x-zennity-logic-selection"

    def _release_scene_interaction(self) -> None:
        if not hasattr(self, "scene") or self.scene is None:
            return
        try:
            self.cancel_connection(refresh=False)
        except (AttributeError, RuntimeError):
            pass
        try:
            self.scene.clearSelection()
        except RuntimeError:
            pass
        try:
            grabber = self.scene.mouseGrabberItem()
            if grabber is not None and grabber.scene() is not None:
                grabber.ungrabMouse()
        except RuntimeError:
            pass
        try:
            focus_item = self.scene.focusItem()
            if focus_item is not None:
                focus_item.clearFocus()
        except RuntimeError:
            pass

    def _remove_scene_item(self, item: QGraphicsItem | None) -> None:
        if item is None or not hasattr(self, "scene") or self.scene is None:
            return
        try:
            item.setSelected(False)
            if item.scene() is not None and self.scene.mouseGrabberItem() is item:
                item.ungrabMouse()
        except RuntimeError:
            pass
        try:
            if item.scene() is self.scene:
                self.scene.removeItem(item)
        except RuntimeError:
            pass

    def _clear_logic_scene(self) -> None:
        self._release_scene_interaction()
        try:
            self.scene.clear()
        except RuntimeError:
            pass

    def refresh_connections(self) -> None:
        if not hasattr(self, "scene"):
            return
        existing = {item.edge_id: item for item in self.edge_items}
        active_ids = {
            str(edge.get("id", "")) for edge in self.graph.get("edges", [])
        }
        for edge_id, item in tuple(existing.items()):
            if edge_id not in active_ids:
                self._remove_scene_item(item)
                existing.pop(edge_id, None)
        next_items: list[LogicEdgeItem] = []
        for edge in self.graph.get("edges", []):
            edge_id = str(edge.get("id", ""))
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
            connection = existing.get(edge_id)
            if connection is None or connection.data_type != data_type:
                if connection is not None:
                    self._remove_scene_item(connection)
                connection = LogicEdgeItem(path, edge_id, data_type)
                self.scene.addItem(connection)
            else:
                connection.setPath(path)
            next_items.append(connection)
        self.edge_items[:] = next_items
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
        refresh_target_hints(self.graph, self.node_items)

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
            self._create_node_from_connection(origin, scene_position)
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
        edge = {
            "id": uuid.uuid4().hex,
            "from_node": source.node.node_id,
            "from_port": source.name,
            "to_node": destination.node.node_id,
            "to_port": destination.name,
            "kind": source.data_type,
        }
        self.graph["edges"].append(edge)
        self.edge_added.emit(edge)
        self.cancel_connection(refresh=False)
        self.refresh_connections()
        self.mark_dirty()
        self._update_validation()

    def _create_node_from_connection(self, origin: LogicPortItem, position: QPointF) -> None:
        """Offer compatible nodes when a wire is released on empty canvas."""
        direction = "input" if origin.direction == "output" else "output"
        choices: list[tuple[str, str, str]] = []
        for node_type, definition in NODE_DEFINITIONS.items():
            ports = node_port_definitions({"type": node_type, "properties": definition.get("properties", {})})
            for port_name, data_type in ports.get(f"{direction}s", []):
                if data_type == origin.data_type or "any" in {data_type, origin.data_type}:
                    label = f"{definition.get('title', node_type)} — {port_name} ({data_type})"
                    choices.append((label, node_type, port_name))
        choices.sort(key=lambda value: value[0].casefold())
        if not choices:
            self.cancel_connection()
            return

        origin_dir = origin.direction
        origin_node_id = origin.node.node_id
        origin_port_name = origin.name
        origin_data_type = origin.data_type

        # Cancela a linha temporária e libera o mouse grab da cena ANTES do diálogo modal
        self.cancel_connection(refresh=False)
        self._release_scene_interaction()

        selected, accepted = QInputDialog.getItem(
            self, "Criar e conectar", "Nó compatível:", [item[0] for item in choices], 0, False
        )
        if not accepted:
            return

        _label, node_type, port_name = next(item for item in choices if item[0] == selected)
        node = create_logic_node(node_type, (position.x(), position.y()))
        self.graph["nodes"].append(node)
        self._create_node_item(node)
        self.node_added.emit(node)

        source_node_id = origin_node_id if origin_dir == "output" else node["id"]
        source_port = origin_port_name if origin_dir == "output" else port_name
        dest_node_id = node["id"] if origin_dir == "output" else origin_node_id
        dest_port = port_name if origin_dir == "output" else origin_port_name

        edge = {
            "id": uuid.uuid4().hex,
            "from_node": source_node_id,
            "from_port": source_port,
            "to_node": dest_node_id,
            "to_port": dest_port,
            "kind": origin_data_type,
        }
        self.graph["edges"].append(edge)
        self.edge_added.emit(edge)
        self.refresh_connections()
        self.mark_dirty()
        self._update_validation()

    def cancel_connection(self, refresh: bool = True) -> None:
        if self._connection_preview is not None and self._connection_preview.scene() is self.scene:
            self._remove_scene_item(self._connection_preview)
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
        edge = {
            "id": uuid.uuid4().hex,
            "from_node": source.node_id,
            "from_port": source_port.name,
            "to_node": target.node_id,
            "to_port": target_port.name,
            "kind": "flow",
        }
        self.graph["edges"].append(edge)
        self.edge_added.emit(edge)
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
        deleted_nodes = [item.node for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        self.graph["edges"] = [
            edge for edge in self.graph["edges"]
            if edge["id"] not in edge_ids and edge["from_node"] not in node_ids and edge["to_node"] not in node_ids
        ]
        for node_id in node_ids:
            item = self.node_items.pop(node_id, None)
            self._remove_scene_item(item)
        layout = self.graph.setdefault("editor", {"groups": [], "comments": []})
        layout["groups"] = [group for group in layout.get("groups", []) if str(group.get("id")) not in group_ids]
        layout["comments"] = [comment for comment in layout.get("comments", []) if str(comment.get("id")) not in comment_ids]
        for group_id in group_ids:
            item = self.group_items.pop(group_id, None)
            self._remove_scene_item(item)
        for comment_id in comment_ids:
            item = self.comment_items.pop(comment_id, None)
            self._remove_scene_item(item)
        self.refresh_connections()
        for node in deleted_nodes:
            self.node_deleted.emit(node)
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
            self.node_added.emit(node)
        self.refresh_connections()
        self.mark_dirty()
        self._update_validation()

    def copy_selected(self) -> bool:
        selected = [item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        if not selected:
            return False
        selected_ids = {item.node_id for item in selected}
        nodes = [deepcopy(item.node) for item in selected]
        edges = [
            deepcopy(edge) for edge in self.graph["edges"]
            if edge["from_node"] in selected_ids and edge["to_node"] in selected_ids
        ]
        payload = {"format": "zennity.logic.selection", "version": 1, "nodes": nodes, "edges": edges}
        text = json.dumps(payload, ensure_ascii=False)
        QApplication.clipboard().setText(text)
        self._logic_clipboard = payload
        self.message.emit("INFO", f"{len(nodes)} nó(s) copiado(s)")
        return True

    def cut_selected(self) -> None:
        if self.copy_selected():
            self.delete_selected()

    def paste_selected(self) -> bool:
        payload = getattr(self, "_logic_clipboard", None)
        try:
            system_payload = json.loads(QApplication.clipboard().text())
            if system_payload.get("format") == "zennity.logic.selection":
                payload = system_payload
        except (AttributeError, TypeError, json.JSONDecodeError):
            pass
        if not isinstance(payload, dict) or not payload.get("nodes"):
            return False
        center = self.view.mapToScene(self.view.viewport().rect().center())
        nodes = deepcopy(payload["nodes"])
        min_x = min(float(node.get("position", [0.0, 0.0])[0]) for node in nodes)
        min_y = min(float(node.get("position", [0.0, 0.0])[1]) for node in nodes)
        id_map: dict[str, str] = {}
        for node in nodes:
            old_id = str(node["id"])
            id_map[old_id] = uuid.uuid4().hex
            node["id"] = id_map[old_id]
            position = node.get("position", [0.0, 0.0])
            node["position"] = [
                center.x() + float(position[0]) - min_x + 24.0,
                center.y() + float(position[1]) - min_y + 24.0,
            ]
        edges = []
        for source in payload.get("edges", []):
            if source.get("from_node") not in id_map or source.get("to_node") not in id_map:
                continue
            edge = deepcopy(source)
            edge["id"] = uuid.uuid4().hex
            edge["from_node"] = id_map[edge["from_node"]]
            edge["to_node"] = id_map[edge["to_node"]]
            edges.append(edge)
        self.scene.clearSelection()
        self.graph["nodes"].extend(nodes)
        self.graph["edges"].extend(edges)
        for node in nodes:
            self._create_node_item(node).setSelected(True)
            self.node_added.emit(node)
        for edge in edges:
            self.edge_added.emit(edge)
        self.refresh_connections()
        self.mark_dirty()
        self._update_validation()
        self.message.emit("INFO", f"{len(nodes)} nó(s) colado(s)")
        return True

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
        self._update_validation()
        self.message.emit("INFO", f"{len(nodes)} nó(s) colado(s)")
        return True

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

    def add_comment_box(self) -> None:
        selected_nodes = [item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        if selected_nodes:
            min_x = min(item.pos().x() for item in selected_nodes) - 20.0
            min_y = min(item.pos().y() for item in selected_nodes) - 40.0
            max_x = max(item.pos().x() + item.width for item in selected_nodes) + 20.0
            max_y = max(item.pos().y() + item.height for item in selected_nodes) + 20.0
            width = max(260.0, max_x - min_x)
            height = max(120.0, max_y - min_y)
            pos = [min_x, min_y]
        else:
            center = self.view.mapToScene(self.view.viewport().rect().center())
            pos = [center.x() - 130.0, center.y() - 60.0]
            width, height = 260.0, 120.0

        comment_data = {
            "id": uuid.uuid4().hex,
            "text": "Lógica do Jogo / Comentário",
            "position": pos,
            "width": width,
            "height": height,
            "color": "#1e3a5f",
        }
        self.graph.setdefault("comments", []).append(comment_data)
        item = LogicCommentItem(self, comment_data)
        self.scene.addItem(item)
        self.comment_items[comment_data["id"]] = item
        self.mark_dirty()
        self.message.emit("INFO", "Caixa de comentário criada (Atalho: C)")

    def auto_arrange_nodes(self) -> None:
        nodes = self.graph.get("nodes", [])
        if not nodes:
            return
        edges = self.graph.get("edges", [])
        graph_map: dict[str, list[str]] = {}
        for edge in edges:
            graph_map.setdefault(edge["from_node"], []).append(edge["to_node"])

        start_nodes = [n for n in nodes if str(n.get("type", "")).startswith("event_") or not any(e["to_node"] == n["id"] for e in edges)]
        visited = set()
        columns: list[list[dict]] = []

        current_layer = start_nodes or nodes[:1]
        while current_layer:
            columns.append(current_layer)
            for n in current_layer:
                visited.add(n["id"])
            next_layer = []
            for n in current_layer:
                for target_id in graph_map.get(n["id"], []):
                    if target_id not in visited:
                        target_node = next((item for item in nodes if item["id"] == target_id), None)
                        if target_node and target_node not in next_layer:
                            next_layer.append(target_node)
            current_layer = next_layer

        unvisited = [n for n in nodes if n["id"] not in visited]
        if unvisited:
            columns.append(unvisited)

        start_x, start_y = 100.0, 100.0
        col_width = 300.0
        row_height = 180.0

        for col_idx, col_nodes in enumerate(columns):
            for row_idx, node in enumerate(col_nodes):
                x = start_x + col_idx * col_width
                y = start_y + row_idx * row_height
                node["position"] = [x, y]
                if node["id"] in self.node_items:
                    self.node_items[node["id"]].setPos(x, y)

        self.refresh_connections()
        self.mark_dirty()
        self.message.emit("INFO", "Grafo re-organizado com sucesso (Auto-Layout Shift+F)")
