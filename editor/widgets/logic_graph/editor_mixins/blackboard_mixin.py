from __future__ import annotations
import json
from copy import deepcopy
from typing import Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidgetItem
from engine.logic.blackboard import coerce_variable_value, save_blackboard_asset
from engine.logic.graph_asset import create_logic_node, load_logic_graph

class LogicGraphBlackboardMixin:
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
