from __future__ import annotations

from editor.gizmos.move_gizmo import MoveGizmo
from editor.widgets.viewport_widget import ViewportWidget


_GIZMO = MoveGizmo()


def install_gizmo_runtime() -> None:
    """Instala overlay de gizmo no draw da cena ativa.

    O desenho precisa acontecer antes do QImage ser enviado ao Qt, por isso o
    patch envolve `_apply_qt_shims` e o `scene.draw`, não o `paintGL`.
    """
    if getattr(ViewportWidget, "_zennity_gizmo_runtime", False):
        return

    original_apply = ViewportWidget._apply_qt_shims

    def _apply_qt_shims(self: ViewportWidget) -> None:
        original_apply(self)
        scene = getattr(self, "active_scene", None)
        if scene is None or getattr(scene, "_zennity_gizmo_wrapped", False):
            return

        original_draw = scene.draw

        def draw_with_gizmo(surface, _scene=scene, _draw=original_draw, _viewport=self):
            _draw(surface)
            selected = None
            if hasattr(_viewport, "selected_object"):
                selected = _viewport.selected_object()
            elif getattr(_viewport, "viewmodel", None) is not None:
                selected = getattr(_viewport.viewmodel, "selected_object", None)
            _GIZMO.draw(surface, selected)

        scene.draw = draw_with_gizmo
        scene._zennity_gizmo_wrapped = True

    ViewportWidget._apply_qt_shims = _apply_qt_shims
    ViewportWidget._zennity_gizmo_runtime = True
