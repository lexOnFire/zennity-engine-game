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
from editor.widgets.logic_graph.palette_tree_widget import PaletteTreeWidget
from editor.widgets.logic_graph.node_groups import NODE_GROUPS
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

from engine.logic.recipes import build_logic_recipe, find_logic_recipes, logic_recipe

from engine.localization import tr
from editor.widgets.logic_graph.definitions import (
    CATEGORY_COLORS,
    NODE_DESCRIPTIONS,
    NODE_PROPERTY_LABELS,
    PORT_COLORS,
    PROPERTY_LABELS,
)

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPainterPathStroker, QPen
from PySide6.QtWidgets import QStyle, QStyledItemDelegate

class CategoryNodeDelegate(QStyledItemDelegate):
    """Delegate visual moderno para exibir barra de cor da categoria e chevron na lista."""

    def paint(self, painter: QPainter, option, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = option.rect
        is_selected = bool(option.state & QStyle.State_Selected)
        is_hovered = bool(option.state & QStyle.State_MouseOver)

        if is_selected:
            bg_color = QColor("#272d3e")
        elif is_hovered:
            bg_color = QColor("#1e2330")
        else:
            bg_color = QColor("#161922")

        painter.fillRect(rect, bg_color)

        category_name = index.data(Qt.UserRole + 1) or "Custom"
        color = CATEGORY_COLORS.get(str(category_name), CATEGORY_COLORS["Custom"])
        bar_rect = QRectF(rect.left() + 4.0, rect.top() + 5.0, 3.5, rect.height() - 10.0)
        painter.fillRect(bar_rect, QBrush(color))

        text = str(index.data(Qt.DisplayRole) or "")
        painter.setPen(QPen(QColor("#f1f5f9" if is_selected else "#cbd5e1")))
        font = painter.font()
        font.setPointSizeF(8.8)
        font.setFamily("Segoe UI")
        painter.setFont(font)
        text_rect = QRectF(rect.left() + 15.0, rect.top(), rect.width() - 36.0, rect.height())
        painter.drawText(text_rect, int(Qt.AlignVCenter | Qt.AlignLeft), text)

        painter.setPen(QPen(QColor("#64748b"), 1.4))
        chevron_x = rect.right() - 14.0
        cy = rect.center().y()
        painter.drawLine(int(chevron_x), int(cy - 3), int(chevron_x + 3), int(cy))
        painter.drawLine(int(chevron_x + 3), int(cy), int(chevron_x), int(cy + 3))

        painter.restore()

    def sizeHint(self, option, index) -> QSize:
        return QSize(option.rect.width(), 30)

class LogicGraphPaletteMixin:
    @staticmethod
    def _search_key(value: Any) -> str:
        normalized = unicodedata.normalize("NFKD", str(value).casefold())
        return "".join(character for character in normalized if not unicodedata.combining(character))

    def _refresh_palette(self, category: str | None = None) -> None:
        if category is not None:
            self._palette_category = category
        query = self._search_key(self.node_search.text()).strip()

        # Decidir entre ListWidget (simples) e TreeWidget (agrupado)
        use_tree = not query and NODE_GROUPS and self._palette_category != "All"

        if use_tree:
            self._refresh_palette_tree(category)
        else:
            self._refresh_palette_list(category, query)

    def _refresh_palette_tree(self, category: str | None = None) -> None:
        """Exibe nós em TreeWidget agrupado por NODE_GROUPS."""
        # Filtra NODE_GROUPS pela categoria selecionada
        filtered_groups = {}
        if category and category in NODE_GROUPS:
            filtered_groups = {category: NODE_GROUPS[category]}
        else:
            filtered_groups = NODE_GROUPS

        # Se já existe um TreeWidget, reutiliza-o
        if not isinstance(self.palette, PaletteTreeWidget):
            # Substitui o ListWidget pelo TreeWidget
            parent = self.palette.parent()
            index = parent.layout().indexOf(self.palette)
            self.palette.setParent(None)
            self.palette = PaletteTreeWidget()
            parent.layout().insertWidget(index, self.palette)
            self.palette.item_double_clicked.connect(self._add_palette_item_tree)

        # Popula o TreeWidget
        count = self.palette.populate_with_groups(filtered_groups, "")
        self.palette_count.setText(f"{count} bloco(s) nesta categoria")

    def _refresh_palette_list(self, category: str | None = None, query: str = "") -> None:
        """Exibe nós em ListWidget simples (modo anterior)."""
        # Se existe um TreeWidget, volta para ListWidget
        if isinstance(self.palette, PaletteTreeWidget):
            parent = self.palette.parent()
            index = parent.layout().indexOf(self.palette)
            self.palette.setParent(None)
            self.palette = QListWidget()
            parent.layout().insertWidget(index, self.palette)
            self.palette.itemDoubleClicked.connect(self._add_palette_item)

        self.palette.clear()
        if self.palette.itemDelegate().__class__ != CategoryNodeDelegate:
            self.palette.setItemDelegate(CategoryNodeDelegate(self.palette))

        # Adiciona nós built-in
        for node_type, definition in NODE_DEFINITIONS.items():
            node_category = str(definition.get("category", "Custom"))
            searchable = self._search_key(
                f"{definition.get('title', '')} {node_category} {node_type} "
                f"{' '.join(str(key) for key in definition.get('properties', {}))} "
                f"{NODE_DESCRIPTIONS.get(node_type, '')}"
            )
            if query:
                if query not in searchable:
                    continue
            elif self._palette_category != "All" and node_category != self._palette_category:
                continue
            label = str(definition["title"])
            if query:
                label = f"{label}  —  {node_category}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, node_type)
            item.setData(Qt.UserRole + 1, node_category)
            description = NODE_DESCRIPTIONS.get(node_type, "Arraste as portas para conectar este bloco ao fluxo.")
            item.setToolTip(f"{node_category} • {description}")
            self.palette.addItem(item)

        # Adiciona custom nodes reutilizáveis (.znode)
        from engine.logic.custom_node_registry import get_custom_node_registry
        project_root = getattr(self, "project_path", None)
        custom_registry = get_custom_node_registry(project_root)
        for custom_id, custom_data in custom_registry.nodes.items():
            node_category = "Custom"
            title = custom_data.get("title", custom_id)
            searchable = self._search_key(f"{title} {node_category} {custom_id} custom_node")
            if query:
                if query not in searchable:
                    continue
            elif self._palette_category != "All" and self._palette_category != "Custom":
                continue

            label = f"{title} (Custom)"
            if query:
                label = f"{label}  —  {node_category}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, f"custom_asset:{custom_id}")
            item.setData(Qt.UserRole + 1, node_category)
            item.setToolTip(f"Custom Node • {custom_data.get('execution_model', 'pure_data').upper()}")
            self.palette.addItem(item)

        self.palette_count.setText(f"{self.palette.count()} bloco(s)" + (" encontrados" if query else " nesta categoria"))

    def _add_palette_item_tree(self, item: QTreeWidgetItem) -> None:
        """Adiciona nó clicado no TreeWidget."""
        node_type = item.data(0, Qt.UserRole)
        if not node_type:
            return
        self._add_palette_item(item)

    def _add_palette_item(self, item: Any) -> None:
        if isinstance(item, QTreeWidgetItem):
            raw_data = item.data(0, Qt.UserRole)
        else:
            try:
                raw_data = item.data(Qt.UserRole)
            except TypeError:
                raw_data = item.data(0, Qt.UserRole) if hasattr(item, "data") else None
        node_type = str(raw_data) if raw_data else ""
        if not node_type or node_type == "None":
            return

        center = self.view.mapToScene(self.view.viewport().rect().center())
        offset = len(self.node_items) * 18.0
        pos = (center.x() + offset, center.y() + offset)

        if node_type.startswith("custom_asset:"):
            custom_id = node_type.split("custom_asset:", 1)[1]
            from engine.logic.custom_node_registry import get_custom_node_registry
            project_root = getattr(self, "project_path", None)
            custom_registry = get_custom_node_registry(project_root)
            new_id = f"node_{uuid.uuid4().hex[:6]}"
            node = custom_registry.instantiate_node_data(custom_id, new_id)
            node["position"] = [pos[0], pos[1]]
        else:
            if node_type in UNIQUE_EVENT_TYPES:
                existing = next(
                    (node_item for node_item in self.node_items.values() if node_item.node.get("type") == node_type),
                    None,
                )
                if existing is not None:
                    self.scene.clearSelection()
                    existing.setSelected(True)
                    self.view.centerOn(existing)
                    self.message.emit(
                        "INFO",
                        "Esse evento já existe; conecte outra ação usando a mesma saída",
                    )
                    return
            node = create_logic_node(node_type, pos)

        self.graph["nodes"].append(node)
        self._create_node_item(node)
        self.node_added.emit(node)
        self.mark_dirty()
        self._update_validation()

    def _category_changed(self, category: str) -> None:
        self._refresh_palette(category)
        self._refresh_recipes(self.recipe_search.text(), category)

    def _refresh_recipes(self, query: str = "", topic: str | None = None) -> None:
        selected_topic = str(topic or self.category_combo.currentData() or "Movement")
        topic_label = self.category_combo.currentText() if topic is None else selected_topic
        self.recipe_topic_label.setText(tr(f"graph.categories.{selected_topic.lower()}", topic_label))
        self.recipe_list.clear()
        for recipe in find_logic_recipes(query, "" if selected_topic == "All" else selected_topic):
            item = QListWidgetItem(str(recipe["title"]))
            item.setData(Qt.UserRole, str(recipe["id"]))
            item.setToolTip(f"{recipe['category']} • {recipe['summary']}")
            self.recipe_list.addItem(item)
        if self.recipe_list.count():
            self.recipe_list.setCurrentRow(0)
        else:
            self.recipe_summary.setText(
                f"Nenhuma receita de {selected_topic} encontrada. Tente outra busca ou escolha outro tópico."
            )
            self.recipe_apply_button.setEnabled(False)

    def _recipe_selection_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        recipe_id = str(current.data(Qt.UserRole)) if current is not None else ""
        if not recipe_id:
            self.recipe_apply_button.setEnabled(False)
            return
        recipe = logic_recipe(recipe_id)
        steps = "\n".join(f"{index}. {step}" for index, step in enumerate(recipe["steps"], 1))
        self.recipe_summary.setText(f"{recipe['summary']}\n\n{steps}")
        self.recipe_apply_button.setEnabled(True)

    def _insert_selected_recipe(self) -> None:
        current = self.recipe_list.currentItem()
        recipe_id = str(current.data(Qt.UserRole)) if current is not None else ""
        if not recipe_id:
            return
        center = self.view.mapToScene(self.view.viewport().rect().center())
        fragment = build_logic_recipe(recipe_id, (center.x(), center.y()))
        merged, reused_events = merge_logic_fragment(self.graph_data(), fragment)
        current_path = self.current_path
        self.set_graph(merged, current_path)
        self.mark_dirty()
        recipe = logic_recipe(recipe_id)
        reused_message = f" • {reused_events} evento(s) reutilizado(s)" if reused_events else ""
        self.message.emit("INFO", f"Receita inserida: {recipe['title']}{reused_message}")

    def _refresh_subgraph_assets(self) -> None:
        self.subgraph_list.clear()
        directory = self.project_root / "Assets" / "Logic"
        if not directory.is_dir():
            return
        for path in sorted(directory.rglob("*.zlogic"), key=lambda entry: str(entry).casefold()):
            if path.name.endswith(".autosave.zlogic"):
                continue
            try:
                if self.current_path is not None and path.resolve() == self.current_path.resolve():
                    continue
                graph = load_logic_graph(path)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            if not any(node.get("type") == "subgraph_start" for node in graph.get("nodes", [])):
                continue
            interface = subgraph_interface(graph)
            item = QListWidgetItem(
                f"{graph.get('name', path.stem)}  ·  {len(interface['inputs'])} entrada(s) / {len(interface['outputs'])} saída(s)"
            )
            item.setData(Qt.UserRole, path.relative_to(self.project_root).as_posix())
            item.setData(Qt.UserRole + 1, interface)
            item.setToolTip(path.relative_to(self.project_root).as_posix())
            self.subgraph_list.addItem(item)

    def _add_subgraph_asset(self, item: QListWidgetItem) -> None:
        path = str(item.data(Qt.UserRole) or "").strip()
        interface = item.data(Qt.UserRole + 1)
        if not path or not isinstance(interface, dict):
            return
        center = self.view.mapToScene(self.view.viewport().rect().center())
        node = create_logic_node("call_subgraph", (center.x(), center.y()))
        node["title"] = f"Executar {Path(path).stem}"
        node["properties"] = {
            "path": path,
            "inputs": deepcopy(interface.get("inputs", [])),
            "outputs": deepcopy(interface.get("outputs", [])),
        }
        self.graph["nodes"].append(node)
        self.scene.clearSelection()
        self._create_node_item(node).setSelected(True)
        self.node_added.emit(node)
        self.mark_dirty()
        self._update_validation()
        self.message.emit("INFO", f"Subgrafo adicionado: {Path(path).stem}")

    def _sync_subgraph_call_interfaces(self, graph: dict[str, Any]) -> None:
        """Mantém chamadas existentes alinhadas ao asset reutilizável salvo."""
        for node in graph.get("nodes", []):
            if node.get("type") != "call_subgraph":
                continue
            properties = node.setdefault("properties", {})
            path = Path(str(properties.get("path", "")))
            if not path.is_absolute():
                path = self.project_root / path
            try:
                resolved = path.resolve()
                if not resolved.is_relative_to(self.project_root) or not resolved.is_file():
                    continue
                interface = subgraph_interface(load_logic_graph(resolved))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            properties["inputs"] = deepcopy(interface["inputs"])
            properties["outputs"] = deepcopy(interface["outputs"])

    def _create_node_item(self, node: dict[str, Any]) -> LogicNodeItem:
        item = LogicNodeItem(self, node)
        self.scene.addItem(item)
        self.node_items[item.node_id] = item
        return item

    def _create_group_item(self, data: dict[str, Any]) -> LogicGroupItem:
        item = LogicGroupItem(self, data)
        self.scene.addItem(item)
        self.group_items[item.group_id] = item
        return item

    def _create_comment_item(self, data: dict[str, Any]) -> LogicCommentItem:
        item = LogicCommentItem(self, data)
        self.scene.addItem(item)
        self.comment_items[item.comment_id] = item
        return item

