"""Testes de UX do Asset Browser (Categorias e Favoritos) e Graph Editors (Comment Frame).
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


def test_asset_browser_favorites():
    """AssetBrowserDock permite adicionar e remover itens dos favoritos."""
    from editor.widgets.asset_browser_dock import AssetBrowserDock

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível")

    dock = AssetBrowserDock()

    path = "Assets/Scenes/MainScene.zscene"
    assert dock.toggle_favorite(path) is True
    assert path in dock.favorites

    assert dock.toggle_favorite(path) is False
    assert path not in dock.favorites


def test_comment_frame_item_creation():
    """CommentFrameItem pode ser instanciado com título e dimensões customizadas."""
    from editor.widgets.graph_editor.comment_frame_item import CommentFrameItem
    from PySide6.QtCore import QRectF

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível")

    frame = CommentFrameItem(title="AI Logic Group", rect=QRectF(0, 0, 400, 300), color_hex="#34495E")

    assert frame.title == "AI Logic Group"
    assert frame.rect().width() == 400
    assert frame.zValue() == -10.0
