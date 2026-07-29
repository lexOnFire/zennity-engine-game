from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_window_menu_keeps_only_animator_and_visual_logic():
    for path in ("editor/interface_smoke_test.py", "editor/phase1_editor_mixins.py"):
        source = _source(path)
        assert 'QAction("Animator", self)' in source
        assert 'QAction("Editor de Lógica Visual", self)' in source
        assert 'addMenu("Ferramentas")' not in source
        assert "UI Builder" not in source
        assert "Build Pipeline & Export" not in source
        assert "Configurações do Projeto" not in source


def test_logic_controller_does_not_repopulate_tools_menu():
    source = _source("editor/logic_workspace_controller.py")
    assert 'h.editor_menus["Ferramentas"]' not in source
    assert "tools_menu.addAction" not in source
    assert 'h.editor_menus["Janela"].addAction' not in source
