"""Canonical readers for the benchmark scenes, UI documents and logic graphs.

PHASE 13 item 13.1-B.

The Phase 8A suite was written against the pre-canonical schema: ``format`` and
``name`` at the root of a ``.zscene``, a flat ``widgets`` list in a ``.zui``, a
``ui`` mapping and a ``logic_graphs`` list directly on each object. 6a3fb0a7
migrated the scenes to the canonical format -- ``format_version``/``scene_name``
and ``components.items`` -- and kept the old files as ``*_legacy.zscene``.

The assertions that survived that migration are re-expressed through the readers
here, so a test says what it means about the game and stops encoding where the
loader happens to keep it. Two shapes in particular are not worth repeating in
every test:

* a component's fields may sit at its top level or under ``properties``. Both
  spellings are in the shipping scenes -- MainMenu nests ``ui_asset``, Victory
  does not -- and both load.
* a ``.zui`` is a tree of ``canvas`` children, not a flat list.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCENES = PROJECT_ROOT / "Assets" / "Scenes"
UI = PROJECT_ROOT / "Assets" / "UI"
LOGIC = PROJECT_ROOT / "Assets" / "Logic"


def load_scene(name: str) -> dict[str, Any]:
    """Read ``<name>.zscene``; ``name`` may include the suffix or not."""
    stem = name[:-len(".zscene")] if name.endswith(".zscene") else name
    return json.loads((SCENES / f"{stem}.zscene").read_text(encoding="utf-8"))


def load_ui(name: str) -> dict[str, Any]:
    stem = name[:-len(".zui")] if name.endswith(".zui") else name
    return json.loads((UI / f"{stem}.zui").read_text(encoding="utf-8"))


def load_logic(name: str) -> dict[str, Any]:
    stem = name[:-len(".zlogic")] if name.endswith(".zlogic") else name
    return json.loads((LOGIC / f"{stem}.zlogic").read_text(encoding="utf-8"))


def objects(scene: dict[str, Any]) -> list[dict[str, Any]]:
    return list(scene.get("objects", []))


def find_object(scene: dict[str, Any], name: str) -> dict[str, Any] | None:
    return next((obj for obj in objects(scene) if obj.get("name") == name), None)


def objects_named_like(scene: dict[str, Any], prefix: str) -> list[dict[str, Any]]:
    """Objects whose name starts with ``prefix``.

    The scenes number their instances -- ``Coin 1``, ``Enemy 3`` -- so an exact
    name match finds nothing.
    """
    return [obj for obj in objects(scene) if str(obj.get("name", "")).startswith(prefix)]


def components(obj: dict[str, Any]) -> list[dict[str, Any]]:
    container = obj.get("components")
    if isinstance(container, dict):
        return [c for c in container.get("items", []) if isinstance(c, dict)]
    if isinstance(container, list):
        return [c for c in container if isinstance(c, dict)]
    return []


def component(obj: dict[str, Any], component_type: str) -> dict[str, Any] | None:
    return next((c for c in components(obj) if c.get("type") == component_type), None)


def component_field(comp: dict[str, Any] | None, field: str) -> Any:
    """Read a component field from either spelling; see the module docstring."""
    if not comp:
        return None
    if comp.get(field) is not None:
        return comp[field]
    properties = comp.get("properties")
    if isinstance(properties, dict):
        return properties.get(field)
    return None


def ui_asset_of(obj: dict[str, Any] | None) -> str | None:
    if obj is None:
        return None
    return component_field(component(obj, "Canvas"), "ui_asset")


def logic_graph_paths(obj: dict[str, Any] | None) -> list[str]:
    """Every graph bound to an object, from both places a binding is stored.

    The editor writes the canonical ``LogicGraph`` component and also a
    ``logic_graphs`` shadow list; a scene may carry either or both.
    """
    if obj is None:
        return []
    found: list[str] = []
    for entry in obj.get("logic_graphs") or []:
        if isinstance(entry, dict) and entry.get("path"):
            found.append(str(entry["path"]))
    for comp in components(obj):
        if comp.get("type") == "LogicGraph":
            path = component_field(comp, "graph_path")
            if path:
                found.append(str(path))
    # Order-preserving de-duplication: the two stores overlap by design.
    return list(dict.fromkeys(found))


def _walk(node: Any) -> Iterator[dict[str, Any]]:
    if not isinstance(node, dict):
        return
    if node.get("name"):
        yield node
    for child in node.get("children") or []:
        yield from _walk(child)


def widgets(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Every named widget in a ``.zui``, flattened from the canvas tree."""
    return list(_walk(document.get("canvas")))


def widget_names(document: dict[str, Any]) -> list[str]:
    return [str(w["name"]) for w in widgets(document)]


def find_widget(document: dict[str, Any], name: str) -> dict[str, Any] | None:
    return next((w for w in widgets(document) if w.get("name") == name), None)


def node_types(graph: dict[str, Any]) -> set[str]:
    return {str(n.get("type")) for n in graph.get("nodes", [])}


def node_ids(graph: dict[str, Any]) -> set[str]:
    return {str(n.get("id")) for n in graph.get("nodes", [])}
