"""Renderizador Qt opt-in para sprites 2D da Scene View."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPixmap


class SpriteOverlayRenderer:
    """Desenha apenas componentes Image que o Qt consegue representar."""

    def __init__(self) -> None:
        self._pixmaps: dict[str, QPixmap] = {}

    @staticmethod
    def _image_component(obj: Any) -> Any | None:
        for component in getattr(obj, "components", ()):
            type_name = getattr(component, "type_name", type(component).__name__)
            if type_name == "Image" and bool(getattr(component, "visible", True)):
                return component
        return None

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

    def collect(self, scene: Any) -> list[tuple[Any, Any, QPixmap]]:
        """Retorna somente sprites válidos que podem sair do caminho legado."""
        objects = getattr(scene, "editable_objects", getattr(scene, "game_objects", ()))
        sprites: list[tuple[Any, Any, QPixmap]] = []
        for obj in objects:
            if not getattr(obj, "active", True):
                continue
            image = self._image_component(obj)
            if image is None or getattr(image, "game_object", obj) is None:
                continue
            pixmap = self._pixmap(getattr(image, "sprite_path", ""))
            if pixmap is not None:
                sprites.append((obj, image, pixmap))
        return sprites

    def draw(self, painter: QPainter, camera: Any, sprites: list[tuple[Any, Any, QPixmap]]) -> None:
        """Desenha os sprites coletados usando o mesmo transform da viewport."""
        for obj, image, pixmap in sprites:
            transform = getattr(obj, "transform", None)
            if transform is None:
                continue
            position = transform.get_world_position()
            cx, cy = camera.world_to_viewport(position)
            width = max(1.0, abs(float(transform.scale[0]) * float(camera.zoom)))
            height = max(1.0, abs(float(transform.scale[1]) * float(camera.zoom)))

            painter.save()
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setOpacity(max(0.0, min(1.0, float(getattr(image, "alpha", 255)) / 255.0)))
            painter.translate(cx, cy)
            painter.rotate(float(getattr(transform, "rz", 0.0)))
            target = QRectF(-width / 2.0, -height / 2.0, width, height)
            source = QRectF(pixmap.rect())
            painter.drawPixmap(target, pixmap, source)
            painter.restore()

