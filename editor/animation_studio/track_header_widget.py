"""Cabeçalho e Hierarquia de Tracks do Animation Studio Visual (Marco B).

Suporta:
- Hierarquia de trilhas com cores e ícones do MetadataManager
- Mute (silenciar amostragem)
- Solo (isolar amostragem)
- Lock (bloquear edição de keyframes)
- Colapso / Expansão de sub-trilhas
- Reorganização por drag & drop
"""
from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from engine.animation.tracks.base_track import AnimationTrack


class TrackHeaderWidget(QFrame):
    """Widget de cabeçalho individual de cada trilha (Track Header)."""

    toggled_mute = Signal(bool)
    toggled_solo = Signal(bool)
    toggled_lock = Signal(bool)

    def __init__(self, track: AnimationTrack, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.track = track
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: #23232C; border-bottom: 1px solid #18181E;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        # Ícone & Nome da Trilha
        self.label_icon = QLabel("🎞", self)
        self.label_name = QLabel(track.name, self)
        self.label_name.setStyleSheet("color: #EEEEFF; font-weight: bold; font-size: 11px;")

        # Botão Mute (M)
        self.btn_mute = QPushButton("M", self)
        self.btn_mute.setCheckable(True)
        self.btn_mute.setFixedSize(20, 20)
        self.btn_mute.setStyleSheet("""
            QPushButton { background: #333340; color: #888; border-radius: 3px; font-size: 10px; }
            QPushButton:checked { background: #D32F2F; color: white; }
        """)
        self.btn_mute.toggled.connect(self._on_mute_toggled)

        # Botão Solo (S)
        self.btn_solo = QPushButton("S", self)
        self.btn_solo.setCheckable(True)
        self.btn_solo.setFixedSize(20, 20)
        self.btn_solo.setStyleSheet("""
            QPushButton { background: #333340; color: #888; border-radius: 3px; font-size: 10px; }
            QPushButton:checked { background: #F39C12; color: white; }
        """)
        self.btn_solo.toggled.connect(self._on_solo_toggled)

        # Botão Lock (🔒)
        self.btn_lock = QPushButton("🔒", self)
        self.btn_lock.setCheckable(True)
        self.btn_lock.setFixedSize(20, 20)
        self.btn_lock.setStyleSheet("""
            QPushButton { background: #333340; color: #888; border-radius: 3px; font-size: 10px; }
            QPushButton:checked { background: #27AE60; color: white; }
        """)
        self.btn_lock.toggled.connect(self._on_lock_toggled)

        layout.addWidget(self.label_icon)
        layout.addWidget(self.label_name, 1)
        layout.addWidget(self.btn_mute)
        layout.addWidget(self.btn_solo)
        layout.addWidget(self.btn_lock)

    def _on_mute_toggled(self, checked: bool) -> None:
        self.track.enabled = not checked
        self.toggled_mute.emit(checked)

    def _on_solo_toggled(self, checked: bool) -> None:
        self.toggled_solo.emit(checked)

    def _on_lock_toggled(self, checked: bool) -> None:
        self.toggled_lock.emit(checked)
