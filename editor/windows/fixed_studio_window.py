from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSplitter, QTabWidget, QTextEdit, QStatusBar

from editor.models.scene_model import SceneModel
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.widgets.viewport_widget import ViewportWidget


class FixedStudioWindow(QMainWindow):
    """Nova UI do zero: fixa, simples e sem docks arrastaveis."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ZennityFixedStudioWindow")
        self.setWindowTitle("Zennity Engine Editor - Fixed Studio")
        self.resize(1440, 900)
        self.scene_model = SceneModel()
        self.scene_view_model = SceneViewModel(self.scene_model)
        self._build_menu()
        self._build_ui()
        self._build_status()

    def _build_menu(self) -> None:
        bar = self.menuBar()
        bar.addMenu("Arquivo")
        bar.addMenu("Editar")
        bar.addMenu("Criar")
        bar.addMenu("Ferramentas")
        run = bar.addMenu("Executar")
        run.addAction("Play", self.play)
        run.addAction("Stop", self.stop)
        view = bar.addMenu("Visualização")
        view.addAction("Restaurar Layout", self.restore_layout)
        view.addAction("Foco Viewport", self.toggle_focus)
        bar.addMenu("Ajuda")

    def _build_ui(self) -> None:
        self.viewport = ViewportWidget(self)
        self.viewport.set_viewmodel(self.scene_view_model)

        left = self._left_tabs()
        center = QTabWidget()
        center.addTab(self.viewport, "Viewport")
        center.addTab(QLabel("Cena"), "Cena")
        right = QTabWidget()
        right.addTab(QLabel("Inspector\n\nTransform\nRenderer\nCollider\nScripts"), "Inspector")

        top = QSplitter(Qt.Horizontal)
        top.addWidget(left)
        top.addWidget(center)
        top.addWidget(right)
        top.setSizes([300, 820, 340])

        bottom = QTabWidget()
        console = QTextEdit()
        console.setReadOnly(True)
        console.setText("Console pronto.")
        bottom.addTab(console, "Console")
        bottom.addTab(QLabel("Profiler"), "Profiler")
        bottom.addTab(QLabel("Preview"), "Preview")

        self.main_split = QSplitter(Qt.Vertical)
        self.main_split.addWidget(top)
        self.main_split.addWidget(bottom)
        self.main_split.setSizes([650, 220])
        self.setCentralWidget(self.main_split)

    def _left_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.addTab(QLabel("MainScene\n- Player\n- Camera"), "Hierarchy")
        tabs.addTab(self._create_panel(), "Criar")
        tabs.addTab(QLabel("Assets"), "Assets")
        return tabs

    def _create_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        for name in ["Player", "Plataforma", "Inimigo", "Sprite 2D", "Camera 2D"]:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked=False, n=name: self.viewport.create_object(n))
            layout.addWidget(btn)
        layout.addStretch(1)
        return panel

    def _build_status(self) -> None:
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Fixed Studio pronto", 5000)

    def restore_layout(self) -> None:
        self.main_split.setSizes([650, 220])

    def toggle_focus(self) -> None:
        self.main_split.setSizes([860, 0] if self.main_split.sizes()[1] else [650, 220])

    def play(self) -> None:
        self.viewport._on_play_state_changed("play")

    def stop(self) -> None:
        self.viewport._on_play_state_changed("stop")
