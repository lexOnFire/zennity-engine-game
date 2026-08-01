"""Validação de estrutura, conexões e tipos do Logic Graph."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.logic.graph_asset import normalize_logic_graph, _event_identity, subgraph_interface, node_port_definitions


def validate_logic_graph(data: Mapping[str, Any] | None) -> list[dict[str, str]]:
    try:
        from engine.logic.graph_asset import (
            normalize_logic_graph, _event_identity, subgraph_interface,
            node_port_definitions,
        )
    except ImportError:  # Self-contained exported runtime.
        from .logic_graph_asset import (
            normalize_logic_graph, _event_identity, subgraph_interface,
            node_port_definitions,
        )

    graph = normalize_logic_graph(data)
    issues: list[dict[str, str]] = []
    if not graph["nodes"]:
        issues.append({"level": "warning", "message": "The graph has no nodes."})
        return issues
    if not str(graph.get("target", {}).get("value", "")).strip():
        issues.append({"level": "error", "message": "Choose the target object for this graph."})
    event_nodes = [
        node for node in graph["nodes"]
        if node["type"].startswith("event_") or node["type"] == "subgraph_start"
    ]
    if not event_nodes:
        issues.append({"level": "warning", "message": "Add On Start, On Update, or On Event Received to execute the graph."})
    connected = {edge["from_node"] for edge in graph["edges"]} | {edge["to_node"] for edge in graph["edges"]}
    connected_inputs = {(edge["to_node"], edge.get("to_port", "in")) for edge in graph["edges"]}
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    event_identities: dict[tuple[str, str], str] = {}
    for node in graph["nodes"]:
        identity = _event_identity(node)
        if identity is not None and identity in event_identities:
            issues.append({"level": "warning", "node": node["id"], "message": "Duplicate event: connect actions to the existing event node."})
        elif identity is not None:
            event_identities[identity] = str(node["id"])
        if node["type"] in {"event_custom", "emit_event"} and not str(node.get("properties", {}).get("name", "")).strip():
            issues.append({"level": "error", "node": node["id"], "message": "Enter the event name."})
        if node["type"] in {"subgraph_input", "subgraph_return"} and not str(node.get("properties", {}).get("name", "")).strip():
            issues.append({"level": "error", "node": node["id"], "message": "Enter the subgraph port name."})
        if node["type"] == "call_subgraph" and not str(node.get("properties", {}).get("path", "")).strip():
            issues.append({"level": "error", "node": node["id"], "message": "Choose the subgraph file."})
        if node["type"] == "create_prefab":
            prefab_properties = node.get("properties", {})
            prefab_path = str(prefab_properties.get("path", "")).strip()
            if not prefab_path:
                issues.append({"level": "error", "node": node["id"], "message": "Choose a .zprefab file."})
            elif Path(prefab_path).suffix.lower() != ".zprefab":
                issues.append({"level": "error", "node": node["id"], "message": "The chosen file must be a .zprefab."})
            if bool(prefab_properties.get("override_scale", False)):
                try:
                    valid_size = (
                        float(prefab_properties.get("width", 0.0)) > 0.0
                        and float(prefab_properties.get("height", 0.0)) > 0.0
                    )
                except (TypeError, ValueError):
                    valid_size = False
                if not valid_size:
                    issues.append({"level": "error", "node": node["id"], "message": "Prefab width and height must be greater than zero."})
            exposed = prefab_properties.get("exposed_properties", [])
            parameters = prefab_properties.get("parameters", {})
            names = {
                str(definition.get("name", "")) for definition in exposed
                if isinstance(definition, Mapping) and str(definition.get("name", "")).strip()
            } if isinstance(exposed, list) else set()
            if isinstance(parameters, Mapping):
                for parameter_name in parameters:
                    if str(parameter_name) not in names:
                        issues.append({
                            "level": "warning",
                            "node": node["id"],
                            "message": f"Parameter not exposed by Prefab: {parameter_name}",
                        })
        if node["type"] in {"set_sprite", "play_animation_asset", "play_sound"}:
            has_path = bool(str(node.get("properties", {}).get("path", "")).strip())
            if not has_path and (node["id"], "path") not in connected_inputs:
                issues.append({"level": "warning", "node": node["id"], "message": "Link a project asset to this node."})
        if node["id"] not in connected and len(graph["nodes"]) > 1:
            issues.append({"level": "warning", "node": node["id"], "message": f"Disconnected node: {node['title']}"})
    interface = subgraph_interface(graph)
    for interface_side, definitions in (("input", interface["inputs"]), ("output", interface["outputs"])):
        names = [str(definition.get("name", "")).strip() for definition in definitions]
        for name in names:
            if name in {"in", "next"}:
                issues.append({"level": "error", "message": f"'{name}' is a reserved port name for {interface_side}."})
            elif name and names.count(name) > 1:
                message = f"Duplicate {interface_side} port: {name}"
                if not any(issue.get("message") == message for issue in issues):
                    issues.append({"level": "error", "message": message})
    occupied_inputs: set[tuple[str, str]] = set()
    for edge in graph["edges"]:
        source = nodes_by_id.get(edge["from_node"])
        target = nodes_by_id.get(edge["to_node"])
        if source is None or target is None:
            continue
        outputs = dict(node_port_definitions(source)["outputs"])
        inputs = dict(node_port_definitions(target)["inputs"])
        from_port = edge.get("from_port", "next")
        to_port = edge.get("to_port", "in")
        source_type = outputs.get(from_port)
        target_type = inputs.get(to_port)
        if source_type is None:
            issues.append({"level": "error", "node": source["id"], "edge": edge["id"], "message": f"Non-existent output port: {from_port}"})
        elif target_type is None:
            issues.append({"level": "error", "node": target["id"], "edge": edge["id"], "message": f"Non-existent input port: {to_port}"})
        elif source_type != target_type and "any" not in {source_type, target_type}:
            issues.append({"level": "error", "node": target["id"], "edge": edge["id"], "message": f"Incompatible types: {source_type} \u2192 {target_type}"})
        input_key = (target["id"], str(to_port))
        if input_key in occupied_inputs:
            issues.append({"level": "error", "node": target["id"], "message": f"Input connected more than once: {to_port}"})
        occupied_inputs.add(input_key)

    flow_adjacency: dict[str, list[str]] = {node_id: [] for node_id in nodes_by_id}
    for edge in graph["edges"]:
        if str(edge.get("kind", "flow")) == "flow":
            flow_adjacency.get(str(edge["from_node"]), []).append(str(edge["to_node"]))
    reachable: set[str] = set()
    pending = [str(node["id"]) for node in event_nodes]
    while pending:
        node_id = pending.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        pending.extend(flow_adjacency.get(node_id, []))
    data_only_types = {
        "get_variable", "get_tag", "number_value", "bool_value", "text_value",
        "add_number", "subtract_number", "multiply_number", "divide_number",
        "absolute_number", "clamp_number", "random_number", "delta_time",
        "join_text", "to_text",
    }
    for node in graph["nodes"]:
        ports = node_port_definitions(node)
        has_flow = any(kind == "flow" for _name, kind in ports["inputs"] + ports["outputs"])
        if (
            has_flow
            and node["type"] not in data_only_types
            and node["id"] not in reachable
            and node["id"] in connected
        ):
            issues.append({
                "level": "warning",
                "node": node["id"],
                "message": f"Unreachable flow from any event: {node['title']}",
            })

    visiting: set[str] = set()
    visited: set[str] = set()
    cycle_nodes: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            cycle_nodes.add(node_id)
            return
        if node_id in visited:
            return
        visiting.add(node_id)
        for target_id in flow_adjacency.get(node_id, []):
            if target_id in visiting:
                cycle_nodes.update({node_id, target_id})
            else:
                visit(target_id)
        visiting.discard(node_id)
        visited.add(node_id)

    for node_id in flow_adjacency:
        visit(node_id)
    for node_id in sorted(cycle_nodes):
        issues.append({
            "level": "warning",
            "node": node_id,
            "message": "Execution cycle detected; use Cooldown to avoid dangerous repetition.",
        })
    return issues
