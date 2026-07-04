"""
editor/viewport/bounding_box.py
─────────────────────────────────────────────────────────────────────────────
Caixa delimitadora (Bounding Box) e 8 alças de controle/escala rotacionadas,
incluindo APIs públicas para o cálculo de limites e detecção de cliques.
"""
from __future__ import annotations

from typing import Any, Callable
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen


def get_object_bounds(obj: Any) -> tuple[float, float, float, float]:
    """Calcula os limites (min_x, min_y, max_x, max_y) do objeto no espaço de mundo.

    Suporta objetos retangulares convencionais e circulares (via CircleCollider ou mesh_type).
    """
    if obj is None or not hasattr(obj, "transform"):
        return (0.0, 0.0, 0.0, 0.0)

    pos = obj.transform.position
    scale = obj.transform.scale

    # Detecta se é círculo via CircleCollider ou mesh_type
    is_circle = False
    radius = 0.0
    if getattr(obj, "mesh_type", "") == "Círculo":
        is_circle = True
        radius = float(scale[0] / 2.0)
    elif hasattr(obj, "get_component"):
        from engine.physics.collider import CircleCollider
        cc = obj.get_component(CircleCollider)
        if cc is not None:
            is_circle = True
            radius = float(getattr(cc, "radius", 0.0))

    if is_circle:
        return (
            float(pos[0] - radius),
            float(pos[1] - radius),
            float(pos[0] + radius),
            float(pos[1] + radius),
        )

    # Retângulo padrão
    return (
        float(pos[0] - scale[0] / 2.0),
        float(pos[1] - scale[1] / 2.0),
        float(pos[0] + scale[0] / 2.0),
        float(pos[1] + scale[1] / 2.0),
    )


def get_handle_positions(bounds: tuple[float, float, float, float]) -> list[tuple[float, float]]:
    """Calcula as coordenadas dos 8 handles a partir de limites (sem rotação).

    A ordem dos handles segue: TL, TC, TR, RC, BR, BC, BL, LC.
    """
    min_x, min_y, max_x, max_y = bounds
    mid_x = (min_x + max_x) / 2.0
    mid_y = (min_y + max_y) / 2.0

    return [
        (min_x, min_y),  # Top-Left (TL)
        (mid_x, min_y),  # Top-Center (TC)
        (max_x, min_y),  # Top-Right (TR)
        (max_x, mid_y),  # Right-Center (RC)
        (max_x, max_y),  # Bottom-Right (BR)
        (mid_x, max_y),  # Bottom-Center (BC)
        (min_x, max_y),  # Bottom-Left (BL)
        (min_x, mid_y),  # Left-Center (LC)
    ]


def hit_test_handle(
    point: tuple[float, float],
    handle_positions: list[tuple[float, float]],
    tolerance: float = 6.0,
) -> int | None:
    """Verifica se um ponto (ex. mouse na tela) colide com algum dos 8 handles.

    Retorna o índice do handle (0-7) ou None se nenhuma colisão for encontrada.
    """
    px, py = point
    for idx, (hx, hy) in enumerate(handle_positions):
        if abs(px - hx) <= tolerance and abs(py - hy) <= tolerance:
            return idx
    return None


class BoundingBoxRenderer:
    """Desenha a caixa limite e, opcionalmente, os 8 handles de escala.

    A caixa pode aparecer para Select, Move e Rotate, mas os handles devem ser
    exibidos somente quando a Scale Tool estiver ativa.
    """

    def __init__(
        self,
        border_color: QColor = QColor(240, 240, 250, 180),
        handle_color: QColor = QColor(80, 160, 255),
        handle_size: float = 6.0,
    ) -> None:
        self.border_color: QColor = border_color
        self.handle_color: QColor = handle_color
        self.handle_size: float = handle_size

    def draw(
        self,
        painter: QPainter,
        selected: Any,
        world_to_viewport: Callable[[Any], tuple[float, float]],
        *,
        show_handles: bool = True,
    ) -> None:
        """Renderiza a linha limite e, quando solicitado, as 8 alças quadradas."""
        if selected is None or not hasattr(selected, "transform"):
            return
        pos = getattr(selected.transform, "position", None)
        scale = getattr(selected.transform, "scale", None)
        if pos is None or scale is None:
            return

        cx, cy = world_to_viewport(pos)

        # Determina largura e altura na tela
        p0 = world_to_viewport((pos[0] - scale[0] / 2.0, pos[1] - scale[1] / 2.0, pos[2]))
        p1 = world_to_viewport((pos[0] + scale[0] / 2.0, pos[1] + scale[1] / 2.0, pos[2]))
        sw = abs(p1[0] - p0[0])
        sh = abs(p1[1] - p0[1])

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # ── 1. Caixa Delimitadora (Tracejada) ─────────────────────────────────
        pen = QPen(self.border_color, 1, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        # Translada o painter para o centro do objeto e aplica rotação
        painter.translate(cx, cy)
        rz = float(getattr(selected.transform, "rz", 0.0))
        painter.rotate(rz)

        # Bounding box rente à escala visual
        painter.drawRect(QRectF(-sw / 2.0, -sh / 2.0, sw, sh))

        if not show_handles:
            painter.restore()
            return

        # ── 2. Plota os 8 Pontos de Controle (Alças Quadradas) ────────────────
        painter.setPen(QPen(self.handle_color.darker(120), 1))
        painter.setBrush(QBrush(self.handle_color))

        hs = self.handle_size
        # Obtém posições locais dos handles
        local_bounds = (-sw / 2.0, -sh / 2.0, sw / 2.0, sh / 2.0)
        points = get_handle_positions(local_bounds)

        for px, py in points:
            # Desenha quadrado local
            painter.drawRect(QRectF(px - hs / 2.0, py - hs / 2.0, hs, hs))

        painter.restore()
