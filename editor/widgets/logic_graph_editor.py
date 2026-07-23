"""Workspace visual para criar e editar assets ``.zlogic``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QTimer, Signal
from .logic_graph.items import (
    LogicPortItem, LogicEdgeItem, LogicGroupItem,
    LogicCommentItem, LogicNodeItem
)
from PySide6.QtWidgets import (
    QGraphicsPathItem,
    QWidget,
)

from engine.logic.graph_asset import (
    default_logic_graph,
)



from .logic_graph.editor_mixins import (
    LogicGraphPaletteMixin, LogicGraphRuntimeViewMixin, LogicGraphCanvasMixin,
    LogicGraphPropertiesMixin, LogicGraphPersistenceMixin,
)
from editor.widgets.logic_graph.editor_mixins.blackboard_mixin import LogicGraphBlackboardMixin


class LogicGraphEditor(
    LogicGraphPaletteMixin, LogicGraphRuntimeViewMixin, LogicGraphCanvasMixin,
    LogicGraphPropertiesMixin, LogicGraphPersistenceMixin, LogicGraphBlackboardMixin, QWidget,
):
    message = Signal(str, str)
    asset_changed = Signal()
    debug_command = Signal(str)
    play_requested = Signal()
    stop_requested = Signal()
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

    def _build_ui(self) -> None:
        from .logic_graph.ui_builder import build_logic_graph_ui

        build_logic_graph_ui(self)
    def _connect_ui(self) -> None:
        self.category_combo.currentTextChanged.connect(self._category_changed)
        self.node_search.textChanged.connect(lambda _text: self._refresh_palette())
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
        self.new_button.clicked.connect(self.new_graph)
        self.new_subgraph_button.clicked.connect(self.new_subgraph)
        self.open_button.clicked.connect(self.open_dialog)
        self.save_button.clicked.connect(self.save)
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

