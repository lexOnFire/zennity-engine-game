from __future__ import annotations

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence

from editor.core.editor_mvp import install_editor_mvp
from editor.windows.main_window import MainWindow


class StudioWindow(MainWindow):
    """Janela alternativa com layout mais próximo de uma engine profissional."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ZennityStudioWindow")
        self.setWindowTitle("Zennity Engine Editor - Studio")
        self.menuBar().show()

        self.studio_settings = QSettings("Zennity", "StudioLayout")
        self._focus_mode = False
        self._focus_hidden_docks = []

        install_editor_mvp(self)
        self.create_studio_actions()
        self.apply_studio_layout()
        self.restore_studio_layout()
        self.statusBar().showMessage("Studio Editor pronto", 5000)

    def create_studio_actions(self) -> None:
        """Adiciona ações para layout, foco e visibilidade de painéis."""
        self.act_focus_viewport = QAction("Foco na Viewport", self)
        self.act_focus_viewport.setShortcut(QKeySequence("Ctrl+Space"))
        self.act_focus_viewport.triggered.connect(self.toggle_focus_mode)
        self.addAction(self.act_focus_viewport)

        self.act_save_studio_layout = QAction("Salvar Layout Atual", self)
        self.act_save_studio_layout.triggered.connect(self.save_studio_layout)

        self.act_restore_studio_layout = QAction("Restaurar Layout Studio", self)
        self.act_restore_studio_layout.triggered.connect(self.apply_studio_layout)

        view_menu = self.menuBar().addMenu("Painéis")
        view_menu.addAction(self.act_focus_viewport)
        view_menu.addSeparator()
        view_menu.addAction(self.dock_hierarchy.toggleViewAction())
        view_menu.addAction(self.dock_create.toggleViewAction())
        view_menu.addAction(self.dock_assets.toggleViewAction())
        view_menu.addAction(self.dock_inspector.toggleViewAction())
        view_menu.addAction(self.dock_console.toggleViewAction())
        view_menu.addAction(self.dock_profiler.toggleViewAction())
        view_menu.addAction(self.dock_code_editor.toggleViewAction())
        view_menu.addSeparator()
        view_menu.addAction(self.act_save_studio_layout)
        view_menu.addAction(self.act_restore_studio_layout)

        run_menu = self.menuBar().addMenu("Executar")
        run_menu.addAction("Play", self.on_play_clicked)
        run_menu.addAction("Pause", self.on_pause_clicked)
        run_menu.addAction("Stop", self.on_stop_clicked)

    def apply_studio_layout(self) -> None:
        """Organiza os docks no estilo Hierarchy / Viewport / Inspector / Console."""
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_hierarchy)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_create)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_assets)
        self.splitDockWidget(self.dock_hierarchy, self.dock_create, Qt.Vertical)
        self.splitDockWidget(self.dock_create, self.dock_assets, Qt.Vertical)

        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_inspector)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_profiler)
        self.tabifyDockWidget(self.dock_console, self.dock_profiler)
        self.dock_console.raise_()

        for dock in self.studio_docks():
            dock.show()

        self.resizeDocks(
            [self.dock_hierarchy, self.dock_inspector],
            [300, 360],
            Qt.Horizontal,
        )
        self.resizeDocks(
            [self.dock_console],
            [220],
            Qt.Vertical,
        )
        self.statusBar().showMessage("Layout Studio restaurado", 3000)

    def studio_docks(self):
        return [
            self.dock_hierarchy,
            self.dock_create,
            self.dock_assets,
            self.dock_inspector,
            self.dock_console,
            self.dock_profiler,
            self.dock_code_editor,
        ]

    def toggle_focus_mode(self) -> None:
        """Oculta painéis para deixar a Viewport maior; Ctrl+Space volta tudo."""
        if not self._focus_mode:
            self._focus_hidden_docks = [dock for dock in self.studio_docks() if dock.isVisible()]
            for dock in self._focus_hidden_docks:
                dock.hide()
            self._focus_mode = True
            self.statusBar().showMessage("Modo foco: painéis ocultos. Ctrl+Space para voltar.", 4000)
            return

        for dock in self._focus_hidden_docks:
            dock.show()
        self._focus_hidden_docks = []
        self._focus_mode = False
        self.statusBar().showMessage("Painéis restaurados", 3000)

    def save_studio_layout(self) -> None:
        """Salva posição/tamanho dos docks após você arrastar os painéis."""
        self.studio_settings.setValue("geometry", self.saveGeometry())
        self.studio_settings.setValue("windowState", self.saveState())
        self.statusBar().showMessage("Layout Studio salvo", 3000)

    def restore_studio_layout(self) -> bool:
        geometry = self.studio_settings.value("geometry")
        state = self.studio_settings.value("windowState")
        if geometry is None or state is None:
            return False
        self.restoreGeometry(geometry)
        self.restoreState(state)
        self.statusBar().showMessage("Layout Studio carregado", 3000)
        return True

    def closeEvent(self, event: QCloseEvent) -> None:
        self.save_studio_layout()
        super().closeEvent(event)
