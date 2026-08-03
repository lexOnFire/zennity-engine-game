from pathlib import Path

from editor.services.shortcut_service import ShortcutService


ROOT = Path(__file__).resolve().parents[2]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_phase1_main_is_thin_official_entrypoint() -> None:
    source = _source("editor/phase1_main.py")
    assert "from editor.editor_app.application import main as run_editor" in source
    assert "isolated_editor_main" not in source
    assert "ZennityPhase1Editor" not in source


def test_editor_app_keeps_legacy_embedded_as_explicit_mode() -> None:
    application = _source("editor/editor_app/application.py")
    bootstrap = _source("editor/editor_app/bootstrap.py")
    assert '"--legacy-embedded" in args' in application
    assert "run_isolated_editor()" in application
    assert "run_legacy_embedded_editor(args)" in application
    assert "ZennityPhase1Editor" in bootstrap


def test_standard_shortcuts_cover_phase1_migration_block() -> None:
    bindings = {binding.command_id: binding.sequence for binding in ShortcutService.STANDARD_BINDINGS}
    assert bindings == {
        "tool.select": "Q",
        "tool.move": "W",
        "tool.rotate": "E",
        "tool.scale": "R",
        "edit.duplicate": "Ctrl+D",
        "edit.undo": "Ctrl+Z",
        "edit.redo": "Ctrl+Y",
        "edit.delete": "Delete",
        "viewport.focus_selected": "F",
        "viewport.toggle_grid": "G",
    }


def test_tool_controller_uses_shortcut_service_and_tool_manager() -> None:
    source = _source("editor/controllers/tool_controller.py")
    viewport = _source("editor/controllers/viewport_controller.py")
    bootstrap = _source("editor/editor_bootstrap_controller.py")
    assert "ShortcutService(host)" in source
    assert "ShortcutService.STANDARD_BINDINGS" in source
    assert "h.editor_context.tools.set_active_tool(next_tool)" in source
    assert "h._viewport_commands.set_tool(next_tool)" in source
    assert "h._scene_objects.duplicate_selected()" in source
    assert "h._scene_objects.delete(h._selected_name)" in source
    assert '"viewport.focus_selected": self.focus_selected' in source
    assert '"viewport.toggle_grid": self.toggle_grid' in source
    assert "class ViewportController" in viewport
    assert '"type": "set_snap"' in viewport
    assert "h._viewport_commands = ViewportController(h)" in bootstrap
    assert "h._tool_controller = ToolController(h)" in bootstrap
    assert "h._tool_controller.configure()" in bootstrap


def test_phase1_uses_selection_controller_for_hierarchy_selection() -> None:
    hierarchy = _source("editor/hierarchy_controller.py")
    selection = _source("editor/controllers/selection_controller.py")
    viewport_events = _source("editor/viewport_event_controller.py")
    bootstrap = _source("editor/editor_bootstrap_controller.py")
    assert "class EditorSelectionController" in selection
    assert "h._selection = EditorSelectionController(h)" in bootstrap
    assert "h._selection.select(name, source=source)" in hierarchy
    assert "self.host._selection.select_for_action(name)" in hierarchy
    assert 'self.host._selection.select(str(message["name"]), source="Viewport")' in viewport_events


def test_inspector_component_controller_uses_selection_facade() -> None:
    inspector = _source("editor/inspector_controller.py")
    inspector_media = _source("editor/inspector_controller_ui_media.py")
    selection = _source("editor/controllers/selection_controller.py")
    assert "return self.host._selection.selected_scene_object()" in inspector
    assert "h._selection.publish_selected_change(select=True, inspect=True)" in inspector
    assert "h._selection.publish_scene()" in inspector
    assert "h._selection.refresh_inspector(name)" in inspector
    assert "h._selection.publish_scene()" in inspector_media
    assert "h._selection.append_scene_object(canvas)" in inspector_media
    assert "def selected_scene_object" in selection
    assert "def publish_selected_change" in selection
    assert "def append_scene_object" in selection


def test_viewport_handles_focus_and_grid_commands() -> None:
    source = _source("editor/runtime/viewport_session.py")
    handler = _source("editor/runtime/viewport_editor_view_commands.py")
    lifecycle = _source("editor/runtime/viewport_session_lifecycle.py")
    assert "self.show_grid = True" in source
    assert "ViewportEditorViewCommandHandler" in source
    assert "ViewportEditorViewState" in source
    assert 'COMMAND_TYPES = frozenset({"focus_selected", "toggle_grid"})' in handler
    assert "float(selected.get(\"x\", 0.0))" in handler
    assert "self.view_mode == \"scene\" and self.show_grid" in lifecycle
