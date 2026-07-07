"""
editor/viewport/selection_outline.py
─────────────────────────────────────────────────────────────────────────────
Desenho da borda de seleção rotacionada para o objeto selecionado.
"""
from __future__ import annotations

from typing import Any, Callable
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen


def _has_visible_sprite(obj: Any) -> bool:
    if obj is None or not hasattr(obj, "components"):
        return False
    for component in getattr(obj, "components", []):
        if getattr(component, "type_name", type(component).__name__) == "Image":
            if str(getattr(component, "sprite_path", "") or "").strip():
                return True
    return False


class SelectionOutlineRenderer:
    """Renderiza a borda de destaque do objeto selecionado."""

    def __init__(
        self,
        color: QColor = QColor(80, 160, 255),
        thickness: int = 2,
    ) -> None:
        self.color: QColor = color
        self.thickness: int = thickness

    def draw(
        self,
        painter: QPainter,
        selected: Any,
        world_to_viewport: Callable[[Any], tuple[float, float]],
    ) -> None:
        if selected is None or not hasattr(selected, "transform"):
            return
        if _has_visible_sprite(selected):
            return
        pos = getattr(selected.transform, "position", None)
        scale = getattr(selected.transform, "scale", None)
        if pos is None or scale is None:
            return

        cx, cy = world_to_viewport(pos)
        p0 = world_to_viewport((pos[0] - scale[0] / 2.0, pos[1] - scale[1] / 2.0, pos[2]))
        p1 = world_to_viewport((pos[0] + scale[0] / 2.0, pos[1] + scale[1] / 2.0, pos[2]))
        sw = abs(p1[0] - p0[0])
        sh = abs(p1[1] - p0[1])
        rect = QRectF(-sw / 2.0 - 3.0, -sh / 2.0 - 3.0, sw + 6.0, sh + 6.0)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(self.color, self.thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.translate(cx, cy)
        rz = float(getattr(selected.transform, "rz", 0.0))
        painter.rotate(rz)

        is_circle = False
        if getattr(selected, "mesh_type", "") == "Círculo":
            is_circle = True
        elif hasattr(selected, "get_component"):
            from engine.physics.collider import CircleCollider
            if selected.get_component(CircleCollider) is not None:
                is_circle = True

        if is_circle:
            painter.drawEllipse(rect)
        else:
            painter.drawRect(rect)

        painter.restore()
