"""Mini Live Viewport Widget — Sprint 7 (Visual Scripting 2.0).

Viewport integrada ao Editor de Scripting Visual para renderizar e visualizar em tempo real
o comportamento do objeto controlado pelo grafo durante o Play Mode, com destaques visuais
de execução de nós, gizmos de física/colisão e overlay de métricas de runtime.
"""
from __future__ import annotations

import time
from typing import Any, Optional
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class MiniLiveViewportWidget(QFrame):
    """Mini Viewport de Preview em Tempo Real para o Visual Scripting 2.0."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("MiniLiveViewportWidget")
        self.setStyleSheet("""
            QFrame#MiniLiveViewportWidget {
                background-color: #121418;
                border: 1px solid #2a2e38;
                border-radius: 4px;
            }
        """)

        self.target_object: Any = None
        self.active_node_id: str | None = None
        self.active_node_name: str = ""
        self.highlight_timer: float = 0.0

        # Runtime overlay stats
        self.fps: float = 60.0
        self.is_grounded: bool = True
        self.velocity: tuple[float, float] = (0.0, 0.0)
        self.health: float = 100.0
        self.state_name: str = "IDLE"

        # Timer para atualizar a renderização em tempo real (60 FPS)
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(16)
        self._update_timer.timeout.connect(self.update)
        self._update_timer.start()

        self._build_header()

    def _build_header(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        header = QHBoxLayout()
        header.setContentsMargins(6, 2, 6, 2)

        title = QLabel("🖼️ Live Preview (Runtime Sync)")
        title.setStyleSheet("font-weight: bold; color: #a4b1cd; font-size: 11px;")
        header.addWidget(title)

        header.addStretch(1)

        self.status_badge = QLabel("● PAUSED")
        self.status_badge.setStyleSheet("color: #e6b85c; font-weight: bold; font-size: 10px;")
        header.addWidget(self.status_badge)

        layout.addLayout(header)
        layout.addStretch(1)

    def set_target_object(self, obj: Any) -> None:
        """Conecta a viewport ao objeto de jogo atualmente inspecionado."""
        self.target_object = obj
        self.update()

    def set_play_mode(self, is_playing: bool) -> None:
        """Alterna estado do indicador de runtime."""
        if is_playing:
            self.status_badge.setText("● PLAYING")
            self.status_badge.setStyleSheet("color: #50c878; font-weight: bold; font-size: 10px;")
        else:
            self.status_badge.setText("● PAUSED")
            self.status_badge.setStyleSheet("color: #e6b85c; font-weight: bold; font-size: 10px;")

    def highlight_execution_node(self, node_id: str, node_name: str) -> None:
        """Destaca o objeto na viewport quando um nó do grafo é acionado no runtime (ex: Move, Jump)."""
        self.active_node_id = str(node_id)
        self.active_node_name = str(node_name)
        self.highlight_timer = time.time() + 0.6  # Ilumina por 600ms
        self.update()

    def paintEvent(self, event) -> None:
        """Renderiza o objeto, gizmos, iluminação de ação e overlay de métricas de runtime."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.contentsRect()
        cx, cy = rect.width() / 2.0, rect.height() / 2.0 + 10.0

        # 1. Renderiza Grade da Viewport
        painter.setPen(QPen(QColor("#1e222a"), 1.0, Qt.DashLine))
        painter.drawLine(0, int(cy), rect.width(), int(cy))
        painter.drawLine(int(cx), 0, int(cx), rect.height())

        # 2. Renderiza Objeto com Highlight
        obj_name = getattr(self.target_object, "name", "MainPlayer") if self.target_object else "Player"
        is_highlighted = time.time() < self.highlight_timer

        # Cor base ou cor iluminada por nó ativo (Move -> Azul / Jump -> Amarelo / Action -> Rosa)
        if is_highlighted:
            glow_color = QColor("#ff4d8d") if "jump" in self.active_node_name.lower() else QColor("#4c9aff")
            painter.setPen(QPen(glow_color, 3.0))
            painter.setBrush(QBrush(glow_color.darker(160)))
            # Círculo de pulso
            painter.drawEllipse(QPointF(cx, cy), 34.0, 34.0)
        else:
            painter.setPen(QPen(QColor("#50c878"), 2.0))
            painter.setBrush(QBrush(QColor("#1b3829")))
            painter.drawRect(QRectF(cx - 24.0, cy - 24.0, 48.0, 48.0))

        # Nome do Objeto
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(QRectF(cx - 60.0, cy - 42.0, 120.0, 18.0), Qt.AlignCenter, obj_name)

        # 3. Renderiza Indicador de Ação Ativa (ex: "⚡ Move() Executando")
        if is_highlighted and self.active_node_name:
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.setPen(QPen(QColor("#ffe600")))
            painter.drawText(QRectF(cx - 100.0, cy + 28.0, 200.0, 18.0), Qt.AlignCenter, f"⚡ {self.active_node_name}")

        # 4. Overlay de Métricas de Runtime (FPS, Velocidade, Estado)
        overlay_x = 10.0
        overlay_y = rect.height() - 40.0
        painter.setFont(QFont("Consolas", 8))
        painter.setPen(QPen(QColor("#8b949e")))
        stats_str = f"FPS: {self.fps:.0f} | State: {self.state_name} | Grounded: {self.is_grounded} | Pos: ({cx:.0f}, {cy:.0f})"
        painter.drawText(QPointF(overlay_x, overlay_y), stats_str)
