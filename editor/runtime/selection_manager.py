from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


SelectionListener = Callable[[Any], None]


@dataclass
class SelectionItem:
    """Item de seleção genérico — não conhece tipos específicos.

    Qualquer sistema (Hierarchy, Visual Scripting, Animation, UI Builder, etc.)
    pode participar da seleção sem alterar o SelectionService.

    Atributos:
        id       — identificador único do item selecionado
        type     — string que descreve o tipo ("game_object", "asset", "node",
                   "keyframe", "ui_component", ou qualquer tipo futuro)
        context  — qual editor/subsistema originou a seleção
        payload  — o objeto Python selecionado (sem restrição de tipo)
    """
    id: str
    type: str
    context: str
    payload: Any = field(default=None)


class SelectionManager:
    """Fonte única de verdade para seleção no editor.

    A Viewport, Hierarchy, Inspector e futuros Gizmos devem consultar este
    gerenciador em vez de manter seleção própria isolada.
    """

    def __init__(self) -> None:
        self._selected: Any = None
        self._listeners: list[SelectionListener] = []
        self._projection_listeners: list[SelectionListener] = []

    @property
    def selected(self) -> Any:
        return self._selected

    def set_selected(self, obj: Any) -> None:
        if obj is self._selected:
            self._notify(self._projection_listeners)
            return

        self._selected = obj
        self._notify([*self._listeners, *self._projection_listeners])

    select = set_selected

    def clear(self) -> None:
        self.set_selected(None)

    def subscribe(self, callback: SelectionListener) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def subscribe_projection(self, callback: SelectionListener) -> None:
        """Registra uma projeção que também ressincroniza seleções idempotentes."""
        if callback not in self._projection_listeners:
            self._projection_listeners.append(callback)

    def unsubscribe(self, callback: SelectionListener) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)
        if callback in self._projection_listeners:
            self._projection_listeners.remove(callback)

    def reset(self) -> None:
        self._selected = None
        self._listeners.clear()
        self._projection_listeners.clear()

    def _notify(self, listeners: list[SelectionListener]) -> None:
        for callback in list(listeners):
            try:
                callback(self._selected)
            except Exception:
                import traceback
                traceback.print_exc()


class SelectionService(SelectionManager):
    """Serviço unificado de seleção do editor com SelectionItem genérico.

    Usa SelectionItem como tipo canônico para que qualquer sistema futuro
    possa participar da seleção sem alterar este serviço.
    """

    def __init__(self) -> None:
        super().__init__()
        self._current_item: SelectionItem | None = None

    @property
    def current_item(self) -> SelectionItem | None:
        return self._current_item

    def select_item(
        self,
        payload: Any,
        type: str = "game_object",
        context: str = "scene",
        id: str | None = None,
    ) -> None:
        """Seleciona um item de qualquer tipo de forma genérica."""
        item_id = id or str(getattr(payload, "name", None) or str(payload))
        self._current_item = SelectionItem(id=item_id, type=type, context=context, payload=payload)
        self.set_selected(payload)

        try:
            from editor.core.event_bus import EventBus, EVENT_SELECTION_CHANGED
            EventBus.emit(
                EVENT_SELECTION_CHANGED,
                item=self._current_item,
                selection=payload,
                selection_type=type,
                context=context,
            )
        except Exception:
            pass

    def clear_selection(self) -> None:
        self._current_item = None
        self.clear()
        try:
            from editor.core.event_bus import EventBus, EVENT_SELECTION_CLEARED
            EventBus.emit(EVENT_SELECTION_CLEARED)
        except Exception:
            pass

    # ── Conveniências mantidas para retrocompatibilidade ───────────────────────

    def select_asset(self, asset_path: str | Any) -> None:
        self.select_item(asset_path, type="asset", context="asset_browser")

    def select_node(self, node_id: str | Any, graph_id: str | None = None) -> None:
        self.select_item(node_id, type="node", context=graph_id or "graph")

    def select_keyframe(self, keyframe_id: str | Any, track_id: str | None = None) -> None:
        self.select_item(keyframe_id, type="keyframe", context=track_id or "animation")

    def select_ui_component(self, component: Any) -> None:
        self.select_item(component, type="ui_component", context="ui_builder")