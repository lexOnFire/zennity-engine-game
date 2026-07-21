"""Focused controllers must not route through shell pass-through methods."""

from pathlib import Path
import ast


REMOVED = [
    "_dragged_asset_path",
    "_attach_script",
    "_get_available_scripts",
    "_send_logic_debug_command",
    "_show_logic_window",
    "_logic_assets",
    "_logic_graphs_for_object",
    "_save_logic_binding",
    "_choose_logic_graph_component",
    "_create_logic_graph_for_selected",
    "_selected_logic_path",
    "_open_selected_logic_graph",
    "_detach_selected_logic_graph",
    "_remove_all_logic_graphs",
    "_update_logic_graph_summary",
    "_toggle_snap",
    "_export_project",
    "_validate_current_project",
    "_show_last_build_report",
    "_send_toolbar_command"
]


def test_migrated_consumers_do_not_use_removed_shell_adapters() -> None:
    paths = (
        "editor/inspector_controller.py",
        "editor/inspector_view_renderer.py",
        "editor/editor_command_controller.py",
        "editor/runtime/editor_event_router.py",
        "editor/logic_workspace_controller.py",
    )
    called_attributes: set[str] = set()
    for path in paths:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"), filename=path)
        called_attributes.update(
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        )
    assert called_attributes.isdisjoint(REMOVED)


def test_adapter_surface_is_below_twenty_methods() -> None:
    import ast
    tree = ast.parse(Path("editor/editor_integration_adapters.py").read_text(encoding="utf-8"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    assert sum(isinstance(node, ast.FunctionDef) for node in cls.body) < 20
