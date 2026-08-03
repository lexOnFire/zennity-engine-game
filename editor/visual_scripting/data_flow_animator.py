"""Data Flow Visualization — Sprint 10 (Visual Scripting 2.0).

Visualização gráfica animada do trajeto de mutação de dados e variáveis:
  Exemplo: speed -> Move() -> Velocity -> RigidBody -> Objeto
"""
from __future__ import annotations

import time
from typing import Any, Optional
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush


class DataFlowVisualizationAnimator:
    """Anima o trajeto do fluxo de mutação de variáveis e dados no grafo e na viewport."""

    def __init__(self) -> None:
        self.active_flows: list[dict[str, Any]] = []

    def trigger_variable_flow(self, var_name: str, target_node: str, new_value: Any) -> None:
        """Inicia uma animação visual do fluxo da variável mutada."""
        flow = {
            "var_name": str(var_name),
            "target_node": str(target_node),
            "value": str(new_value),
            "start_time": time.time(),
            "duration": 1.2,  # 1.2 segundos de duração da animação
        }
        self.active_flows.append(flow)

    def draw_data_flows(self, painter: QPainter, rect: QRectF) -> None:
        """Renderiza as partículas de dados e rótulos de mutação de variáveis."""
        now = time.time()
        self.active_flows = [f for f in self.active_flows if now - f["start_time"] < f["duration"]]

        for idx, flow in enumerate(self.active_flows):
            progress = (now - flow["start_time"]) / flow["duration"]
            x = rect.width() * 0.2 + progress * (rect.width() * 0.6)
            y = rect.height() * 0.3 + (idx * 22.0)

            # Partícula de fluxo de dado (Cor Dourada / Amarela)
            painter.setPen(QPen(QColor("#ffe600"), 2.0))
            painter.setBrush(QBrush(QColor("#ff9933")))
            painter.drawEllipse(QPointF(x, y), 7.0, 7.0)

            # Rótulo de mutação: speed = 3.5 -> Move()
            painter.setFont(QFont("Consolas", 8, QFont.Bold))
            painter.setPen(QPen(QColor("#ffffff")))
            painter.drawText(QPointF(x + 12.0, y + 4.0), f"{flow['var_name']} = {flow['value']} ➔ {flow['target_node']}")
