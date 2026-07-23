"""Workspace visual para criar e editar assets ``.zlogic``."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from editor.widgets.logic_graph.items import (
    LogicNodeItem
)
from PySide6.QtWidgets import (
    QInputDialog,
    QTreeWidgetItem,
)

from editor.widgets.logic_asset_picker import LogicAssetPickerDialog

from engine.prefabs.prefab_asset import load_prefab_asset, resolve_prefab_parameters

from editor.widgets.logic_graph.definitions import (
    NODE_PROPERTY_LABELS,
    PROPERTY_LABELS,
)

class LogicGraphPropertiesMixin:
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
            if key in {"exposed_properties", "parameters"}:
                continue
            item = QTreeWidgetItem([
                NODE_PROPERTY_LABELS.get(str(node.get("type", "")), {}).get(
                    str(key), PROPERTY_LABELS.get(str(key), str(key))
                ),
                json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value,
            ])
            item.setData(0, Qt.UserRole, str(key))
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.property_tree.addTopLevelItem(item)
        if str(node.get("type", "")) == "create_prefab":
            exposed = node.get("properties", {}).get("exposed_properties", [])
            parameters = node.get("properties", {}).get("parameters", {})
            for definition in exposed if isinstance(exposed, list) else []:
                if not isinstance(definition, dict):
                    continue
                name = str(definition.get("name", "")).strip()
                if not name:
                    continue
                value = parameters.get(name, definition.get("default")) if isinstance(parameters, dict) else definition.get("default")
                item = QTreeWidgetItem([
                    f"Prefab • {definition.get('label', name)}",
                    json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value,
                ])
                item.setData(0, Qt.UserRole, f"prefab_parameter:{name}")
                item.setToolTip(0, str(definition.get("description", definition.get("target", ""))))
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
        if str(node.get("type", "")) == "create_prefab":
            self._sync_prefab_node_interface(node)
            old_item = selected[0]
            self.scene.removeItem(old_item)
            self.node_items.pop(old_item.node_id, None)
            self.scene.clearSelection()
            selected = [self._create_node_item(node)]
            selected[0].setSelected(True)
            self.refresh_connections()
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
        if key.startswith("prefab_parameter:"):
            name = key.split(":", 1)[1]
            node_item.node.setdefault("properties", {}).setdefault("parameters", {})[name] = value
        elif key == "title":
            node_item.node["title"] = str(value)
            node_item.title_item.setPlainText(str(value))
        else:
            node_item.node.setdefault("properties", {})[key] = value
        if key == "path" and str(node_item.node.get("type", "")) == "create_prefab":
            self._sync_prefab_node_interface(node_item.node)
            node = node_item.node
            self.scene.removeItem(node_item)
            self.node_items.pop(node_item.node_id, None)
            self.scene.clearSelection()
            node_item = self._create_node_item(node)
            node_item.setSelected(True)
            self.refresh_connections()
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

    def _choose_exposed_property_asset(self, item: QTreeWidgetItem, column: int) -> None:
        if column not in {0, 1}:
            return
        key = str(item.data(0, Qt.UserRole) or "")
        if not key.startswith("prefab_parameter:"):
            return
        selected = [entry for entry in self.scene.selectedItems() if isinstance(entry, LogicNodeItem)]
        if len(selected) != 1:
            return
        node = selected[0].node
        name = key.split(":", 1)[1]
        definitions = node.get("properties", {}).get("exposed_properties", [])
        definition = next(
            (entry for entry in definitions if isinstance(entry, dict) and str(entry.get("name")) == name), None
        )
        if not isinstance(definition, dict):
            return
        asset_kind = str(definition.get("asset_kind", ""))
        if asset_kind not in {"image", "animation", "audio"}:
            return
        picker = LogicAssetPickerDialog(self.project_root, asset_kind, self)
        if not picker.exec() or not picker.selected_path:
            return
        self._updating_properties = True
        item.setText(1, picker.selected_path)
        self._updating_properties = False
        node.setdefault("properties", {}).setdefault("parameters", {})[name] = picker.selected_path
        selected[0].refresh_text()
        self.mark_dirty()
        self._update_validation()
        self.message.emit("INFO", f"Asset definido em {definition.get('label', name)}: {picker.selected_path}")

    def _sync_prefab_node_interface(self, node: dict[str, Any]) -> bool:
        if str(node.get("type", "")) != "create_prefab":
            return False
        properties = node.setdefault("properties", {})
        path = Path(str(properties.get("path", "")))
        if not str(path):
            return False
        if not path.is_absolute():
            path = self.project_root / path
        try:
            asset = load_prefab_asset(path, self.project_root)
        except (OSError, ValueError, json.JSONDecodeError):
            return False
        definitions = deepcopy(asset.get("exposed_properties", []))
        previous = properties.get("parameters", {})
        properties["exposed_properties"] = definitions
        properties["parameters"] = resolve_prefab_parameters(definitions, previous)
        return True

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

