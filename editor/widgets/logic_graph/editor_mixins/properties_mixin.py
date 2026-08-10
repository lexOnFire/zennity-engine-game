"""Workspace visual para criar e editar assets ``.zlogic``."""

from __future__ import annotations

import json
import unicodedata
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
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
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
from editor.widgets.logic_asset_picker import ASSET_KINDS, LogicAssetPickerDialog
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

from engine.prefabs.prefab_asset import load_prefab_asset, resolve_prefab_parameters

from editor.widgets.logic_graph.definitions import (
    CATEGORY_COLORS,
    NODE_DESCRIPTIONS,
    NODE_PROPERTY_LABELS,
    PORT_COLORS,
    PROPERTY_LABELS,
)

class LogicGraphPropertiesMixin:
    CODE_EDITABLE_PROPERTIES = {
        "compare_number": (("value", "Comparison value"),),
        "cooldown": (("seconds", "Cooldown seconds"),),
        "create_object": (
            ("x", "X position"),
            ("y", "Y position"),
            ("max_instances", "Max instances"),
            ("lifetime", "Lifetime seconds"),
        ),
        "destroy_after_time": (("seconds", "Lifetime seconds"),),
        "event_timer": (("seconds", "Timer seconds"),),
        "jump": (("force", "Jump force"),),
        "move": (("speed", "Movement speed"),),
        "move_by": (("x", "X speed"), ("y", "Y speed")),
        "number_value": (("value", "Number value"),),
        "patrol_axis": (
            ("minimum", "Minimum position"),
            ("maximum", "Maximum position"),
            ("speed", "Patrol speed"),
        ),
        "rotate": (("degrees", "Rotation degrees"),),
        "set_position": (("x", "X position"), ("y", "Y position")),
        "start_continuous_motion": (("x", "X speed"), ("y", "Y speed")),
        "start_texture_scroll": (("speed_x", "Texture scroll X speed"), ("speed_y", "Texture scroll Y speed")),
        "update_continuous_motion": (("x", "X speed"), ("y", "Y speed")),
    }

    def edit_node_code_value(self, node_item: LogicNodeItem) -> bool:
        node_type = str(node_item.node.get("type", ""))
        edit_fields = self.CODE_EDITABLE_PROPERTIES.get(node_type)
        if edit_fields is None:
            self.message.emit("INFO", "Select the node and edit its values in Properties.")
            return False
        properties = node_item.node.setdefault("properties", {})
        updates = self._request_code_value_edits(node_item.node, edit_fields, properties)
        if updates is None:
            return True
        for key, value in updates.items():
            properties[key] = self._coerce_code_edit_value(properties.get(key), value)
        node_item.refresh_text()
        self._selection_changed()
        self.mark_dirty()
        self._update_validation()
        self.message.emit("INFO", f"Updated code values for {node_item.node.get('title', node_type)}")
        return True

    def _request_code_value_edits(
        self,
        node: dict[str, Any],
        fields: tuple[tuple[str, str], ...],
        properties: dict[str, Any],
    ) -> dict[str, float] | None:
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit {node.get('title', 'node')} code values")
        form = QFormLayout(dialog)
        editors: dict[str, QDoubleSpinBox] = {}
        for key, label in fields:
            editor = QDoubleSpinBox(dialog)
            editor.setDecimals(3)
            editor.setRange(-1_000_000.0, 1_000_000.0)
            editor.setKeyboardTracking(False)
            current = properties.get(key, 0)
            editor.setValue(self._safe_code_float(current))
            form.addRow(label, editor)
            editors[key] = editor
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.Accepted:
            return None
        return {key: editor.value() for key, editor in editors.items()}

    @staticmethod
    def _safe_code_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _coerce_code_edit_value(current: Any, value: float) -> int | float:
        if isinstance(current, int) and float(value).is_integer():
            return int(value)
        return int(value) if float(value).is_integer() else value

    def _selection_changed(self) -> None:
        selected = [item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        selected_groups = [item for item in self.scene.selectedItems() if isinstance(item, LogicGroupItem)]
        self._updating_properties = True
        self.property_tree.clear()

        if len(selected_groups) == 1 and not selected:
            group_item = selected_groups[0]
            group_data = group_item.group_data
            title = str(group_data.get("title", "Grupo"))
            color = str(group_data.get("color", "#2d3545"))

            self.selected_label.setText(f"{title}\nOrganização • Grupo")
            if hasattr(self, "validation_badge"):
                self.validation_badge.setText("Grupo  📁")
                self.validation_badge.setStyleSheet("color: #3b82f6; font-weight: bold; font-size: 11px;")

            self.property_asset_button.hide()
            self.property_color_button.show()
            self.property_color_button.setText("Escolher cor do grupo...")
            self.property_color_button.setStyleSheet(f"border-left: 18px solid {color};")
            self.breakpoint_condition_edit.clear()
            self.breakpoint_condition_edit.setEnabled(False)

            title_item = QTreeWidgetItem(["title", title])
            title_item.setData(0, Qt.UserRole, "group_title")
            title_item.setFlags(title_item.flags() | Qt.ItemIsEditable)
            self.property_tree.addTopLevelItem(title_item)

            color_item = QTreeWidgetItem(["color", color])
            color_item.setData(0, Qt.UserRole, "group_color")
            color_item.setToolTip(1, "Use o seletor visual de cor abaixo")
            color_item.setFlags(color_item.flags() | Qt.ItemIsEditable)
            self.property_tree.addTopLevelItem(color_item)

            self._updating_properties = False
            return

        if len(selected) != 1:
            self.selected_label.setText("Selecione um nó para editar seus valores")
            if hasattr(self, "validation_badge"):
                self.validation_badge.setText("Sem seleção")
                self.validation_badge.setStyleSheet("color: #64748b; font-weight: bold; font-size: 11px;")
            self.property_asset_button.hide()
            self.property_color_button.hide()
            self.breakpoint_condition_edit.clear()
            self.breakpoint_condition_edit.setEnabled(False)
            self._updating_properties = False
            self.node_selected.emit(None)
            return
        node = selected[0].node
        if hasattr(self, "validation_badge"):
            self.validation_badge.setText("Válido  ✓")
            self.validation_badge.setStyleSheet("color: #22c55e; font-weight: bold; font-size: 11px;")
        self.node_selected.emit(node)
        asset_kind = self._asset_kind_for_node(str(node.get("type", "")))
        self.property_asset_button.setVisible(asset_kind is not None)
        color_property = next(
            (
                key for key in ("color", "background_color")
                if key in node.get("properties", {})
            ),
            None,
        )
        self.property_color_button.setVisible(color_property is not None)
        if color_property is not None:
            color = self._qcolor(node["properties"].get(color_property))
            self.property_color_button.setText(
                "Escolher cor de fundo..."
                if color_property == "background_color"
                else "Escolher cor..."
            )
            self.property_color_button.setStyleSheet(
                f"border-left: 18px solid {color.name()};"
            )
        if asset_kind is not None:
            asset_label = ASSET_KINDS[asset_kind][0]
            self.property_asset_button.setText(f"Escolher {asset_label}...")
            self.property_asset_button.setToolTip(
                f"Abre a biblioteca de {asset_label.lower()} do projeto"
            )
        asset_property = (
            "texture"
            if str(node.get("type", "")) in {
                "create_object", "add_sprite_renderer",
            }
            else "path"
        )
        node_type = str(node.get("type", ""))
        definition = NODE_DEFINITIONS.get(node_type, {})
        if definition:
            if str(node.get("category", "")).casefold() in {"custom", ""}:
                node["category"] = definition.get("category", "Custom")
            if str(node.get("title", "")) in {node_type, ""}:
                node["title"] = definition.get("title", node_type)

        self.selected_label.setText(f"{node.get('title', node_type)}\n{node.get('category', 'Custom')} • {node_type}")
        if hasattr(self, "help_dock") and self.help_dock is not None:
            try:
                self.help_dock.show_node_help(node.get("type") or node["title"])
            except Exception:
                pass
        breakpoints = self.graph.get("debug", {}).get("breakpoints", [])
        has_breakpoint = str(node["id"]) in breakpoints
        condition = self.graph.get("debug", {}).get("breakpoint_conditions", {}).get(str(node["id"]), "")
        self.breakpoint_condition_edit.setEnabled(has_breakpoint)
        self.breakpoint_condition_edit.setText(str(condition))
        default_props = definition.get("properties", {})
        properties = node.setdefault("properties", {})
        for prop_key, prop_val in default_props.items():
            if prop_key not in properties:
                properties[prop_key] = deepcopy(prop_val)

        ports = node_port_definitions(node_type)
        inputs = definition.get("inputs") or ports.get("inputs", [])
        for pin in inputs:
            if isinstance(pin, (list, tuple)) and len(pin) >= 2:
                pin_id, pin_type = str(pin[0]), str(pin[1])
                if pin_type not in {"flow", "exec"} and pin_id not in properties:
                    if pin_id == "widget_name":
                        properties[pin_id] = "comida"
                    elif pin_id == "variable_name":
                        properties[pin_id] = "comida"
                    elif pin_id == "property":
                        properties[pin_id] = "value"
                    elif pin_id == "parent":
                        properties[pin_id] = "Panel_HUD"
                    elif pin_id == "value":
                        properties[pin_id] = "Novo Texto"
                    elif pin_id == "target":
                        properties[pin_id] = ""
                    elif pin_type == "number":
                        properties[pin_id] = 0.0
                    elif pin_type == "bool":
                        properties[pin_id] = True
                    else:
                        properties[pin_id] = ""

        title_item = QTreeWidgetItem(["title", str(node["title"])])
        title_item.setData(0, Qt.UserRole, "title")
        title_item.setFlags(title_item.flags() | Qt.ItemIsEditable)
        self.property_tree.addTopLevelItem(title_item)
        for key, value in properties.items():
            if key in {"exposed_properties", "parameters"}:
                continue
            item = QTreeWidgetItem([
                NODE_PROPERTY_LABELS.get(node_type, {}).get(
                    str(key), PROPERTY_LABELS.get(str(key), str(key))
                ),
                json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value,
            ])
            item.setData(0, Qt.UserRole, str(key))
            if str(key) == color_property:
                item.setToolTip(1, "Use o seletor visual de cor abaixo")
            elif asset_kind is not None and str(key) == asset_property:
                item.setToolTip(1, "Use o botão abaixo para escolher na biblioteca")
            else:
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
                if str(definition.get("asset_kind", "")) in ASSET_KINDS:
                    item.setToolTip(1, "Dê duplo clique para escolher na biblioteca")
                else:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.property_tree.addTopLevelItem(item)
        self._updating_properties = False

    @staticmethod
    def _asset_kind_for_node(node_type: str) -> str | None:
        return {
            "set_sprite": "image",
            "set_texture_scroll": "image",
            "start_texture_scroll": "image",
            "create_object": "image",
            "create_prefab": "prefab",
            "call_subgraph": "logic",
            "start_behavior_tree": "behavior",
            "play_animation_asset": "animation",
            "play_sound": "audio",
            "add_sprite_renderer": "image",
            "add_animator": "animation",
            "add_audio_source": "audio",
            "add_ui_image": "image",
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
        if str(node.get("type", "")) == "add_sprite_renderer":
            property_name = "texture"
        node.setdefault("properties", {})[property_name] = picker.selected_path
        if str(node.get("type", "")) == "create_prefab":
            self._sync_prefab_node_interface(node)
            old_item = selected[0]
            self._remove_scene_item(old_item)
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

    @staticmethod
    def _qcolor(value: Any) -> QColor:
        if isinstance(value, str):
            color = QColor(value)
            return color if color.isValid() else QColor("#ffffff")
        if isinstance(value, (list, tuple)) and len(value) >= 3:
            try:
                return QColor(*(int(channel) for channel in value[:3]))
            except (TypeError, ValueError):
                pass
        return QColor("#ffffff")

    def _choose_selected_node_color(self) -> None:
        selected = [
            item for item in self.scene.selectedItems()
            if isinstance(item, LogicNodeItem)
        ]
        selected_groups = [
            item for item in self.scene.selectedItems()
            if isinstance(item, LogicGroupItem)
        ]

        if len(selected_groups) == 1 and not selected:
            group_item = selected_groups[0]
            current_color = QColor(str(group_item.group_data.get("color", "#2d3545")))
            chosen = QColorDialog.getColor(current_color, self, "Escolher Cor do Grupo")
            if chosen.isValid():
                group_item.group_data["color"] = chosen.name()
                group_item._apply_style()
                self._selection_changed()
                self.mark_dirty()
                self.message.emit("INFO", f"Cor do grupo atualizada: {chosen.name()}")
            return

        if len(selected) != 1:
            return
        node_item = selected[0]
        properties = node_item.node.setdefault("properties", {})
        key = next(
            (name for name in ("color", "background_color") if name in properties),
            None,
        )
        if key is None:
            return
        chosen = QColorDialog.getColor(
            self._qcolor(properties.get(key)),
            self,
            "Escolher cor",
        )
        if not chosen.isValid():
            return
        properties[key] = (
            [chosen.red(), chosen.green(), chosen.blue()]
            if key == "background_color"
            else chosen.name()
        )
        node_item.refresh_text()
        self._selection_changed()
        self.mark_dirty()
        self._update_validation()
        self.message.emit("INFO", f"Cor atualizada: {chosen.name()}")

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
        selected_groups = [entry for entry in self.scene.selectedItems() if isinstance(entry, LogicGroupItem)]

        if len(selected_groups) == 1 and not selected:
            group_item = selected_groups[0]
            key = str(item.data(0, Qt.UserRole) or item.text(0))
            text = item.text(1).strip()
            if key in {"group_title", "title"}:
                group_item.title_item.setPlainText(text)
                group_item.group_data["title"] = text
                self.selected_label.setText(f"{text}\nOrganização • Grupo")
            elif key in {"group_color", "color"}:
                group_item.group_data["color"] = text
                group_item._apply_style()
            self.mark_dirty()
            return

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
            self._remove_scene_item(node_item)
            self.node_items.pop(node_item.node_id, None)
            self.scene.clearSelection()
            node_item = self._create_node_item(node)
            node_item.setSelected(True)
            self.refresh_connections()
        if key == "type" and node_item.node.get("type") in {"subgraph_input", "subgraph_return"}:
            node = node_item.node
            self._remove_scene_item(node_item)
            self.node_items.pop(node_item.node_id, None)
            self.scene.clearSelection()
            self._create_node_item(node).setSelected(True)
            self.refresh_connections()
        else:
            node_item.refresh_text()
        self.mark_dirty()
        self._update_validation()

    def _choose_exposed_property_asset(self, item: QTreeWidgetItem, column: int) -> None:
        key = str(item.data(0, Qt.UserRole) or "")
        if not key.startswith("prefab_parameter:"):
            if item.flags() & Qt.ItemIsEditable:
                self.property_tree.editItem(item, 1)
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
            if item.flags() & Qt.ItemIsEditable:
                self.property_tree.editItem(item, 1)
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


