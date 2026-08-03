"""Dock de Configurações de Projeto (Project Settings Dock)."""
from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel, QLineEdit, QCheckBox


class ProjectSettingsDock(QDockWidget):
    """Dock para Gerenciamento de Configurações Globais do Projeto."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("⚙️ Project Settings", parent)
        self.setObjectName("ProjectSettingsDock")

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)

        layout.addWidget(QLabel("Nome do Projeto:", self))
        self.txt_name = QLineEdit("Zennity Game", self)
        layout.addWidget(self.txt_name)

        layout.addWidget(QLabel("Cena Inicial:", self))
        self.txt_start_scene = QLineEdit("MainScene.zscene", self)
        layout.addWidget(self.txt_start_scene)

        self.chk_vsync = QCheckBox("Habilitar V-Sync (60 FPS)", self)
        self.chk_vsync.setChecked(True)
        layout.addWidget(self.chk_vsync)

        layout.addStretch(1)
        self.setWidget(container)
