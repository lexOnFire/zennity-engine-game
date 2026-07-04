from __future__ import annotations

from PySide6.QtGui import QPainter

from editor.gizmos.qt_gizmo_overlay import QtMoveGizmoOverlay
from editor.widgets.viewport_widget import ViewportWidget


class Phase1ViewportWidget(ViewportWidget):
    """Viewport da Fase 1 com overlay de gizmo Qt seguro.

    Herda toda a lógica funcional da Viewport original e apenas desenha o gizmo
    por cima, sem tocar em eventos de mouse/teclado ou scene.draw.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.move_gizmo_overlay = QtMoveGizmoOverlay()

    def paintGL(self) -> None:
        super().paintGL()
        selected = None
        if hasattr(self, "selected_object"):
            selected = self.selected_object()
        elif getattr(self, "viewmodel", None) is not None:
            selected = getattr(self.viewmodel, "selected_object", None)
        if selected is None:
            return
        painter = QPainter(self)
        self.move_gizmo_overlay.draw(painter, selected)
        painter.end()
