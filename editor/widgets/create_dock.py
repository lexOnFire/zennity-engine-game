from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QFrame,
)


class CreateDock(QDockWidget):
    """Painel visível para criar objetos e templates no editor.

    O objetivo deste dock é deixar o editor com fluxo de engine: escolher um
    preset, criar na Viewport, selecionar na Hierarchy e editar no Inspector.
    """

    create_requested = Signal(str)
    template_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Criar", parent)
        self.setObjectName("CreateDock")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        root = QWidget()
        root.setObjectName("CreateDockRoot")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("Adicionar à cena")
        title.setObjectName("PanelTitle")
        layout.addWidget(title)

        hint = QLabel("Comece pelo 2D. O 3D ainda é experimental.")
        hint.setObjectName("PanelHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addWidget(self._section_label("Presets 2D"))
        layout.addLayout(self._buttons_grid([
            ("Empty", "Empty Object"),
            ("Sprite", "Sprite 2D"),
            ("Player", "Player"),
            ("Platform", "Plataforma"),
            ("Enemy", "Inimigo"),
            ("Camera", "Camera 2D"),
        ]))

        layout.addWidget(self._separator())
        layout.addWidget(self._section_label("Templates"))
        layout.addLayout(self._template_grid([
            ("Plataforma 2D", "template_platformer_2d"),
            ("Top-down 2D", "template_topdown_2d"),
        ]))

        layout.addWidget(self._separator())
        layout.addWidget(self._section_label("Presets 3D experimental"))
        layout.addLayout(self._buttons_grid([
            ("Cube", "Cube 3D"),
            ("Plane", "Plane 3D"),
            ("Camera", "Camera 3D"),
            ("Light", "Light 3D"),
        ]))

        layout.addStretch(1)
        self.setWidget(root)

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionLabel")
        return label

    def _separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setObjectName("PanelSeparator")
        return line

    def _buttons_grid(self, items: list[tuple[str, str]]) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(6)
        for index, (text, preset) in enumerate(items):
            button = QPushButton(text)
            button.setObjectName("CreatePresetButton")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked=False, p=preset: self.create_requested.emit(p))
            grid.addWidget(button, index // 2, index % 2)
        return grid

    def _template_grid(self, items: list[tuple[str, str]]) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(6)
        for index, (text, template) in enumerate(items):
            button = QPushButton(text)
            button.setObjectName("CreateTemplateButton")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked=False, t=template: self.template_requested.emit(t))
            grid.addWidget(button, index, 0)
        return grid
