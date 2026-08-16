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
    "event.every_frame": "event_update",
    "physics.on_trigger_enter": "event_trigger_enter",
    "physics.on_trigger_exit": "event_trigger_exit",
    "physics.on_collision_enter": "event_collision_enter",
    "physics.on_collision_exit": "event_collision_exit",
    "logic.branch": "if_else",
    "logic.noop": "sequence",
    "variable.get": "get_variable",
    "variables.get": "get_variable",
    "variable.set": "set_variable",
    "variables.set": "set_variable",
    "math.add": "add_number",
    "math.subtract": "subtract_number",
    "math.multiply": "multiply_number",
    # PHASE 9 recovery item 16C. The three siblings above were mapped and this
    # one was not, which is the whole defect: divide_number exists, declares the
    # same a/b -> value contract, and has the same evaluator. Two graphs author
    # math.divide and both were left with a phantom node and orphan edges only
    # because of the omission.
    "math.divide": "divide_number",
    "math.clamp": "clamp_number",
    "audio.play_sound": "play_sound",
    "ui.update_label": "set_ui_text",
    "ui.update_progress": "set_ui_progress_bar",
    # Same family, second spelling. The line above already establishes
    # set_ui_progress_bar as the canonical target for the legacy ui.* progress
    # bar; BossHealthLogic and PlayerHealthLogic simply use the other name.
    "ui.set_progress_bar": "set_ui_progress_bar",
    "object.destroy": "destroy_object",
    "object.get_position": "get_position",
    "transform.get_position": "get_position",
    "physics.set_velocity": "move_by",
    "input.axis": "input_axis",
    "math.vector2_create": "vector2",
    "math.vector2_normalize": "normalize_vector",
    "math.sign": "sign_number",
    "math.vector2_magnitude": "magnitude_vector",
    "animator.set_parameter": "set_animator_parameter",
    # PHASE 9 recovery item 17. animator_set_trigger exists, has a runtime
    # executor and a declared exec/target/trigger_name contract; only the map
    # entry was missing, so every boss and enemy trigger resolved to a phantom
    # that silently did nothing. The neighbouring set_animator_parameter target
    # does NOT exist -- see the item 17 doc; that one is still debt.
    "animator.set_trigger": "animator_set_trigger",
    "input.keyboard_key_down": "key_pressed",
    "move.y": "move_y",
}

LEGACY_PORTS = {
    "out": "next",
    "frame": "next",
    "done": "next",
    "played": "next",
    "success": "next",
    "execute": "in",
    "true": "true",
    "false": "false",
    "result": "value",
    "normalized": "value",
    "magnitude": "value",
    "collider": "other",
    "in": "in",
}


def is_legacy_visual_script(data: Mapping[str, Any]) -> bool:
    format_name = str(data.get("format", "")).casefold()
    if format_name in {"zennity.generic_graph", "zennity.visual_script", "zscriptgraph"}:
        return True
    if str(data.get("type", "")).casefold() in {"visual_script", "visual scripting"}:
        return True
    for node in data.get("nodes", []):
        ntype = str(node.get("type", ""))
        if ntype.startswith("vs.") or ntype in LEGACY_NODE_TYPES:
            return True
    return False


def migrate_visual_script_graph(data: Mapping[str, Any]) -> dict[str, Any]:
    """Convert legacy nodes/connections while preserving unknown data in properties."""
    metadata = data.get("metadata", {}) if isinstance(data.get("metadata"), Mapping) else {}
    from .node_definitions import NODE_DEFINITIONS

    graph_name = str(data.get("name") or metadata.get("name") or "MigratedVisualScript")
    target_value = "Player"
    name_lower = graph_name.lower()
    if "boss" in name_lower:
        target_value = "Boss"
    elif "hud" in name_lower:
        target_value = "HUD"
    elif "canvas" in name_lower:
        target_value = "Canvas"
    elif "menu" in name_lower:
        target_value = "MenuUI"
    elif "enemy" in name_lower:
        target_value = "Enemy"
    elif "coin" in name_lower:
        target_value = "Coin"
    elif "key" in name_lower:
        target_value = "Key"
    elif "door" in name_lower:
        target_value = "Door"

    graph = {
        "format": "zennity.logic_graph",
        "version": 1,
        "enabled": True,
        "name": graph_name,
        "target": {"type": "name", "value": target_value},
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
        config = source.get("config", {})
        if isinstance(config, Mapping):
            properties.update(deepcopy(config))
        inputs = source.get("inputs", {})
        if isinstance(inputs, Mapping):
            properties.update(deepcopy(inputs))
        if "variable_name" in properties and "name" not in properties:
            properties["name"] = properties["variable_name"]
        if "element_name" in properties and "object_name" not in properties:
            properties["object_name"] = properties["element_name"]
        if "sound_name" in properties and "path" not in properties:
            properties["path"] = properties["sound_name"]
        node["properties"].update(properties)
        node["editor"]["legacy_type"] = source_type
        migrated_nodes.append(node)
    graph["nodes"] = migrated_nodes

    raw_edges = data.get("edges", data.get("connections", []))
    edges: list[dict[str, Any]] = []
    for source in raw_edges:
        if not isinstance(source, Mapping):
            continue
        from_node = str(source.get("from_node", source.get("source_node", source.get("from", ""))))
        to_node = str(source.get("to_node", source.get("target_node", source.get("to", ""))))
        if from_node not in known_ids or to_node not in known_ids:
            continue
        from_port = str(source.get("from_port", source.get("source_port", source.get("from_pin", "out"))))
        to_port = str(source.get("to_port", source.get("target_port", source.get("to_pin", "in"))))
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
