"""Dock Principal do Animation Studio Visual (Unifica Marcos A, B, C, D).

Integra:
- Toolbar de Playback (Play/Pause/Stop/Scrubbing/Loop/Speed/Hot Reload - Marco D)
- Régua Temporal (TimelineRuler - Marco A)
- Cabeçalhos de Trilhas (TrackHeaderWidget - Marco B)
- Canvas de Keyframes (KeyframeCanvas - Marco C)
- Serviço oficial AnimationPlayerService para amostragem no Runtime
"""
from __future__ import annotations
from typing import List, Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QScrollArea,
    QSplitter,
)

from engine.animation.tracks import AnimationTrack, TransformTrack, PropertyTrack
from engine.animation.animation_player_service import AnimationPlayerService, AnimationPlaybackState
from editor.animation_studio.timeline_ruler import TimelineRuler
from editor.animation_studio.track_header_widget import TrackHeaderWidget
from editor.animation_studio.keyframe_canvas import KeyframeCanvas


class AnimationStudioDock(QDockWidget):
    """Dock visual principal do Animation Studio da Zennity Engine."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("🎞 Animation Studio Visual", parent)
        self.setObjectName("AnimationStudioDock")
        self.setMinimumHeight(280)

        # Dados da Animação
        self.tracks: List[AnimationTrack] = [
            TransformTrack(name="Transform"),
            PropertyTrack(name="Opacity", property_name="opacity"),
        ]
        self.player_service = AnimationPlayerService()
        self.playback_state = AnimationPlaybackState.STOPPED
        self.playback_speed: float = 1.0

        # Timer para amostragem de tempo real (Marco D - Preview)
        self._playback_timer = QTimer(self)
        self._playback_timer.setInterval(16)  # ~60 FPS
        self._playback_timer.timeout.connect(self._on_timer_tick)

        # UI Principal
        container = QWidget(self)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # 1. Toolbar de Playback (Marco D)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(6)

        self.btn_play = QPushButton("▶ Play", self)
        self.btn_play.clicked.connect(self.play)

        self.btn_pause = QPushButton("⏸ Pause", self)
        self.btn_pause.clicked.connect(self.pause)

        self.btn_stop = QPushButton("⏹ Stop", self)
        self.btn_stop.clicked.connect(self.stop)

        self.spin_speed = QDoubleSpinBox(self)
        self.spin_speed.setRange(0.1, 5.0)
        self.spin_speed.setValue(1.0)
        self.spin_speed.setSingleStep(0.1)
        self.spin_speed.setSuffix("x")
        self.spin_speed.valueChanged.connect(self._on_speed_changed)

        self.btn_hot_reload = QPushButton("⚡ Hot Reload", self)
        self.btn_hot_reload.clicked.connect(self.trigger_hot_reload)

        toolbar_layout.addWidget(self.btn_play)
        toolbar_layout.addWidget(self.btn_pause)
        toolbar_layout.addWidget(self.btn_stop)
        toolbar_layout.addWidget(QLabel("Speed:", self))
        toolbar_layout.addWidget(self.spin_speed)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.btn_hot_reload)

        main_layout.addLayout(toolbar_layout)

        # 2. Splitter de Timeline (Headers à Esquerda | Canvas & Ruler à Direita)
        splitter = QSplitter(Qt.Horizontal, container)

        # Painel Esquerdo: Track Headers (Marco B)
        left_panel = QWidget(splitter)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        header_top_filler = QWidget(left_panel)
        header_top_filler.setFixedHeight(32)
        header_top_filler.setStyleSheet("background: #1A1A22; border-bottom: 1px solid #333;")
        left_layout.addWidget(header_top_filler)

        self.headers_container = QWidget(left_panel)
        self.headers_layout = QVBoxLayout(self.headers_container)
        self.headers_layout.setContentsMargins(0, 0, 0, 0)
        self.headers_layout.setSpacing(0)
        left_layout.addWidget(self.headers_container)
        left_layout.addStretch(1)

        # Painel Direito: Ruler (Marco A) & KeyframeCanvas (Marco C)
        right_panel = QWidget(splitter)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.ruler = TimelineRuler(right_panel)
        self.ruler.time_changed.connect(self._on_ruler_time_changed)
        right_layout.addWidget(self.ruler)

        self.canvas = KeyframeCanvas(right_panel)
        self.canvas.tracks = self.tracks
        right_layout.addWidget(self.canvas, 1)

        splitter.setSizes([200, 600])
        main_layout.addWidget(splitter, 1)

        self.setWidget(container)
        self.rebuild_track_headers()

    def rebuild_track_headers(self) -> None:
        # Limpa layout antigo
        while self.headers_layout.count():
            item = self.headers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for track in self.tracks:
            header = TrackHeaderWidget(track, self.headers_container)
            self.headers_layout.addWidget(header)

    def play(self) -> None:
        self.playback_state = AnimationPlaybackState.PLAYING
        self._playback_timer.start()

    def pause(self) -> None:
        self.playback_state = AnimationPlaybackState.PAUSED
        self._playback_timer.stop()

    def stop(self) -> None:
        self.playback_state = AnimationPlaybackState.STOPPED
        self._playback_timer.stop()
        self.ruler.set_current_time(0.0)
        self.canvas.current_time = 0.0
        self.canvas.update()

    def _on_timer_tick(self) -> None:
        if self.playback_state == AnimationPlaybackState.PLAYING:
            dt = (16 / 1000.0) * self.playback_speed
            new_time = self.ruler.current_time + dt
            if new_time > self.ruler.duration:
                new_time = 0.0
            self.ruler.set_current_time(new_time)
            self.canvas.current_time = new_time
            self.canvas.update()

    def _on_ruler_time_changed(self, time_seconds: float) -> None:
        self.canvas.current_time = time_seconds
        self.canvas.update()

    def _on_speed_changed(self, val: float) -> None:
        self.playback_speed = float(val)

    def trigger_hot_reload(self) -> None:
        self.player_service.on_asset_reimported("AnimationStudio")
        self.canvas.update()
