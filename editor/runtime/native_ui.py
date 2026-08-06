"""Renderizacao screen-space dos componentes de UI no viewport isolado.

O editor isolado trabalha com snapshots (dicionarios) em outro processo. Este
adaptador conserva esse limite e representa os mesmos componentes registrados
em ``engine.ui.runtime_components`` sem criar uma segunda cena de runtime.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import pygame


UI_TYPES = {"canvas", "text", "image", "button", "progress_bar"}


def normalize_ui(data: Any) -> dict[str, Any] | None:
    """Retorna um componente de UI valido e com defaults retrocompativeis."""
    if not isinstance(data, dict):
        return None
    kind = str(data.get("type", "")).strip().lower()
    aliases = {
        "label": "text", "uilabel": "text", "uiimage": "image", "uibutton": "button",
        "progressbar": "progress_bar", "progress": "progress_bar",
    }
    kind = aliases.get(kind, kind)
    if kind not in UI_TYPES:
        return None
    defaults: dict[str, Any] = {
        "type": kind,
        "visible": True,
        "x": 16.0,
        "y": 16.0,
        "width": 180.0,
        "height": 42.0,
        "z_order": 0,
        "text": "Texto" if kind == "text" else ("Botao" if kind == "button" else ""),
        "font_size": 24,
        "color": [255, 255, 255],
        "path": "",
        "alpha": 255,
        "interactable": True,
        "event": "click",
        "target": "",
        "anchor": "",
        "margin_x": 16.0,
        "margin_y": 16.0,
        "value": 100.0,
        "max_value": 100.0,
        "fill_color": [46, 204, 113],
        "bg_color": [28, 35, 48],
    }
    defaults.update(data)
    defaults["type"] = kind
    return defaults


def scene_item_to_ui(item: Any) -> dict[str, Any] | None:
    """Converte um item serializado pelo sistema nativo para o snapshot."""
    if not isinstance(item, dict):
        return None
    type_name = str(item.get("type", "")).lower()
    kind = {
        "canvas": "canvas",
        "label": "text",
        "uilabel": "text",
        "image": "image",
        "uiimage": "image",
        "button": "button",
        "uibutton": "button",
        "progressbar": "progress_bar",
    }.get(type_name)
    if kind is None:
        return None
    properties = dict(item.get("properties") or {})
    properties["type"] = kind
    if "sprite_path" in properties and "path" not in properties:
        properties["path"] = properties.pop("sprite_path")
    properties.setdefault("visible", bool(item.get("enabled", True)))
    return normalize_ui(properties)


def ui_to_scene_item(data: Any) -> dict[str, Any] | None:
    """Converte o snapshot para o formato oficial de componentes da cena."""
    ui = normalize_ui(data)
    if ui is None:
        return None
    type_name = {
        "canvas": "Canvas", "text": "Label", "image": "Image", "button": "Button",
        "progress_bar": "ProgressBar",
    }[ui["type"]]
    properties = {key: value for key, value in ui.items() if key != "type"}
    if "path" in properties:
        properties["sprite_path"] = properties.pop("path")
    return {"type": type_name, "enabled": bool(ui.get("visible", True)), "properties": properties}


class NativeUIRenderer:
    """Desenha componentes nativos de UI e faz hit-test de botoes."""

    def __init__(self) -> None:
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}
        self._images: dict[str, pygame.Surface | None] = {}

    def clear_caches(self) -> None:
        """Libera fonts e surfaces retidas pelo renderer."""
        self._fonts.clear()
        self._images.clear()

    @staticmethod
    def _values(objects: Any) -> list[dict[str, Any]]:
        values: Iterable[Any] = objects.values() if isinstance(objects, dict) else objects
        return [obj for obj in values if isinstance(obj, dict) and bool(obj.get("active", True))]

    def _flatten_zui_widget(self, widget: dict[str, Any], z_order: int = 0) -> list[dict[str, Any]]:
        result = []
        w_type = str(widget.get("type", "")).lower()
        kind_map = {
            "uilabel": "text", "label": "text", "text": "text",
            "uiimage": "image", "image": "image",
            "uibutton": "button", "button": "button",
            "uiprogressbar": "progress_bar", "progress_bar": "progress_bar", "progress": "progress_bar",
        }
        kind = kind_map.get(w_type)
        if kind is not None and bool(widget.get("visible", True)):
            color = widget.get("text_color") or widget.get("color") or [255, 255, 255]
            ui_dict = {
                "type": kind,
                "visible": bool(widget.get("visible", True)),
                "x": float(widget.get("x", 0.0)),
                "y": float(widget.get("y", 0.0)),
                "width": float(widget.get("width", 100.0)),
                "height": float(widget.get("height", 40.0)),
                "text": str(widget.get("text", "")),
                "font_size": int(widget.get("font_size", 24)),
                "color": color,
                "path": str(widget.get("texture_path", widget.get("path", ""))),
                "alpha": int(widget.get("alpha", 255)),
                "interactable": bool(widget.get("interactable", True)),
                "z_order": z_order,
            }
            norm = normalize_ui(ui_dict)
            if norm is not None:
                result.append(norm)
        for child in widget.get("children", []):
            if isinstance(child, dict):
                result.extend(self._flatten_zui_widget(child, z_order))
        return result

    def _load_zui_layout(self, layout_path: str) -> list[dict[str, Any]]:
        import json
        path = Path(layout_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            canvas_data = data.get("canvas", data)
            if isinstance(canvas_data, dict):
                return self._flatten_zui_widget(canvas_data)
        except Exception:
            pass
        return []

    def components(self, objects: Any) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        values = self._values(objects)
        canvas_objs = [obj for obj in values if (normalize_ui(obj.get("ui")) or {}).get("type") == "canvas"]
        if not canvas_objs:
            return []
        result = []
        # Carrega elementos vindos de arquivos .zui vinculados ao Canvas
        for canvas_obj in canvas_objs:
            c_ui = normalize_ui(canvas_obj.get("ui")) or {}
            layout_path = str(c_ui.get("layout_path", "")).strip()
            if layout_path:
                for item_ui in self._load_zui_layout(layout_path):
                    result.append((canvas_obj, item_ui))

        # Adiciona demais componentes isolados da cena
        for obj in values:
            ui = normalize_ui(obj.get("ui"))
            if ui is not None and ui["type"] != "canvas" and bool(ui.get("visible", True)):
                result.append((obj, ui))
        return sorted(result, key=lambda pair: int(pair[1].get("z_order", 0)))

    def draw(self, objects: Any, screen: pygame.Surface) -> None:
        for _obj, ui in self.components(objects):
            kind = ui["type"]
            if kind == "text":
                self._draw_text(ui, screen)
            elif kind == "image":
                self._draw_image(ui, screen)
            elif kind == "button":
                self._draw_button(ui, screen)
            elif kind == "progress_bar":
                self._draw_progress_bar(ui, screen)

    def button_at(self, objects: Any, position: tuple[int, int]) -> tuple[dict[str, Any], dict[str, Any]] | None:
        for obj, ui in reversed(self.components(objects)):
            if ui["type"] != "button" or not bool(ui.get("interactable", True)):
                continue
            if self._rect(ui).collidepoint(position):
                return obj, ui
        return None

    @staticmethod
    def _rect(ui: dict[str, Any], screen: pygame.Surface | None = None) -> pygame.Rect:
        width = max(1, int(ui.get("width", 1)))
        height = max(1, int(ui.get("height", 1)))
        x, y = int(ui.get("x", 0)), int(ui.get("y", 0))
        if screen is not None:
            screen_width, screen_height = screen.get_size()
            anchor = str(ui.get("anchor", "")).strip().lower().replace("-", "_")
            margin_x, margin_y = int(ui.get("margin_x", 16)), int(ui.get("margin_y", 16))
            if anchor in {"top_right", "bottom_right"}:
                x = screen_width - width - margin_x
            elif anchor in {"top_left", "bottom_left"}:
                x = margin_x
            if anchor in {"bottom_left", "bottom_right"}:
                y = screen_height - height - margin_y
            elif anchor in {"top_left", "top_right"}:
                y = margin_y
        return pygame.Rect(x, y, width, height)

    def _font(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (max(8, min(160, int(size))), bool(bold))
        if key not in self._fonts:
            self._fonts[key] = pygame.font.SysFont("sans", key[0], bold=key[1])
        return self._fonts[key]

    def _parse_color(self, value: Any, fallback: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int, int]:
        try:
            if isinstance(value, str):
                v = value.strip().lstrip("#")
                if len(v) == 6:
                    return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))
            if isinstance(value, (list, tuple)):
                nums = [max(0, min(255, int(x))) for x in value[:3]]
                while len(nums) < 3:
                    nums.append(255)
                return (nums[0], nums[1], nums[2])
        except Exception:
            pass
        return fallback

    def _draw_text(self, ui: dict[str, Any], screen: pygame.Surface) -> None:
        color = self._parse_color(ui.get("color"), (255, 255, 255))
        surface = self._font(int(ui.get("font_size", 24))).render(str(ui.get("text", "")), True, color)
        screen.blit(surface, self._rect(ui, screen).topleft)

    def _draw_image(self, ui: dict[str, Any], screen: pygame.Surface) -> None:
        rect = self._rect(ui, screen)
        path_text = str(ui.get("path", ""))
        surface = self._load_image(path_text) if path_text else None
        if surface is None:
            surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            color = self._parse_color(ui.get("color"), (255, 255, 255))
            surface.fill((*color, max(0, min(255, int(ui.get("alpha", 255))))))
            pygame.draw.rect(surface, (255, 255, 255, 90), surface.get_rect(), 1)
        else:
            surface = pygame.transform.smoothscale(surface, rect.size)
            if int(ui.get("alpha", 255)) < 255:
                surface = surface.copy()
                surface.set_alpha(max(0, min(255, int(ui["alpha"]))))
        screen.blit(surface, rect.topleft)

    def _draw_button(self, ui: dict[str, Any], screen: pygame.Surface) -> None:
        rect = self._rect(ui, screen)
        enabled = bool(ui.get("interactable", True))
        pygame.draw.rect(screen, (56, 91, 155) if enabled else (60, 60, 65), rect, border_radius=6)
        pygame.draw.rect(screen, (115, 151, 216) if enabled else (90, 90, 95), rect, 1, border_radius=6)
        text_color = self._parse_color(ui.get("color"), (255, 255, 255))
        text = self._font(int(ui.get("font_size", 18)), True).render(
            str(ui.get("text", "Botao")), True, text_color
        )
        screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))

    def _draw_progress_bar(self, ui: dict[str, Any], screen: pygame.Surface) -> None:
        rect = self._rect(ui, screen)
        maximum = max(0.0001, float(ui.get("max_value", 100.0)))
        ratio = max(0.0, min(1.0, float(ui.get("value", maximum)) / maximum))
        bg_color = self._parse_color(ui.get("bg_color"), (28, 35, 48))
        pygame.draw.rect(screen, bg_color, rect, border_radius=4)
        fill = rect.copy()
        fill.width = max(0, round(rect.width * ratio))
        if fill.width:
            fill_color = self._parse_color(ui.get("fill_color"), (46, 204, 113))
            pygame.draw.rect(screen, fill_color, fill, border_radius=4)
        pygame.draw.rect(screen, (150, 170, 200), rect, 1, border_radius=4)

    def _load_image(self, path_text: str) -> pygame.Surface | None:
        path = Path(path_text)
        if not path.is_absolute():
            path = Path.cwd() / path
        key = str(path.resolve())
        if key not in self._images:
            try:
                self._images[key] = pygame.image.load(str(path)).convert_alpha() if path.is_file() else None
            except (OSError, pygame.error):
                self._images[key] = None
        return self._images[key]
