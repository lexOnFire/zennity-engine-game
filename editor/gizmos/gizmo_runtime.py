from __future__ import annotations

from typing import Any

from editor.gizmos.move_gizmo import MoveGizmo
from editor.widgets.viewport_widget import ViewportWidget


_GIZMO = MoveGizmo()


def install_gizmo_runtime() -> None:
    """Instala overlay de gizmo no paintGL da Viewport.

    Evita alterar diretamente o arquivo grande da Viewport durante a Fase 1.2.
    """
    if getattr(ViewportWidget, "_zennity_gizmo_runtime", False):
        return

    original_paint = ViewportWidget.paintGL

    def paintGL(self: ViewportWidget) -> None:
        original_paint(self)
        selected = None
        if hasattr(self, "selected_object"):
            selected = self.selected_object()
        elif getattr(self, "viewmodel", None) is not None:
            selected = getattr(self.viewmodel, "selected_object", None)
        if getattr(self, "pg_surface", None) is not None:
            _GIZMO.draw(self.pg_surface, selected)

    ViewportWidget.paintGL = paintGL
    ViewportWidget._zennity_gizmo_runtime = True
