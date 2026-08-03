"""Runtime Timeline Widget — Sprint 13 (Visual Scripting 2.0).

Timeline visual de runtime na parte inferior do editor que exibe cada frame gravado:
  - Nós executados em cada instante (linha temporal)
  - Eventos disparados (ex: Colisão, Tecla, Animação)
  - Mutações de variáveis
  - Erros e Warnings de execução
Navegação livre selecionando qualquer frame da linha do tempo.
"""
from __future__ import annotations

from typing import Any, Optional
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QSlider, QVBoxLayout, QWidget


class RuntimeTimelineWidget(QFrame):
    """Runtime Timeline & Event Log Widget (Sprint 13)."""

    frame_selected = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("RuntimeTimelineWidget")
        self.setStyleSheet("""
            QFrame#RuntimeTimelineWidget {
                background-color: #121418;
                border-top: 1px solid #2a2e38;
            }
        """)

        self.recorded_frames: list[dict[str, Any]] = []
        self.current_frame_index: int = 0

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        header = QHBoxLayout()
        title = QLabel("⏱️ Runtime Timeline (Frame History & Event Log)", self)
        title.setStyleSheet("font-weight: bold; color: #a4b1cd; font-size: 11px;")
        header.addWidget(title)

        header.addStretch(1)

        self.lbl_frame_info = QLabel("Frame: 0 / 0", self)
        self.lbl_frame_info.setStyleSheet("color: #7ee787; font-family: Consolas; font-size: 10px;")
        header.addWidget(self.lbl_frame_info)

        layout.addLayout(header)

        # Timeline Slider & Event List
        self.timeline_slider = QSlider(Qt.Horizontal, self)
        self.timeline_slider.setRange(0, 0)
        self.timeline_slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.timeline_slider)

        self.events_list = QListWidget(self)
        self.events_list.setMaximumHeight(80)
        self.events_list.setStyleSheet("background-color: #0b0c0e; color: #b8beca; border: none; font-size: 10px;")
        layout.addWidget(self.events_list)

    def record_frame_snapshot(self, frame_id: int, node_name: str, events: list[str], variables: dict[str, Any]) -> None:
        """Registra o snapshot completo de um frame de runtime."""
        snapshot = {
            "frame": frame_id,
            "node_name": node_name,
            "events": events or ["Update"],
            "variables": variables or {},
        }
        self.recorded_frames.append(snapshot)
        self.timeline_slider.setRange(0, max(0, len(self.recorded_frames) - 1))
        self.timeline_slider.setValue(len(self.recorded_frames) - 1)
        self.lbl_frame_info.setText(f"Frame: {frame_id} / {len(self.recorded_frames)}")

    def _on_slider_changed(self, index: int) -> None:
        if 0 <= index < len(self.recorded_frames):
            self.current_frame_index = index
            snapshot = self.recorded_frames[index]
            self.lbl_frame_info.setText(f"Frame: {snapshot['frame']} [{index + 1}/{len(self.recorded_frames)}]")
            self.events_list.clear()

            item_str = f"⚡ [{snapshot['node_name']}] Eventos: {', '.join(snapshot['events'])} | Vars: {snapshot['variables']}"
            item = QListWidgetItem(item_str)
            item.setForeground(QColor("#7ee787"))
            self.events_list.addItem(item)

            self.frame_selected.emit(index)
