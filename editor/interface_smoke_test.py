"""Teste isolado da interface do Zennity Editor, sem Pygame ou Viewport.

Execute a partir da raiz do projeto:
    python -m editor.interface_smoke_test
"""
from __future__ import annotations

import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QMainWindow,
    QToolBar,
    QWidget,
)
from editor.ui.icons import TOOLBAR_ICONS, editor_icon
from editor.ui.empty_state import EmptyStateWidget


class InterfaceSmokeTest(QMainWindow):
    """Shell do editor para validar dock, splitter, menu e resize do Qt."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Zennity — Teste de Interface (sem Viewport)")
        self.resize(1440, 900)
        self.setMinimumSize(1000, 650)
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)
        self._build_menu()
        self._build_toolbar()
        self._build_center()
        self._build_docks()
        from editor.ui import polish_editor_widgets
        polish_editor_widgets(self)
        self.statusBar().showMessage("Teste isolado: não há Pygame nem renderização de cena.")

    def _build_menu(self) -> None:
        self.editor_menus = {}
        for name in ("Arquivo", "Editar", "Janela", "Criar", "Ferramentas", "Build", "Executar", "Ajuda"):
            menu = self.menuBar().addMenu(name)
            self.editor_menus[name] = menu

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Ferramentas")
        toolbar.setObjectName("CommandBar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(17, 17))
        self.addToolBar(toolbar)
        self.toolbar_actions = {}
        for label, icon_name in TOOLBAR_ICONS.items():
            action = QAction(editor_icon(icon_name), label, self)
            action.setStatusTip(label)
            action.setToolTip(label)
            self.toolbar_actions[label] = action
            toolbar.addAction(action)
        toolbar.addSeparator()
        mode = QComboBox()
        mode.setObjectName("ModeSwitch")
        mode.addItems(["2D", "3D (experimental)"])
        toolbar.addWidget(mode)

    def _build_center(self) -> None:
        from editor.ui.workspace_builder import build_center_workspace
        build_center_workspace(self)

    def _build_docks(self) -> None:
        from editor.ui.docks_builder import build_docks_layout
        build_docks_layout(self)
    def _dock(self, title: str, widget: QWidget, area: Qt.DockWidgetArea, width: int) -> None:
        dock = QDockWidget(title, self)
        dock.setObjectName(f"SmokeTest_{title}")
        dock.setWidget(widget)
        dock.setMinimumWidth(width if area in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea) else 200)
        self.addDockWidget(area, dock)

    @staticmethod
    def _placeholder(text: str) -> QWidget:
        return EmptyStateWidget(text or "Nenhum conteúdo", "Este painel ainda não possui dados.")


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    from editor.ui import apply_editor_theme
    apply_editor_theme(app)
    window = InterfaceSmokeTest()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
