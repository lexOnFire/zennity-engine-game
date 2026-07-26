from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_visual_logic_window_hosts_all_graph_domains() -> None:
    source = (ROOT / "editor" / "visual_scripting" / "visual_scripting_dock.py").read_text(
        encoding="utf-8"
    )
    for label in ("Logic Graph", "Behavior Tree", "Dialogue", "Material", "Animator Graph"):
        assert f'"{label}"' in source
    assert "graph_mode_tabs" in source
    assert "open_graph_tool" in source


def test_main_menu_exposes_only_one_graph_editor_entry() -> None:
    source = (ROOT / "editor" / "windows" / "main_window_menus.py").read_text(
        encoding="utf-8"
    )
    assert source.count('QAction("Editor de Lógica Visual"') == 1
    for obsolete_entry in (
        "dock_behavior_tree.toggleViewAction",
        "dock_dialogue.toggleViewAction",
        "dock_material.toggleViewAction",
        "dock_animation_studio.toggleViewAction",
    ):
        assert obsolete_entry not in source


def test_specialized_graph_editor_has_real_document_actions() -> None:
    source = (ROOT / "editor" / "widgets" / "generic_graph_editor.py").read_text(
        encoding="utf-8"
    )
    for method in ("new_document", "open_dialog", "load_document", "save"):
        assert f"def {method}(" in source
    assert "self.canvas._spawn_node(ndef.id)" in source
