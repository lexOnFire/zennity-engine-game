from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame


def _image_component(obj: Any) -> Any | None:
    for component in getattr(obj, "components", []):
        if getattr(component, "type_name", type(component).__name__) == "Image":
            if str(getattr(component, "sprite_path", "") or "").strip():
                return component
    return None


def _load_surface(sprite_path: str) -> pygame.Surface | None:
    try:
        from engine.ui.runtime_components import ImageComponent
        surface = ImageComponent.load_surface(sprite_path)
        if surface is not None:
            return surface
    except Exception:
        pass

    raw = Path(str(sprite_path).strip().replace("\\", "/"))
    candidates = [raw] if raw.is_absolute() else [Path.cwd() / raw, Path(__file__).resolve().parents[2] / raw]
    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        try:
            return pygame.image.load(str(path)).convert_alpha()
        except Exception:
            return None
    return None


def apply_editor2d_sprite_no_border_patch() -> bool:
    try:
        from editor_legacy.editor_2d import Editor2DScene
    except Exception:
        return False

    if getattr(Editor2DScene, "_zennity_sprite_no_border_patch_applied", False):
        return True

    base_draw = getattr(Editor2DScene, "_draw_object")

    def draw_without_legacy_shape(self, screen: pygame.Surface, obj: Any, idx: int, zoom: float, lay: dict) -> None:
        image = _image_component(obj)
        if image is None:
            base_draw(self, screen, obj, idx, zoom, lay)
            return
        if bool(getattr(obj, "runtime_hidden", False)):
            return

        sprite_path = str(getattr(image, "sprite_path", "") or "")
        surface = _load_surface(sprite_path)
        if surface is None:
            # Se existe Image com caminho, nao desenha a forma antiga. Isso evita
            # o quadrado verde ficar por tras quando a camada Qt desenha o sprite.
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

    Editor2DScene._draw_object = draw_without_legacy_shape
    Editor2DScene._zennity_sprite_no_border_patch_applied = True
    return True
