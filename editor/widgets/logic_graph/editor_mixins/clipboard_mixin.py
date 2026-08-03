"""Clipboard and duplication operations for the visual logic canvas."""
from __future__ import annotations

import json
import uuid
from copy import deepcopy

from PySide6.QtWidgets import QApplication

from editor.widgets.logic_graph.items import LogicNodeItem


class LogicGraphClipboardMixin:
    def duplicate_selected(self) -> None:
        selected = [item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        if not selected:
            return
        old_ids = {item.node_id for item in selected}
        id_map = {item.node_id: uuid.uuid4().hex for item in selected}
        copies = []
        for item in selected:
            node = deepcopy(item.node)
            node["id"] = id_map[item.node_id]
            node["position"] = [float(item.pos().x()) + 32.0, float(item.pos().y()) + 32.0]
            copies.append(node)
        copied_edges = []
        for source in self.graph["edges"]:
            if source["from_node"] not in old_ids or source["to_node"] not in old_ids:
                continue
            edge = deepcopy(source)
            edge.update(
                id=uuid.uuid4().hex,
                from_node=id_map[source["from_node"]],
                to_node=id_map[source["to_node"]],
            )
            copied_edges.append(edge)
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
        QApplication.clipboard().setText(json.dumps(payload, ensure_ascii=False))
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
        id_map = {}
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
            edge.update(
                id=uuid.uuid4().hex,
                from_node=id_map[source["from_node"]],
                to_node=id_map[source["to_node"]],
            )
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
