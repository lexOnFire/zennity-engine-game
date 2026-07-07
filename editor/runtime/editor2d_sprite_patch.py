from __future__ import annotations

from typing import Any

import pygame


def apply_editor2d_sprite_patch() -> bool:
    """Faz o viewport 2D desenhar ImageComponent como sprite quando existir.

    O Editor2D legado desenha objetos diretamente como formas coloridas e nao
    chama GameObject.draw(). Por isso, ao adicionar Image no Inspector, o Player
    continuava aparecendo como quadrado. Este patch preserva o desenho antigo
    como fallback e troca apenas objetos que possuem ImageComponent com sprite.
    """
    try:
        from editor_legacy.editor_2d import Editor2DScene
        from engine.ui.runtime_components import ImageComponent
        import editor_legacy.theme as T
    except Exception:
        return False

    if getattr(Editor2DScene, "_zennity_sprite_patch_applied", False):
        return True

    original_draw_object = Editor2DScene._draw_object

    def patched_draw_object(self, screen: pygame.Surface, obj: Any, idx: int, zoom: float, lay: dict) -> None:
        image = obj.get_component(ImageComponent) if hasattr(obj, "get_component") else None
        sprite_path = str(getattr(image, "sprite_path", "") or "") if image is not None else ""
        surface = ImageComponent.load_surface(sprite_path) if sprite_path else None
        if surface is None:
            original_draw_object(self, screen, obj, idx, zoom, lay)
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

        draw_w = max(1, int(abs(sw)))
        draw_h = max(1, int(abs(sh)))
        if surface.get_size() != (draw_w, draw_h):
            surface = pygame.transform.scale(surface, (draw_w, draw_h))
        alpha = int(getattr(image, "alpha", 255))
        if alpha < 255:
            surface = surface.copy()
            surface.set_alpha(max(0, min(255, alpha)))

        rz = getattr(obj.transform, "rz", 0.0)
        if rz != 0.0:
            surface = pygame.transform.rotate(surface, -rz)

        rect = surface.get_rect(center=(int(sx), int(sy)))
        screen.blit(surface, rect.topleft)

        selected = idx == self.selected_index
        if selected:
            pygame.draw.rect(screen, T.ACCENT, rect, 2, border_radius=4)

        name_s = self.font_sm.render(obj.name, True, T.TEXT_PRIMARY)
        screen.blit(name_s, (int(sx) - name_s.get_width() // 2, int(sy - sh / 2) - 14))

    Editor2DScene._draw_object = patched_draw_object
    Editor2DScene._zennity_sprite_patch_applied = True
    return True
