"""Política compartilhada de ordenação visual 2D."""
from __future__ import annotations

from typing import Any, Iterable


SORTING_LAYER_ORDER = {
    "Background": 0,
    "Midground": 1,
    "Default": 2,
    "Foreground": 3,
    "UI": 4,
}


def normalize_sorting_layer(value: Any) -> str:
    name = str(value or "Default").strip()
    return name if name in SORTING_LAYER_ORDER else "Default"


def sorting_key(layer: Any, order_in_layer: Any, source_order: int) -> tuple[int, int, int]:
    normalized = normalize_sorting_layer(layer)
    try:
        order = int(order_in_layer)
    except (TypeError, ValueError):
        order = 0
    return SORTING_LAYER_ORDER[normalized], order, int(source_order)


def sprite_component(obj: Any) -> Any | None:
    """Retorna o primeiro renderer 2D habilitado usado para ordenar o objeto."""
    for component in getattr(obj, "components", ()):
        type_name = getattr(component, "type_name", type(component).__name__)
        if type_name not in {"Image", "SpriteRenderer"}:
            continue
        if getattr(component, "enabled", True) and getattr(component, "visible", True):
            return component
    return None


def sorted_scene_objects(objects: Iterable[Any]) -> list[Any]:
    """Ordena objetos de modo estável pela política visual compartilhada."""
    entries = list(enumerate(objects))

    def key(entry: tuple[int, Any]) -> tuple[int, int, int]:
        source_order, obj = entry
        component = sprite_component(obj)
        if component is None:
            return sorting_key("Default", 0, source_order)
        return sorting_key(
            getattr(component, "sorting_layer", "Default"),
            getattr(component, "order_in_layer", getattr(component, "layer", 0)),
            source_order,
        )

    return [obj for _, obj in sorted(entries, key=key)]

