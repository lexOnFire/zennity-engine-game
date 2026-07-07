from __future__ import annotations

from typing import Any

import pygame


def apply_editor2d_sprite_no_border_patch() -> bool:
    try:
        from editor_legacy.editor_2d import Editor2DScene
        from engine.ui.runtime_components import ImageComponent
    except Exception:
        return False

    if getattr(Editor2DScene, "_zennity_sprite_no_border_patch_applied", False):
        return True

    base_draw = getattr(Editor2DScene, "_draw_object")

    def draw_without_legacy_rect(self, screen: pygame.Surface, obj: Any, idx: int, zoom: float, lay: dict) -> None:
        image = obj.get_component(ImageComponent) if hasattr(obj, "get_component") else None
        sprite_path = str(getattr(image, "sprite_path", "") or "") if image is not None else ""
        surface = ImageComponent.load_surface(sprite_path) if sprite_path else None
        if surface is None:
            base_draw(self, screen, obj, idx, zoom, lay)
            return
        if bool(getattr(obj, "runtime_hidden", False)):
            return

        pos = obj.transform.position
        scale = obj.transform.scale
        sx, sy = self._world_to_vp(pos, lay)
        sw = float(scale[0]) * float(zoom)
        sh = float(scale[1]) * float(zoom)
        if sx + sw / 2 < lay["vp_left"] or sx - sw / 2 > lay["vp_right"]:
            return
        if sy + sh / 2 < lay["vp_top"] or sy - sh / 2 > lay["vp_bottom"]:
            return

        size = (max(1, int(abs(sw))), max(1, int(abs(sh))))
        if surface.get_size() != size:
            surface = pygame.transform.scale(surface, size)
        alpha = int(getattr(image, "alpha", 255))
        if alpha < 255:
            surface = surface.copy()
            surface.set_alpha(max(0, min(255, alpha)))
        rz = getattr(obj.transform, "rz", 0.0)
        if rz != 0.0:
            surface = pygame.transform.rotate(surface, -rz)

        rect = surface.get_rect(center=(int(sx), int(sy)))
        screen.blit(surface, rect.topleft)
        label = self.font_sm.render(obj.name, True, (235, 235, 235))
        screen.blit(label, (int(sx) - label.get_width() // 2, int(sy - sh / 2) - 14))

    Editor2DScene._draw_object = draw_without_legacy_rect
    Editor2DScene._zennity_sprite_no_border_patch_applied = True
    return True
