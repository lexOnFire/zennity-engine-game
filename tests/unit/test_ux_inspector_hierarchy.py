"""Testes de UX do Inspector (Multi-Seleção e Busca) e Hierarchy (Ícones e ExtendedSelection).
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


class FakeGameObject:
    def __init__(self, name: str = "Player"):
        self.name = name
        self.active = True
        self.id = f"id_{name.lower()}"
        self.components: list = []


def test_inspector_multi_selection_load():
    """Inspector aceita e carrega múltiplos objetos simultaneamente."""
    from editor.premium_inspector_panel import RealInspectorPanel

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível")

    panel = RealInspectorPanel()

    obj1 = FakeGameObject("Player1")
    obj2 = FakeGameObject("Player2")

    panel.load_objects([obj1, obj2])

    assert len(panel.current_objects) == 2
    assert "2 Objetos" in panel.object_name.text()


def test_hierarchy_icon_prefixes():
    """HierarchyDock atribui ícones visuais para pastas, câmeras e luzes."""
    from editor.widgets.hierarchy_dock import HierarchyDock
    from engine.game_object import GameObject

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível")

    dock = HierarchyDock()
    root = dock.tree.invisibleRootItem()

    folder_obj = GameObject("Folder_Main")
    camera_obj = GameObject("MainCamera")

    dock.add_object_node(root, folder_obj)
    dock.add_object_node(root, camera_obj)

    item_folder = root.child(0)
    item_camera = root.child(1)

    assert "📁" in item_folder.text(0)
    assert "📷" in item_camera.text(0)
