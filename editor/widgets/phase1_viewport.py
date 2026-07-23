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
from editor.render.adapters import (
    BackgroundRendererAdapter,
    FramebufferPresentRendererAdapter,
    FramePreparationAdapter,
    GizmoRendererAdapter,
    GridRendererAdapter,
    LegacySceneRendererAdapter,
    OverlayRendererAdapter,
    SpriteRendererAdapter,
)
from editor.render.render_pipeline import (
    BackgroundPass,
    FramebufferPresentPass,
    GizmoPass,
    GridPass,
    LegacySceneAdapter,
    LegacyScenePass,
    OverlayPass,
    RenderPipeline,
    SpriteOverlayPass,
    TransformGizmoPass,
)
from editor.render.sprite_overlay_renderer import SpriteDrawCommand, SpriteOverlayRenderer
from editor.runtime.command_manager import CommandManager, FunctionCommand
from editor.runtime.editor_state import EditorState
from editor.runtime.tool_manager import EditorTool, ToolManager
from editor.viewport.bounding_box import get_handle_positions, hit_test_handle
from editor.widgets.viewport_widget import ViewportWidget
from editor.widgets.viewport_gizmo_drag import ViewportGizmoDragMixin
from editor.widgets.transform_interaction import (
    activate_gizmo_reference,
    draw_transform_overlay,
    emit_transform_changed,
    event_position,
    move_axis_at,
    request_editor_frame,
    sync_camera_to_engine,
)

# Novos módulos da Fase 2
from editor.viewport.viewport_camera import ViewportCamera
from editor.viewport.viewport_renderer import ViewportRenderer


class Phase1ViewportWidget(ViewportGizmoDragMixin, ViewportWidget):
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
        self.runtime_manager: Any | None = None

        # Estado do drag de Move
        self._move_drag_object: Any = None
        self._move_start_world = np.zeros(3, dtype=np.float32)
        self._move_start_position = np.zeros(3, dtype=np.float32)
        self._move_axis_lock: str | None = None

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
        self._pipeline_grid_states: list[tuple[Any, bool]] = []
        self._pipeline_real_show_grid: bool = True
        self._pipeline_modern_sprites: list[SpriteDrawCommand] = []
        self.sprite_overlay_renderer = SpriteOverlayRenderer()
        self.background_renderer_adapter = BackgroundRendererAdapter()
        self.legacy_scene_renderer_adapter = LegacySceneRendererAdapter(
            self, self.background_renderer_adapter
        )
        self.grid_renderer_adapter = GridRendererAdapter(self)
        self.gizmo_renderer_adapter = GizmoRendererAdapter(self)
        self.overlay_renderer_adapter = OverlayRendererAdapter(self)
        self.frame_preparation_adapter = FramePreparationAdapter(
            self, QPainter, self.sprite_overlay_renderer
        )
        self.framebuffer_present_renderer_adapter = FramebufferPresentRendererAdapter(self)
        self.sprite_renderer_adapter = SpriteRendererAdapter(self, self.sprite_overlay_renderer)
        self.render_pipeline = self._build_render_pipeline()

    def _build_render_pipeline(self) -> RenderPipeline:
        return RenderPipeline([
            # O fundo permanece no legado até sua migração poder preservar
            # exatamente Camera.clear_color e fundos infinitos.
            BackgroundPass(self.background_renderer_adapter.render),
            LegacyScenePass(LegacySceneAdapter(self.legacy_scene_renderer_adapter.render)),
            GizmoPass(self.gizmo_renderer_adapter.render_components),
            FramebufferPresentPass(self.framebuffer_present_renderer_adapter.render),
            # Mantém a grade acima dos sprites, como no framebuffer legado.
            SpriteOverlayPass(self.sprite_renderer_adapter.render),
            GridPass(self.grid_renderer_adapter.render),
            OverlayPass(self.overlay_renderer_adapter.render),
            # Preserva a ordem histórica acima de seleção, bounding box e HUD.
            TransformGizmoPass(self.gizmo_renderer_adapter.render_transform),
        ])

    # ── Injeção de dependências ───────────────────────────────────────────────

    def set_tool_manager(self, tool_manager: ToolManager) -> None:
        if self.tool_manager is not None:
            self.tool_manager.unsubscribe(self._on_tool_changed)
        self.tool_manager = tool_manager
        tool_manager.subscribe(self._on_tool_changed)
        self._on_tool_changed(tool_manager.active_tool)

    def _on_tool_changed(self, tool: EditorTool) -> None:
        activate_gizmo_reference(self, tool)
        self.request_render("tool")

    def set_editor_state(self, editor_state: EditorState) -> None:
        self.editor_state = editor_state

    def set_command_manager(self, command_manager: CommandManager) -> None:
        self.command_manager = command_manager

    def select_object(self, obj: Any) -> None:
        if hasattr(self, "viewmodel") and self.viewmodel is not None:
            self.viewmodel.selected_object = obj

    def set_runtime_manager(self, runtime_manager: Any) -> None:
        self.runtime_manager = runtime_manager

    def set_view_mode(self, mode: str) -> None:
        self.view_mode = "game" if str(mode).lower() == "game" else "scene"
        self.request_render("view-mode")

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

    def _grid_state_targets(self) -> list[Any]:
        scene = getattr(self, "active_scene", None)
        if scene is None:
            return []
        targets = [scene]
        inner_scene = getattr(scene, "scene", None)
        if inner_scene is not None and inner_scene is not scene:
            targets.append(inner_scene)
        return targets

    def _capture_grid_state(self) -> list[tuple[Any, bool]]:
        states: list[tuple[Any, bool]] = []
        for target in self._grid_state_targets():
            states.append((target, bool(getattr(target, "show_grid", True))))
        return states

    def _set_grid_visible(self, visible: bool) -> None:
        for target in self._grid_state_targets():
            if hasattr(target, "show_grid"):
                target.show_grid = bool(visible)

    def _restore_grid_state(self, states: list[tuple[Any, bool]]) -> None:
        for target, visible in states:
            if hasattr(target, "show_grid"):
                target.show_grid = visible

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
        self.camera.set_viewport_size(max(32, int(w)), max(32, int(h)))
        self.request_render("camera-resize")
        sync_camera_to_engine(self)

    # ── Drag/Drop de Transformações ───────────────────────────────────────────


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
        sync_camera_to_engine(self)
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.is_game_view():
            super().mousePressEvent(event)
            return
        if self._is_playing():
            super().mousePressEvent(event)
            return

        tool = self._active_tool()
        x, y = event_position(event)

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
            selected = self._selected_transform_object()
            axis = move_axis_at(self, x, y, selected)
            target = selected if axis is not None else self._object_at_viewport_point(x, y)
            if target is not None and self._begin_move_drag(target, x, y):
                self._move_axis_lock = axis
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

        x, y = event_position(event)

        # Processa Pan ativo
        if self._panning:
            dx = x - self._pan_last_mouse[0]
            dy = y - self._pan_last_mouse[1]
            self.camera.pan(dx, dy)
            self._pan_last_mouse = (x, y)
            sync_camera_to_engine(self)
            request_editor_frame(self)
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

        camera_animating = not math.isclose(
            float(self.camera.zoom), float(self.camera.target_zoom), abs_tol=0.001
        )
        if is_runtime_scene or self._is_playing() or camera_animating:
            self.request_render("continuous")
        else:
            self._frame_invalidation.record_idle_tick()

    # ── Ciclo de Renderização (paintGL) ───────────────────────────────────────

    def paintGL(self) -> None:
        context = self.frame_preparation_adapter.create_context()
        if context is None:
            return
        try:
            self.render_pipeline.render(context)
        finally:
            self.frame_preparation_adapter.finish(context)
        draw_transform_overlay(self)
