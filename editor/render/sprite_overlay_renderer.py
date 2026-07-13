"""Renderizador Qt opt-in para sprites 2D da Scene View."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap

from engine.graphics.sorting import normalize_sorting_layer, sorting_key
from engine.graphics.tint import combined_alpha, normalize_tint


@dataclass(frozen=True, slots=True)
class SpriteDrawCommand:
    """Descrição normalizada de um sprite, sem impor novas regras visuais."""

    obj: Any
    component: Any
    pixmap: QPixmap
    mode: str
    source_order: int
    sorting_layer: str
    order_in_layer: int
    tint: tuple[int, int, int, int]
    alpha: int
    flip_x: bool
    flip_y: bool


class SpriteOverlayRenderer:
    """Desenha apenas componentes Image que o Qt consegue representar."""

    def __init__(self) -> None:
        self._pixmaps: dict[str, QPixmap] = {}

    def _pixmap(self, sprite_path: str) -> QPixmap | None:
        path = Path(str(sprite_path or ""))
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.is_file():
            return None
        key = str(path.resolve())
        pixmap = self._pixmaps.get(key)
        if pixmap is None:
            pixmap = QPixmap(key)
            if pixmap.isNull():
                return None
            self._pixmaps[key] = pixmap
        return pixmap

    @staticmethod
    def _surface_pixmap(surface: Any) -> QPixmap | None:
        if surface is None:
            return None
        try:
            import pygame
            width, height = surface.get_size()
            rgba = pygame.image.tobytes(surface, "RGBA")
            image = QImage(rgba, width, height, width * 4, QImage.Format_RGBA8888).copy()
            pixmap = QPixmap.fromImage(image)
            return None if pixmap.isNull() else pixmap
        except Exception:
            return None

    def _component_pixmap(self, component: Any) -> tuple[QPixmap | None, str]:
        type_name = getattr(component, "type_name", type(component).__name__)
        if type_name == "Image":
            return self._pixmap(getattr(component, "sprite_path", "")), "image"
        if type_name != "SpriteRenderer":
            return None, ""
        module = type(component).__module__
        surface = getattr(component, "surface", getattr(component, "image", None))
        mode = "renderer2d" if module.endswith("renderer2d") else "surface"
        return self._surface_pixmap(surface), mode

    @staticmethod
    def _normalized_tint(component: Any) -> tuple[int, int, int, int]:
        return normalize_tint(getattr(component, "color", (255, 255, 255, 255)))

    @staticmethod
    def _tinted_pixmap(pixmap: QPixmap, tint: tuple[int, int, int, int]) -> QPixmap:
        if tint[:3] == (255, 255, 255):
            return pixmap
        result = pixmap.copy()
        tint_painter = QPainter(result)
        tint_painter.setCompositionMode(QPainter.CompositionMode_Multiply)
        tint_painter.fillRect(result.rect(), QColor(*tint[:3]))
        tint_painter.end()
        return result

    def collect(self, scene: Any) -> list[SpriteDrawCommand]:
        """Retorna somente sprites válidos que podem sair do caminho legado."""
        objects = getattr(scene, "editable_objects", getattr(scene, "game_objects", ()))
        sprites: list[SpriteDrawCommand] = []
        source_order = 0
        for obj in objects:
            if not getattr(obj, "active", True):
                continue
            for component in getattr(obj, "components", ()):
                if not getattr(component, "enabled", True) or not getattr(component, "visible", True):
                    continue
                if getattr(component, "game_object", obj) is None:
                    continue
                pixmap, mode = self._component_pixmap(component)
                if pixmap is not None:
                    sprites.append(SpriteDrawCommand(
                        obj=obj,
                        component=component,
                        pixmap=pixmap,
                        mode=mode,
                        source_order=source_order,
                        sorting_layer=normalize_sorting_layer(
                            getattr(component, "sorting_layer", "Default")
                        ),
                        order_in_layer=int(getattr(component, "order_in_layer", getattr(component, "layer", 0))),
                        tint=self._normalized_tint(component),
                        alpha=max(0, min(255, int(getattr(component, "alpha", 255)))),
                        flip_x=bool(getattr(component, "flip_x", False)),
                        flip_y=bool(getattr(component, "flip_y", False)),
                    ))
                    source_order += 1
        return sprites

    def draw(
        self,
        painter: QPainter,
        camera: Any,
        sprites: list[SpriteDrawCommand],
    ) -> None:
        """Desenha os sprites coletados usando o mesmo transform da viewport."""
        ordered_sprites = sorted(
            sprites,
            key=lambda command: sorting_key(
                command.sorting_layer,
                command.order_in_layer,
                command.source_order,
            ),
        )
        for command in ordered_sprites:
            obj = command.obj
            pixmap = self._tinted_pixmap(command.pixmap, command.tint)
            mode = command.mode
            transform = getattr(obj, "transform", None)
            if transform is None:
                continue
            position = transform.get_world_position()
            cx, cy = camera.world_to_viewport(position)
            if mode == "surface":
                width = max(1.0, float(pixmap.width()) * float(camera.zoom))
                height = max(1.0, float(pixmap.height()) * float(camera.zoom))
                rotation = 0.0
            elif mode == "renderer2d":
                width = max(1.0, float(pixmap.width()) * abs(float(transform.scale[0]) * float(camera.zoom)))
                height = max(1.0, float(pixmap.height()) * abs(float(transform.scale[1]) * float(camera.zoom)))
                rotation = float(getattr(transform, "rz", 0.0))
            else:
                width = max(1.0, abs(float(transform.scale[0]) * float(camera.zoom)))
                height = max(1.0, abs(float(transform.scale[1]) * float(camera.zoom)))
                rotation = float(getattr(transform, "rz", 0.0))

            painter.save()
            
            painter.setOpacity(float(combined_alpha(command.alpha, command.tint)) / 255.0)
            painter.translate(cx, cy)
            painter.rotate(rotation)
            if mode == "surface":
                painter.scale(
                    -1.0 if command.flip_x else 1.0,
                    -1.0 if command.flip_y else 1.0,
                )
            target = QRectF(-width / 2.0, -height / 2.0, width, height)
            source = QRectF(pixmap.rect())
            painter.drawPixmap(target, pixmap, source)
            painter.restore()
