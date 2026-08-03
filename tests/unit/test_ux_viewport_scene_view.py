"""Testes de UX da Viewport (Snapping, Camera Bookmarks e Overlays).
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


def test_viewport_snapping_calculation():
    """Viewport aplica arredondamento por passo quando snapping está ativo."""
    from editor.widgets.viewport_widget import ViewportWidget

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível")

    vp = ViewportWidget()
    vp.snap_enabled = True
    vp.snap_grid_size = 1.0

    assert vp.snap_value(1.4) == 1.0
    assert vp.snap_value(1.6) == 2.0
    assert vp.snap_value(5.2, step=2.0) == 6.0

    vp.snap_enabled = False
    assert vp.snap_value(1.4) == 1.4


def test_viewport_camera_bookmarks():
    """Viewport salva e restaura bookmarks de câmera."""
    from editor.widgets.viewport_widget import ViewportWidget

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível")

    vp = ViewportWidget()

    vp.save_camera_bookmark(1, 10.0, -20.0, 1.5)
    bm = vp.restore_camera_bookmark(1)

    assert bm == (10.0, -20.0, 1.5)
    assert vp.restore_camera_bookmark(9) is None
