"""
editor/widgets/phase1_viewport.py
─────────────────────────────────────────────────────────────────────────────
Viewport da Fase 1 com suporte a Move Tool e Rotate Tool.

Regras desta camada:
  * Não altera scene.draw.
  * Não usa monkey patch.
  * Todo estado de runtime vem de EditorContext (injetado via setters).
  * Cada operação que muda Transform é registrada como FunctionCommand
    no CommandManager para suportar Ctrl+Z / Ctrl+Y.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtGui import QMouseEvent

from editor.gizmos.qt_gizmo_overlay import QtMoveGizmoOverlay
from editor.gizmos.rotate_gizmo import QtRotateGizmoOverlay
from editor.runtime.command_manager import CommandManager, FunctionCommand
from editor.runtime.editor_state import EditorState
from editor.runtime.tool_manager import EditorTool, ToolManager
from editor.widgets.viewport_widget import ViewportWidget


class Phase1ViewportWidget(ViewportWidget):
    """Viewport da Fase 1 com overlay de gizmo Qt seguro.

    Herda toda a lógica funcional da Viewport original e apenas desenha o gizmo
    por cima, sem tocar em eventos de mouse/teclado ou scene.draw.
    """

    object_transform_changed = Signal(object)
    tool_message_requested = Signal(str)
    history_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Gizmos de overlay
        self.move_gizmo_overlay = QtMoveGizmoOverlay()
        self.rotate_gizmo_overlay = QtRotateGizmoOverlay()

        # Serviços injetados pelo EditorContext
        self.tool_manager: ToolManager | None = None
        self.editor_state: EditorState | None = None
        self.command_manager: CommandManager | None = None

        # Estado do drag de Move
        self._move_drag_object: Any = None
        self._move_start_world = np.zeros(3, dtype=np.float32)
        self._move_start_position = np.zeros(3, dtype=np.float32)

        # Estado do drag de Rotate
        self._rotate_drag_object: Any = None
        self._rotate_start_rz: float = 0.0
        self._rotate_start_angle: float = 0.0  # ângulo atan2 no início do drag
        self._rotate_center_screen: tuple[float, float] = (0.0, 0.0)
        self._rotate_current_mouse: tuple[float, float] | None = None

    # ── Injeção de dependências ───────────────────────────────────────────────

    def set_tool_manager(self, tool_manager: ToolManager) -> None:
        self.tool_manager = tool_manager

    def set_editor_state(self, editor_state: EditorState) -> None:
        self.editor_state = editor_state

    def set_command_manager(self, command_manager: CommandManager) -> None:
        """Injeta o CommandManager para registrar undo/redo de operacoes de editor."""
        self.command_manager = command_manager

    # ── Helpers de estado ─────────────────────────────────────────────────────

    def _active_tool(self) -> EditorTool:
        if self.tool_manager is None:
            return EditorTool.SELECT
        return self.tool_manager.active_tool

    def _is_playing(self) -> bool:
        return bool(getattr(getattr(self, "active_scene", None), "playing", False))

    def _should_draw_gizmo(self, selected: Any) -> bool:
        return selected is not None and not self._is_playing()

    # ── Snap de posição (Move Tool) ───────────────────────────────────────────

    def _snap_size(self) -> float:
        if self.editor_state is None:
            return 1.0
        return max(1.0, float(self.editor_state.snap_size))

    def _snap_enabled(self) -> bool:
        return bool(self.editor_state is not None and self.editor_state.snap_enabled)

    def _apply_snap(self, position: np.ndarray) -> np.ndarray:
        """Snap de grade sobre posição absoluta (não relativa ao delta)."""
        if not self._snap_enabled():
            return position
        snap = self._snap_size()
        snapped = position.copy()
        snapped[0] = round(float(snapped[0]) / snap) * snap
        snapped[1] = round(float(snapped[1]) / snap) * snap
        return snapped

    # ── Snap angular (Rotate Tool) ────────────────────────────────────────────

    def _snap_angle(self) -> float:
        if self.editor_state is None:
            return 15.0
        return max(1.0, float(self.editor_state.snap_angle))

    def _apply_snap_angle(self, degrees: float) -> float:
        """Snap angular sobre graus absolutos (não delta)."""
        if not self._snap_enabled():
            return degrees
        snap = self._snap_angle()
        return round(degrees / snap) * snap

    # ── Hit-test e seleção ────────────────────────────────────────────────────

    def _selected_transform_object(self) -> Any:
        selected = self.selected_object() if hasattr(self, "selected_object") else None
        if selected is not None and hasattr(selected, "transform"):
            return selected
        return None

    def _object_at_viewport_point(self, x: float, y: float) -> Any:
        scene = getattr(self, "active_scene", None)
        if scene is None:
            return None
        world = self.viewport_to_world((x, y))
        for obj in reversed(list(getattr(scene, "editable_objects", []))):
            transform = getattr(obj, "transform", None)
            if transform is None:
                continue
            pos = getattr(transform, "position", None)
            scale = getattr(transform, "scale", None)
            if pos is None or scale is None:
                continue
            if getattr(obj, "mesh_type", "") == "Círculo":
                if math.hypot(world[0] - pos[0], world[1] - pos[1]) <= scale[0] / 2:
                    return obj
            elif abs(world[0] - pos[0]) <= scale[0] / 2 and abs(world[1] - pos[1]) <= scale[1] / 2:
                return obj
        return None

    # ── Move Tool: drag ───────────────────────────────────────────────────────

    def _gizmo_hit_at_viewport_point(self, x: float, y: float, selected: Any) -> bool:
        if not self._should_draw_gizmo(selected) or not hasattr(selected, "transform"):
            return False
        cx, cy = self.world_to_viewport(selected.transform.position)
        length = float(self.move_gizmo_overlay.axis_length)
        if math.hypot(x - cx, y - cy) <= 10.0:
            return True
        near_x_axis = cx <= x <= cx + length + 16 and abs(y - cy) <= 10.0
        near_y_axis = cy - length - 16 <= y <= cy and abs(x - cx) <= 10.0
        return near_x_axis or near_y_axis

    def _begin_move_drag(self, obj: Any, x: float, y: float) -> bool:
        if self._active_tool() != EditorTool.MOVE:
            return False
        if self._is_playing():
            return False
        if obj is None or not hasattr(obj, "transform"):
            return False
        world = self.viewport_to_world((x, y))
        self._move_drag_object = obj
        self._move_start_world = world.copy()
        self._move_start_position = obj.transform.position.copy()
        self.select_object(obj)
        self._update_hover_cursor(x, y)
        return True

    def _update_move_drag(self, x: float, y: float) -> None:
        obj = self._move_drag_object
        if obj is None or not hasattr(obj, "transform"):
            return
        world = self.viewport_to_world((x, y))
        delta = world - self._move_start_world
        next_position = self._move_start_position + delta
        # Snap é aplicado sobre a posição absoluta, não sobre o delta.
        # Não condicionar ao delta — snap com delta zero ainda pode corrigir
        # uma posição que está fora da grade.
        next_position = self._apply_snap(next_position)
        obj.transform.position[0] = next_position[0]
        obj.transform.position[1] = next_position[1]
        self.object_transform_changed.emit(obj)
        self.update()

    def _end_move_drag(self) -> None:
        """Finaliza o drag e registra um Command reversível no CommandManager."""
        obj = self._move_drag_object
        if obj is not None and hasattr(obj, "transform"):
            final_position = obj.transform.position.copy()
            start_position = self._move_start_position.copy()
            # Só registra undo se houve movimento real
            moved = not np.allclose(final_position[:2], start_position[:2])
            if moved and self.command_manager is not None:
                def _do(p=final_position, o=obj) -> None:
                    o.transform.position[0] = p[0]
                    o.transform.position[1] = p[1]
                    self.object_transform_changed.emit(o)

                def _undo(p=start_position, o=obj) -> None:
                    o.transform.position[0] = p[0]
                    o.transform.position[1] = p[1]
                    self.object_transform_changed.emit(o)

                self.command_manager.execute(
                    FunctionCommand(
                        description=f"Move {getattr(obj, 'name', 'object')}",
                        do=_do,
                        undo_action=_undo,
                    )
                )
                self.history_changed.emit()
        self._move_drag_object = None
        self._update_hover_cursor(*self._qt_mouse_pos)

    # ── Rotate Tool: drag ─────────────────────────────────────────────────────

    def _rotate_gizmo_hit_at_viewport_point(self, x: float, y: float, selected: Any) -> bool:
        """True se (x, y) está sobre o anel ou o centro do rotate gizmo."""
        if not self._should_draw_gizmo(selected):
            return False
        return self.rotate_gizmo_overlay.hit_test(x, y, selected, self.world_to_viewport)

    def _begin_rotate_drag(self, obj: Any, x: float, y: float) -> bool:
        """Inicia o drag de rotação. Retorna True se o drag foi aceito."""
        if self._active_tool() != EditorTool.ROTATE:
            return False
        if self._is_playing():
            return False
        if obj is None or not hasattr(obj, "transform"):
            return False
        cx, cy = self.world_to_viewport(obj.transform.position)
        self._rotate_drag_object = obj
        self._rotate_start_rz = float(obj.transform.rz)
        # Ângulo atan2 do centro ao ponto de clique inicial (graus, tela)
        self._rotate_start_angle = math.degrees(math.atan2(y - cy, x - cx))
        self._rotate_center_screen = (cx, cy)
        self._rotate_current_mouse = (x, y)
        self.select_object(obj)
        self._update_hover_cursor(x, y)
        return True

    def _update_rotate_drag(self, x: float, y: float) -> None:
        """Atualiza o rz do objeto durante o drag."""
        obj = self._rotate_drag_object
        if obj is None or not hasattr(obj, "transform"):
            return
        # Recomputa o centro a cada frame — posição não muda durante rotate,
        # mas protege contra edge cases (câmera movida por atalho).
        cx, cy = self.world_to_viewport(obj.transform.position)
        current_angle = math.degrees(math.atan2(y - cy, x - cx))
        delta = current_angle - self._rotate_start_angle
        new_rz = self._apply_snap_angle(self._rotate_start_rz + delta)
        obj.transform.rz = new_rz
        self._rotate_current_mouse = (x, y)
        self.object_transform_changed.emit(obj)
        self.update()

    def _end_rotate_drag(self) -> None:
        """Finaliza o drag e registra um Command reversível no CommandManager."""
        obj = self._rotate_drag_object
        if obj is not None and hasattr(obj, "transform"):
            final_rz = float(obj.transform.rz)
            start_rz = self._rotate_start_rz
            # Só registra undo se houve rotação real (tolerância de 0.01°)
            rotated = not math.isclose(final_rz, start_rz, abs_tol=0.01)
            if rotated and self.command_manager is not None:
                def _do(rz=final_rz, o=obj) -> None:
                    o.transform.rz = rz
                    self.object_transform_changed.emit(o)

                def _undo(rz=start_rz, o=obj) -> None:
                    o.transform.rz = rz
                    self.object_transform_changed.emit(o)

                self.command_manager.execute(
                    FunctionCommand(
                        description=f"Rotate {getattr(obj, 'name', 'object')}",
                        do=_do,
                        undo_action=_undo,
                    )
                )
                self.history_changed.emit()
        self._rotate_drag_object = None
        self._rotate_current_mouse = None
        self._update_hover_cursor(*self._qt_mouse_pos)

    # ── Cursores ──────────────────────────────────────────────────────────────

    def _update_hover_cursor(self, x: float, y: float) -> None:
        if self._is_playing():
            self.unsetCursor()
            return
        tool = self._active_tool()
        selected = self._selected_transform_object()

        # Drag ativos têm prioridade
        if self._move_drag_object is not None or self._rotate_drag_object is not None:
            self.setCursor(Qt.ClosedHandCursor)

        elif tool == EditorTool.MOVE and (
            self._gizmo_hit_at_viewport_point(x, y, selected)
            or self._object_at_viewport_point(x, y) is not None
        ):
            self.setCursor(Qt.OpenHandCursor)

        elif tool == EditorTool.ROTATE and (
            self._rotate_gizmo_hit_at_viewport_point(x, y, selected)
            or self._object_at_viewport_point(x, y) is not None
        ):
            # Qt não tem cursor de rotação nativo — CrossCursor sinaliza interação
            self.setCursor(Qt.CrossCursor)

        elif tool == EditorTool.SELECT and self._object_at_viewport_point(x, y) is not None:
            self.setCursor(Qt.PointingHandCursor)

        else:
            self.unsetCursor()

    # ── Mensagem de ferramenta não implementada ───────────────────────────────

    def _show_unimplemented_tool_message(self, tool: EditorTool) -> None:
        self.tool_message_requested.emit(f"{tool.value.title()} em desenvolvimento")

    # ── Eventos de mouse ──────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent) -> None:
        tool = self._active_tool()
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        x, y = float(event.x()), float(event.y())

        if tool == EditorTool.SELECT:
            self.select_object(self._object_at_viewport_point(x, y))
            event.accept()
            return

        if tool == EditorTool.MOVE:
            clicked = self._object_at_viewport_point(x, y)
            selected = self._selected_transform_object()
            target = clicked
            if target is None and self._gizmo_hit_at_viewport_point(x, y, selected):
                target = selected
            if target is not None and self._begin_move_drag(target, x, y):
                event.accept()
                return
            event.accept()
            return

        if tool == EditorTool.ROTATE:
            clicked = self._object_at_viewport_point(x, y)
            selected = self._selected_transform_object()
            target = clicked
            # Fallback: se clicou no anel do gizmo sem clicar num objeto
            if target is None and self._rotate_gizmo_hit_at_viewport_point(x, y, selected):
                target = selected
            if target is not None and self._begin_rotate_drag(target, x, y):
                event.accept()
                return
            event.accept()
            return

        if tool == EditorTool.SCALE:
            self._show_unimplemented_tool_message(tool)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        x, y = float(event.x()), float(event.y())

        if self._active_tool() == EditorTool.MOVE and self._move_drag_object is not None:
            self._update_move_drag(x, y)
            event.accept()
            return

        if self._rotate_drag_object is not None:
            self._update_rotate_drag(x, y)
            event.accept()
            return

        self._update_hover_cursor(x, y)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            if self._move_drag_object is not None:
                self._end_move_drag()
                event.accept()
                return
            if self._rotate_drag_object is not None:
                self._end_rotate_drag()
                event.accept()
                return
        super().mouseReleaseEvent(event)

    # ── Renderização ──────────────────────────────────────────────────────────

    def paintGL(self) -> None:
        super().paintGL()
        selected = None
        if hasattr(self, "selected_object"):
            selected = self.selected_object()
        elif getattr(self, "viewmodel", None) is not None:
            selected = getattr(self.viewmodel, "selected_object", None)
        if not self._should_draw_gizmo(selected):
            return

        painter = QPainter(self)
        self._draw_selection_outline(painter, selected)

        tool = self._active_tool()
        if tool == EditorTool.MOVE:
            self.move_gizmo_overlay.draw(painter, selected, self.world_to_viewport)
        elif tool == EditorTool.ROTATE:
            mouse = self._rotate_current_mouse if self._rotate_drag_object is not None else None
            self.rotate_gizmo_overlay.draw(
                painter, selected, self.world_to_viewport, current_mouse=mouse
            )

        painter.end()

    def _draw_selection_outline(self, painter: QPainter, selected: Any) -> None:
        if selected is None or not hasattr(selected, "transform"):
            return
        pos = getattr(selected.transform, "position", None)
        scale = getattr(selected.transform, "scale", None)
        if pos is None or scale is None:
            return

        cx, cy = self.world_to_viewport(pos)
        
        # Converte as extremidades para obter largura e altura na viewport (considerando zoom)
        p0 = self.world_to_viewport((pos[0] - scale[0] / 2, pos[1] - scale[1] / 2, pos[2]))
        p1 = self.world_to_viewport((pos[0] + scale[0] / 2, pos[1] + scale[1] / 2, pos[2]))
        sw = abs(p1[0] - p0[0])
        sh = abs(p1[1] - p0[1])

        # Cria retângulo local centralizado em (0,0) com padding de 3px
        rect = QRectF(-sw / 2 - 3.0, -sh / 2 - 3.0, sw + 6.0, sh + 6.0)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor(80, 160, 255), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        # Move para o centro do objeto e rotaciona
        painter.translate(cx, cy)
        rz = float(getattr(selected.transform, "rz", 0.0))
        painter.rotate(rz)
        
        painter.drawRect(rect)
        painter.restore()
