from __future__ import annotations

from typing import Any

from editor.core.event_bus import EventBus, EVENT_SELECTION_CHANGED
from editor.widgets.viewport_widget import ViewportWidget


def install_viewport_selection_api() -> None:
    """Instala métodos oficiais de seleção na Viewport.

    Mantemos isso separado do ViewportWidget por enquanto para evitar mexer no
    arquivo grande durante a estabilização da Fase 1.
    """
    if hasattr(ViewportWidget, "select_object"):
        return

    def select_object(self: ViewportWidget, obj: Any) -> None:
        scene = getattr(self, "active_scene", None)
        objects = list(getattr(scene, "editable_objects", [])) if scene else []

        if scene is not None:
            scene.selected_index = objects.index(obj) if obj in objects else -1

        if getattr(self, "viewmodel", None) is not None:
            self.viewmodel._selected_object = obj if obj in objects else None
            self.viewmodel.selection_changed.emit(self.viewmodel._selected_object)

        EventBus.emit(EVENT_SELECTION_CHANGED, obj=obj if obj in objects else None)
        self.update()

    def selected_object(self: ViewportWidget) -> Any:
        scene = getattr(self, "active_scene", None)
        if scene is None:
            return None
        objects = list(getattr(scene, "editable_objects", []))
        index = getattr(scene, "selected_index", -1)
        return objects[index] if 0 <= index < len(objects) else None

    def clear_selection(self: ViewportWidget) -> None:
        select_object(self, None)

    ViewportWidget.select_object = select_object
    ViewportWidget.selected_object = selected_object
    ViewportWidget.clear_selection = clear_selection
