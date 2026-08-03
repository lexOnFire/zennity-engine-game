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
from engine.logic.code_preview import node_code_preview
from engine.logic.recipes import build_logic_recipe, find_logic_recipes, logic_recipe
from engine.logic.graph_templates import GRAPH_TEMPLATES, build_logic_template
from engine.prefabs.prefab_asset import load_prefab_asset, resolve_prefab_parameters


from .logic_graph.definitions import (
    CATEGORY_COLORS,
    NODE_DESCRIPTIONS,
    NODE_PROPERTY_LABELS,
    PORT_COLORS,
    PROPERTY_LABELS,
)

from .logic_graph.editor_mixins import (
    LogicGraphPaletteMixin, LogicGraphRuntimeViewMixin, LogicGraphCanvasMixin,
    LogicGraphClipboardMixin, LogicGraphPropertiesMixin, LogicGraphOrganizeMixin,
    LogicGraphPersistenceMixin,
)
from editor.widgets.logic_graph.editor_mixins.blackboard_mixin import LogicGraphBlackboardMixin


class LogicGraphEditor(
    LogicGraphPaletteMixin, LogicGraphRuntimeViewMixin, LogicGraphCanvasMixin, LogicGraphClipboardMixin,
    LogicGraphPropertiesMixin, LogicGraphOrganizeMixin, LogicGraphPersistenceMixin, LogicGraphBlackboardMixin, QWidget,
):
    message = Signal(str, str)
    asset_changed = Signal()
    node_selected = Signal(object)
    node_added = Signal(object)
    node_deleted = Signal(object)
    edge_added = Signal(object)
    debug_command = Signal(str)
    play_requested = Signal()
    stop_requested = Signal()
    # Visible debugger sections retained as part of the official workspace:
    # "CONDIÇÃO DO BREAKPOINT", "OBSERVADORES" and "VALORES EM EXECUÇÃO".
    MAGNET_RADIUS_PIXELS = 42.0

    def __init__(self, project_root: str | Path | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LogicWorkspace")
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.current_path: Path | None = None
        self.graph = default_logic_graph()
        self.node_items: dict[str, LogicNodeItem] = {}
        self.edge_items: list[LogicEdgeItem] = []
        self.group_items: dict[str, LogicGroupItem] = {}
        self.comment_items: dict[str, LogicCommentItem] = {}
        self._connection_origin: LogicPortItem | None = None
        self._connection_candidate: LogicPortItem | None = None
        self._connection_preview: QGraphicsPathItem | None = None
        self._runtime_trace_active = False
        self._palette_category = "Movimento"
        self._blackboard_selected_name = ""
        self._dirty = False
        self._updating_properties = False
        self._history: list[dict[str, Any]] = []
        self._history_index = -1
        self._restoring_history = False
        self._loading_graph = False
        self._history_timer = QTimer(self)
        self._history_timer.setSingleShot(True)
        self._history_timer.setInterval(180)
        self._history_timer.timeout.connect(self._capture_history)
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(700)
        self._autosave_timer.timeout.connect(self._autosave)
        self._build_ui()
        self._connect_ui()
        self.set_graph(self.graph)
        self._category_changed(str(self.category_combo.currentData() or "All"))

    def set_embedded_mode(self, embedded: bool = True) -> None:
        """Show only the production graph surface when hosted by VS 2.0."""
        for widget in (
            getattr(self, "header_widget", None),
            getattr(self, "category_widget", None),
        ):
            if widget is not None:
                widget.setVisible(not embedded)
        # Compatibility-only toolbar: it is intentionally not part of the
        # layout. Never promote it to a top-level window when modes change.
        toolbar = getattr(self, "toolbar_widget", None)
        if toolbar is not None:
            toolbar.hide()
        layout = self.layout()
        if layout is not None:
            layout.setContentsMargins(2, 2, 2, 2)
            layout.setSpacing(2)

    def _build_ui(self) -> None:
        from .logic_graph.ui_builder import build_logic_graph_ui
        build_logic_graph_ui(self)
        qss_path = Path(__file__).parent.parent / "themes" / "modern_logic_graph.qss"
        try: self.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        except OSError: pass
    def _connect_ui(self) -> None:
        self.category_combo.currentIndexChanged.connect(lambda _idx: self._category_changed(str(self.category_combo.currentData() or "")))
        self.node_search.textChanged.connect(lambda _text: self._refresh_palette(str(self.category_combo.currentData() or "")))
        self.palette.itemClicked.connect(lambda item: getattr(self, "help_dock", None) and self.help_dock.show_node_help(item.text()))
        self.palette.itemDoubleClicked.connect(self._add_palette_item)
        self.recipe_search.textChanged.connect(lambda text: self._refresh_recipes(text))
        self.recipe_list.currentItemChanged.connect(self._recipe_selection_changed)
        self.recipe_list.itemDoubleClicked.connect(lambda _item: self._insert_selected_recipe())
        self.recipe_apply_button.clicked.connect(self._insert_selected_recipe)
        self.subgraph_list.itemDoubleClicked.connect(self._add_subgraph_asset)
        self.scene.selectionChanged.connect(self._selection_changed)
        self.property_tree.itemChanged.connect(self._property_changed)
        self.property_tree.itemDoubleClicked.connect(self._choose_exposed_property_asset)
        self.property_asset_button.clicked.connect(self._choose_selected_node_asset)
        self.property_color_button.clicked.connect(self._choose_selected_node_color)
        self.new_button.clicked.connect(self.new_graph)
        self.new_subgraph_button.clicked.connect(self.new_subgraph)
        self.open_button.clicked.connect(self.open_dialog)
        self.save_button.clicked.connect(self.save)
        self.compile_button.clicked.connect(self.validate_graph)
        self.save_as_button.clicked.connect(lambda: self.save(save_as=True))
        self.demo_button.clicked.connect(self.open_demo)
        self.play_button.clicked.connect(self.request_play)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.fit_button.clicked.connect(self.fit_graph)
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)
        self.add_group_button.clicked.connect(self.add_group)
        self.add_comment_button.clicked.connect(self.add_comment)
        self.organize_button.clicked.connect(self.organize_graph)
        self.align_button.clicked.connect(self.align_selected)
        self.distribute_button.clicked.connect(self.distribute_selected)
        self.breakpoint_button.clicked.connect(self.toggle_selected_breakpoint)
        self.continue_debug_button.clicked.connect(lambda: self.debug_command.emit("continue"))
        self.step_debug_button.clicked.connect(lambda: self.debug_command.emit("step"))
        self.restart_debug_button.clicked.connect(lambda: self.debug_command.emit("restart"))
        self.breakpoint_condition_edit.editingFinished.connect(self._update_breakpoint_condition)
        self.add_watch_button.clicked.connect(self._add_watch)
        self.remove_watch_button.clicked.connect(self._remove_watch)
        self.watch_expression_edit.returnPressed.connect(self._add_watch)
        self.blackboard_tree.itemSelectionChanged.connect(self._select_blackboard_variable)
        self.blackboard_tree.itemDoubleClicked.connect(lambda _item, _column: self._add_blackboard_node("get_variable"))
        self.blackboard_save_button.clicked.connect(self._save_blackboard_variable)
        self.blackboard_remove_button.clicked.connect(self._remove_blackboard_variable)
        self.blackboard_get_button.clicked.connect(lambda: self._add_blackboard_node("get_variable"))
        self.blackboard_set_button.clicked.connect(lambda: self._add_blackboard_node("set_variable"))
        self.connect_button.clicked.connect(self.connect_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.target_type.currentIndexChanged.connect(lambda _index: (self.mark_dirty(), self._refresh_target_hints()))
        self.target_value.textChanged.connect(lambda _text: (self.mark_dirty(), self._refresh_target_hints()))
        self.graph_enabled_check.toggled.connect(lambda _checked: self.mark_dirty())
