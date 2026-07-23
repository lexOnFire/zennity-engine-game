"""
tests/editor/test_phase1_scale_tool.py
─────────────────────────────────────────────────────────────────────────────
Testes unitários e de integração para a Scale Tool (Fase 1).
"""
from __future__ import annotations

import math
import os
import numpy as np

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from editor.phase1_editor import ZennityPhase1Editor
from editor.runtime.tool_manager import EditorTool


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def phase1_editor(qapp: QApplication) -> ZennityPhase1Editor:
    editor = ZennityPhase1Editor()
    yield editor
    editor.close()
    editor.deleteLater()
    qapp.processEvents()


def _selected(editor: ZennityPhase1Editor):
    return editor.scene_objects()[1]


def test_scale_tool_begin_drag_returns_true_on_valid_object(phase1_editor: ZennityPhase1Editor) -> None:
    vp = phase1_editor.viewport
    obj = _selected(phase1_editor)
    
    # Ativa Scale Tool
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.SCALE)
    
    # Inicia arraste na alça 3 (Right-Center)
    assert vp._begin_scale_drag(obj, 100.0, 100.0, 3) is True
    assert vp._scale_drag_object is obj
    assert vp._scale_handle_idx == 3


def test_scale_tool_begin_drag_returns_false_for_wrong_tool(phase1_editor: ZennityPhase1Editor) -> None:
    vp = phase1_editor.viewport
    obj = _selected(phase1_editor)
    
    # Ativa SELECT Tool
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.SELECT)
    
    assert vp._begin_scale_drag(obj, 100.0, 100.0, 3) is False
    assert vp._scale_drag_object is None


def test_scale_tool_drag_changes_scale_right_center(phase1_editor: ZennityPhase1Editor) -> None:
    vp = phase1_editor.viewport
    obj = _selected(phase1_editor)
    
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.SCALE)
    
    # Coordenadas iniciais
    orig_scale = obj.transform.scale.copy()
    orig_pos = obj.transform.position.copy()
    
    # Centro na tela
    cx, cy = vp.world_to_viewport(orig_pos)
    
    # Inicia arraste no handle 3 (Right-Center) a partir do centro (apenas para teste de fluxo)
    vp._begin_scale_drag(obj, cx, cy, 3)
    
    # Arrasta para a direita por 50 pixels de tela (zoom = 1.0)
    vp._update_scale_drag(cx + 50.0, cy)
    
    # Escala deve aumentar na largura
    assert obj.transform.scale[0] > orig_scale[0]
    # Comportamento de ancoragem: o centro se desloca para a direita
    assert obj.transform.position[0] > orig_pos[0]
    
    vp._end_scale_drag()
    assert vp._scale_drag_object is None


def test_scale_tool_snap_enabled(phase1_editor: ZennityPhase1Editor) -> None:
    vp = phase1_editor.viewport
    obj = _selected(phase1_editor)
    
    # Configura snap de 10 unidades
    phase1_editor.editor_context.state.snap_enabled = True
    phase1_editor.editor_context.state.snap_size = 10.0
    
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.SCALE)
    orig_scale = obj.transform.scale.copy()
    
    cx, cy = vp.world_to_viewport(obj.transform.position)
    
    vp._begin_scale_drag(obj, cx, cy, 3)
    
    # Arrasta 33 pixels de tela (que equivale a 33 unidades no mundo com zoom=1.0)
    vp._update_scale_drag(cx + 33.0, cy)
    
    # A largura final deve estar alinhada ao snap (múltiplo de 10)
    assert int(obj.transform.scale[0]) % 10 == 0
    
    vp._end_scale_drag()


def test_scale_tool_registers_undo_command(phase1_editor: ZennityPhase1Editor) -> None:
    vp = phase1_editor.viewport
    obj = _selected(phase1_editor)
    
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.SCALE)
    orig_scale = obj.transform.scale.copy()
    orig_pos = obj.transform.position.copy()
    
    cx, cy = vp.world_to_viewport(orig_pos)
    
    vp._begin_scale_drag(obj, cx, cy, 3)
    vp._update_scale_drag(cx + 40.0, cy)
    vp._end_scale_drag()
    
    scaled_scale = obj.transform.scale.copy()
    scaled_pos = obj.transform.position.copy()
    
    # Executa Undo
    assert phase1_editor.editor_context.commands.can_undo is True
    phase1_editor.editor_context.commands.undo()
    
    assert obj.transform.scale[0] == pytest.approx(orig_scale[0])
    assert obj.transform.position[0] == pytest.approx(orig_pos[0])
    
    # Executa Redo
    assert phase1_editor.editor_context.commands.can_redo is True
    phase1_editor.editor_context.commands.redo()
    
    assert obj.transform.scale[0] == pytest.approx(scaled_scale[0])
    assert obj.transform.position[0] == pytest.approx(scaled_pos[0])


def test_scale_tool_blocked_during_play_mode(phase1_editor: ZennityPhase1Editor) -> None:
    vp = phase1_editor.viewport
    obj = _selected(phase1_editor)
    
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.SCALE)
    
    # Ativa o modo de jogo
    phase1_editor.play()
    
    assert vp._begin_scale_drag(obj, 100.0, 100.0, 3) is False
    assert vp._scale_drag_object is None
