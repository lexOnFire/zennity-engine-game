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
    bootstrap = _source("editor/editor_bootstrap_controller.py")
    assert "ShortcutService(host)" in source
    assert "ShortcutService.STANDARD_BINDINGS" in source
    assert "h.editor_context.tools.set_active_tool(next_tool)" in source
    assert '"viewport.focus_selected": self.focus_selected' in source
    assert '"viewport.toggle_grid": self.toggle_grid' in source
    assert "h._tool_controller = ToolController(h)" in bootstrap
    assert "h._tool_controller.configure()" in bootstrap


def test_viewport_handles_focus_and_grid_commands() -> None:
    source = _source("editor/runtime/viewport_session.py")
    lifecycle = _source("editor/runtime/viewport_session_lifecycle.py")
    assert "self.show_grid = True" in source
    assert 'command_type == "toggle_grid"' in source
    assert 'command_type != "focus_selected"' in source
    assert "self.camera_x = float(selected.get" in source
    assert "self.view_mode == \"scene\" and self.show_grid" in lifecycle
