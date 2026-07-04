"""
editor/gizmos/rotate_gizmo.py
─────────────────────────────────────────────────────────────────────────────
Overlay Qt para a Rotate Tool da Fase 1.

Responsabilidades:
  * Desenhar o anel de rotação (círculo tracejado) ao redor do objeto selecionado.
  * Desenhar a linha-indicador mostrando o ângulo rz atual do objeto.
  * Expor hit_test() para que a viewport saiba se o cursor está sobre o anel.

Este módulo NÃO processa eventos de entrada — apenas renderização.
"""
from __future__ import annotations

import math
from typing import Any, Callable

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen


class QtRotateGizmoOverlay:
    """Gizmo Qt para a ferramenta Rotate (anel de rotação + indicador de ângulo).

    Desenhado diretamente sobre o widget Qt via QPainter, sem tocar em
    pygame, scene.draw ou qualquer estado da cena.

    Atributos configuráveis:
        radius (int): raio do anel em pixels de tela (padrão 60).
        tolerance (int): margem de hit-test em pixels (padrão 12).
        color (QColor): cor base do gizmo.
    """

    def __init__(
        self,
        radius: int = 60,
        tolerance: int = 12,
        color: QColor | None = None,
    ) -> None:
        self.radius = radius
        self.tolerance = tolerance
        self.color: QColor = color or QColor(255, 195, 40)  # âmbar

    # ── Renderização ──────────────────────────────────────────────────────────

    def draw(
        self,
        painter: QPainter,
        selected: Any,
        world_to_viewport: Callable[[Any], tuple[float, float]],
        *,
        current_mouse: tuple[float, float] | None = None,
    ) -> None:
        """Desenha o anel de rotação para *selected*.

        Args:
            painter: Painter Qt ativo sobre o widget.
            selected: Objeto com atributo ``transform`` (position, rz).
            world_to_viewport: Função de conversão de coordenadas mundo→tela.
            current_mouse: Posição atual do mouse em coordenadas de tela.
                           Quando não-None e durante drag, desenha a linha
                           de arco até a posição do cursor.
        """
        if selected is None or not hasattr(selected, "transform"):
            return
        pos = getattr(selected.transform, "position", None)
        if pos is None:
            return

        cx, cy = world_to_viewport(pos)
        rz = float(getattr(selected.transform, "rz", 0.0))

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # ── Anel tracejado ────────────────────────────────────────────────────
        ring_pen = QPen(self.color, 2, Qt.DashLine)
        painter.setPen(ring_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), self.radius, self.radius)

        # ── Linha-indicador do ângulo rz atual ────────────────────────────────
        # Coordenadas de tela: eixo y aponta para baixo, portanto sin positivo
        # corresponde ao sentido horário na tela.
        rad = math.radians(rz)
        tip_x = cx + self.radius * math.cos(rad)
        tip_y = cy + self.radius * math.sin(rad)

        indicator_pen = QPen(self.color, 2, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(indicator_pen)
        painter.drawLine(QPointF(cx, cy), QPointF(tip_x, tip_y))

        # ── Linha fantasma até o mouse (durante drag) ─────────────────────────
        if current_mouse is not None:
            mx, my = current_mouse
            ghost_pen = QPen(QColor(255, 255, 255, 100), 1, Qt.DotLine)
            painter.setPen(ghost_pen)
            painter.drawLine(QPointF(cx, cy), QPointF(mx, my))

        # ── Ponto central ─────────────────────────────────────────────────────
        painter.setPen(QPen(self.color.darker(130), 1))
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(QPointF(cx, cy), 5, 5)

        painter.restore()

    # ── Detecção de hit ───────────────────────────────────────────────────────

    def hit_test(
        self,
        x: float,
        y: float,
        selected: Any,
        world_to_viewport: Callable[[Any], tuple[float, float]],
    ) -> bool:
        """Retorna True se (x, y) está sobre o anel de rotação.

        O hit-test aceita pontos dentro da margem ``tolerance`` pixels
        ao redor do raio do anel.  Também aceita o centro (raio ≤ tolerance)
        para facilitar o início do drag quando o cursor está sobre o pivot.
        """
        if selected is None or not hasattr(selected, "transform"):
            return False
        pos = getattr(selected.transform, "position", None)
        if pos is None:
            return False
        cx, cy = world_to_viewport(pos)
        dist = math.hypot(x - cx, y - cy)
        # Aceita: perto do centro OU perto do anel
        return dist <= self.tolerance or abs(dist - self.radius) <= self.tolerance
