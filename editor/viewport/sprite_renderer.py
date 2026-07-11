"""
editor/viewport/sprite_renderer.py

Renderizador de sprites 2D para o Editor Qt.

Substitui a lógica dos monkey patches:
  - editor/runtime/editor2d_sprite_patch.py
  - editor/runtime/editor2d_sprite_no_border_patch.py

Responsabilidades:
  - Iterar scene.editable_objects
  - Localizar ImageComponent via get_component / iteração por type_name
  - Usar ImageComponent.load_surface() + fallback direto via pygame.image.load
  - Aplicar scale, alpha e rotação (rz)
  - Desenhar sprite no pg_surface
  - Desenhar borda de seleção usando selected_obj (SelectionManager)
  - Desenhar label de nome acima do sprite

NÃO usa selected_index.
NÃO monkey-patcha nenhuma classe.
NÃO importa editor_legacy a não ser via duck-typing em tempo de execução.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame

# Cor da borda de seleção (mesmo tom de accent do theme legado)
_SELECTION_COLOR: tuple[int, int, int] = (80, 160, 255)
_SELECTION_WIDTH: int = 2
_LABEL_COLOR: tuple[int, int, int] = (235, 235, 235)

# Cache simples: (sprite_path, draw_w, draw_h, rz) -> pygame.Surface
# Evita transform.scale + transform.rotate a cada frame
_SURFACE_CACHE: dict[tuple[str, int, int, float], pygame.Surface] = {}
_CACHE_MAX = 256


def _evict_cache() -> None:
    """Remove metade das entradas mais antigas quando o cache enche."""
    global _SURFACE_CACHE
    keys = list(_SURFACE_CACHE.keys())
    for k in keys[: len(keys) // 2]:
        del _SURFACE_CACHE[k]


def _find_image_component(obj: Any) -> Any | None:
    """Retorna ImageComponent com sprite_path válido, ou None.

    Tenta primeiro get_component(ImageComponent) (preferido),
    depois faz iteração por type_name == 'Image' (compatibilidade legada).
    """
    # Tentativa 1: API moderna
    try:
        from engine.ui.runtime_components import ImageComponent  # type: ignore
        comp = obj.get_component(ImageComponent) if hasattr(obj, "get_component") else None
        if comp is not None and str(getattr(comp, "sprite_path", "") or "").strip():
            return comp
    except Exception:
        pass

    # Tentativa 2: duck-typing por type_name (compatibilidade com patches antigos)
    for comp in getattr(obj, "components", []):
        if getattr(comp, "type_name", type(comp).__name__) == "Image":
            if str(getattr(comp, "sprite_path", "") or "").strip():
                return comp

    return None


def _load_surface(sprite_path: str) -> pygame.Surface | None:
    """Carrega superfície via ImageComponent.load_surface com fallback direto."""
    # Tentativa 1: cache interno do ImageComponent
    try:
        from engine.ui.runtime_components import ImageComponent  # type: ignore
        surf = ImageComponent.load_surface(sprite_path)
        if surf is not None:
            return surf
    except Exception:
        pass

    # Tentativa 2: carga direta (mesmo comportamento do no-border patch)
    raw = Path(str(sprite_path).strip().replace("\\", "/"))
    candidates = (
        [raw]
        if raw.is_absolute()
        else [Path.cwd() / raw, Path(__file__).resolve().parents[2] / raw]
    )
    for path in candidates:
        if path.exists() and path.is_file():
            try:
                return pygame.image.load(str(path)).convert_alpha()
            except Exception:
                return None
    return None


def _get_or_create_surface(
    base: pygame.Surface,
    draw_w: int,
    draw_h: int,
    rz: float,
    alpha: int,
    sprite_path: str,
) -> pygame.Surface:
    """Aplica scale, alpha e rotação com cache."""
    cache_key = (sprite_path, draw_w, draw_h, rz)
    cached = _SURFACE_CACHE.get(cache_key)
    if cached is not None:
        # Alpha pode mudar sem invalidar o cache de transformação — aplica na cópia
        if alpha < 255:
            s = cached.copy()
            s.set_alpha(max(0, min(255, alpha)))
            return s
        return cached

    # Scale
    surf = base if base.get_size() == (draw_w, draw_h) else pygame.transform.scale(base, (draw_w, draw_h))

    # Rotação
    if rz != 0.0:
        surf = pygame.transform.rotate(surf, -rz)

    # Armazena no cache (sem alpha — aplicado na hora para evitar sujar o cache)
    if len(_SURFACE_CACHE) >= _CACHE_MAX:
        _evict_cache()
    _SURFACE_CACHE[cache_key] = surf

    if alpha < 255:
        surf = surf.copy()
        surf.set_alpha(max(0, min(255, alpha)))

    return surf


def _get_font(font_attr: Any = None) -> pygame.font.Font:
    """Retorna fonte de label (reutiliza font_sm da cena se disponível)."""
    if font_attr is not None and isinstance(font_attr, pygame.font.Font):
        return font_attr
    return pygame.font.SysFont("Arial", 11)


class SpriteRenderer:
    """Renderer de sprites 2D para o Qt viewport do Editor.

    Uso:
        renderer = SpriteRenderer()
        renderer.draw(pg_surface, scene, selected_obj, layout, zoom)

    Parâmetros de draw():
        surface      : pygame.Surface — o pg_surface do ViewportWidget
        scene        : Editor2DScene ou duck-type com editable_objects + _world_to_vp + _layout
        selected_obj : objeto selecionado (via SelectionManager); pode ser None
        layout       : dict retornado por scene._layout() (com vp_left/right/top/bottom)
        zoom         : float — zoom atual da câmera
    """

    def draw(
        self,
        surface: pygame.Surface,
        scene: Any,
        selected_obj: Any,
        layout: dict,
        zoom: float = 1.0,
    ) -> None:
        """Renderiza todos os sprites 2D da cena sobre o surface."""
        if surface is None or scene is None:
            return

        editable = list(getattr(scene, "editable_objects", []))
        world_to_vp = getattr(scene, "_world_to_vp", None)
        if world_to_vp is None:
            return

        font = _get_font(getattr(scene, "font_sm", None))

        for obj in editable:
            self._draw_object(surface, obj, world_to_vp, layout, zoom, selected_obj, font)

    def _draw_object(
        self,
        surface: pygame.Surface,
        obj: Any,
        world_to_vp: Any,
        layout: dict,
        zoom: float,
        selected_obj: Any,
        font: pygame.font.Font,
    ) -> None:
        """Desenha um único objeto se tiver ImageComponent com sprite_path válido."""
        if bool(getattr(obj, "runtime_hidden", False)):
            return

        image = _find_image_component(obj)
        if image is None:
            return  # sem ImageComponent: o _draw_object legado já cuidou disso

        sprite_path = str(getattr(image, "sprite_path", "") or "")
        base_surf = _load_surface(sprite_path)
        if base_surf is None:
            # Tem ImageComponent mas superfície não carregou:
            # não desenha nada (evita quadrado legado por trás)
            return

        pos = obj.transform.position
        scale = obj.transform.scale
        try:
            sx, sy = world_to_vp(pos, layout)
        except Exception:
            return

        sw = float(scale[0]) * float(zoom)
        sh = float(scale[1]) * float(zoom)

        # Culling
        vp_left  = layout.get("vp_left",  layout.get("viewport_x", 0))
        vp_right  = layout.get("vp_right", layout.get("viewport_x", 0) + layout.get("viewport_w", surface.get_width()))
        vp_top    = layout.get("vp_top",   layout.get("viewport_y", 0))
        vp_bottom = layout.get("vp_bottom", layout.get("viewport_y", 0) + layout.get("viewport_h", surface.get_height()))

        if sx + sw / 2 < vp_left or sx - sw / 2 > vp_right:
            return
        if sy + sh / 2 < vp_top or sy - sh / 2 > vp_bottom:
            return

        draw_w = max(1, int(abs(sw)))
        draw_h = max(1, int(abs(sh)))
        alpha = int(getattr(image, "alpha", 255))
        rz = float(getattr(obj.transform, "rz", 0.0))

        surf = _get_or_create_surface(base_surf, draw_w, draw_h, rz, alpha, sprite_path)

        rect = surf.get_rect(center=(int(sx), int(sy)))
        surface.blit(surf, rect.topleft)

        # Borda de seleção — via selected_obj (SelectionManager), não selected_index
        if selected_obj is obj:
            base_rect = pygame.Rect(
                int(sx - draw_w / 2),
                int(sy - draw_h / 2),
                draw_w,
                draw_h,
            )
            pygame.draw.rect(surface, _SELECTION_COLOR, base_rect, _SELECTION_WIDTH, border_radius=4)

        # Label de nome
        label = font.render(obj.name, True, _LABEL_COLOR)
        surface.blit(label, (int(sx) - label.get_width() // 2, int(sy - sh / 2) - 14))
