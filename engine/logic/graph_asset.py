"""Persistent format for visual logic graphs.

This module is deliberately independent of Qt and Pygame. The editor handles
appearance, while the future runtime can execute the same document.
"""

from __future__ import annotations

import json
import importlib
import unicodedata
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

try:
    from .prefab_asset import parameter_port, port_type
except ImportError:
    from engine.prefabs.prefab_asset import parameter_port, port_type

try:
    from .blackboard import normalize_variable_definitions
except ImportError:  # Self-contained exported runtime.
    from .logic_blackboard import normalize_variable_definitions


# ---------------------------------------------------------------------------
# Category migration — converts legacy Portuguese category names to English.
# Called automatically by normalize_logic_graph so that old .zlogic files
# are transparently updated on next save without any manual intervention.
# ---------------------------------------------------------------------------

_CATEGORY_MIGRATIONS: dict[str, str] = {
    # Action
    "acao": "Action", "ação": "Action",
    # Condition
    "condicao": "Condition", "condição": "Condition",
    # Events
    "eventos": "Events",
    # Logic
    "logica": "Logic", "lógica": "Logic",
    # Math
    "matematica": "Math", "matemática": "Math",
    # Movement
    "movimento": "Movement",
    # Objects
    "objetos": "Objects",
    # Position
    "posicao": "Position", "posição": "Position",
    # Subgraphs
    "subgrafos": "Subgraphs",
    # Text
    "texto": "Text",
    # Variables
    "variaveis": "Variables", "variáveis": "Variables",
}


def _migrate_category(raw: str) -> str:
    """Return the canonical English category name, migrating legacy Portuguese."""
    stripped = raw.strip()
    # Normalize to ASCII lowercase for lookup (handles accented variants).
    key = unicodedata.normalize("NFD", stripped).encode("ascii", "ignore").decode().lower()
    return _CATEGORY_MIGRATIONS.get(key, stripped) or stripped


LOGIC_GRAPH_FORMAT = "zennity.logic_graph"
LOGIC_GRAPH_VERSION = 1

UNIQUE_EVENT_TYPES = {
    "event_start", "event_update", "event_collision_enter", "event_collision_exit",
    "event_trigger_enter", "event_trigger_exit", "event_object_created",
}

try:
    from engine.logic.node_definitions import NODE_DEFINITIONS
except ImportError:  # Self-contained exported runtime.
    from .node_definitions import NODE_DEFINITIONS

NODE_PORT_DEFINITIONS: dict[str, dict[str, list[tuple[str, str]]]] = {
    "event_start": {"inputs": [], "outputs": [("next", "flow")]},
    "event_update": {"inputs": [], "outputs": [("next", "flow")]},
    "event_custom": {"inputs": [], "outputs": [("next", "flow"), ("payload", "any")]},
    "event_collision_enter": {"inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_collision_exit": {"inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_trigger_enter": {"inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_trigger_exit": {"inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_timer": {"inputs": [], "outputs": [("next", "flow")]},
    "event_key_pressed": {"inputs": [], "outputs": [("next", "flow")]},
    "ui.button_clicked": {"inputs": [], "outputs": [("next", "flow"), ("widget", "text")]},
    "button_clicked": {"inputs": [], "outputs": [("next", "flow"), ("widget", "text")]},
    "on_ui_click": {"inputs": [], "outputs": [("next", "flow"), ("widget", "text")]},
    "event_object_created": {"inputs": [], "outputs": [("next", "flow"), ("object", "object")]},
    "self_object": {"inputs": [], "outputs": [("object", "object")]},
    "find_tag": {"inputs": [("in", "flow")], "outputs": [("next", "flow"), ("object", "object")]},
    "find_nearest_object": {
        "inputs": [("exec", "flow"), ("tag", "text"), ("max_distance", "number")],
        "outputs": [("exec_found", "flow"), ("exec_none", "flow"), ("object", "object"), ("distance", "number")],
    },
    "get_tag": {"inputs": [("target", "object")], "outputs": [("value", "text")]},
    "get_object_name": {"inputs": [("target", "object")], "outputs": [("value", "text")]},
    "get_prefab_parameter": {"inputs": [("target", "object")], "outputs": [("value", "any")]},
    "create_object": {
        "inputs": [("in", "flow"), ("source", "object"), ("name", "text"), ("x", "number"), ("y", "number")],
        "outputs": [("next", "flow"), ("limit_reached", "flow"), ("object", "object")],
    },
    "create_prefab": {
        "inputs": [
            ("in", "flow"), ("x", "number"), ("y", "number"),
            ("rotation", "number"), ("width", "number"), ("height", "number"),
        ],
        "outputs": [("next", "flow"), ("limit_reached", "flow"), ("object", "object")],
    },
    "clone_object": {"inputs": [("in", "flow"), ("target", "object"), ("name", "text")], "outputs": [("next", "flow"), ("limit_reached", "flow"), ("object", "object")]},
    "add_component": {"inputs": [("in", "flow"), ("target", "object")], "outputs": [("next", "flow")]},
    "remove_component": {"inputs": [("in", "flow"), ("target", "object")], "outputs": [("next", "flow")]},
    "input_axis": {"inputs": [("in", "flow")], "outputs": [("next", "flow"), ("value", "number")]},
    "move": {"inputs": [("in", "flow"), ("value", "number")], "outputs": [("next", "flow")]},
    "jump": {"inputs": [("in", "flow"), ("force", "number")], "outputs": [("next", "flow")]},
    "get_position": {"inputs": [("target", "object")], "outputs": [("x", "number"), ("y", "number")]},
    "move_by": {"inputs": [("in", "flow"), ("target", "object"), ("x", "number"), ("y", "number")], "outputs": [("next", "flow")]},
    "start_continuous_motion": {
        "inputs": [("in", "flow"), ("target", "object"), ("x", "number"), ("y", "number")],
        "outputs": [("next", "flow"), ("movement", "movement")],
    },
    "update_continuous_motion": {
        "inputs": [("in", "flow"), ("target", "object"), ("movement", "movement"), ("x", "number"), ("y", "number")],
        "outputs": [("next", "flow")],
    },
    "pause_continuous_motion": {"inputs": [("in", "flow"), ("target", "object"), ("movement", "movement")], "outputs": [("next", "flow")]},
    "resume_continuous_motion": {"inputs": [("in", "flow"), ("target", "object"), ("movement", "movement")], "outputs": [("next", "flow")]},
    "stop_continuous_motion": {"inputs": [("in", "flow"), ("target", "object"), ("movement", "movement")], "outputs": [("next", "flow")]},
    "get_continuous_motion": {
        "inputs": [("in", "flow"), ("target", "object"), ("movement", "movement")],
        "outputs": [
            ("next", "flow"), ("x", "number"), ("y", "number"), ("speed", "number"),
            ("paused", "bool"), ("active", "bool"),
        ],
    },
    "patrol_axis": {"inputs": [("in", "flow"), ("target", "object"), ("minimum", "number"), ("maximum", "number"), ("speed", "number")], "outputs": [("next", "flow"), ("direction", "number"), ("position", "number")]},
    "if_else": {"inputs": [("in", "flow"), ("condition", "any")], "outputs": [("true", "flow"), ("false", "flow")]},
    "sequence": {"inputs": [("in", "flow")], "outputs": [("then_0", "flow"), ("then_1", "flow"), ("next", "flow")]},
    "once": {"inputs": [("in", "flow")], "outputs": [("next", "flow"), ("blocked", "flow")]},
    "cooldown": {"inputs": [("in", "flow"), ("seconds", "number")], "outputs": [("next", "flow"), ("blocked", "flow")]},
    "and": {"inputs": [("a", "bool"), ("b", "bool")], "outputs": [("value", "bool")]},
    "or": {"inputs": [("a", "bool"), ("b", "bool")], "outputs": [("value", "bool")]},
    "not": {"inputs": [("value", "bool")], "outputs": [("value", "bool")]},
    "key_pressed": {"inputs": [("in", "flow")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "key_held": {"inputs": [("in", "flow")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "is_grounded": {"inputs": [("in", "flow")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "compare_number": {"inputs": [("in", "flow"), ("value", "number")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "compare_text": {"inputs": [("in", "flow"), ("value", "text"), ("other", "text")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "play_animation": {"inputs": [("in", "flow"), ("target", "object"), ("state", "text")], "outputs": [("next", "flow"), ("exec_failure", "flow")]},
    "play_animation_asset": {"inputs": [("in", "flow"), ("path", "text")], "outputs": [("next", "flow")]},
    "stop_animation": {"inputs": [("in", "flow"), ("target", "object")], "outputs": [("next", "flow"), ("exec_failure", "flow")]},
    "play_sound": {"inputs": [("in", "flow"), ("path", "text")], "outputs": [("next", "flow")]},
    "set_ui_text": {"inputs": [("in", "flow"), ("text", "text")], "outputs": [("next", "flow")]},
    "set_ui_progress_bar": {"inputs": [("in", "flow"), ("value", "number")], "outputs": [("next", "flow")]},
    "get_ui_widget_property": {"inputs": [("in", "flow"), ("widget_name", "text"), ("property", "text")], "outputs": [("next", "flow"), ("value", "text")]},
    "get_progress_bar_value": {"inputs": [("in", "flow"), ("widget_name", "text")], "outputs": [("next", "flow"), ("value", "number")]},
    "bind_ui_to_variable": {"inputs": [("in", "flow"), ("widget_name", "text"), ("variable_name", "text"), ("property", "text")], "outputs": [("next", "flow"), ("exec_success", "flow"), ("exec_not_found", "flow"), ("exec_failure", "flow")]},
    "update_ui_binding": {"inputs": [("in", "flow"), ("widget_name", "text"), ("variable_name", "text"), ("property", "text")], "outputs": [("next", "flow"), ("exec_success", "flow"), ("exec_not_found", "flow"), ("exec_failure", "flow")]},
    "update_ui_widget_property": {"inputs": [("in", "flow"), ("parent", "text"), ("widget_name", "text"), ("property", "text"), ("value", "any")], "outputs": [("success", "flow"), ("failure", "flow")]},
    "set_sprite": {"inputs": [("in", "flow"), ("target", "object"), ("path", "text")], "outputs": [("next", "flow")]},
    "start_texture_scroll": {
        "inputs": [
            ("in", "flow"), ("target", "object"), ("path", "text"),
            ("speed_x", "number"), ("speed_y", "number"),
        ],
        "outputs": [("next", "flow")],
    },
    "stop_texture_scroll": {"inputs": [("in", "flow"), ("target", "object")], "outputs": [("next", "flow")]},
    "set_hud": {"inputs": [("in", "flow"), ("text", "text")], "outputs": [("next", "flow")]},
    "emit_event": {"inputs": [("in", "flow"), ("payload", "any")], "outputs": [("next", "flow")]},
    "set_position": {"inputs": [("in", "flow"), ("target", "object"), ("x", "number"), ("y", "number")], "outputs": [("next", "flow")]},
    "rotate": {"inputs": [("in", "flow"), ("target", "object"), ("degrees", "number")], "outputs": [("next", "flow")]},
    "set_active": {"inputs": [("in", "flow"), ("target", "object"), ("active", "bool")], "outputs": [("next", "flow")]},
    "destroy_object": {"inputs": [("in", "flow"), ("target", "object")], "outputs": []},
    "destroy_after_time": {"inputs": [("in", "flow"), ("target", "object"), ("seconds", "number")], "outputs": [("next", "flow")]},
    "restart_scene": {"inputs": [("in", "flow")], "outputs": []},
    "log_message": {"inputs": [("in", "flow"), ("text", "text")], "outputs": [("next", "flow")]},
    "subgraph_start": {"inputs": [], "outputs": [("next", "flow")]},
    "subgraph_input": {"inputs": [], "outputs": [("value", "any")]},
    "subgraph_return": {"inputs": [("in", "flow"), ("value", "any")], "outputs": []},
    "call_subgraph": {"inputs": [("in", "flow")], "outputs": [("next", "flow")]},
    "vector2": {"inputs": [("x", "number"), ("y", "number")], "outputs": [("vector", "vector2"), ("value", "vector2")]},
    "normalize_vector": {"inputs": [("vector", "vector2")], "outputs": [("value", "vector2")]},
    "magnitude_vector": {"inputs": [("vector", "vector2")], "outputs": [("value", "number")]},
    "sign_number": {"inputs": [("value", "number")], "outputs": [("value", "number")]},
    "move_by": {"inputs": [("in", "flow"), ("velocity", "vector2"), ("delta_x", "number"), ("delta_y", "number"), ("x", "number"), ("y", "number")], "outputs": [("next", "flow")]},
    "move_x": {"inputs": [("in", "flow"), ("target", "object"), ("speed", "number"), ("x", "number")], "outputs": [("next", "flow"), ("movement", "movement")]},
    "move_y": {"inputs": [("in", "flow"), ("target", "object"), ("speed", "number"), ("y", "number")], "outputs": [("next", "flow"), ("movement", "movement")]},
    "move_towards": {"inputs": [("in", "flow"), ("target", "object"), ("destination_x", "number"), ("destination_y", "number"), ("speed", "number")], "outputs": [("next", "flow"), ("handle", "movement")]},
    "set_animator_parameter": {"inputs": [("in", "flow"), ("value", "any")], "outputs": [("next", "flow")]},
    "input_axis": {"inputs": [("in", "flow")], "outputs": [("next", "flow"), ("value", "number")]},
    "get_variable": {"inputs": [("in", "flow")], "outputs": [("next", "flow"), ("value", "any")]},
    "set_variable": {"inputs": [("in", "flow"), ("value", "any")], "outputs": [("next", "flow")]},
    "number_value": {"inputs": [], "outputs": [("value", "number")]},
    "bool_value": {"inputs": [], "outputs": [("value", "bool")]},
    "text_value": {"inputs": [], "outputs": [("value", "text")]},
    "add_number": {"inputs": [("a", "number"), ("b", "number")], "outputs": [("value", "number")]},
    "subtract_number": {"inputs": [("a", "number"), ("b", "number")], "outputs": [("value", "number")]},
    "multiply_number": {"inputs": [("a", "number"), ("b", "number")], "outputs": [("value", "number")]},
    "divide_number": {"inputs": [("a", "number"), ("b", "number")], "outputs": [("value", "number")]},
    "absolute_number": {"inputs": [("value", "number")], "outputs": [("value", "number")]},
    "clamp_number": {"inputs": [("value", "number"), ("minimum", "number"), ("maximum", "number")], "outputs": [("value", "number")]},
    "random_number": {"inputs": [("minimum", "number"), ("maximum", "number")], "outputs": [("value", "number")]},
    "delta_time": {"inputs": [], "outputs": [("value", "number")]},
    "join_text": {"inputs": [("a", "any"), ("b", "any")], "outputs": [("value", "text")]},
    "to_text": {"inputs": [("value", "any")], "outputs": [("value", "text")]},
}

# Keep extracted declarative definitions aligned with the public graph contract.
for _node_type, _definition in NODE_DEFINITIONS.items():
    _definition["category"] = _migrate_category(str(_definition.get("category", "Custom")))
    NODE_PORT_DEFINITIONS.setdefault(
        _node_type,
        {
            "inputs": list(_definition.get("inputs", [])),
            "outputs": list(_definition.get("outputs", [])),
        },
    )
    _props = _definition.setdefault("properties", {})
    for _pin in _definition.get("inputs", []):
        if isinstance(_pin, (list, tuple)) and len(_pin) >= 2:
            _pin_id, _pin_type = str(_pin[0]), str(_pin[1])
            if _pin_type not in ("flow", "exec") and _pin_id not in _props:
                if _pin_id == "widget_name":
                    _props[_pin_id] = "comida"
                elif _pin_id == "variable_name":
                    _props[_pin_id] = "comida"
                elif _pin_id == "property":
                    _props[_pin_id] = "value"
                elif _pin_id == "target":
                    _props[_pin_id] = ""
                elif _pin_type == "number":
                    _props[_pin_id] = 0.0
                elif _pin_type == "bool":
                    _props[_pin_id] = True
                else:
                    _props[_pin_id] = ""

NODE_DEFINITIONS["key_pressed"].update(
    title="Key Pressed Now?", category="Condition", properties={"key": "SPACE"}
)
NODE_DEFINITIONS["key_held"].update(title="Key Held?", category="Condition")
NODE_PORT_DEFINITIONS.setdefault(
    "key_pressed",
    {"inputs": [("in", "flow")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
)

# These four fall back to the declarative NodeDefinition classes, which name their
# flow output ``exec_done``. Every graph and every other node here uses ``next``,
# and the runtime matches the edge's port name literally, so the fallback left the
# flow dead. Pin the contract to the convention that is actually in use.
NODE_PORT_DEFINITIONS["read_key_axis"] = {
    "inputs": [("in", "flow")], "outputs": [("next", "flow"), ("value", "number")],
}
NODE_PORT_DEFINITIONS["set_ui_visible"] = {
    "inputs": [("in", "flow"), ("visible", "bool")], "outputs": [("next", "flow")],
}
NODE_PORT_DEFINITIONS["bind_ui_to_blackboard"] = {
    "inputs": [("in", "flow")], "outputs": [("next", "flow")],
}
NODE_PORT_DEFINITIONS["start_behavior_tree"] = {
    "inputs": [("in", "flow"), ("path", "text")],
    "outputs": [("next", "flow"), ("exec_failure", "flow")],
}

# Explicit editor/runtime contracts for object creation and inspector components.
# Keeping defaults here makes newly created nodes immediately editable and ensures
# exported graphs remain self-contained.
NODE_DEFINITIONS["create_object"].setdefault("properties", {}).update({
    "name": "Object", "x": 0.0, "y": 0.0, "width": 32.0, "height": 32.0,
    "color": "#4c9aff", "texture": "", "tag": "", "relative": True,
    "inherit_source": True, "inherit_logic": False, "lifetime": 0.0,
    "max_instances": 0, "max_distance": 0.0, "use_pool": False,
})
NODE_DEFINITIONS["start_continuous_motion"].setdefault("properties", {}).update({
    "movement": "Movement", "x": 100.0, "y": 0.0, "space": "global",
    "acceleration": 0.0, "deceleration": 0.0,
})
NODE_DEFINITIONS["number_value"].setdefault("properties", {})["value"] = 0.0
NODE_DEFINITIONS["bool_value"].setdefault("properties", {})["value"] = True
NODE_DEFINITIONS["text_value"].setdefault("properties", {})["value"] = ""

_COMPONENT_NODE_DEFAULTS = {
    "add_sprite_renderer": {"texture": "", "color": "#ffffff", "sort_order": 0},
    "add_animator": {"controller": "", "autoplay": True},
    "add_rigidbody": {"body_type": "dynamic", "mass": 1.0, "gravity_scale": 1.0},
    "add_box_collider": {"width": 32.0, "height": 32.0, "is_trigger": False},
    "add_circle_collider": {"radius": 16.0, "is_trigger": False},
    "add_camera": {"background_color": [22, 24, 31], "zoom": 1.0, "active": True},
    "add_audio_source": {"path": "", "volume": 1.0, "loop": False, "autoplay": False},
    "add_ui_canvas": {"sort_order": 0},
    "add_ui_text": {"text": "Text", "color": "#ffffff", "font_size": 24},
    "add_ui_image": {"texture": "", "color": "#ffffff"},
    "add_ui_button": {"text": "Button", "color": "#4c9aff"},
}
for _node_type, _properties in _COMPONENT_NODE_DEFAULTS.items():
    NODE_DEFINITIONS[_node_type] = {
        "title": _node_type.removeprefix("add_").replace("_", " ").title(),
        "category": "Components",
        "inputs": [("in", "flow"), ("target", "object")],
        "outputs": [("next", "flow")],
        "properties": _properties,
    }
    NODE_PORT_DEFINITIONS[_node_type] = {
        "inputs": [("in", "flow"), ("target", "object")],
        "outputs": [("next", "flow")],
    }


def node_port_definitions(node_type: str | Mapping[str, Any]) -> dict[str, list[tuple[str, str]]]:
    """Return copies of a node type's ports with a compatible fallback."""
    node = node_type if isinstance(node_type, Mapping) else None
    type_name = str(node.get("type", "")) if node is not None else str(node_type)
    definition = NODE_PORT_DEFINITIONS.get(type_name)
    if definition is None:
        declarative = NODE_DEFINITIONS.get(type_name, {})
        definition = {
            "inputs": list(declarative.get("inputs", [("in", "flow")])),
            "outputs": list(declarative.get("outputs", [("next", "flow")])),
        }
    ports = {
        "inputs": list(definition.get("inputs", [])),
        "outputs": list(definition.get("outputs", [])),
    }
    if node is None:
        return ports
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}
    value_type = _safe_port_type(properties.get("type", "any"))
    if type_name == "sequence":
        try:
            output_count = int(properties.get("outputs", 2))
        except (TypeError, ValueError):
            output_count = 2
        output_count = max(1, min(32, output_count))
        ports["outputs"] = [(f"then_{index}", "flow") for index in range(output_count)]
        ports["outputs"].append(("next", "flow"))
    elif type_name == "create_prefab":
        exposed = properties.get("exposed_properties", [])
        if isinstance(exposed, list):
            for definition in exposed:
                if not isinstance(definition, Mapping) or not str(definition.get("name", "")).strip():
                    continue
                port = str(definition.get("port", parameter_port(str(definition["name"]))))
                if port not in {name for name, _kind in ports["inputs"]}:
                    ports["inputs"].append((port, port_type(str(definition.get("type", "text")))))
    elif type_name == "get_prefab_parameter":
        ports["outputs"] = [("value", port_type(str(properties.get("type", "text"))))]
    elif type_name == "subgraph_input":
        ports["outputs"] = [("value", value_type)]
    elif type_name == "subgraph_return":
        ports["inputs"] = [("in", "flow"), ("value", value_type)]
    elif type_name == "call_subgraph":
        ports["inputs"].extend(_declared_interface_ports(properties.get("inputs")))
        ports["outputs"].extend(_declared_interface_ports(properties.get("outputs")))
    return ports


def subgraph_interface(data: Mapping[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    """Derive the public interface from input and return nodes."""
    graph = normalize_logic_graph(data)
    inputs: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    for node in graph["nodes"]:
        properties = node.get("properties", {})
        if node["type"] == "subgraph_input":
            inputs.append({
                "name": str(properties.get("name", "input")).strip(),
                "type": _safe_port_type(properties.get("type", "any")),
                "default": deepcopy(properties.get("default")),
            })
        elif node["type"] == "subgraph_return":
            outputs.append({
                "name": str(properties.get("name", "result")).strip(),
                "type": _safe_port_type(properties.get("type", "any")),
            })
    return {"inputs": inputs, "outputs": outputs}


def default_logic_graph(name: str = "NewLogic") -> dict[str, Any]:
    return {
        "format": LOGIC_GRAPH_FORMAT,
        "version": LOGIC_GRAPH_VERSION,
        "enabled": True,
        "name": str(name).strip() or "NewLogic",
        "target": {"type": "name", "value": "Player"},
        "debug": {"breakpoints": [], "breakpoint_conditions": {}, "watches": []},
        "variables": {},
        "editor": {"groups": [], "comments": []},
        "nodes": [],
        "edges": [],
    }


def create_logic_node(node_type: str, position: tuple[float, float] = (0.0, 0.0)) -> dict[str, Any]:
    definition = NODE_DEFINITIONS.get(str(node_type), {})
    return {
        "id": uuid.uuid4().hex,
        "type": str(node_type),
        "title": str(definition.get("title", node_type)),
        "category": str(definition.get("category", "Custom")),
        "position": [float(position[0]), float(position[1])],
        "editor": {"collapsed": False, "width": 210.0, "height": 0.0},
        "properties": deepcopy(definition.get("properties", {})),
    }


def normalize_logic_graph(data: Mapping[str, Any] | None) -> dict[str, Any]:
    module_name = "engine.logic.graph_normalizer" if __package__ == "engine.logic" else f"{__package__}.graph_normalizer"
    _norm = importlib.import_module(module_name).normalize_logic_graph
    return _norm(data)


def _event_identity(node: Mapping[str, Any]) -> tuple[str, str] | None:
    node_type = str(node.get("type", ""))
    if node_type in UNIQUE_EVENT_TYPES:
        return node_type, ""
    if node_type == "event_custom":
        return node_type, str(node.get("properties", {}).get("name", "event")).strip().casefold()
    if node_type == "event_key_pressed":
        return node_type, str(node.get("properties", {}).get("key", "D")).strip().casefold()
    return None


def consolidate_logic_events(data: Mapping[str, Any] | None) -> tuple[dict[str, Any], int]:
    """Merge equivalent events and preserve all outgoing branches."""
    graph = normalize_logic_graph(data)
    canonical: dict[tuple[str, str], str] = {}
    remap: dict[str, str] = {}
    nodes: list[dict[str, Any]] = []
    removed = 0
    for node in graph["nodes"]:
        identity = _event_identity(node)
        if identity is not None and identity in canonical:
            remap[str(node["id"])] = canonical[identity]
            removed += 1
            continue
        if identity is not None:
            canonical[identity] = str(node["id"])
        nodes.append(node)
    graph["nodes"] = nodes
    debug = graph.setdefault("debug", {})
    debug["breakpoints"] = list(dict.fromkeys(
        remap.get(str(node_id), str(node_id)) for node_id in debug.get("breakpoints", [])
    ))
    conditions = debug.get("breakpoint_conditions", {})
    if isinstance(conditions, Mapping):
        debug["breakpoint_conditions"] = {
            remap.get(str(node_id), str(node_id)): str(expression)
            for node_id, expression in conditions.items()
        }
    signatures: set[tuple[str, str, str, str, str]] = set()
    edges: list[dict[str, Any]] = []
    for source in graph["edges"]:
        edge = deepcopy(source)
        edge["from_node"] = remap.get(str(edge["from_node"]), str(edge["from_node"]))
        edge["to_node"] = remap.get(str(edge["to_node"]), str(edge["to_node"]))
        if edge["from_node"] == edge["to_node"]:
            continue
        signature = (
            str(edge["from_node"]), str(edge.get("from_port", "next")),
            str(edge["to_node"]), str(edge.get("to_port", "in")), str(edge.get("kind", "flow")),
        )
        if signature in signatures:
            continue
        signatures.add(signature)
        edges.append(edge)
    graph["edges"] = edges
    return normalize_logic_graph(graph), removed


def merge_logic_fragment(
    data: Mapping[str, Any] | None,
    fragment: Mapping[str, Any],
) -> tuple[dict[str, Any], int]:
    """Insert a recipe reusing unique events that already exist in the graph."""
    graph, consolidated = consolidate_logic_events(data)
    identities = {
        identity: str(node["id"])
        for node in graph["nodes"]
        if (identity := _event_identity(node)) is not None
    }
    remap: dict[str, str] = {}
    reused = consolidated
    for source in fragment.get("nodes", []):
        node = deepcopy(source)
        identity = _event_identity(node)
        if identity is not None and identity in identities:
            remap[str(node["id"])] = identities[identity]
            reused += 1
            continue
        graph["nodes"].append(node)
        if identity is not None:
            identities[identity] = str(node["id"])
    signatures = {
        (str(edge["from_node"]), str(edge.get("from_port", "next")), str(edge["to_node"]), str(edge.get("to_port", "in")), str(edge.get("kind", "flow")))
        for edge in graph["edges"]
    }
    for source in fragment.get("edges", []):
        edge = deepcopy(source)
        edge["from_node"] = remap.get(str(edge["from_node"]), str(edge["from_node"]))
        edge["to_node"] = remap.get(str(edge["to_node"]), str(edge["to_node"]))
        signature = (
            str(edge["from_node"]), str(edge.get("from_port", "next")),
            str(edge["to_node"]), str(edge.get("to_port", "in")), str(edge.get("kind", "flow")),
        )
        if edge["from_node"] != edge["to_node"] and signature not in signatures:
            signatures.add(signature)
            graph["edges"].append(edge)
    return normalize_logic_graph(graph), reused


def validate_logic_graph(data: Mapping[str, Any] | None) -> list[dict[str, str]]:
    module_name = "engine.logic.graph_validator" if __package__ == "engine.logic" else f"{__package__}.graph_validator"
    _validate = importlib.import_module(module_name).validate_logic_graph
    return _validate(data)


def load_logic_graph(path: str | Path) -> dict[str, Any]:
    graph_path = Path(path)
    raw = json.loads(graph_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("The Logic Graph must contain a JSON object.")
    from engine.logic.legacy_visual_script import is_legacy_visual_script, migrate_visual_script_graph
    if is_legacy_visual_script(raw):
        return migrate_visual_script_graph(raw)
    if raw.get("format", LOGIC_GRAPH_FORMAT) != LOGIC_GRAPH_FORMAT:
        raise ValueError("Unrecognized Logic Graph format.")
    return normalize_logic_graph(raw)


def save_logic_graph(path: str | Path, data: Mapping[str, Any]) -> dict[str, Any]:
    graph_path = Path(path)
    if graph_path.suffix.lower() != ".zlogic":
        graph_path = graph_path.with_suffix(".zlogic")
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_logic_graph(data)
    temporary = graph_path.with_suffix(graph_path.suffix + ".tmp")
    temporary.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(graph_path)
    return normalized


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(fallback)


def _safe_port_type(value: Any) -> str:
    port_type = str(value).strip().lower()
    return port_type if port_type in {"any", "number", "bool", "text", "object"} else "any"


def _declared_interface_ports(value: Any) -> list[tuple[str, str]]:
    ports: list[tuple[str, str]] = []
    used: set[str] = set()
    if not isinstance(value, list):
        return ports
    for entry in value:
        if not isinstance(entry, Mapping):
            continue
        name = str(entry.get("name", "")).strip()
        if not name or name in {"in", "next"} or name in used:
            continue
        used.add(name)
        ports.append((name, _safe_port_type(entry.get("type", "any"))))
    return ports
