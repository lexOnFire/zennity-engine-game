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


def test_top_toolbars_are_fixed_and_not_floatable():
    for path in (
        "editor/interface_smoke_test.py",
        "editor/editor_command_controller.py",
        "editor/phase1_editor_mixins.py",
        "editor/premium_editor.py",
        "editor/windows/main_window_menus.py",
    ):
        source = _source(path)
        assert ".setFloatable(False)" in source
        assert ".setAllowedAreas(Qt.TopToolBarArea)" in source
        assert "QToolBar::handle { width: 0px; image: none; }" in source


def test_embedded_animation_studio_does_not_leave_floating_dock_shell():
    source = _source("editor/ui/workspace_builder.py")
    assert "window.animation_track_studio = AnimationStudioDock()" in source
    assert "track_workspace = window.animation_track_studio.widget()" in source
    assert "window.animation_track_studio.hide()" in source
    assert "window.animation_track_studio.setParent(None)" in source
    assert 'window.animation_mode_tabs.addTab(track_workspace, "Tracks & Keyframes")' in source
