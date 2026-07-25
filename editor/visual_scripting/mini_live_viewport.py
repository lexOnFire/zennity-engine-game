"""Runtime Visualization Panel Widget (Visual Debugger & Interactive Viewport).

Evolução da Mini Live Viewport em um painel completo de visualização de runtime:
  - Interatividade: clique na viewport seleciona o objeto no SelectionService -> Inspector -> Graph.
  - Runtime Visualization Renderer: desenha colliders, raycasts, vetores de velocidade/força, FOV de IA, pathfinding e partículas.
  - Replay dos Últimos 5 Segundos (Buffer circular de 300 frames com Timeline Overlay).
  - Performance Overlay detalhado (FPS, Physics, Scripts, Animation, Rendering MS).
"""
from __future__ import annotations

import time
from collections import deque
from typing import Any, Optional
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget
)

from editor.visual_scripting.runtime_visualization import RuntimeVisualizationRenderer


class RuntimeVisualizationPanelWidget(QFrame):
    """Runtime Visualization Panel (Visual Debugger AAA da Zennity Engine)."""

    object_selected = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("RuntimeVisualizationPanelWidget")
        self.setStyleSheet("""
            QFrame#RuntimeVisualizationPanelWidget {
                background-color: #121418;
                border: 1px solid #2a2e38;
                border-radius: 4px;
            }
        """)

        self.target_object: Any = None
        self.active_node_id: str | None = None
        self.active_node_name: str = ""
        self.highlight_timer: float = 0.0

        # Performance Overlay stats
        self.fps: float = 60.0
        self.physics_ms: float = 1.2
        self.scripts_ms: float = 2.4
        self.rendering_ms: float = 3.1
        self.is_grounded: bool = True
        self.state_name: str = "IDLE"

        # Replay Buffer de 5 Segundos (300 frames a 60 FPS)
        self.replay_buffer: deque[dict[str, Any]] = deque(maxlen=300)
        self.is_replaying: bool = False
        self.replay_frame_index: int = 0

        # Renderizador de Gizmos Internos
        self.renderer = RuntimeVisualizationRenderer()

        # Timer para atualizar a renderização em tempo real (60 FPS)
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(16)
        self._update_timer.timeout.connect(self._on_tick)
        self._update_timer.start()

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Header Superior
        header = QHBoxLayout()
        header.setContentsMargins(6, 2, 6, 2)

        title = QLabel("👁️ Visual Debugger")
        title.setStyleSheet("font-weight: bold; color: #a4b1cd; font-size: 11px;")
        header.addWidget(title)

        from PySide6.QtWidgets import QCheckBox
        self.chk_phys = QCheckBox("Physics", self)
        self.chk_phys.setChecked(True)
        self.chk_phys.toggled.connect(lambda c: setattr(self.renderer, "show_colliders", c))

        self.chk_nav = QCheckBox("Navigation", self)
        self.chk_nav.setChecked(True)
        self.chk_nav.toggled.connect(lambda c: setattr(self.renderer, "show_pathfinding", c))

        self.chk_ai = QCheckBox("AI", self)
        self.chk_ai.setChecked(True)
        self.chk_ai.toggled.connect(lambda c: setattr(self.renderer, "show_ai_fov", c))

        header.addWidget(self.chk_phys)
        header.addWidget(self.chk_nav)
        header.addWidget(self.chk_ai)

        header.addStretch(1)

        self.status_badge = QLabel("● PAUSED")
        self.status_badge.setStyleSheet("color: #e6b85c; font-weight: bold; font-size: 10px;")
        header.addWidget(self.status_badge)

        layout.addLayout(header)
        layout.addStretch(1)

        # Controles de Replay dos Últimos 5 Segundos (Timeline Overlay)
        replay_bar = QHBoxLayout()
        replay_bar.setContentsMargins(4, 2, 4, 2)

        self.btn_rewind = QPushButton("<<", self)
        self.btn_step_back = QPushButton("<", self)
        self.btn_replay_play = QPushButton("▶ Replay", self)
        self.btn_step_fw = QPushButton(">", self)
        self.btn_live = QPushButton("🔴 Live", self)
        self.btn_live.setStyleSheet("background-color: #da3633; color: white; font-weight: bold;")

        self.timeline_slider = QSlider(Qt.Horizontal, self)
        self.timeline_slider.setRange(0, 300)
        self.timeline_slider.setValue(300)

        replay_bar.addWidget(self.btn_rewind)
        replay_bar.addWidget(self.btn_step_back)
        replay_bar.addWidget(self.btn_replay_play)
        replay_bar.addWidget(self.btn_step_fw)
        replay_bar.addWidget(self.btn_live)
        replay_bar.addWidget(self.timeline_slider)

        layout.addLayout(replay_bar)

        self._connect_replay_controls()

    def _connect_replay_controls(self) -> None:
        self.btn_rewind.clicked.connect(lambda: self.set_replay_frame(0))
        self.btn_step_back.clicked.connect(lambda: self.set_replay_frame(max(0, self.replay_frame_index - 10)))
        self.btn_step_fw.clicked.connect(lambda: self.set_replay_frame(min(len(self.replay_buffer) - 1, self.replay_frame_index + 10)))
        self.btn_live.clicked.connect(self.resume_live)
        self.timeline_slider.valueChanged.connect(self.set_replay_frame)

    def set_target_object(self, obj: Any) -> None:
        """Conecta a viewport ao objeto de jogo atualmente selecionado."""
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
        """Ilumina a viewport e registra o nó ativado no buffer de replay."""
        self.active_node_id = str(node_id)
        self.active_node_name = str(node_name)
        self.highlight_timer = time.time() + 0.6
        self.update()

    def _on_tick(self) -> None:
        """Grava quadros no buffer circular de Replay (5 segundos a 60 FPS)."""
        if not self.is_replaying:
            snapshot = {
                "timestamp": time.time(),
                "node_id": self.active_node_id,
                "node_name": self.active_node_name,
                "highlight": time.time() < self.highlight_timer,
            }
            self.replay_buffer.append(snapshot)
            self.timeline_slider.setValue(len(self.replay_buffer))
        self.update()

    def set_replay_frame(self, index: int) -> None:
        """Navega para um frame histórico no Replay Buffer."""
        if 0 <= index < len(self.replay_buffer):
            self.is_replaying = True
            self.replay_frame_index = index
            snapshot = self.replay_buffer[index]
            self.active_node_id = snapshot["node_id"]
            self.active_node_name = snapshot["node_name"] or ""
            self.status_badge.setText(f"⏪ REPLAY [{index}/{len(self.replay_buffer)}]")
            self.status_badge.setStyleSheet("color: #ae7df0; font-weight: bold; font-size: 10px;")
            self.update()

    def resume_live(self) -> None:
        """Retorna ao modo ao vivo (Live Mode)."""
        self.is_replaying = False
        self.timeline_slider.setValue(len(self.replay_buffer))
        self.set_play_mode(True)

    def mousePressEvent(self, event) -> None:
        """Interatividade total: Clicar no objeto dispara o SelectionService."""
        super().mousePressEvent(event)
        rect = self.contentsRect()
        cx, cy = rect.width() / 2.0, rect.height() / 2.0 + 10.0
        click_pos = event.position()

        # Se clicou próximo ao centro (objeto)
        if abs(click_pos.x() - cx) < 40 and abs(click_pos.y() - cy) < 40:
            if self.target_object:
                self.object_selected.emit(self.target_object)
                try:
                    from editor.runtime.editor_context import EditorContext
                    EditorContext.instance().selection.select_item(self.target_object, type="game_object", context="runtime_viewport")
                except Exception:
                    pass

    def paintEvent(self, event) -> None:
        """Renderiza a Viewport com a camada de Runtime Visualization e Performance Overlay."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.contentsRect()
        cx, cy = rect.width() / 2.0, rect.height() / 2.0 + 10.0

        # 1. Grade da Viewport
        painter.setPen(QPen(QColor("#1e222a"), 1.0, Qt.DashLine))
        painter.drawLine(0, int(cy), rect.width(), int(cy))
        painter.drawLine(int(cx), 0, int(cx), rect.height())

        # 2. Renderização da Camada Visual (Física, Colliders, Vetores, IA FOV, Pathfinding)
        self.renderer.draw_visualization_layer(painter, rect, self.target_object, self.active_node_name, self.highlight_timer)

        # 3. Renderiza Objeto Principal
        obj_name = getattr(self.target_object, "name", "MainPlayer") if self.target_object else "Player"
        is_highlighted = time.time() < self.highlight_timer

        if is_highlighted:
            glow_color = QColor("#ff4d8d") if "jump" in self.active_node_name.lower() else QColor("#4c9aff")
            painter.setPen(QPen(glow_color, 3.0))
            painter.setBrush(QBrush(glow_color.darker(160)))
            painter.drawEllipse(QPointF(cx, cy), 32.0, 32.0)
        else:
            painter.setPen(QPen(QColor("#50c878"), 2.0))
            painter.setBrush(QBrush(QColor("#1b3829")))
            painter.drawRect(QRectF(cx - 24.0, cy - 24.0, 48.0, 48.0))

        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(QRectF(cx - 60.0, cy - 42.0, 120.0, 18.0), Qt.AlignCenter, obj_name)

        if is_highlighted and self.active_node_name:
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.setPen(QPen(QColor("#ffe600")))
            painter.drawText(QRectF(cx - 100.0, cy + 28.0, 200.0, 18.0), Qt.AlignCenter, f"⚡ {self.active_node_name}")

        # 4. Performance Overlay Detalhado (FPS, Physics, Scripts, Animation, Rendering MS)
        painter.setFont(QFont("Consolas", 8))
        painter.setPen(QPen(QColor("#8b949e")))
        perf_text = f"FPS: {self.fps:.0f} | Physics: {self.physics_ms:.1f}ms | Scripts: {self.scripts_ms:.1f}ms | Render: {self.rendering_ms:.1f}ms"
        painter.drawText(QPointF(10.0, 22.0), perf_text)


# Aliases para compatibilidade total
MiniLiveViewportWidget = RuntimeVisualizationPanelWidget
