"""Shared layer and sort_order logic for viewport rendering and hit testing."""
from __future__ import annotations

from typing import Any

LAYER_ORDER: dict[str, int] = {
    "Background": 0,
    "Default": 1,
    "Foreground": 2,
    "UI": 3,
}


def object_sort_key(item: tuple[str, dict[str, Any]], index: int = 0) -> tuple[int, int, int]:
    """
    Key for sorting objects in ascending render order (bottom to top).
    - render_layer value (Background=0, Default=1, Foreground=2, UI=3)
    - sort_order integer
    - original dictionary insertion index
    """
    name, obj = item
    layer_val = LAYER_ORDER.get(str(obj.get("render_layer", "Default")), 1)
    sort_val = int(obj.get("sort_order", 0))
    return (layer_val, sort_val, index)


def sort_objects_for_rendering(objects: dict[str, dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    """Returns (name, obj) pairs sorted from back to front (bottom to top for drawing)."""
    indexed = list(enumerate(objects.items()))
    indexed.sort(key=lambda entry: object_sort_key(entry[1], entry[0]))
    return [pair for _idx, pair in indexed]


def sort_objects_for_hit_testing(objects: dict[str, dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    """Returns (name, obj) pairs sorted from front to back (top to bottom for hit testing)."""
    rendering_order = sort_objects_for_rendering(objects)
    rendering_order.reverse()
    return rendering_order
