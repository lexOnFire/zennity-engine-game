from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any

import pygame

from engine.core.component import Component


class RuntimeUIElement(Component):
    """Base oficial para componentes de UI em Runtime Screen Space.

    CONSOLIDAÇÃO (mapa dos 4 sistemas de UI paralelos da engine): este módulo
    (``engine.ui.runtime_components``) é o ÚNICO formato de PERSISTÊNCIA
    oficial de UI em ``.zscene`` (via ``component_registry``). Os outros três
    sistemas de UI da engine são consumidores ou tradutores deste, nunca o
    contrário:
      - ``engine.ui`` (base.py/canvas.py/label.py/...) é a API "code-first"
        usada por jogos escritos 100% em Python sem passar pelo editor visual
        (zennity_run.py, demos/demo_ui.py) — não participa da persistência
        `.zscene` nem do pipeline de export.
      - ``engine.ui.runtime`` (runtime/widgets.py) é usado só pelo UI Builder
        do editor (editor/ui_builder/ui_builder_dock.py) para desenhar/editar
        visualmente; salva num formato próprio ("zennity.ui") que hoje não
        alimenta nenhum runtime de jogo.
      - ``editor/runtime/native_ui.py`` é o motor de RENDERIZAÇÃO do Play Mode
        isolado e também do jogo EXPORTADO (é copiado literalmente para
        dentro do pacote final por engine/build/project_exporter.py) — ele
        converte de/para este módulo via scene_item_to_ui()/ui_to_scene_item(),
        nunca define seu próprio schema de dados persistente.
    Ao adicionar um campo novo aqui, sempre checar se `native_ui.normalize_ui`
    precisa do mesmo default (ele preserva chaves desconhecidas via dict
    merge, então não quebra, mas os defaults ficam divergentes se esquecido).
    """

    component_type = "UIElement"

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 100.0,
        height: float = 30.0,
        visible: bool = True,
        z_order: int = 0,
        widget_name: str = "",
        anchor: str = "",
        margin_x: float = 16.0,
        margin_y: float = 16.0,
    ) -> None:
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.visible = bool(visible)
        self.z_order = int(z_order)
        # BUG FIX (ambiguidade de HUD): quando um GameObject composto (ex.:
        # "HUD") tem vários componentes de UI do MESMO tipo (duas Labels: uma
        # de título, outra de contador de moedas), `get_component(LabelComponent)`
        # sempre retorna só o primeiro da lista — não há como o Logic Graph
        # apontar para o widget certo. `widget_name` é um identificador livre
        # (definido no editor) que os nós set_ui_text/set_ui_progress_bar/
        # set_ui_visible usam para desambiguar; veja ui_nodes.py `_find_widget`.
        self.widget_name = str(widget_name)
        # CONSOLIDAÇÃO: editor/runtime/native_ui.py já normaliza "anchor"/
        # "margin_x"/"margin_y" (posicionamento relativo a um canto da tela,
        # 4 opções) no snapshot de Play Mode, mas este componente serializável
        # não tinha esses campos — hoje o editor ainda não expõe um controle
        # de Inspector para editá-los, então não é um bug ativo, mas sem isso
        # o valor se perderia silenciosamente no primeiro save/load assim que
        # esse controle existir. Adicionado agora, antes de virar bug.
        self.anchor = str(anchor)
        self.margin_x = float(margin_x)
        self.margin_y = float(margin_y)

    def on_runtime_start(self) -> None:
        """Isola objetos puramente UI do world draw sem esconder objetos mistos."""
        if self.game_object is None:
            return None
        if self._owner_is_pure_ui():
            self.game_object.runtime_hidden = True
        elif hasattr(self.game_object, "runtime_hidden"):
            delattr(self.game_object, "runtime_hidden")

        # PHASE 3G: Auto-register no UIRuntimeService
        try:
            from engine.ui.runtime_service import UIRuntimeService
            ui_service = UIRuntimeService.instance()
            ui_service.register_widget(self)
        except (ImportError, AttributeError):
            # Service indisponível — fallback silencioso
            pass
        return None

    def destroy(self) -> None:
        """PHASE 3H: Auto-unregister do UIRuntimeService ao destruir."""
        try:
            from engine.ui.runtime_service import UIRuntimeService
            ui_service = UIRuntimeService.instance()
            ui_service.unregister_widget(self)
        except (ImportError, AttributeError):
            pass  # Service indisponível

    def _owner_is_pure_ui(self) -> bool:
        if self.game_object is None:
            return False
        for component in getattr(self.game_object, "components", []):
            if component is self or isinstance(component, RuntimeUIElement):
                continue
            if getattr(component, "required", False) or type(component).__name__ == "Transform":
                continue
            return False
        return True

    def serialize_properties(self) -> dict[str, Any]:
        return {
            "x": float(self.x),
            "y": float(self.y),
            "width": float(self.width),
            "height": float(self.height),
            "visible": bool(self.visible),
            "z_order": int(self.z_order),
            "widget_name": str(self.widget_name),
            "anchor": str(self.anchor),
            "margin_x": float(self.margin_x),
            "margin_y": float(self.margin_y),
        }

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        self.x = float(data.get("x", self.x))
        self.y = float(data.get("y", self.y))
        self.width = float(data.get("width", self.width))
        self.height = float(data.get("height", self.height))
        self.visible = bool(data.get("visible", self.visible))
        self.z_order = int(data.get("z_order", self.z_order))
        self.widget_name = str(data.get("widget_name", self.widget_name))
        self.anchor = str(data.get("anchor", self.anchor))
        self.margin_x = float(data.get("margin_x", self.margin_x))
        self.margin_y = float(data.get("margin_y", self.margin_y))


class Canvas(RuntimeUIElement):
    """Agrupa elementos de UI e define a ordem de renderizacao do HUD."""

    component_type = "Canvas"
    unique = True

    def __init__(self, visible: bool = True, z_order: int = 0) -> None:
        super().__init__(x=0.0, y=0.0, width=0.0, height=0.0, visible=visible, z_order=z_order)


class LabelComponent(RuntimeUIElement):
    component_type = "Label"

    def __init__(
        self,
        text: str = "Label",
        x: float = 0.0,
        y: float = 0.0,
        font_size: int = 20,
        color: tuple[int, int, int] = (255, 255, 255),
        visible: bool = True,
        z_order: int = 0,
    ) -> None:
        super().__init__(x=x, y=y, width=0.0, height=0.0, visible=visible, z_order=z_order)
        self.text = str(text)
        self.font_size = int(font_size)
        self.color = tuple(color)

    def serialize_properties(self) -> dict[str, Any]:
        data = super().serialize_properties()
        data.update({"text": self.text, "font_size": int(self.font_size), "color": list(self.color)})
        return data

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        super().deserialize_properties(data)
        self.text = str(data.get("text", self.text))
        self.font_size = int(data.get("font_size", self.font_size))
        self.color = tuple(data.get("color", self.color))


class ImageComponent(RuntimeUIElement):
    component_type = "Image"
    _surface_cache: OrderedDict[str, tuple[tuple[int, int], pygame.Surface]] = OrderedDict()
    _transformed_cache: OrderedDict[tuple[str, int, int, int, float], pygame.Surface] = OrderedDict()
    _max_surface_cache = 128
    _max_transformed_cache = 256

    def __init__(
        self,
        sprite_path: str = "",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 64.0,
        height: float = 64.0,
        color: tuple[int, int, int] = (255, 255, 255),
        alpha: int = 255,
        visible: bool = True,
        z_order: int = 0,
        sorting_layer: str = "Default",
        order_in_layer: int = 0,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height, visible=visible, z_order=z_order)
        self._sprite_path = str(sprite_path)
        self.color = tuple(color)
        self.alpha = int(alpha)
        self.sorting_layer = str(sorting_layer)
        self.order_in_layer = int(order_in_layer)

    @property
    def sprite_path(self) -> str:
        return self._sprite_path

    @sprite_path.setter
    def sprite_path(self, value: str) -> None:
        previous = getattr(self, "_sprite_path", "")
        self._sprite_path = str(value)
        if previous and previous != self._sprite_path:
            type(self).invalidate_path(previous)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.visible or self._owner_is_pure_ui():
            return
        if self.game_object is None:
            return
        transform = self.game_object.transform
        zoom = 1.0
        world_pos = transform.get_world_position()
        try:
            from engine.graphics.active_camera import get_active_camera
            main_cam = get_active_camera()
            if main_cam:
                x, y = main_cam.world_to_screen(world_pos, screen.get_width(), screen.get_height())
                zoom = float(getattr(main_cam, "zoom", 1.0))
            else:
                x, y = float(world_pos[0]), float(world_pos[1])
        except Exception:
            x, y = float(world_pos[0]), float(world_pos[1])
        width = max(1, int(abs(float(transform.scale[0]) * zoom)))
        height = max(1, int(abs(float(transform.scale[1]) * zoom)))
        if not self._is_screen_rect_visible(float(x), float(y), width, height, screen):
            return
        rz = float(getattr(transform, "rz", 0.0))
        surface = self.transformed_surface(self.sprite_path, width, height, 255, rz)
        if surface is None:
            return
        from engine.graphics.tint import apply_pygame_tint
        surface = apply_pygame_tint(surface, self.color, self.alpha)
        rect = surface.get_rect(center=(int(x), int(y)))
        screen.blit(surface, rect.topleft)

    @staticmethod
    def _resolved_key(sprite_path: str) -> str:
        if not sprite_path:
            return ""
        path = Path(str(sprite_path))
        if not path.is_absolute():
            path = Path.cwd() / path
        return str(path.resolve())

    @staticmethod
    def _file_signature(path: Path) -> tuple[int, int]:
        stat = path.stat()
        return int(stat.st_mtime_ns), int(stat.st_size)

    @staticmethod
    def _trim_cache(cache: OrderedDict, limit: int) -> None:
        while len(cache) > limit:
            cache.popitem(last=False)

    @staticmethod
    def _is_screen_rect_visible(
        x: float,
        y: float,
        width: int,
        height: int,
        screen: pygame.Surface,
    ) -> bool:
        radius = max(float(width), float(height), 32.0) * 0.75
        return not (
            x + radius < 0
            or x - radius > screen.get_width()
            or y + radius < 0
            or y - radius > screen.get_height()
        )

    @classmethod
    def invalidate_path(cls, sprite_path: str) -> None:
        key = cls._resolved_key(sprite_path)
        cls._surface_cache.pop(key, None)
        for transformed_key in tuple(cls._transformed_cache):
            if transformed_key[0] == key:
                cls._transformed_cache.pop(transformed_key, None)

    @classmethod
    def clear_caches(cls) -> None:
        cls._surface_cache.clear()
        cls._transformed_cache.clear()

    @classmethod
    def load_surface(cls, sprite_path: str) -> pygame.Surface | None:
        if not sprite_path:
            return None
        key = cls._resolved_key(sprite_path)
        resolved = Path(key)
        if not resolved.exists():
            cls.invalidate_path(sprite_path)
            return None
        signature = cls._file_signature(resolved)
        cached = cls._surface_cache.get(key)
        if cached is not None and cached[0] == signature:
            cls._surface_cache.move_to_end(key)
            return cached[1]
        if cached is not None:
            cls.invalidate_path(sprite_path)
        try:
            loaded = pygame.image.load(str(resolved))
            surface = loaded.convert_alpha() if pygame.display.get_surface() is not None else loaded.copy()
        except Exception:
            return None
        cls._surface_cache[key] = (signature, surface)
        cls._trim_cache(cls._surface_cache, cls._max_surface_cache)
        return surface

    @classmethod
    def transformed_surface(
        cls,
        sprite_path: str,
        width: int,
        height: int,
        alpha: int,
        rz: float,
    ) -> pygame.Surface | None:
        base = cls.load_surface(sprite_path)
        if base is None:
            return None
        width = max(1, int(width))
        height = max(1, int(height))
        alpha = max(0, min(255, int(alpha)))
        rotation = round(float(rz), 1)
        key = (cls._resolved_key(sprite_path), width, height, alpha, rotation)
        cached = cls._transformed_cache.get(key)
        if cached is not None:
            cls._transformed_cache.move_to_end(key)
            return cached
        surface = base
        if surface.get_size() != (width, height):
            surface = pygame.transform.smoothscale(surface, (width, height))
        if alpha < 255:
            surface = surface.copy()
            surface.set_alpha(alpha)
        if rotation != 0.0:
            surface = pygame.transform.rotate(surface, -rotation)
        cls._transformed_cache[key] = surface
        cls._trim_cache(cls._transformed_cache, cls._max_transformed_cache)
        return surface

    def serialize_properties(self) -> dict[str, Any]:
        data = super().serialize_properties()
        data.update({
            "sprite_path": self.sprite_path,
            "color": list(self.color),
            "alpha": int(self.alpha),
            "sorting_layer": self.sorting_layer,
            "order_in_layer": int(self.order_in_layer),
        })
        return data

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        super().deserialize_properties(data)
        self.sprite_path = str(data.get("sprite_path", self.sprite_path))
        self.color = tuple(data.get("color", self.color))
        self.alpha = int(data.get("alpha", self.alpha))
        self.sorting_layer = str(data.get("sorting_layer", self.sorting_layer))
        self.order_in_layer = int(data.get("order_in_layer", self.order_in_layer))


class InfiniteBackground(Component):
    """Fundo infinito/tileable para jogos 2D, ideal para céu espacial em movimento."""

    component_type = "InfiniteBackground"
    unique = True
    _tile_cache: OrderedDict[tuple[str, int, int, int, int], pygame.Surface] = OrderedDict()
    _max_tile_cache = 64

    def __init__(
        self,
        sprite_path: str = "",
        speed_x: float = 40.0,
        speed_y: float = 0.0,
        direction: str = "horizontal",
        parallax: float = 0.0,
        tile_scale: float = 1.0,
        alpha: int = 255,
        visible: bool = True,
        scale_to_screen: bool = True,
    ) -> None:
        super().__init__()
        self._sprite_path = str(sprite_path)
        self.speed_x = float(speed_x)
        self.speed_y = float(speed_y)
        self.direction = str(direction or "horizontal").lower()
        self.parallax = float(parallax)
        self.tile_scale = max(0.01, float(tile_scale))
        self.alpha = int(alpha)
        self.visible = bool(visible)
        self.scale_to_screen = bool(scale_to_screen)
        self._offset_x = 0.0
        self._offset_y = 0.0

    @property
    def sprite_path(self) -> str:
        return self._sprite_path

    @sprite_path.setter
    def sprite_path(self, value: str) -> None:
        previous = getattr(self, "_sprite_path", "")
        self._sprite_path = str(value)
        if previous and previous != self._sprite_path:
            self.invalidate_path(previous)

    @classmethod
    def invalidate_path(cls, sprite_path: str) -> None:
        key = ImageComponent._resolved_key(sprite_path)
        for tile_key in tuple(cls._tile_cache):
            if tile_key[0] == key:
                cls._tile_cache.pop(tile_key, None)
        ImageComponent.invalidate_path(sprite_path)

    @classmethod
    def clear_cache(cls) -> None:
        cls._tile_cache.clear()

    def _background_tile(
        self,
        source: pygame.Surface,
        width: int,
        height: int,
    ) -> pygame.Surface:
        alpha = max(0, min(255, int(self.alpha)))
        key = (
            ImageComponent._resolved_key(self.sprite_path),
            int(width),
            int(height),
            alpha,
            id(source),
        )
        cached = self._tile_cache.get(key)
        if cached is not None:
            self._tile_cache.move_to_end(key)
            return cached
        surface = source
        if surface.get_size() != (width, height):
            surface = pygame.transform.smoothscale(surface, (width, height))
        if alpha < 255:
            surface = surface.copy()
            surface.set_alpha(alpha)
        self._tile_cache[key] = surface
        ImageComponent._trim_cache(self._tile_cache, self._max_tile_cache)
        return surface

    def update(self, dt: float) -> None:
        if not self.enabled or not self.visible:
            return
        self._offset_x = (self._offset_x + float(self.speed_x) * float(dt)) % 100000.0
        self._offset_y = (self._offset_y + float(self.speed_y) * float(dt)) % 100000.0

    def on_runtime_update(self, delta_time: float) -> None:
        self.update(delta_time)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.enabled or not self.visible:
            return
        surface = ImageComponent.load_surface(self.sprite_path)
        if surface is None:
            return
        sw, sh = max(1, int(screen.get_width())), max(1, int(screen.get_height()))
        if self.scale_to_screen:
            tw, th = sw, sh
        else:
            tw = max(1, int(surface.get_width() * self.tile_scale))
            th = max(1, int(surface.get_height() * self.tile_scale))
        surface = self._background_tile(surface, tw, th)

        cam_x = cam_y = 0.0
        if self.parallax:
            try:
                from engine.graphics.active_camera import get_active_camera
                cam = get_active_camera()
                if cam is not None and getattr(cam, "transform", None) is not None:
                    cam_x = float(cam.transform.position[0]) * self.parallax
                    cam_y = float(cam.transform.position[1]) * self.parallax
            except Exception:
                pass

        direction = self.direction.lower()
        loop_x = direction in ("horizontal", "both", "xy", "x")
        loop_y = direction in ("vertical", "both", "xy", "y")
        ox = (self._offset_x + cam_x) % tw if loop_x else 0.0
        oy = (self._offset_y + cam_y) % th if loop_y else 0.0
        start_x = -int(ox) if loop_x else 0
        start_y = -int(oy) if loop_y else 0
        end_x = sw + (tw if loop_x else 0)
        end_y = sh + (th if loop_y else 0)
        x_values = range(start_x, end_x + 1, tw) if loop_x else range(0, 1)
        y_values = range(start_y, end_y + 1, th) if loop_y else range(0, 1)
        for x in x_values:
            for y in y_values:
                screen.blit(surface, (x, y))

    def serialize_properties(self) -> dict[str, Any]:
        return {
            "sprite_path": self.sprite_path,
            "speed_x": float(self.speed_x),
            "speed_y": float(self.speed_y),
            "direction": self.direction,
            "parallax": float(self.parallax),
            "tile_scale": float(self.tile_scale),
            "alpha": int(self.alpha),
            "visible": bool(self.visible),
            "scale_to_screen": bool(self.scale_to_screen),
        }

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        self.sprite_path = str(data.get("sprite_path", self.sprite_path))
        self.speed_x = float(data.get("speed_x", self.speed_x))
        self.speed_y = float(data.get("speed_y", self.speed_y))
        self.direction = str(data.get("direction", self.direction)).lower()
        self.parallax = float(data.get("parallax", self.parallax))
        self.tile_scale = max(0.01, float(data.get("tile_scale", self.tile_scale)))
        self.alpha = int(data.get("alpha", self.alpha))
        self.visible = bool(data.get("visible", self.visible))
        self.scale_to_screen = bool(data.get("scale_to_screen", self.scale_to_screen))


class ButtonComponent(RuntimeUIElement):
    component_type = "Button"

    def __init__(
        self,
        text: str = "Button",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 140.0,
        height: float = 38.0,
        visible: bool = True,
        z_order: int = 0,
        interactable: bool = True,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height, visible=visible, z_order=z_order)
        self.text = str(text)
        self.interactable = bool(interactable)

    def serialize_properties(self) -> dict[str, Any]:
        data = super().serialize_properties()
        data.update({"text": self.text, "interactable": bool(self.interactable)})
        return data

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        super().deserialize_properties(data)
        self.text = str(data.get("text", self.text))
        self.interactable = bool(data.get("interactable", self.interactable))


class ProgressBarComponent(RuntimeUIElement):
    """
    Componente de barra de progresso em Runtime Screen Space (HP/MP/XP bars).

    BUG FIX: cenas de projeto reais (ex.: Assets/Scenes/NebulaDefensePro.zscene)
    já salvam componentes do tipo "ProgressBar", mas nenhuma classe com esse
    nome existia em engine.ui.runtime_components nem estava registrada em
    component_registry — o carregador caía no fallback genérico (Component
    vazio) e a barra perdia todo o comportamento/propriedades silenciosamente.
    """

    component_type = "ProgressBar"

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 180.0,
        height: float = 18.0,
        value: float = 100.0,
        max_value: float = 100.0,
        fill_color: tuple[int, int, int] = (46, 204, 113),
        bg_color: tuple[int, int, int] = (28, 35, 48),
        visible: bool = True,
        z_order: int = 0,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height, visible=visible, z_order=z_order)
        self.value = float(value)
        self.max_value = max(0.0001, float(max_value))
        self.fill_color = tuple(fill_color)
        self.bg_color = tuple(bg_color)

    def set_value(self, value: float) -> None:
        self.value = max(0.0, min(self.max_value, float(value)))

    def serialize_properties(self) -> dict[str, Any]:
        data = super().serialize_properties()
        data.update({
            "value": float(self.value),
            "max_value": float(self.max_value),
            "fill_color": list(self.fill_color),
            "bg_color": list(self.bg_color),
        })
        return data

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        super().deserialize_properties(data)
        self.value = float(data.get("value", self.value))
        self.max_value = max(0.0001, float(data.get("max_value", self.max_value)))
        self.fill_color = tuple(data.get("fill_color", self.fill_color))
        self.bg_color = tuple(data.get("bg_color", self.bg_color))


UIElement = RuntimeUIElement
