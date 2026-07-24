"""
tests/editor/test_phase1_rotate_tool.py
─────────────────────────────────────────────────────────────────────────────
Testes unitários e de integração para a Rotate Tool da Fase 1.

Cobre:
  * Estrutura: gizmo overlay existe e hit_test funciona
  * Drag: begin, update, end
  * Undo/Redo via CommandManager
  * Snap angular
  * Bloqueio durante play mode
  * Select Tool não inicia drag de rotação
  * EditorState: snap_angle presente
"""
from __future__ import annotations

import math
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from editor.gizmos.rotate_gizmo import QtRotateGizmoOverlay
from editor.phase1_editor import ZennityPhase1Editor
from editor.runtime import EditorContext
from editor.runtime.tool_manager import EditorTool
from editor.runtime.editor_state import EditorState


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(scope="module")
def shared_phase1_editor(qapp: QApplication) -> ZennityPhase1Editor:
    editor = ZennityPhase1Editor()
    yield editor
    editor.close()
    editor.deleteLater()
    qapp.processEvents()


@pytest.fixture
def phase1_editor(shared_phase1_editor: ZennityPhase1Editor) -> ZennityPhase1Editor:
    # Reset estado
    shared_phase1_editor.editor_context.commands.clear()
    shared_phase1_editor._update_undo_redo_states()
    shared_phase1_editor.editor_context.tools.set_active_tool(EditorTool.SELECT)
    shared_phase1_editor.editor_context.state.snap_enabled = False
    shared_phase1_editor.editor_context.state.snap_angle = 15
    shared_phase1_editor.editor_context.selection.clear()
    
    for obj in shared_phase1_editor.scene_objects():
        import numpy as np
        obj.transform.position = np.array([0, 0, 0], dtype=np.float32)
        obj.transform.rotation = np.array([0, 0, 0], dtype=np.float32)
        obj.transform.scale = np.array([1, 1, 1], dtype=np.float32)
        obj.transform.rz = 0.0
        
    shared_phase1_editor.viewport._rotate_drag_object = None
    shared_phase1_editor.viewport._rotate_current_mouse = None
    shared_phase1_editor.viewport._move_drag_object = None
    shared_phase1_editor.viewport.active_scene.playing = False
    
    return shared_phase1_editor


# ── Helpers ───────────────────────────────────────────────────────────────────

def _selected(editor: ZennityPhase1Editor):
    return editor.scene_objects()[1]


def _set_rotate_tool(editor: ZennityPhase1Editor) -> None:
    editor.editor_context.tools.set_active_tool(EditorTool.ROTATE)
    editor.editor_context.commands.clear()


# ── Testes de estrutura ───────────────────────────────────────────────────────

def test_rotate_gizmo_overlay_exists_on_viewport(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """A viewport deve ter um QtRotateGizmoOverlay injetado."""
    assert isinstance(phase1_editor.viewport.rotate_gizmo_overlay, QtRotateGizmoOverlay)


def test_editor_state_has_snap_angle() -> None:
    """EditorState deve expor snap_angle com default=15."""
    state = EditorState()
    assert hasattr(state, "snap_angle")
    assert state.snap_angle == 15


def test_rotate_tool_status_message(phase1_editor: ZennityPhase1Editor) -> None:
    """Ativar Rotate Tool deve mostrar mensagem 'Ferramenta ativa: Rotate'."""
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.ROTATE)
    assert phase1_editor.status_msg.text() == "Ferramenta ativa: Rotate"


# ── Testes de hit-test do gizmo ───────────────────────────────────────────────

def test_rotate_gizmo_hit_test_detects_ring(phase1_editor: ZennityPhase1Editor) -> None:
    """hit_test retorna True quando o cursor está sobre o anel do gizmo."""
    selected = _selected(phase1_editor)
    phase1_editor.select_object(selected)
    _set_rotate_tool(phase1_editor)

    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)
    gizmo = phase1_editor.viewport.rotate_gizmo_overlay
    radius = gizmo.radius

    # Ponto exatamente no anel (ângulo 0° → ponto à direita do centro)
    assert gizmo.hit_test(cx + radius, cy, selected, phase1_editor.viewport.world_to_viewport)


def test_rotate_gizmo_hit_test_detects_center(phase1_editor: ZennityPhase1Editor) -> None:
    """hit_test retorna True quando o cursor está sobre o centro (pivot)."""
    selected = _selected(phase1_editor)
    phase1_editor.select_object(selected)

    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)
    gizmo = phase1_editor.viewport.rotate_gizmo_overlay

    # Ponto no centro exato
    assert gizmo.hit_test(cx, cy, selected, phase1_editor.viewport.world_to_viewport)


def test_rotate_gizmo_hit_test_rejects_far_point(phase1_editor: ZennityPhase1Editor) -> None:
    """hit_test retorna False para pontos longe do anel e do centro."""
    selected = _selected(phase1_editor)
    phase1_editor.select_object(selected)

    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)
    gizmo = phase1_editor.viewport.rotate_gizmo_overlay

    far_x = cx + gizmo.radius * 3
    far_y = cy + gizmo.radius * 3
    assert not gizmo.hit_test(far_x, far_y, selected, phase1_editor.viewport.world_to_viewport)


# ── Testes de drag ────────────────────────────────────────────────────────────

def test_rotate_tool_begin_drag_returns_true_on_valid_object(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """_begin_rotate_drag aceita um objeto válido com a Rotate Tool ativa."""
    selected = _selected(phase1_editor)
    phase1_editor.select_object(selected)
    _set_rotate_tool(phase1_editor)
    start = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    result = phase1_editor.viewport._begin_rotate_drag(selected, start[0] + 60, start[1])

    assert result is True
    assert phase1_editor.viewport._rotate_drag_object is selected


def test_rotate_tool_begin_drag_returns_false_for_select_tool(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """_begin_rotate_drag deve recusar quando a ferramenta ativa é SELECT."""
    selected = _selected(phase1_editor)
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.SELECT)
    start = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    result = phase1_editor.viewport._begin_rotate_drag(selected, start[0] + 60, start[1])

    assert result is False
    assert phase1_editor.viewport._rotate_drag_object is None


def test_rotate_tool_drag_changes_rz(phase1_editor: ZennityPhase1Editor) -> None:
    """Drag de 90° deve aumentar rz em aproximadamente 90°."""
    selected = _selected(phase1_editor)
    selected.transform.rz = 0.0
    phase1_editor.select_object(selected)
    _set_rotate_tool(phase1_editor)
    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    # Clique à direita do centro (ângulo 0°)
    phase1_editor.viewport._begin_rotate_drag(selected, cx + 60, cy)
    # Move para baixo do centro (ângulo 90° em coordenadas de tela)
    phase1_editor.viewport._update_rotate_drag(cx, cy + 60)

    # Delta = 90° - 0° = 90°
    assert float(selected.transform.rz) == pytest.approx(90.0, abs=1.0)


def test_rotate_tool_drag_does_not_move_position(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Rotate Tool não deve alterar a posição x/y do objeto."""
    selected = _selected(phase1_editor)
    original_x = float(selected.transform.position[0])
    original_y = float(selected.transform.position[1])
    phase1_editor.select_object(selected)
    _set_rotate_tool(phase1_editor)
    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    phase1_editor.viewport._begin_rotate_drag(selected, cx + 60, cy)
    phase1_editor.viewport._update_rotate_drag(cx, cy + 60)
    phase1_editor.viewport._end_rotate_drag()

    assert float(selected.transform.position[0]) == pytest.approx(original_x)
    assert float(selected.transform.position[1]) == pytest.approx(original_y)


# ── Testes de undo/redo ───────────────────────────────────────────────────────

def test_rotate_tool_registers_undo_command(phase1_editor: ZennityPhase1Editor) -> None:
    """Após drag completo, CommandManager deve ter um comando de undo."""
    selected = _selected(phase1_editor)
    selected.transform.rz = 0.0
    phase1_editor.select_object(selected)
    _set_rotate_tool(phase1_editor)
    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    phase1_editor.viewport._begin_rotate_drag(selected, cx + 60, cy)
    phase1_editor.viewport._update_rotate_drag(cx, cy + 60)
    phase1_editor.viewport._end_rotate_drag()

    assert phase1_editor.editor_context.commands.can_undo


def test_rotate_tool_undo_restores_rz(phase1_editor: ZennityPhase1Editor) -> None:
    """Ctrl+Z após rotate deve restaurar o rz original."""
    selected = _selected(phase1_editor)
    selected.transform.rz = 0.0
    phase1_editor.select_object(selected)
    _set_rotate_tool(phase1_editor)
    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    phase1_editor.viewport._begin_rotate_drag(selected, cx + 60, cy)
    phase1_editor.viewport._update_rotate_drag(cx, cy + 60)
    phase1_editor.viewport._end_rotate_drag()

    rotated_rz = float(selected.transform.rz)
    assert rotated_rz != pytest.approx(0.0, abs=1.0)

    phase1_editor.editor_context.commands.undo()

    assert float(selected.transform.rz) == pytest.approx(0.0, abs=0.01)


def test_rotate_tool_redo_reapplies_rz(phase1_editor: ZennityPhase1Editor) -> None:
    """Ctrl+Y após undo deve reaplicar a rotação."""
    selected = _selected(phase1_editor)
    selected.transform.rz = 0.0
    phase1_editor.select_object(selected)
    _set_rotate_tool(phase1_editor)
    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    phase1_editor.viewport._begin_rotate_drag(selected, cx + 60, cy)
    phase1_editor.viewport._update_rotate_drag(cx, cy + 60)
    phase1_editor.viewport._end_rotate_drag()

    final_rz = float(selected.transform.rz)

    phase1_editor.editor_context.commands.undo()
    assert float(selected.transform.rz) == pytest.approx(0.0, abs=0.01)

    phase1_editor.editor_context.commands.redo()
    assert float(selected.transform.rz) == pytest.approx(final_rz, abs=0.01)


def test_rotate_tool_no_command_when_no_rotation(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Drag que não altera rz (clique e soltar no mesmo ponto) não registra comando."""
    selected = _selected(phase1_editor)
    selected.transform.rz = 0.0
    phase1_editor.select_object(selected)
    _set_rotate_tool(phase1_editor)
    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    # Começa e termina no mesmo ponto — delta = 0
    phase1_editor.viewport._begin_rotate_drag(selected, cx + 60, cy)
    phase1_editor.viewport._end_rotate_drag()

    assert not phase1_editor.editor_context.commands.can_undo


# ── Testes de snap angular ────────────────────────────────────────────────────

def test_rotate_tool_snap_enabled_snaps_to_angle(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Com snap ativado, o rz deve ser múltiplo de snap_angle."""
    selected = _selected(phase1_editor)
    selected.transform.rz = 0.0
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.state.snap_enabled = True
    phase1_editor.editor_context.state.snap_angle = 15
    _set_rotate_tool(phase1_editor)
    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    # Drag para ângulo ~47° — com snap=15 deve arredondar para 45°
    angle_rad = math.radians(47)
    tx = cx + 60 * math.cos(angle_rad)
    ty = cy + 60 * math.sin(angle_rad)

    phase1_editor.viewport._begin_rotate_drag(selected, cx + 60, cy)  # começa em 0°
    phase1_editor.viewport._update_rotate_drag(tx, ty)

    rz = float(selected.transform.rz)
    assert rz % 15.0 == pytest.approx(0.0, abs=0.01), f"rz={rz} não é múltiplo de 15°"


def test_rotate_tool_snap_disabled_allows_free_rotation(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Com snap desativado, a rotação pode ter qualquer ângulo."""
    selected = _selected(phase1_editor)
    selected.transform.rz = 0.0
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.state.snap_enabled = False
    _set_rotate_tool(phase1_editor)
    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    # Drag para ângulo ~47° — sem snap deve ficar próximo de 47°
    angle_rad = math.radians(47)
    tx = cx + 60 * math.cos(angle_rad)
    ty = cy + 60 * math.sin(angle_rad)

    phase1_editor.viewport._begin_rotate_drag(selected, cx + 60, cy)  # começa em 0°
    phase1_editor.viewport._update_rotate_drag(tx, ty)

    rz = float(selected.transform.rz)
    # Deve estar próximo de 47° mas NÃO necessariamente múltiplo de 15
    assert rz == pytest.approx(47.0, abs=2.0)


# ── Testes de bloqueio durante play ──────────────────────────────────────────

def test_rotate_tool_blocked_during_play_mode(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """_begin_rotate_drag deve retornar False quando a simulação está ativa."""
    selected = _selected(phase1_editor)
    selected.transform.rz = 0.0
    phase1_editor.select_object(selected)
    _set_rotate_tool(phase1_editor)
    phase1_editor.viewport.active_scene.playing = True
    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)
    original_rz = float(selected.transform.rz)

    result = phase1_editor.viewport._begin_rotate_drag(selected, cx + 60, cy)
    phase1_editor.viewport._update_rotate_drag(cx, cy + 60)

    assert result is False
    assert phase1_editor.viewport._rotate_drag_object is None
    assert float(selected.transform.rz) == pytest.approx(original_rz)

    # Cleanup
    phase1_editor.viewport.active_scene.playing = False


# ── Testes de isolamento entre ferramentas ────────────────────────────────────

def test_rotate_drag_does_not_interfere_with_move_drag(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Após um drag de rotate, _move_drag_object deve continuar None."""
    selected = _selected(phase1_editor)
    selected.transform.rz = 0.0
    phase1_editor.select_object(selected)
    _set_rotate_tool(phase1_editor)
    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    phase1_editor.viewport._begin_rotate_drag(selected, cx + 60, cy)
    phase1_editor.viewport._update_rotate_drag(cx, cy + 60)
    phase1_editor.viewport._end_rotate_drag()

    assert phase1_editor.viewport._move_drag_object is None


def test_viewport_rotate_drag_cleans_up_after_end(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Após _end_rotate_drag, todo estado temporário de drag deve ser limpo."""
    selected = _selected(phase1_editor)
    selected.transform.rz = 0.0
    phase1_editor.select_object(selected)
    _set_rotate_tool(phase1_editor)
    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    phase1_editor.viewport._begin_rotate_drag(selected, cx + 60, cy)
    phase1_editor.viewport._update_rotate_drag(cx, cy + 60)
    phase1_editor.viewport._end_rotate_drag()

    assert phase1_editor.viewport._rotate_drag_object is None
    assert phase1_editor.viewport._rotate_current_mouse is None


# ── Testes de Undo/Redo Toolbar Integration ──────────────────────────────────

def test_undo_redo_toolbar_actions_enabled_state(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Verifica se os estados de habilitado/desabilitado dos botões de Undo/Redo no toolbar são sincronizados."""
    # Início: pilha vazia, botões desabilitados
    assert not phase1_editor.act_undo.isEnabled()
    assert not phase1_editor.act_redo.isEnabled()

    selected = _selected(phase1_editor)
    phase1_editor.select_object(selected)
    _set_rotate_tool(phase1_editor)
    cx, cy = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    # Realiza rotação
    phase1_editor.viewport._begin_rotate_drag(selected, cx + 60, cy)
    phase1_editor.viewport._update_rotate_drag(cx, cy + 60)
    phase1_editor.viewport._end_rotate_drag()

    # Botão de desfazer deve estar habilitado, refazer desabilitado
    assert phase1_editor.act_undo.isEnabled()
    assert not phase1_editor.act_redo.isEnabled()

    # Desfaz
    phase1_editor.act_undo.trigger()
    assert not phase1_editor.act_undo.isEnabled()
    assert phase1_editor.act_redo.isEnabled()

    # Refaz
    phase1_editor.act_redo.trigger()
    assert phase1_editor.act_undo.isEnabled()
    assert not phase1_editor.act_redo.isEnabled()
