"""Adaptadores tipados entre RenderPass e os renderizadores da Scene View."""
from __future__ import annotations

import time
from typing import Any

from editor.render.render_pipeline import RenderContext


class BackgroundRendererAdapter:
    """Resolve limpeza, cor da câmera e desenho de fundos da cena."""

    def __init__(self) -> None:
        self.managed = False

    def render(self, context: RenderContext) -> None:
        draw_background = getattr(context.active_scene, "_zennity_draw_background", None)
        if not callable(draw_background):
            draw_background = getattr(context.active_scene, "draw_background", None)
        if callable(draw_background):
            self.managed = True
            draw_background(context.pygame_surface)
            return
        color = getattr(context.active_scene, "_zennity_background_color", None)
        if color is None and callable(getattr(context.active_scene, "draw_content", None)):
            main_camera = None
            try:
                from engine.graphics.camera import Camera
                main_camera = Camera.main
            except ImportError:
                pass
            color = tuple(main_camera.clear_color) if main_camera is not None else (30, 30, 30)
        self.managed = color is not None
        if self.managed:
            context.pygame_surface.fill(color)


class LegacySceneRendererAdapter:
    """Seleciona draw integral ou draw_content sem conhecer outros passes."""

    def __init__(self, viewport: Any, background: BackgroundRendererAdapter) -> None:
        self.viewport = viewport
        self.background = background

    def render(self, context: RenderContext) -> None:
        draw_content = None
        if self.background.managed:
            draw_content = getattr(context.active_scene, "_zennity_draw_content", None)
            if not callable(draw_content):
                draw_content = getattr(context.active_scene, "draw_content", None)
        self.viewport._draw_legacy_scene_content(scene_draw=draw_content)


class GridRendererAdapter:
    """Adapta a câmera da viewport ao contrato existente do GridRenderer."""

    def __init__(self, viewport: Any) -> None:
        self.viewport = viewport

    def render(self, context: RenderContext) -> None:
        viewport = self.viewport
        visible = viewport._pipeline_real_show_grid
        editor_view = not viewport.is_game_view() and not viewport._is_playing()
        if visible and editor_view:
            viewport.renderer.grid_renderer.draw(
                painter=context.painter,
                vp_w=viewport.camera.vp_w,
                vp_h=viewport.camera.vp_h,
                zoom=viewport.camera.zoom,
                camera_pos=viewport.camera.position,
                world_to_viewport=viewport.camera.world_to_viewport,
            )


class GizmoRendererAdapter:
    """Adapta gizmos Pygame de componentes e gizmos Qt de transformação."""

    def __init__(self, viewport: Any) -> None:
        self.viewport = viewport

    def render_components(self, context: RenderContext) -> None:
        self.viewport._draw_legacy_gizmos()

    def render_transform(self, context: RenderContext) -> None:
        viewport = self.viewport
        selected = viewport._selected_transform_object()
        active_tool = viewport._active_tool()
        tool_name = str(getattr(active_tool, "value", active_tool)).lower()
        if not viewport._should_draw_gizmo(selected):
            return
        if tool_name == "move":
            viewport.move_gizmo_overlay.draw(context.painter, selected, viewport.world_to_viewport)
        elif tool_name == "rotate":
            mouse = viewport._rotate_current_mouse if viewport._rotate_drag_object is not None else None
            viewport.rotate_gizmo_overlay.draw(
                context.painter,
                selected,
                viewport.world_to_viewport,
                current_mouse=mouse,
            )


class OverlayRendererAdapter:
    """Coordena seleção, bounding box, HUD e coordenadas da Scene View."""

    def __init__(self, viewport: Any) -> None:
        self.viewport = viewport

    def render(self, context: RenderContext) -> None:
        viewport = self.viewport
        if viewport.is_game_view():
            return
        selected = viewport._selected_transform_object()
        active_tool = viewport._active_tool()
        object_count = len(context.active_scene.editable_objects)
        viewport.renderer.render_selection_overlays(
            painter=context.painter,
            camera=viewport.camera,
            selected=selected,
            active_tool_name=active_tool.value,
            is_playing=viewport._is_playing(),
        )
        viewport.renderer.render_hud_overlays(
            painter=context.painter,
            camera=viewport.camera,
            active_tool_name=active_tool.value,
            object_count=object_count,
            grid_size=viewport.renderer.grid_renderer.grid_size,
            snap_on=viewport._snap_enabled(),
            mouse_screen_pos=viewport._qt_mouse_pos,
            is_playing=viewport._is_playing(),
        )


class FramePreparationAdapter:
    """Prepara câmera, grid, sprites e RenderContext de um único frame."""

    def __init__(self, viewport: Any, painter_factory: Any, sprite_renderer: Any) -> None:
        self.viewport = viewport
        self.painter_factory = painter_factory
        self.sprite_renderer = sprite_renderer

    def create_context(self) -> RenderContext | None:
        viewport = self.viewport
        if not viewport.pg_surface or not viewport.active_scene:
            return None
        viewport._frame_invalidation.consume()
        viewport._sync_legacy_scale_handles()
        viewport.sync_camera_from_engine()
        now = time.time()
        dt = min(now - viewport._last_render_time, 0.1)
        viewport._last_render_time = now
        if not viewport._is_playing() and not viewport.is_game_view():
            viewport.camera.update(dt)
        viewport._pipeline_grid_states = viewport._capture_grid_state()
        viewport._pipeline_real_show_grid = (
            viewport._pipeline_grid_states[0][1]
            if viewport._pipeline_grid_states else True
        )
        viewport._set_grid_visible(False)
        use_modern_sprites = not viewport._is_playing() and not viewport.is_game_view()
        viewport._pipeline_modern_sprites = (
            self.sprite_renderer.collect(viewport.active_scene) if use_modern_sprites else []
        )
        viewport.active_scene._zennity_modern_sprite_component_ids = {
            id(command.component) for command in viewport._pipeline_modern_sprites
        }
        return RenderContext(
            viewport=viewport,
            painter=self.painter_factory(viewport),
            pygame_surface=viewport.pg_surface,
            active_scene=viewport.active_scene,
            editor_context=viewport.editor_state,
            runtime_manager=viewport.runtime_manager,
            selection_manager=getattr(viewport, "selection_manager", None),
        )

    def finish(self, context: RenderContext) -> None:
        viewport = self.viewport
        if viewport.active_scene is not None:
            viewport.active_scene._zennity_modern_sprite_component_ids = set()
        viewport._restore_grid_state(viewport._pipeline_grid_states)
        context.painter.end()


class FramebufferPresentRendererAdapter:
    """Restaura o grid legado e apresenta o framebuffer no QPainter atual."""

    def __init__(self, viewport: Any) -> None:
        self.viewport = viewport

    def render(self, context: RenderContext) -> None:
        self.viewport._restore_grid_state(self.viewport._pipeline_grid_states)
        self.viewport._present_legacy_framebuffer(context.painter)


class SpriteRendererAdapter:
    """Liga SpriteOverlayPass ao renderizador moderno e ao frame preparado."""

    def __init__(self, viewport: Any, renderer: Any) -> None:
        self.viewport = viewport
        self.renderer = renderer

    def render(self, context: RenderContext) -> None:
        self.renderer.draw(
            context.painter,
            self.viewport.camera,
            self.viewport._pipeline_modern_sprites,
        )
