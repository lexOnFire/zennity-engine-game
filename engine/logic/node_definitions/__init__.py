"""Node definition metadata for Logic Graph editor.

This package is the public source imported by ``engine.logic.graph_asset``.
It keeps the legacy ``NODE_DEFINITIONS`` dictionary available while also
harvesting the modern declarative ``NodeDefinition`` objects declared in the
submodules.  This matters because Python resolves this package before the
legacy sibling module ``engine/logic/node_definitions.py``; without the export
step below, the editor only sees a tiny fallback catalog and many visual nodes
disappear from the Logic Graph palette.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any

# Initialize with basic node structure from NODE_PORT_DEFINITIONS
NODE_DEFINITIONS: dict[str, dict] = {
    # Basic event nodes
    "event_start": {"id": "event_start", "title": "On Start", "category": "Events", "inputs": [], "outputs": [("next", "flow")]},
    "event_update": {"id": "event_update", "title": "On Update", "category": "Events", "inputs": [], "outputs": [("next", "flow")]},
    "event_custom": {"id": "event_custom", "title": "Custom Event", "category": "Events", "inputs": [], "outputs": [("next", "flow"), ("payload", "any")]},
    "event_collision_enter": {"id": "event_collision_enter", "title": "On Collision Enter", "category": "Events", "inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_collision_exit": {"id": "event_collision_exit", "title": "On Collision Exit", "category": "Events", "inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_trigger_enter": {"id": "event_trigger_enter", "title": "On Trigger Enter", "category": "Events", "inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_trigger_exit": {"id": "event_trigger_exit", "title": "On Trigger Exit", "category": "Events", "inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_timer": {"id": "event_timer", "title": "Timer", "category": "Events", "inputs": [], "outputs": [("next", "flow")]},
    "event_key_pressed": {"id": "event_key_pressed", "title": "On Key Pressed", "category": "Events", "inputs": [], "outputs": [("next", "flow")]},
    "event_object_created": {"id": "event_object_created", "title": "On Object Created", "category": "Events", "inputs": [], "outputs": [("next", "flow"), ("object", "object")]},

    # Self/object access
    "self_object": {"id": "self_object", "title": "This Object", "category": "Objects", "inputs": [], "outputs": [("object", "object")]},
    "find_tag": {"id": "find_tag", "title": "Find by Tag", "category": "Objects", "inputs": [("in", "flow")], "outputs": [("next", "flow"), ("object", "object")]},
    "get_tag": {"id": "get_tag", "title": "Get Tag", "category": "Objects", "inputs": [("target", "object")], "outputs": [("value", "text")]},
    "get_prefab_parameter": {"id": "get_prefab_parameter", "title": "Get Prefab Parameter", "category": "Objects", "inputs": [("target", "object")], "outputs": [("value", "any")]},

    # Object creation
    "create_object": {"id": "create_object", "title": "Create Object", "category": "Objects", "inputs": [("in", "flow"), ("source", "object"), ("name", "text"), ("x", "number"), ("y", "number")], "outputs": [("next", "flow"), ("limit_reached", "flow"), ("object", "object")]},
    "create_prefab": {"id": "create_prefab", "title": "Create Prefab Instance", "category": "Objects", "inputs": [("in", "flow"), ("prefab", "text"), ("x", "number"), ("y", "number")], "outputs": [("next", "flow"), ("object", "object")]},

    # Condition nodes
    "key_pressed": {"id": "key_pressed", "title": "Key Pressed?", "category": "Condition", "inputs": [], "outputs": [], "properties": {"key": "SPACE"}},
    "key_held": {"id": "key_held", "title": "Key Held?", "category": "Condition", "inputs": [], "outputs": []},

    # Motion
    "start_continuous_motion": {"id": "start_continuous_motion", "title": "Start Continuous Motion", "category": "Movement", "inputs": [], "outputs": [], "properties": {}},

    # Value nodes
    "number_value": {"id": "number_value", "title": "Number", "category": "Values", "inputs": [], "outputs": [], "properties": {"value": 0.0}},
    "bool_value": {"id": "bool_value", "title": "Boolean", "category": "Values", "inputs": [], "outputs": [], "properties": {"value": True}},
    "text_value": {"id": "text_value", "title": "Text", "category": "Values", "inputs": [], "outputs": [], "properties": {"value": ""}},

    # UI Binding
    "bind_ui_to_variable": {"id": "bind_ui_to_variable", "title": "Vincular UI → Variável", "category": "UI", "inputs": [("in", "flow"), ("widget_name", "text"), ("variable_name", "text"), ("property", "text")], "outputs": [("next", "flow"), ("exec_success", "flow"), ("exec_not_found", "flow"), ("exec_failure", "flow")], "properties": {"widget_name": "comida", "variable_name": "comida", "property": "value"}},
    "update_ui_binding": {"id": "update_ui_binding", "title": "Atualizar Binding UI", "category": "UI", "inputs": [("in", "flow"), ("widget_name", "text"), ("variable_name", "text"), ("property", "text")], "outputs": [("next", "flow"), ("exec_success", "flow"), ("exec_not_found", "flow"), ("exec_failure", "flow")], "properties": {"widget_name": "comida", "variable_name": "comida", "property": "value"}},
}

def _populate_node_definitions():
    """Populate NODE_DEFINITIONS with nodes from MetadataManager if available."""
    try:
        from engine.metadata.manager import MetadataManager
        manager = MetadataManager()
        metadata = manager.get_nodes_metadata()

        for node_id, node_def in metadata.items():
            if node_id not in NODE_DEFINITIONS:  # Don't overwrite basic nodes
                NODE_DEFINITIONS[node_id] = {
                    "id": node_id,
                    "title": node_def.get("title", node_id),
                    "category": node_def.get("category", "Custom"),
                    "description": node_def.get("description", ""),
                    "inputs": node_def.get("inputs", []),
                    "outputs": node_def.get("outputs", []),
                    "properties": node_def.get("properties", {}),
                }
    except Exception:
        pass


_DECLARATIVE_MODULES = (
    "actions_nodes",
    "animation_nodes",
    "audio_advanced_nodes",
    "camera_nodes",
    "components_nodes",
    "dialog_nodes",
    "dynamic_ui_nodes",
    "event_nodes",
    "flow_nodes",
    "input_advanced_nodes",
    "misc_nodes",
    "movement_nodes",
    "particle_nodes",
    "pathfinding_nodes",
    "physics_nodes",
    "prefab_nodes",
    "save_load_nodes",
    "state_machine_nodes",
    "ui_binding_nodes",
    "ui_nodes",
)


def _legacy_pin_type(pin_type: Any) -> str:
    value = str(getattr(pin_type, "value", pin_type)).lower()
    return {
        "exec": "flow",
        "float": "number",
        "int": "number",
        "string": "text",
        "vector2": "vector2",
        "vector3": "vector3",
        "color": "color",
        "bool": "bool",
        "object": "object",
    }.get(value, value or "any")


def _pin_tuple(pin: Any) -> tuple[str, str]:
    return (str(getattr(pin, "id", "")), _legacy_pin_type(getattr(pin, "pin_type", "any")))


def _definition_to_legacy(definition: Any) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    for pin in list(getattr(definition, "inputs", [])):
        pin_type = _legacy_pin_type(getattr(pin, "pin_type", "any"))
        pin_id = str(getattr(pin, "id", ""))
        default = getattr(pin, "default_value", None)
        if pin_type != "flow" and pin_id and default is not None:
            properties[pin_id] = default
    category = str(getattr(definition, "category_key", "") or "Custom")
    category = {"Actions": "Action"}.get(category, category)
    return {
        "id": str(getattr(definition, "id", "")),
        "title": str(getattr(definition, "title_key", "") or getattr(definition, "name_key", "") or getattr(definition, "id", "")),
        "category": category,
        "description": str(getattr(definition, "description_key", "") or ""),
        "inputs": [_pin_tuple(pin) for pin in list(getattr(definition, "inputs", []))],
        "outputs": [_pin_tuple(pin) for pin in list(getattr(definition, "outputs", []))],
        "properties": properties,
    }


def _collect_declarative_definitions(module: ModuleType) -> None:
    for value in vars(module).values():
        definition = getattr(value, "__node_definition__", None)
        if definition is None and getattr(value, "__class__", None).__name__ == "NodeDefinition":
            definition = value
        if definition is None:
            continue
        node_id = str(getattr(definition, "id", "")).strip()
        if not node_id:
            continue
        NODE_DEFINITIONS[node_id] = _definition_to_legacy(definition)


def _populate_declarative_node_definitions() -> None:
    for module_name in _DECLARATIVE_MODULES:
        try:
            module = import_module(f"{__name__}.{module_name}")
        except Exception:
            continue
        _collect_declarative_definitions(module)


_populate_declarative_node_definitions()
_populate_node_definitions()

# Public graph/runtime compatibility contracts.  Some newer declarative nodes
# use friendlier authoring pins (for example ``a``/``b``/``operation``), but
# existing ``.zlogic`` assets and the runtime still consume these legacy
# properties and ports.
NODE_DEFINITIONS.setdefault("if_else", {}).setdefault("properties", {"condition": False})
NODE_DEFINITIONS["compare_number"].update({
    "inputs": [("in", "flow"), ("value", "number")],
    "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")],
    "properties": {"operator": ">", "value": 0.0},
})
NODE_DEFINITIONS["compare_text"].update({
    "inputs": [("in", "flow"), ("value", "text")],
    "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")],
    "properties": {"operator": "==", "value": ""},
})
