"""Normalização e sanitização de dados para o Logic Graph."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

try:
    from engine.logic.graph_asset import (
        NODE_DEFINITIONS, _migrate_category, _safe_float, _safe_int,
        default_logic_graph, normalize_variable_definitions,
    )
except ImportError:  # Self-contained exported runtime.
    from .logic_graph_asset import (
        NODE_DEFINITIONS, _migrate_category, _safe_float, _safe_int,
        default_logic_graph, normalize_variable_definitions,
    )


def normalize_logic_graph(data: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(data or {})
    result = default_logic_graph(str(source.get("name", "NewLogic")))
    result["enabled"] = bool(source.get("enabled", True))
    result["target"] = _normalize_target(source.get("target", {}))
    result["variables"] = normalize_variable_definitions(source.get("variables", {}))
    result["editor"] = _normalize_editor(source.get("editor", {}))
    result["debug"] = _normalize_debug(source.get("debug", {}))
    nodes, node_ids = _normalize_nodes(source.get("nodes", []))
    result["nodes"] = nodes
    _remove_unknown_debug_nodes(result["debug"], node_ids)
    result["edges"] = _normalize_edges(source.get("edges", []), node_ids)
    return result


def _normalize_target(raw_target: Any) -> dict[str, str]:
    if not isinstance(raw_target, Mapping):
        return {"type": "name", "value": "Player"}
    target_type = str(raw_target.get("type", "name")).lower()
    return {
        "type": target_type if target_type in {"name", "tag"} else "name",
        "value": str(raw_target.get("value", "Player")).strip() or "Player",
    }


def _normalize_editor(raw_editor: Any) -> dict[str, list[dict[str, Any]]]:
    source = raw_editor if isinstance(raw_editor, Mapping) else {}
    groups = [
        group for raw_group in source.get("groups", [])
        if (group := _normalize_group(raw_group)) is not None
    ]
    comments = [
        comment for raw_comment in source.get("comments", [])
        if (comment := _normalize_comment(raw_comment)) is not None
    ]
    return {"groups": groups, "comments": comments}


def _pair(value: Any, default: tuple[float, float]) -> tuple[Any, Any]:
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        return default
    return value[0], value[1]


def _normalize_group(raw_group: Any) -> dict[str, Any] | None:
    if not isinstance(raw_group, Mapping):
        return None
    x, y = _pair(raw_group.get("position"), (0.0, 0.0))
    width, height = _pair(raw_group.get("size"), (460.0, 280.0))
    return {
        "id": str(raw_group.get("id", "")).strip() or uuid.uuid4().hex,
        "title": str(raw_group.get("title", "Group")).strip() or "Group",
        "position": [_safe_float(x), _safe_float(y)],
        "size": [
            max(240.0, min(1600.0, _safe_float(width) or 460.0)),
            max(140.0, min(1200.0, _safe_float(height) or 280.0)),
        ],
        "color": str(raw_group.get("color", "#35506b")),
    }


def _normalize_comment(raw_comment: Any) -> dict[str, Any] | None:
    if not isinstance(raw_comment, Mapping):
        return None
    x, y = _pair(raw_comment.get("position"), (0.0, 0.0))
    width = _safe_float(raw_comment.get("width", 260.0)) or 260.0
    return {
        "id": str(raw_comment.get("id", "")).strip() or uuid.uuid4().hex,
        "text": str(raw_comment.get("text", "Comment")),
        "position": [_safe_float(x), _safe_float(y)],
        "width": max(160.0, min(720.0, width)),
        "color": str(raw_comment.get("color", "#6b5b2f")),
    }


def _normalize_debug(raw_debug: Any) -> dict[str, Any]:
    source = raw_debug if isinstance(raw_debug, Mapping) else {}
    breakpoints = source.get("breakpoints", [])
    conditions = source.get("breakpoint_conditions", {})
    watches = source.get("watches", [])
    return {
        "breakpoints": _unique_strings(breakpoints),
        "breakpoint_conditions": {
            str(node_id): str(expression).strip()
            for node_id, expression in conditions.items()
            if str(node_id).strip() and str(expression).strip()
        } if isinstance(conditions, Mapping) else {},
        "watches": _unique_strings(watches),
    }


def _unique_strings(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    return list(dict.fromkeys(
        str(value).strip() for value in values if str(value).strip()
    ))


def _normalize_nodes(raw_nodes: Any) -> tuple[list[dict[str, Any]], set[str]]:
    nodes: list[dict[str, Any]] = []
    node_ids: set[str] = set()
    if not isinstance(raw_nodes, list):
        return nodes, node_ids
    for index, raw_node in enumerate(raw_nodes):
        node = _normalize_node(raw_node, index, node_ids)
        if node is not None:
            nodes.append(node)
            node_ids.add(node["id"])
    return nodes, node_ids


def _normalize_node(
    raw_node: Any, index: int, node_ids: set[str],
) -> dict[str, Any] | None:
    if not isinstance(raw_node, Mapping):
        return None
    node_type = str(raw_node.get("type", "custom")).strip() or "custom"
    definition = NODE_DEFINITIONS.get(node_type, {})
    node_id = str(raw_node.get("id", "")).strip() or uuid.uuid4().hex
    if node_id in node_ids:
        node_id = uuid.uuid4().hex
    default_position = (80.0 + (index % 4) * 230.0, 80.0 + (index // 4) * 130.0)
    raw_position = raw_node.get("position", default_position)
    x, y = _pair(raw_position, (80.0, 80.0))
    properties = deepcopy(definition.get("properties", {}))
    raw_properties = raw_node.get("properties", {})
    if isinstance(raw_properties, Mapping):
        properties.update(deepcopy(raw_properties))
    raw_editor = raw_node.get("editor", {})
    editor = raw_editor if isinstance(raw_editor, Mapping) else {}
    return {
        "id": node_id,
        "type": node_type,
        "title": str(raw_node.get("title", definition.get("title", node_type))),
        "category": _migrate_category(
            str(raw_node.get("category", definition.get("category", "Custom")))
        ),
        "position": [_safe_float(x), _safe_float(y)],
        "editor": {
            "collapsed": bool(editor.get("collapsed", False)),
            "width": max(170.0, min(520.0, _safe_float(editor.get("width", 210.0)) or 210.0)),
            "height": max(0.0, min(720.0, _safe_float(editor.get("height", 0.0)))),
        },
        "properties": properties,
    }


def _remove_unknown_debug_nodes(debug: dict[str, Any], node_ids: set[str]) -> None:
    debug["breakpoints"] = [
        node_id for node_id in debug["breakpoints"] if node_id in node_ids
    ]
    debug["breakpoint_conditions"] = {
        node_id: expression
        for node_id, expression in debug["breakpoint_conditions"].items()
        if node_id in node_ids
    }


def _normalize_edges(raw_edges: Any, node_ids: set[str]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    if not isinstance(raw_edges, list):
        return edges
    for index, raw_edge in enumerate(raw_edges):
        if not isinstance(raw_edge, Mapping):
            continue
        source = str(raw_edge.get("from_node", ""))
        target = str(raw_edge.get("to_node", ""))
        if source not in node_ids or target not in node_ids or source == target:
            continue
        edges.append({
            "id": str(raw_edge.get("id", "")).strip() or uuid.uuid4().hex,
            "from_node": source,
            "from_port": str(raw_edge.get("from_port", "next")),
            "to_node": target,
            "to_port": str(raw_edge.get("to_port", "in")),
            "kind": str(raw_edge.get("kind", "flow")),
            "order": _safe_int(raw_edge.get("order", index), index),
        })
    return edges
