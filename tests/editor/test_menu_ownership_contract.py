from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_visual_tools_are_not_duplicated_in_window_menu():
    for path in ("editor/interface_smoke_test.py", "editor/phase1_editor_mixins.py"):
        source = _source(path)
        assert "tools_menu.addAction(act)" in source
        assert "window_menu.addAction(act)" not in source
        assert "janela_menu.addAction(act)" not in source


def test_logic_controller_adds_animation_only_to_tools_menu():
    source = _source("editor/logic_workspace_controller.py")
    assert 'tools_menu = h.editor_menus["Ferramentas"]' in source
    assert "tools_menu.addAction(animation_action)" in source
    assert 'h.editor_menus["Janela"].addAction' not in source
