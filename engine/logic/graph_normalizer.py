"""Normalização e sanilização de dados para o Logic Graph."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from engine.logic.node_definitions.catalogue import resolve_node_id as _resolve_node_id
from engine.logic.port_aliases import flow_pins as _flow_pins
from engine.logic.port_aliases import resolve_input_port as _resolve_input_port
from engine.logic.port_aliases import resolve_node_output_port as _resolve_output_port

_log = logging.getLogger(__name__)


def _definition_pins(node_type: str, key: str) -> list:
    """Declared pins for *node_type*, empty when the type is unknown.

    An unknown type has no contract to resolve against, so its ports are left
    exactly as saved rather than guessed at.
    """
    return (NODE_DEFINITIONS.get(node_type) or {}).get(key, []) or []

try:
    from engine.logic.graph_asset import (
        LOGIC_GRAPH_FORMAT, LOGIC_GRAPH_VERSION, NODE_DEFINITIONS,
        _migrate_category, _safe_float, _safe_int, default_logic_graph,
        normalize_variable_definitions,
    )
except ImportError:  # Self-contained exported runtime.
    from .logic_graph_asset import (
        LOGIC_GRAPH_FORMAT, LOGIC_GRAPH_VERSION, NODE_DEFINITIONS,
        _migrate_category, _safe_float, _safe_int, default_logic_graph,
        normalize_variable_definitions,
    )


# Properties renomeadas ao longo da evolução da engine: a chave da esquerda é
# o nome legado gravado em assets antigos; a da direita é o nome atual (sempre
# alinhado ao pino de entrada correspondente, que é o que o executor lê).
# Sem esta migração o valor antigo virava lixo silencioso: normalize_logic_graph
# injeta o default da property nova, e o executor lê a nova -- então o texto que
# o usuário digitou no Inspector era simplesmente ignorado em tempo de execução.
_RENAMED_NODE_PROPERTIES: dict[str, dict[str, str]] = {
    "log_message": {"message": "text"},
    # PHASE 9 recovery item 4.2: the authoring property is "state". A graph
    # saved with "animation_name" is migrated here, once, at load -- the same
    # mechanism log_message already used, rather than a second fallback path.
    "play_animation": {"animation_name": "state"},
    # PHASE 9 recovery item 6: the declared pin is "slot_name" and the real
    # executors read it. The MainMenuLogic nodes were saved with "slot" by the
    # stub executor that has now been removed -- it invented its own property
    # name and defaulted to "autosave", so the slot an author picked in the
    # Inspector never reached the save system.
    "load_game": {"slot": "slot_name"},
    "has_save": {"slot": "slot_name"},
    "save_game": {"slot": "slot_name"},
    "delete_save": {"slot": "slot_name"},
}


def _migrate_renamed_properties(node_type: str, properties: Mapping[str, Any]) -> dict[str, Any]:
    """Renomeia properties legadas de *node_type*, preservando as atuais."""
    renames = _RENAMED_NODE_PROPERTIES.get(node_type)
    migrated = dict(properties)
    if not renames:
        return migrated
    for legacy_key, current_key in renames.items():
        if legacy_key in migrated and current_key not in migrated:
            migrated[current_key] = migrated.pop(legacy_key)
    return migrated


def normalize_logic_graph(data: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(data or {})
    result = default_logic_graph(str(source.get("name", "NewLogic")))
    result["enabled"] = bool(source.get("enabled", True))
    raw_target = source.get("target", {})
    if isinstance(raw_target, Mapping):
        target_type = str(raw_target.get("type", "name")).lower()
        result["target"] = {
            "type": target_type if target_type in {"name", "tag"} else "name",
            "value": str(raw_target.get("value", "Player")).strip() or "Player",
        }
    result["variables"] = normalize_variable_definitions(source.get("variables", {}))
    raw_editor_layout = source.get("editor", {})
    if not isinstance(raw_editor_layout, Mapping):
        raw_editor_layout = {}
    groups: list[dict[str, Any]] = []
    for raw_group in raw_editor_layout.get("groups", []):
        if not isinstance(raw_group, Mapping):
            continue
        position = raw_group.get("position", [0.0, 0.0])
        size = raw_group.get("size", [460.0, 280.0])
        if not isinstance(position, (list, tuple)) or len(position) < 2:
            position = [0.0, 0.0]
        if not isinstance(size, (list, tuple)) or len(size) < 2:
            size = [460.0, 280.0]
        groups.append({
            "id": str(raw_group.get("id", "")).strip() or uuid.uuid4().hex,
            "title": str(raw_group.get("title", "Group")).strip() or "Group",
            "position": [_safe_float(position[0]), _safe_float(position[1])],
            "size": [
                max(240.0, min(1600.0, _safe_float(size[0]) or 460.0)),
                max(140.0, min(1200.0, _safe_float(size[1]) or 280.0)),
            ],
            "color": str(raw_group.get("color", "#35506b")),
        })
    comments: list[dict[str, Any]] = []
    for raw_comment in raw_editor_layout.get("comments", []):
        if not isinstance(raw_comment, Mapping):
            continue
        position = raw_comment.get("position", [0.0, 0.0])
        if not isinstance(position, (list, tuple)) or len(position) < 2:
            position = [0.0, 0.0]
        comments.append({
            "id": str(raw_comment.get("id", "")).strip() or uuid.uuid4().hex,
            "text": str(raw_comment.get("text", "Comment")),
            "position": [_safe_float(position[0]), _safe_float(position[1])],
            "width": max(160.0, min(720.0, _safe_float(raw_comment.get("width", 260.0)) or 260.0)),
            "color": str(raw_comment.get("color", "#6b5b2f")),
        })
    result["editor"] = {"groups": groups, "comments": comments}
    for metadata_key in ("template", "migrated_from"):
        metadata_value = str(raw_editor_layout.get(metadata_key, "")).strip()
        if metadata_value:
            result["editor"][metadata_key] = metadata_value
    raw_debug = source.get("debug", {})
    raw_breakpoints = raw_debug.get("breakpoints", []) if isinstance(raw_debug, Mapping) else []
    raw_conditions = raw_debug.get("breakpoint_conditions", {}) if isinstance(raw_debug, Mapping) else {}
    raw_watches = raw_debug.get("watches", []) if isinstance(raw_debug, Mapping) else []
    result["debug"] = {
        "breakpoints": list(dict.fromkeys(str(value) for value in raw_breakpoints if str(value).strip()))
        if isinstance(raw_breakpoints, (list, tuple, set)) else [],
        "breakpoint_conditions": {
            str(node_id): str(expression).strip()
            for node_id, expression in raw_conditions.items()
            if str(node_id).strip() and str(expression).strip()
        } if isinstance(raw_conditions, Mapping) else {},
        "watches": list(dict.fromkeys(
            str(expression).strip() for expression in raw_watches if str(expression).strip()
        )) if isinstance(raw_watches, (list, tuple, set)) else [],
    }

    nodes: list[dict[str, Any]] = []
    node_ids: set[str] = set()
    # Node ids are resolved first, so port normalization below looks the pins up
    # on the definition the node actually resolved to. Doing it the other way
    # round would consult the wrong contract.
    node_types: dict[str, str] = {}
    raw_nodes = source.get("nodes", [])
    if isinstance(raw_nodes, list):
        for index, raw_node in enumerate(raw_nodes):
            if not isinstance(raw_node, Mapping):
                continue
            node_type = str(raw_node.get("type", "custom")).strip() or "custom"
            # PHASE 9 recovery item 2: legacy spellings (load_scene, quit_game,
            # button_clicked, set_ui_enabled) resolve to the id that owns the
            # definition, once, at load time -- so everything downstream, and
            # anything saved afterwards, only ever sees canonical ids.
            canonical_type = _resolve_node_id(node_type)
            if canonical_type != node_type:
                _log.debug("Legacy node id: %s -> %s", node_type, canonical_type)
                node_type = canonical_type
            definition = NODE_DEFINITIONS.get(node_type, {})
            node_id = str(raw_node.get("id", "")).strip() or uuid.uuid4().hex
            if node_id in node_ids:
                node_id = uuid.uuid4().hex
            node_ids.add(node_id)
            node_types[node_id] = node_type
            position = raw_node.get("position", [80.0 + (index % 4) * 230.0, 80.0 + (index // 4) * 130.0])
            if not isinstance(position, (list, tuple)) or len(position) < 2:
                position = [80.0, 80.0]
            properties = deepcopy(definition.get("properties", {}))
            for pin in definition.get("inputs", []):
                if isinstance(pin, (list, tuple)) and len(pin) >= 2:
                    pin_id, pin_type = str(pin[0]), str(pin[1])
                    if pin_type not in ("flow", "exec") and pin_id not in properties:
                        if pin_id == "widget_name":
                            properties[pin_id] = "comida"
                        elif pin_id == "variable_name":
                            properties[pin_id] = "comida"
                        elif pin_id == "property":
                            properties[pin_id] = "value"
                        elif pin_id == "target":
                            properties[pin_id] = ""
                        elif pin_type == "number":
                            properties[pin_id] = 0.0
                        elif pin_type == "bool":
                            properties[pin_id] = True
                        else:
                            properties[pin_id] = ""
            raw_properties = raw_node.get("properties", {})
            if isinstance(raw_properties, Mapping):
                properties.update(deepcopy(_migrate_renamed_properties(node_type, raw_properties)))
            raw_editor = raw_node.get("editor", {})
            if not isinstance(raw_editor, Mapping):
                raw_editor = {}
            editor_width = max(170.0, min(520.0, _safe_float(raw_editor.get("width", 210.0)) or 210.0))
            editor_height = max(0.0, min(720.0, _safe_float(raw_editor.get("height", 0.0))))
            nodes.append({
                "id": node_id,
                "type": node_type,
                "title": str(raw_node.get("title", definition.get("title", node_type))),
                "category": _migrate_category(str(raw_node.get("category", definition.get("category", "Custom")))),
                "position": [_safe_float(position[0]), _safe_float(position[1])],
                "editor": {
                    "collapsed": bool(raw_editor.get("collapsed", False)),
                    "width": editor_width,
                    "height": editor_height,
                },
                "properties": properties,
            })
    result["nodes"] = nodes
    result["debug"]["breakpoints"] = [node_id for node_id in result["debug"]["breakpoints"] if node_id in node_ids]
    result["debug"]["breakpoint_conditions"] = {
        node_id: expression
        for node_id, expression in result["debug"]["breakpoint_conditions"].items()
        if node_id in node_ids
    }

    edges: list[dict[str, Any]] = []
    raw_edges = source.get("edges", [])
    if isinstance(raw_edges, list):
        for edge_index, raw_edge in enumerate(raw_edges):
            if not isinstance(raw_edge, Mapping):
                continue
            source_node = str(raw_edge.get("from_node", raw_edge.get("from", "")))
            target_node = str(raw_edge.get("to_node", raw_edge.get("to", "")))
            if source_node not in node_ids or target_node not in node_ids or source_node == target_node:
                continue
            # PHASE 9 recovery item 5: legacy flow-port spellings resolve
            # against the target node's own contract, once, at load. There is no
            # global rename -- "in" is correct for 44 node types and wrong for 3,
            # so only the node's declaration can say which is which.
            raw_from = str(raw_edge.get("from_port", raw_edge.get("from_pin", "next")))
            raw_to = str(raw_edge.get("to_port", raw_edge.get("to_pin", "in")))
            from_port = _resolve_output_port(
                node_types.get(source_node, ""),
                raw_from,
                _flow_pins(_definition_pins(node_types.get(source_node, ""), "outputs")),
            )
            to_port = _resolve_input_port(
                raw_to, _flow_pins(_definition_pins(node_types.get(target_node, ""), "inputs"))
            )
            if from_port != raw_from:
                _log.debug("Legacy flow output: %s.%s -> %s",
                           node_types.get(source_node, "?"), raw_from, from_port)
            if to_port != raw_to:
                _log.debug("Legacy flow input: %s.%s -> %s",
                           node_types.get(target_node, "?"), raw_to, to_port)
            edges.append({
                "id": str(raw_edge.get("id", "")).strip() or uuid.uuid4().hex,
                "from_node": source_node,
                "from_port": from_port,
                "to_node": target_node,
                "to_port": to_port,
                "kind": str(raw_edge.get("kind", "flow")),
                "order": _safe_int(raw_edge.get("order", edge_index), edge_index),
            })
    result["edges"] = edges
    return result
