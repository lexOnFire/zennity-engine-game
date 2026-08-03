"""Runtime Visualization Renderer — Desempenha a camada de depuração visual interna da Viewport.

Renderiza em tempo real:
  - Física & Colisão: Colliders, Setas de Velocidade (azul), Setas de Força (amarelo/vermelho), Raycasts e Ponto de Contato.
  - IA & Navegação: Cone de Campo de Visão (FOV), Rotas de Pathfinding, Waypoints e Ponto de Destino.
  - Áudio & Partículas: Indicadores de Ondas Sonoras e Partículas Ativas.
  - Destaque por Nó Selecionado: `Move`, `Jump`, `PlayAnimation`.
"""
from __future__ import annotations

import math
import time
from typing import Any, Optional
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygonF


class RuntimeVisualizationRenderer:
    """Renderiza a camada de Runtime Visualization (Visual Debugger) sobre a Viewport."""

    def __init__(self) -> None:
        self.show_colliders: bool = True
        self.show_velocity: bool = True
        self.show_forces: bool = True
        self.show_ai_fov: bool = True
        self.show_pathfinding: bool = True
        self.show_audio_waves: bool = True

    def draw_visualization_layer(
        self,
        painter: QPainter,
        rect: QRectF,
        target_object: Any,
        selected_node_name: str,
        highlight_timer: float,
    ) -> None:
        """Renderiza todas as forças e gizmos de depuração de runtime."""
        cx, cy = rect.width() / 2.0, rect.height() / 2.0 + 10.0
        node_lower = selected_node_name.lower()
        is_active = time.time() < highlight_timer

        # 1. Renderiza Colliders (Física)
        if self.show_colliders:
            painter.setPen(QPen(QColor("#50c878"), 1.8, Qt.DashLine))
            painter.setBrush(QBrush(QColor(80, 200, 120, 25)))
            painter.drawRect(QRectF(cx - 28.0, cy - 28.0, 56.0, 56.0))

        # 2. Renderiza Cone de Visão da IA (FOV)
        if self.show_ai_fov:
            fov_angle = 60.0
            fov_distance = 90.0
            poly = QPolygonF()
            poly.append(QPointF(cx, cy))
            poly.append(QPointF(cx + fov_distance, cy - 40.0))
            poly.append(QPointF(cx + fov_distance, cy + 40.0))

            painter.setPen(QPen(QColor(230, 184, 92, 120), 1.2, Qt.DashLine))
            painter.setBrush(QBrush(QColor(230, 184, 92, 35)))
            painter.drawPolygon(poly)

        # 3. Renderiza Pathfinding Waypoints & Destino
        if self.show_pathfinding:
            dest_x, dest_y = cx + 110.0, cy - 30.0
            painter.setPen(QPen(QColor("#4c9aff"), 1.5, Qt.DotLine))
            painter.drawLine(int(cx), int(cy), int(dest_x), int(dest_y))

            # Marcador de Destino da IA
            painter.setPen(QPen(QColor("#4c9aff"), 2.0))
            painter.setBrush(QBrush(QColor("#1f6feb")))
            painter.drawEllipse(QPointF(dest_x, dest_y), 6.0, 6.0)

        # 4. Renderiza Setas de Velocidade e Força (Destaque Contextual por Nó Selecionado)
        if is_active or "move" in node_lower:
            # Seta de Direção de Movimento (Velocidade)
            vx, vy = 65.0, 0.0
            painter.setPen(QPen(QColor("#58a6ff"), 3.0))
            painter.drawLine(int(cx), int(cy), int(cx + vx), int(cy + vy))
            # Cabeça da Seta
            painter.setBrush(QBrush(QColor("#58a6ff")))
            painter.drawEllipse(QPointF(cx + vx, cy + vy), 4.0, 4.0)

            painter.setFont(QFont("Consolas", 8, QFont.Bold))
            painter.setPen(QPen(QColor("#58a6ff")))
            painter.drawText(QPointF(cx + 10.0, cy - 10.0), "Vect: (4.5, 0.0)")

        if is_active and "jump" in node_lower:
            # Seta Vertical de Força do Salto
            fy = -75.0
            painter.setPen(QPen(QColor("#ff4d8d"), 3.4))
            painter.drawLine(int(cx), int(cy), int(cx), int(cy + fy))
            # Cabeça da Seta Superior
            painter.setBrush(QBrush(QColor("#ff4d8d")))
            painter.drawEllipse(QPointF(cx, cy + fy), 5.0, 5.0)

            # Destaca Ground Collider Check
            painter.setPen(QPen(QColor("#ff4d8d"), 2.2, Qt.SolidLine))
            painter.drawLine(int(cx - 30.0), int(cy + 30.0), int(cx + 30.0), int(cy + 30.0))

            painter.setFont(QFont("Consolas", 8, QFont.Bold))
            painter.setPen(QPen(QColor("#ff4d8d")))
            painter.drawText(QPointF(cx + 8.0, cy - 40.0), "JumpForce: 12.0 N")

        if is_active and "play_sound" in node_lower:
            # Ondas de Áudio Pulsantes
            painter.setPen(QPen(QColor("#ae7df0"), 1.8, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), 45.0, 45.0)
            painter.drawEllipse(QPointF(cx, cy), 70.0, 70.0)
