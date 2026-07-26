"""Lossless-enough migration from pre-1.0 visual-script documents to ``.zlogic``."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

LEGACY_NODE_TYPES = {
    "vs.event_on_start": "event_start",
    "vs.event_on_update": "event_update",
    "vs.if_else": "if_else",
    "vs.set_position": "set_position",
    "vs.log_message": "log_message",
}

LEGACY_PORTS = {
    "out": "next",
    "true": "true",
    "false": "false",
    "in": "in",
}


def is_legacy_visual_script(data: Mapping[str, Any]) -> bool:
    format_name = str(data.get("format", "")).casefold()
    return (
        format_name in {"zennity.generic_graph", "zennity.visual_script", "zscriptgraph"}
        or str(data.get("type", "")).casefold() in {"visual_script", "visual scripting"}
        or any(str(node.get("type", "")).startswith("vs.") for node in data.get("nodes", []))
    )


def migrate_visual_script_graph(data: Mapping[str, Any]) -> dict[str, Any]:
    """Convert legacy nodes/connections while preserving unknown data in properties."""
    metadata = data.get("metadata", {}) if isinstance(data.get("metadata"), Mapping) else {}
    from .node_definitions import NODE_DEFINITIONS

    graph = {
        "format": "zennity.logic_graph",
        "version": 1,
        "enabled": True,
        "name": str(data.get("name") or metadata.get("name") or "MigratedVisualScript"),
        "target": {"type": "name", "value": "Player"},
        "debug": {"breakpoints": [], "breakpoint_conditions": {}, "watches": []},
        "variables": {},
        "editor": {
            "groups": [],
            "comments": [],
            "migrated_from": str(data.get("format") or data.get("type") or "legacy"),
        },
        "nodes": [],
        "edges": [],
    }
    migrated_nodes: list[dict[str, Any]] = []
    known_ids: set[str] = set()
    for index, source in enumerate(data.get("nodes", [])):
        if not isinstance(source, Mapping):
            continue
        source_type = str(source.get("type", "custom"))
        node_type = LEGACY_NODE_TYPES.get(source_type, source_type.removeprefix("vs."))
        position = source.get("position", [80.0 + index * 240.0, 100.0])
        if isinstance(position, Mapping):
            position = [position.get("x", 0.0), position.get("y", 0.0)]
        definition = NODE_DEFINITIONS.get(node_type, {})
        node = {
            "id": uuid.uuid4().hex,
            "type": node_type,
            "title": str(definition.get("title", node_type)),
            "category": str(definition.get("category", "Custom")),
            "position": [float(position[0]), float(position[1])],
            "editor": {"collapsed": False, "width": 210.0, "height": 0.0},
            "properties": deepcopy(definition.get("properties", {})),
        }
        node["id"] = str(source.get("id") or uuid.uuid4().hex)
        known_ids.add(node["id"])
        properties = deepcopy(source.get("properties", {}))
        inputs = source.get("inputs", {})
        if isinstance(inputs, Mapping):
            properties.update(deepcopy(inputs))
        node["properties"].update(properties)
        node["editor"]["legacy_type"] = source_type
        migrated_nodes.append(node)
    graph["nodes"] = migrated_nodes

    raw_edges = data.get("edges", data.get("connections", []))
    edges: list[dict[str, Any]] = []
    for source in raw_edges:
        if not isinstance(source, Mapping):
            continue
        from_node = str(source.get("from_node", source.get("source_node", "")))
        to_node = str(source.get("to_node", source.get("target_node", "")))
        if from_node not in known_ids or to_node not in known_ids:
            continue
        from_port = str(source.get("from_port", source.get("source_port", "out")))
        to_port = str(source.get("to_port", source.get("target_port", "in")))
        edges.append({
            "id": str(source.get("id") or uuid.uuid4().hex),
            "from_node": from_node,
            "from_port": LEGACY_PORTS.get(from_port, from_port),
            "to_node": to_node,
            "to_port": LEGACY_PORTS.get(to_port, to_port),
            "kind": "flow" if from_port in {"out", "next", "true", "false"} else str(source.get("kind", "any")),
        })
    graph["edges"] = edges
    return graph


__all__ = ["LEGACY_NODE_TYPES", "is_legacy_visual_script", "migrate_visual_script_graph"]
