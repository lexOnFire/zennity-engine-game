"""Node definition metadata for Logic Graph editor.

Legacy NODE_DEFINITIONS dict for backward compatibility with graph_asset.py.
Initialized with basic node definitions to prevent KeyError on startup.
"""

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
