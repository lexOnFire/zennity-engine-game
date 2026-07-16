from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_logic_and_animation_use_independent_windows_not_viewport_tabs():
    interface = _source("editor/interface_smoke_test.py")
    editor = _source("editor/isolated_editor_main.py")
    assert 'self.viewport_tabs.addTab(QWidget(), "Animation")' not in interface
    assert 'self.viewport_tabs.addTab(QWidget(), "Logic")' not in interface
    assert "class DetachedWorkspaceWindow(QMainWindow)" in interface
    assert "self.animation_window = DetachedWorkspaceWindow" in interface
    assert "self.logic_window = DetachedWorkspaceWindow" in interface
    assert "self.logic_workspace = LogicGraphEditor()" in interface
    assert "def _show_logic_window" in editor
    assert "def _show_animation_window" in editor
    assert 'editor_icon("play")' in editor
    assert 'editor_icon("snap")' in editor
    assert 'editor_icon("animation")' not in editor
    assert 'editor_icon("script")' not in editor
    assert 'component == "logic"' not in editor


def test_python_script_component_is_not_offered_or_executed() -> None:
    picker = _source("editor/widgets/component_picker.py")
    viewport = _source("editor/isolated_viewport.py")
    assert '("Código", "Script", "script"' not in picker
    assert "scripts Python estão desativados" in viewport
    assert "hydrate_logic_graphs(objects, Path.cwd())" in viewport


def test_logic_workspace_exposes_palette_canvas_connections_and_properties():
    source = _source("editor/widgets/logic_graph_editor.py")
    assert "class LogicGraphView(QGraphicsView)" in source
    assert "class LogicNodeItem(QGraphicsRectItem)" in source
    assert "class LogicPortItem(QGraphicsEllipseItem)" in source
    assert "class LogicEdgeItem(QGraphicsPathItem)" in source
    assert "def begin_connection" in source
    assert "def finish_connection" in source
    assert "def cancel_connection" in source
    assert "MAGNET_RADIUS_PIXELS" in source
    assert "def _nearest_compatible_port" in source
    assert "self._connection_candidate" in source
    assert 'set_connection_state("candidate")' in source
    assert "_ports_compatible" in source
    assert "Qt.Key_Delete" in source
    assert "def duplicate_selected" in source
    assert "QPainterPathStroker" in source
    assert "self._autosave_timer" in source
    assert "Conectar selecionados" in source
    for category in ("Movimento", "Ação", "Lógica", "Condição", "Eventos", "Objetos", "Variáveis"):
        assert category in source
    assert "QPainterPath" in source
    assert "self.property_tree.itemChanged.connect" in source


def test_logic_workspace_can_create_open_save_and_load_demo():
    source = _source("editor/widgets/logic_graph_editor.py")
    assert "default_logic_graph" in source
    assert "load_logic_graph" in source
    assert "save_logic_graph" in source
    assert '"PlayerMovement.zlogic"' in source


def test_logic_workspace_receives_throttled_runtime_debug_traces():
    editor = _source("editor/widgets/logic_graph_editor.py")
    viewport = _source("editor/isolated_viewport.py")
    bridge = _source("editor/isolated_editor_main.py")
    assert "def apply_runtime_trace" in editor
    assert "def clear_runtime_trace" in editor
    assert "set_runtime_state" in editor
    assert "set_runtime_active" in editor
    assert "VALORES EM EXECUÇÃO" in editor
    assert "trace_now - logic_trace_last_sent >= 0.10" in viewport
    assert '"type": "logic_trace"' in viewport
    assert 'message.get("type") == "logic_trace"' in bridge


def test_logic_workspace_supports_breakpoints_continue_and_single_step():
    editor = _source("editor/widgets/logic_graph_editor.py")
    viewport = _source("editor/isolated_viewport.py")
    bridge = _source("editor/isolated_editor_main.py")
    runtime = _source("engine/logic/runtime.py")
    assert "def toggle_breakpoint" in editor
    assert "● Breakpoint" in editor
    assert "Próximo nó" in editor
    assert 'self.debug_command.emit("continue")' in editor
    assert 'self.debug_command.emit("step")' in editor
    assert "self.logic_workspace.debug_command.connect" in bridge
    assert 'command.get("type") == "logic_debug_command"' in viewport
    assert "runtime.continue_execution()" in viewport
    assert "runtime.step()" in viewport
    assert "def continue_execution" in runtime
    assert "def step" in runtime
    assert "runtime.debug_paused" in viewport


def test_logic_debugger_exposes_conditions_watches_highlight_and_restart():
    editor = _source("editor/widgets/logic_graph_editor.py")
    viewport = _source("editor/isolated_viewport.py")
    bridge = _source("editor/isolated_editor_main.py")
    runtime = _source("engine/logic/runtime.py")
    assert "CONDIÇÃO DO BREAKPOINT" in editor
    assert "OBSERVADORES" in editor
    assert "PAUSADO ANTES DE EXECUTAR" in editor
    assert 'self.debug_command.emit("restart")' in editor
    assert "_update_breakpoint_condition" in editor
    assert "_refresh_watch_values" in editor
    assert 'debug_action == "restart"' in viewport
    assert '"breakpoint_conditions"' in bridge
    assert '"watches"' in bridge
    assert "def _evaluate_debug_expression" in runtime
    assert "def restart" in runtime


def test_logic_workspace_exposes_typed_scoped_blackboard_panel():
    editor = _source("editor/widgets/logic_graph_editor.py")
    viewport = _source("editor/isolated_viewport.py")
    bridge = _source("editor/isolated_editor_main.py")
    assert "BLACKBOARD" in editor
    assert "blackboard_scope_combo" in editor
    assert "blackboard_type_combo" in editor
    assert "_save_blackboard_variable" in editor
    assert "_add_blackboard_node" in editor
    assert "ProjectBlackboard.zblackboard" in editor
    assert "BlackboardStore" in viewport
    assert "scene_blackboard" in viewport
    assert 'self._collect_logic_variables("scene")' in bridge


def test_visual_event_nodes_are_shared_debuggable_and_exportable():
    graph = _source("engine/logic/graph_asset.py")
    runtime = _source("engine/logic/runtime.py")
    viewport = _source("editor/isolated_viewport.py")
    editor = _source("editor/widgets/logic_graph_editor.py")
    assert '"event_custom"' in graph
    assert '"emit_event"' in graph
    assert "LogicEventBus" in runtime
    assert "_receive_custom_event" in runtime
    assert '"events": list(self.event_bus.recent' in runtime
    assert "logic_event_bus.dispatch()" in viewport
    assert 'f"evento:{event.get' in editor
