"""
editor/widgets/phase1_viewport.py
─────────────────────────────────────────────────────────────────────────────
Viewport da Fase 2 do Zennity Editor.
Integra câmera com pan/zoom suave direcionado, grid infinito e overlays de HUD/caixas.
"""
from __future__ import annotations

import math
import time
from typing import Any

import numpy as np
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QMouseEvent, QWheelEvent

from editor.gizmos.qt_gizmo_overlay import QtMoveGizmoOverlay
from editor.gizmos.rotate_gizmo import QtRotateGizmoOverlay
from editor.runtime.command_manager import CommandManager, FunctionCommand
from editor.runtime.editor_state import EditorState
from editor.runtime.tool_manager import EditorTool, ToolManager
from editor.viewport.bounding_box import get_handle_positions, hit_test_handle
from editor.widgets.viewport_widget import ViewportWidget

# Novos módulos da Fase 2
from editor.viewport.viewport_camera import ViewportCamera
from editor.viewport.viewport_renderer import ViewportRenderer


class Phase1ViewportWidget(ViewportWidget):
    """Viewport da Fase 2 com câmera profissional, grid infinito, outlines e HUD overlays."""

    object_transform_changed = Signal(object)
    tool_message_requested = Signal(str)
    history_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        
        # Câmera e Renderizador da Viewport (Fase 2)
        self.camera = ViewportCamera()
        self.renderer = ViewportRenderer()

        # Gizmos legados / Fase 1
        self.move_gizmo_overlay = QtMoveGizmoOverlay()
        self.rotate_gizmo_overlay = QtRotateGizmoOverlay()

        # Serviços injetados
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
        self._rotate_start_angle: float = 0.0
        self._rotate_center_screen: tuple[float, float] = (0.0, 0.0)
        self._rotate_current_mouse: tuple[float, float] | None = None

        # Estado do drag de Scale
        self._scale_drag_object: Any = None
        self._scale_handle_idx: int | None = None
        self._scale_start_world = np.zeros(3, dtype=np.float32)
        self._scale_start_position = np.zeros(3, dtype=np.float32)
        self._scale_start_scale = np.ones(3, dtype=np.float32)

        # Estado de Panning
        self._panning: bool = False
        self._pan_last_mouse: tuple[float, float] = (0.0, 0.0)

        # Tempo do último render
        self._last_render_time: float = time.time()
        self.view_mode: str = "scene"

    # ── Injeção de dependências ───────────────────────────────────────────────

    def set_tool_manager(self, tool_manager: ToolManager) -> None:
        self.tool_manager = tool_manager

    def set_editor_state(self, editor_state: EditorState) -> None:
        self.editor_state = editor_state

    def set_command_manager(self, command_manager: CommandManager) -> None:
        self.command_manager = command_manager

    def set_view_mode(self, mode: str) -> None:
        self.view_mode = "game" if str(mode).lower() == "game" else "scene"

    def is_game_view(self) -> bool:
        return self.view_mode == "game"

    # ── Helpers de estado ─────────────────────────────────────────────────────

    def _active_tool(self) -> EditorTool:
        if self.tool_manager is None:
            return EditorTool.SELECT
        return self.tool_manager.active_tool

    def _is_playing(self) -> bool:
        if self.editor_state is not None and bool(getattr(self.editor_state, "is_playing", False)):
            return True
        return bool(getattr(getattr(self, "active_scene", None), "playing", False))

    def _should_draw_gizmo(self, selected: Any) -> bool:
        return selected is not None and not self._is_playing() and not self.is_game_view()

    def _snap_size(self) -> float:
        if self.editor_state is None:
            return 1.0
        return max(1.0, float(self.editor_state.snap_size))

    def _snap_enabled(self) -> bool:
        return bool(self.editor_state is not None and self.editor_state.snap_enabled)

    def _apply_snap(self, position: np.ndarray) -> np.ndarray:
        if not self._snap_enabled():
            return position
        snap = self._snap_size()
        snapped = position.copy()
        snapped[0] = round(float(snapped[0]) / snap) * snap
        snapped[1] = round(float(snapped[1]) / snap) * snap
        return snapped

    def _snap_angle(self) -> float:
        if self.editor_state is None:
            return 15.0
        return max(1.0, float(self.editor_state.snap_angle))

    def _apply_snap_angle(self, degrees: float) -> float:
        if not self._snap_enabled():
            return degrees
        snap = self._snap_angle()
        return round(degrees / snap) * snap

    # ── API Pública da Viewport (Mapeamento de Coordenadas) ───────────────────

    def world_to_viewport(self, point: tuple[float, float] | np.ndarray) -> tuple[float, float]:
        """Converte ponto no mundo [x, y] para coordenadas locais da viewport [px, py]."""
        return self.camera.world_to_viewport(point)

    def viewport_to_world(self, point: tuple[float, float]) -> np.ndarray:
        """Converte coordenadas locais da viewport [px, py] para ponto no mundo [x, y, 0]."""
        return self.camera.viewport_to_world(point)

    def screen_to_world(self, point: tuple[float, float]) -> np.ndarray:
        """Mapeia ponto de tela para coordenadas de mundo."""
        return self.camera.screen_to_world(point)

    def world_to_screen(self, point: tuple[float, float] | np.ndarray) -> tuple[float, float]:
        """Mapeia coordenadas de mundo para coordenadas de tela."""
        return self.camera.world_to_screen(point)

    # ── Sincronização ─────────────────────────────────────────────────────────

    def sync_camera_from_engine(self) -> None:
        """Atualiza a câmera a partir da engine se modificada externamente (ex. testes)."""
        from engine.graphics.camera2d import Camera2D
        if self.is_game_view():
            try:
                from engine.graphics.camera import Camera
                main_camera = Camera.main
            except Exception:
                main_camera = None
            if main_camera is not None and getattr(main_camera, "game_object", None) is not None:
                transform = main_camera.game_object.transform
                self.camera.zoom = float(getattr(main_camera, "zoom", 1.0))
                self.camera.target_zoom = self.camera.zoom
                self.camera.position[0] = float(transform.position[0])
                self.camera.position[1] = float(transform.position[1])
                return
        if Camera2D.main is not None:
            if self._is_playing():
                # Em modo de jogo, copia passivamente sem restrições
                self.camera.zoom = Camera2D.main.zoom
                self.camera.target_zoom = Camera2D.main.zoom
                self.camera.position[0] = Camera2D.main.transform.position[0]
                self.camera.position[1] = Camera2D.main.transform.position[1]
            else:
                # Sincroniza de volta se não estiver sob controle manual ativo
                if self.camera.zoom_anchor is None and not self._panning:
                    if not math.isclose(self.camera.zoom, Camera2D.main.zoom, abs_tol=1e-3):
                        self.camera.zoom = Camera2D.main.zoom
                        self.camera.target_zoom = Camera2D.main.zoom
                    if not np.allclose(self.camera.position[:2], Camera2D.main.transform.position[:2], atol=1e-3):
                        self.camera.position[0] = Camera2D.main.transform.position[0]
                        self.camera.position[1] = Camera2D.main.transform.position[1]

    def _sync_legacy_scale_handles(self) -> None:
        scene = getattr(self, "active_scene", None)
        if scene is None:
            return
        # Desativa permanentemente os handles legados (eixos desalinhados) na nova viewport
        scene.show_scale_handles = False

    # ── Seleção e Hover ───────────────────────────────────────────────────────

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
                if math.hypot(world[0] - pos[0], world[1] - pos[1]) <= scale[0] / 2.0:
                    return obj
            elif abs(world[0] - pos[0]) <= scale[0] / 2.0 and abs(world[1] - pos[1]) <= scale[1] / 2.0:
                return obj
        return None

    # ── Eventos de Redimensionamento ──────────────────────────────────────────

    def resizeGL(self, w: int, h: int) -> None:
        super().resizeGL(w, h)
        self.camera.set_viewport_size(w, h)

    # ── Drag/Drop de Transformações ───────────────────────────────────────────

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
        next_position = self._apply_snap(next_position)
        obj.transform.position[0] = next_position[0]
        obj.transform.position[1] = next_position[1]
        self.object_transform_changed.emit(obj)
        self.update()

    def _end_move_drag(self) -> None:
        obj = self._move_drag_object
        if obj is not None and hasattr(obj, "transform"):
            final_position = obj.transform.position.copy()
            start_position = self._move_start_position.copy()
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

    def _rotate_gizmo_hit_at_viewport_point(self, x: float, y: float, selected: Any) -> bool:
        if not self._should_draw_gizmo(selected):
            return False
        return self.rotate_gizmo_overlay.hit_test(x, y, selected, self.world_to_viewport)

    def _begin_rotate_drag(self, obj: Any, x: float, y: float) -> bool:
        if self._active_tool() != EditorTool.ROTATE:
            return False
        if self._is_playing():
            return False
        if obj is None or not hasattr(obj, "transform"):
            return False
        cx, cy = self.world_to_viewport(obj.transform.position)
        self._rotate_drag_object = obj
        self._rotate_start_rz = float(obj.transform.rz)
        self._rotate_start_angle = math.degrees(math.atan2(y - cy, x - cx))
        self._rotate_center_screen = (cx, cy)
        self._rotate_current_mouse = (x, y)
        self.select_object(obj)
        self._update_hover_cursor(x, y)
        return True

    def _update_rotate_drag(self, x: float, y: float) -> None:
        obj = self._rotate_drag_object
        if obj is None or not hasattr(obj, "transform"):
            return
        cx, cy = self.world_to_viewport(obj.transform.position)
        current_angle = math.degrees(math.atan2(y - cy, x - cx))
        delta = current_angle - self._rotate_start_angle
        new_rz = self._apply_snap_angle(self._rotate_start_rz + delta)
        obj.transform.rz = new_rz
        self._rotate_current_mouse = (x, y)
        self.object_transform_changed.emit(obj)
        self.update()

    def _end_rotate_drag(self) -> None:
        obj = self._rotate_drag_object
        if obj is not None and hasattr(obj, "transform"):
            final_rz = float(obj.transform.rz)
            start_rz = self._rotate_start_rz
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

    def _scale_handle_positions(self, obj: Any) -> list[tuple[float, float]]:
        if obj is None or not hasattr(obj, "transform"):
            return []
        pos = getattr(obj.transform, "position", None)
        scale = getattr(obj.transform, "scale", None)
        if pos is None or scale is None:
            return []

        p0 = self.world_to_viewport((pos[0] - scale[0] / 2.0, pos[1] - scale[1] / 2.0, pos[2]))
        p1 = self.world_to_viewport((pos[0] + scale[0] / 2.0, pos[1] + scale[1] / 2.0, pos[2]))
        bounds = (
            min(p0[0], p1[0]),
            min(p0[1], p1[1]),
            max(p0[0], p1[0]),
            max(p0[1], p1[1]),
        )
        return get_handle_positions(bounds)

    def _scale_handle_at_viewport_point(self, x: float, y: float, selected: Any) -> int | None:
        if self._active_tool() != EditorTool.SCALE:
            return None
        if not self._should_draw_gizmo(selected):
            return None
        return hit_test_handle((x, y), self._scale_handle_positions(selected), tolerance=8.0)

    def _begin_scale_drag(self, obj: Any, x: float, y: float, handle_idx: int) -> bool:
        if self._active_tool() != EditorTool.SCALE:
            return False
        if self._is_playing():
            return False
        if obj is None or not hasattr(obj, "transform"):
            return False
        self._scale_drag_object = obj
        self._scale_handle_idx = int(handle_idx)
        self._scale_start_world = self.viewport_to_world((x, y)).copy()
        self._scale_start_position = obj.transform.position.copy()
        self._scale_start_scale = obj.transform.scale.copy()
        self.select_object(obj)
        self._update_hover_cursor(x, y)
        return True

    def _update_scale_drag(self, x: float, y: float) -> None:
        obj = self._scale_drag_object
        handle_idx = self._scale_handle_idx
        if obj is None or handle_idx is None or not hasattr(obj, "transform"):
            return

        world = self.viewport_to_world((x, y))
        delta = world - self._scale_start_world
        next_position = self._scale_start_position.copy()
        next_scale = self._scale_start_scale.copy()

        affects_left = handle_idx in (0, 6, 7)
        affects_right = handle_idx in (2, 3, 4)
        affects_top = handle_idx in (0, 1, 2)
        affects_bottom = handle_idx in (4, 5, 6)

        if affects_right:
            next_scale[0] = self._scale_start_scale[0] + delta[0]
            next_position[0] = self._scale_start_position[0] + delta[0] / 2.0
        elif affects_left:
            next_scale[0] = self._scale_start_scale[0] - delta[0]
            next_position[0] = self._scale_start_position[0] + delta[0] / 2.0

        if affects_bottom:
            next_scale[1] = self._scale_start_scale[1] + delta[1]
            next_position[1] = self._scale_start_position[1] + delta[1] / 2.0
        elif affects_top:
            next_scale[1] = self._scale_start_scale[1] - delta[1]
            next_position[1] = self._scale_start_position[1] + delta[1] / 2.0

        if self._snap_enabled():
            snap = self._snap_size()
            next_scale[0] = round(float(next_scale[0]) / snap) * snap
            next_scale[1] = round(float(next_scale[1]) / snap) * snap

        next_scale[0] = max(1.0, float(next_scale[0]))
        next_scale[1] = max(1.0, float(next_scale[1]))

        obj.transform.position[0] = next_position[0]
        obj.transform.position[1] = next_position[1]
        obj.transform.scale[0] = next_scale[0]
        obj.transform.scale[1] = next_scale[1]
        self.object_transform_changed.emit(obj)
        self.update()

    def _end_scale_drag(self) -> None:
        obj = self._scale_drag_object
        if obj is not None and hasattr(obj, "transform"):
            final_position = obj.transform.position.copy()
            final_scale = obj.transform.scale.copy()
            start_position = self._scale_start_position.copy()
            start_scale = self._scale_start_scale.copy()
            scaled = (
                not np.allclose(final_scale[:2], start_scale[:2])
                or not np.allclose(final_position[:2], start_position[:2])
            )
            if scaled and self.command_manager is not None:
                def _do(p=final_position, s=final_scale, o=obj) -> None:
                    o.transform.position[0] = p[0]
                    o.transform.position[1] = p[1]
                    o.transform.scale[0] = s[0]
                    o.transform.scale[1] = s[1]
                    self.object_transform_changed.emit(o)

                def _undo(p=start_position, s=start_scale, o=obj) -> None:
                    o.transform.position[0] = p[0]
                    o.transform.position[1] = p[1]
                    o.transform.scale[0] = s[0]
                    o.transform.scale[1] = s[1]
                    self.object_transform_changed.emit(o)

                self.command_manager.execute(
                    FunctionCommand(
                        description=f"Scale {getattr(obj, 'name', 'object')}",
                        do=_do,
                        undo_action=_undo,
                    )
                )
                self.history_changed.emit()
        self._scale_drag_object = None
        self._scale_handle_idx = None
        self._update_hover_cursor(*self._qt_mouse_pos)

    # ── Cursores e Mensagens ──────────────────────────────────────────────────

    def _update_hover_cursor(self, x: float, y: float) -> None:
        if self._is_playing() or self.is_game_view():
            self.unsetCursor()
            return
        tool = self._active_tool()
        selected = self._selected_transform_object()

        if (
            self._move_drag_object is not None
            or self._rotate_drag_object is not None
            or self._scale_drag_object is not None
            or self._panning
        ):
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
            self.setCursor(Qt.CrossCursor)
        elif tool == EditorTool.SCALE and self._scale_handle_at_viewport_point(x, y, selected) is not None:
            self.setCursor(Qt.SizeAllCursor)
        elif tool == EditorTool.SELECT and self._object_at_viewport_point(x, y) is not None:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.unsetCursor()

    def _show_unimplemented_tool_message(self, tool: EditorTool) -> None:
        self.tool_message_requested.emit(f"{tool.value.title()} em desenvolvimento")

    # ── Eventos de Entrada (Mouse / Wheel) ────────────────────────────────────

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.is_game_view():
            event.accept()
            return
        """Processa zoom suave centralizado no cursor do mouse."""
        degrees = event.angleDelta().y() / 8.0
        steps = degrees / 15.0
        factor = 1.15 if steps > 0 else 1.0 / 1.15
        
        pos = event.position()
        self.camera.zoom_to_mouse(factor, pos.x(), pos.y())
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.is_game_view():
            super().mousePressEvent(event)
            return
        if self._is_playing():
            super().mousePressEvent(event)
            return

        tool = self._active_tool()
        x, y = float(event.x()), float(event.y())

        # Intercepta Pan (Botão do meio)
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_last_mouse = (x, y)
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

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
            if target is None and self._rotate_gizmo_hit_at_viewport_point(x, y, selected):
                target = selected
            if target is not None and self._begin_rotate_drag(target, x, y):
                event.accept()
                return
            event.accept()
            return

        if tool == EditorTool.SCALE:
            selected = self._selected_transform_object()
            handle_idx = self._scale_handle_at_viewport_point(x, y, selected)
            if selected is not None and handle_idx is not None and self._begin_scale_drag(selected, x, y, handle_idx):
                event.accept()
                return
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.is_game_view():
            super().mouseMoveEvent(event)
            return
        if self._is_playing():
            super().mouseMoveEvent(event)
            return

        x, y = float(event.x()), float(event.y())

        # Processa Pan ativo
        if self._panning:
            dx = x - self._pan_last_mouse[0]
            dy = y - self._pan_last_mouse[1]
            self.camera.pan(dx, dy)
            self._pan_last_mouse = (x, y)
            event.accept()
            return

        if self._active_tool() == EditorTool.MOVE and self._move_drag_object is not None:
            self._update_move_drag(x, y)
            event.accept()
            return

        if self._rotate_drag_object is not None:
            self._update_rotate_drag(x, y)
            event.accept()
            return

        if self._scale_drag_object is not None:
            self._update_scale_drag(x, y)
            event.accept()
            return

        self._update_hover_cursor(x, y)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.is_game_view():
            super().mouseReleaseEvent(event)
            return
        if self._is_playing():
            super().mouseReleaseEvent(event)
            return

        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self._update_hover_cursor(float(event.x()), float(event.y()))
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            if self._move_drag_object is not None:
                self._end_move_drag()
                event.accept()
                return
            if self._rotate_drag_object is not None:
                self._end_rotate_drag()
                event.accept()
                return
            if self._scale_drag_object is not None:
                self._end_scale_drag()
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def _tick(self) -> None:
        now = time.time()
        dt = min(now - self._last_time, 0.1)
        self._last_time = now

        if self.active_scene:
            runtime_playing = (
                self.runtime_manager is not None
                and getattr(self.runtime_manager, "is_playing", False)
            )
            is_runtime_scene = (
                runtime_playing
                and getattr(self.runtime_manager, "runtime_scene", None) is self.active_scene
            )
            if is_runtime_scene:
                self.runtime_manager.tick(dt)
            elif not runtime_playing:
                self.active_scene.update(dt)
                self._sync_selection_to_model()

        self.update()

    # ── Ciclo de Renderização (paintGL) ───────────────────────────────────────

    def paintGL(self) -> None:
        if not self.pg_surface or not self.active_scene:
            return

        self._sync_legacy_scale_handles()

        # Sincroniza modificações externas do Camera2D.main
        self.sync_camera_from_engine()

        # Atualiza a interpolação do zoom suave apenas se não estiver em modo de jogo
        now = time.time()
        dt = min(now - self._last_render_time, 0.1)
        self._last_render_time = now
        if not self._is_playing() and not self.is_game_view():
            self.camera.update(dt)

        # Salva o estado real do grid e desativa temporariamente para o blit do Pygame
        real_show_grid = True
        if self.active_scene is not None:
            real_show_grid = getattr(self.active_scene, "show_grid", True)
            self.active_scene.show_grid = False

        # Chama a renderização base (blit da superfície do pygame com os objetos)
        super().paintGL()

        # Restaura o estado real do grid na cena
        if self.active_scene is not None:
            self.active_scene.show_grid = real_show_grid

        painter = QPainter(self)
        
        # 1. Renderiza o Grid infinito usando QPainter por cima do fundo do Pygame
        draw_editor_overlays = not self.is_game_view() and not self._is_playing()
        self.renderer.render_grid(painter, self.camera, real_show_grid and draw_editor_overlays)

        # 2. Renderiza overlays Qt usando QPainter (Outlines, HUD, Bounding box, coordenadas)
        selected = self._selected_transform_object()
        active_tool = self._active_tool()
        object_count = len(self.active_scene.editable_objects) if self.active_scene else 0
        grid_size = self.renderer.grid_renderer.grid_size
        snap_on = self._snap_enabled()

        if not self.is_game_view():
            self.renderer.render_qt_overlays(
                painter=painter,
                camera=self.camera,
                selected=selected,
                active_tool_name=active_tool.value,
                object_count=object_count,
                grid_size=grid_size,
                snap_on=snap_on,
                mouse_screen_pos=self._qt_mouse_pos,
                is_playing=self._is_playing(),
            )

        # Renderiza os Gizmos clássicos (MOVE/ROTATE) por cima do HUD/Outlines
        if self._should_draw_gizmo(selected):
            if active_tool == EditorTool.MOVE:
                self.move_gizmo_overlay.draw(painter, selected, self.world_to_viewport)
            elif active_tool == EditorTool.ROTATE:
                mouse = self._rotate_current_mouse if self._rotate_drag_object is not None else None
                self.rotate_gizmo_overlay.draw(
                    painter, selected, self.world_to_viewport, current_mouse=mouse
                )

        painter.end()
