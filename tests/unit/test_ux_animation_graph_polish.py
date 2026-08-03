"""Testes das melhorias de UX do Animation Studio (Curve Editor & Event Markers) e Graph Editors (Minimapa & Comment Frames).
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


def test_animation_studio_curves_and_markers():
    """KeyframeCanvas aceita adição de Event Markers e alteração de curvas Bezier/Linear."""
    from editor.animation_studio.keyframe_canvas import KeyframeCanvas

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível")

    canvas = KeyframeCanvas()

    canvas.set_curve_mode("Bezier")
    assert canvas.curve_mode == "Bezier"

    canvas.add_event_marker(1.5, "footstep_sound")
    assert len(canvas.event_markers) == 1
    assert canvas.event_markers[0]["name"] == "footstep_sound"


def test_graph_canvas_comment_frames_and_minimap():
    """GraphCanvas permite adicionar Comment Frames e possui flag de Minimapa."""
    from editor.widgets.graph_editor.graph_canvas import GraphCanvas

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível")

    gc = GraphCanvas()
    assert gc.minimap_enabled is True

    frame = gc.add_comment_frame("Behavior Logic", color_hex="#27AE60")
    assert frame in gc.comment_frames
    assert frame.title == "Behavior Logic"
