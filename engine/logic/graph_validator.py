"""Validação de estrutura, conexões e tipos do Logic Graph."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

Issue = dict[str, str]


def validate_logic_graph(data: Mapping[str, Any] | None) -> list[Issue]:
    normalize, event_identity, subgraph_interface, port_definitions = _graph_api()
    graph = normalize(data)
    issues: list[Issue] = []
    if not graph["nodes"]:
        return [{"level": "warning", "message": "The graph has no nodes."}]
    if not str(graph.get("target", {}).get("value", "")).strip():
        issues.append({"level": "error", "message": "Choose the target object for this graph."})
    event_nodes = _event_nodes(graph)
    if not event_nodes:
        issues.append({
            "level": "warning",
            "message": "Add On Start, On Update, or On Event Received to execute the graph.",
        })
    connected = _connected_node_ids(graph)
    connected_inputs = {
        (edge["to_node"], edge.get("to_port", "in")) for edge in graph["edges"]
    }
    _validate_nodes(graph, connected, connected_inputs, event_identity, issues)
    _validate_interface(subgraph_interface(graph), issues)
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    _validate_edges(graph["edges"], nodes_by_id, port_definitions, issues)
    _validate_flow(graph, nodes_by_id, event_nodes, connected, port_definitions, issues)
    return issues


def _graph_api() -> tuple[Callable[..., Any], ...]:
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
    return (
        normalize_logic_graph, _event_identity, subgraph_interface,
        node_port_definitions,
    )


def _event_nodes(graph: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        node for node in graph["nodes"]
        if node["type"].startswith("event_") or node["type"] == "subgraph_start"
    ]


def _connected_node_ids(graph: Mapping[str, Any]) -> set[str]:
    return (
        {edge["from_node"] for edge in graph["edges"]}
        | {edge["to_node"] for edge in graph["edges"]}
    )


def _validate_nodes(
    graph: Mapping[str, Any],
    connected: set[str],
    connected_inputs: set[tuple[str, str]],
    event_identity: Callable[[Mapping[str, Any]], tuple[str, str] | None],
    issues: list[Issue],
) -> None:
    identities: dict[tuple[str, str], str] = {}
    for node in graph["nodes"]:
        identity = event_identity(node)
        if identity is not None and identity in identities:
            issues.append({
                "level": "warning", "node": node["id"],
                "message": "Duplicate event: connect actions to the existing event node.",
            })
        elif identity is not None:
            identities[identity] = str(node["id"])
        _validate_required_node_properties(node, issues)
        if node["type"] == "create_prefab":
            _validate_prefab_node(node, issues)
        if node["type"] in {"set_sprite", "play_animation_asset", "play_sound"}:
            has_path = bool(str(node.get("properties", {}).get("path", "")).strip())
            if not has_path and (node["id"], "path") not in connected_inputs:
                issues.append({
                    "level": "warning", "node": node["id"],
                    "message": "Link a project asset to this node.",
                })
        if node["id"] not in connected and len(graph["nodes"]) > 1:
            issues.append({
                "level": "warning", "node": node["id"],
                "message": f"Disconnected node: {node['title']}",
            })


def _validate_required_node_properties(node: Mapping[str, Any], issues: list[Issue]) -> None:
    properties = node.get("properties", {})
    rules = (
        (node["type"] in {"event_custom", "emit_event"}, "name", "Enter the event name."),
        (
            node["type"] in {"subgraph_input", "subgraph_return"},
            "name", "Enter the subgraph port name.",
        ),
        (node["type"] == "call_subgraph", "path", "Choose the subgraph file."),
    )
    for applies, field, message in rules:
        if applies and not str(properties.get(field, "")).strip():
            issues.append({"level": "error", "node": node["id"], "message": message})


def _validate_prefab_node(node: Mapping[str, Any], issues: list[Issue]) -> None:
    properties = node.get("properties", {})
    prefab_path = str(properties.get("path", "")).strip()
    if not prefab_path:
        issues.append({
            "level": "error", "node": node["id"], "message": "Choose a .zprefab file.",
        })
    elif Path(prefab_path).suffix.lower() != ".zprefab":
        issues.append({
            "level": "error", "node": node["id"],
            "message": "The chosen file must be a .zprefab.",
        })
    if bool(properties.get("override_scale", False)) and not _positive_prefab_size(properties):
        issues.append({
            "level": "error", "node": node["id"],
            "message": "Prefab width and height must be greater than zero.",
        })
    exposed = properties.get("exposed_properties", [])
    parameters = properties.get("parameters", {})
    names = {
        str(definition.get("name", ""))
        for definition in exposed
        if isinstance(definition, Mapping) and str(definition.get("name", "")).strip()
    } if isinstance(exposed, list) else set()
    if isinstance(parameters, Mapping):
        for parameter_name in parameters:
            if str(parameter_name) not in names:
                issues.append({
                    "level": "warning", "node": node["id"],
                    "message": f"Parameter not exposed by Prefab: {parameter_name}",
                })


def _positive_prefab_size(properties: Mapping[str, Any]) -> bool:
    try:
        return (
            float(properties.get("width", 0.0)) > 0.0
            and float(properties.get("height", 0.0)) > 0.0
        )
    except (TypeError, ValueError):
        return False


def _validate_interface(interface: Mapping[str, Any], issues: list[Issue]) -> None:
    for side, definitions in (("input", interface["inputs"]), ("output", interface["outputs"])):
        names = [str(definition.get("name", "")).strip() for definition in definitions]
        for name in names:
            if name in {"in", "next"}:
                issues.append({
                    "level": "error",
                    "message": f"'{name}' is a reserved port name for {side}.",
                })
            elif name and names.count(name) > 1:
                message = f"Duplicate {side} port: {name}"
                if not any(issue.get("message") == message for issue in issues):
                    issues.append({"level": "error", "message": message})


def _validate_edges(
    edges: list[Mapping[str, Any]],
    nodes_by_id: Mapping[str, Mapping[str, Any]],
    port_definitions: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    issues: list[Issue],
) -> None:
    occupied_inputs: set[tuple[str, str]] = set()
    for edge in edges:
        source = nodes_by_id.get(edge["from_node"])
        target = nodes_by_id.get(edge["to_node"])
        if source is None or target is None:
            continue
        outputs = dict(port_definitions(source)["outputs"])
        inputs = dict(port_definitions(target)["inputs"])
        from_port = edge.get("from_port", "next")
        to_port = edge.get("to_port", "in")
        source_type = outputs.get(from_port)
        target_type = inputs.get(to_port)
        _validate_edge_ports(edge, source, target, from_port, to_port, source_type, target_type, issues)
        input_key = (target["id"], str(to_port))
        if input_key in occupied_inputs:
            issues.append({
                "level": "error", "node": target["id"],
                "message": f"Input connected more than once: {to_port}",
            })
        occupied_inputs.add(input_key)


def _validate_edge_ports(
    edge: Mapping[str, Any],
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    from_port: Any,
    to_port: Any,
    source_type: Any,
    target_type: Any,
    issues: list[Issue],
) -> None:
    if source_type is None:
        issues.append({
            "level": "error", "node": source["id"], "edge": edge["id"],
            "message": f"Non-existent output port: {from_port}",
        })
    elif target_type is None:
        issues.append({
            "level": "error", "node": target["id"], "edge": edge["id"],
            "message": f"Non-existent input port: {to_port}",
        })
    elif source_type != target_type and "any" not in {source_type, target_type}:
        issues.append({
            "level": "error", "node": target["id"], "edge": edge["id"],
            "message": f"Incompatible types: {source_type} → {target_type}",
        })


def _validate_flow(
    graph: Mapping[str, Any],
    nodes_by_id: Mapping[str, Mapping[str, Any]],
    event_nodes: list[Mapping[str, Any]],
    connected: set[str],
    port_definitions: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    issues: list[Issue],
) -> None:
    adjacency = _flow_adjacency(graph["edges"], nodes_by_id)
    reachable = _reachable_nodes(adjacency, [str(node["id"]) for node in event_nodes])
    data_only = {
        "get_variable", "get_tag", "number_value", "bool_value", "text_value",
        "add_number", "subtract_number", "multiply_number", "divide_number",
        "absolute_number", "clamp_number", "random_number", "delta_time",
        "join_text", "to_text",
    }
    for node in graph["nodes"]:
        ports = port_definitions(node)
        has_flow = any(
            kind == "flow" for _name, kind in ports["inputs"] + ports["outputs"]
        )
        if has_flow and node["type"] not in data_only and node["id"] not in reachable and node["id"] in connected:
            issues.append({
                "level": "warning", "node": node["id"],
                "message": f"Unreachable flow from any event: {node['title']}",
            })
    for node_id in sorted(_cycle_nodes(adjacency)):
        issues.append({
            "level": "warning", "node": node_id,
            "message": "Execution cycle detected; use Cooldown to avoid dangerous repetition.",
        })


def _flow_adjacency(
    edges: list[Mapping[str, Any]], nodes_by_id: Mapping[str, Any],
) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in nodes_by_id}
    for edge in edges:
        if str(edge.get("kind", "flow")) == "flow":
            adjacency.get(str(edge["from_node"]), []).append(str(edge["to_node"]))
    return adjacency


def _reachable_nodes(adjacency: Mapping[str, list[str]], starts: list[str]) -> set[str]:
    reachable: set[str] = set()
    pending = list(starts)
    while pending:
        node_id = pending.pop()
        if node_id not in reachable:
            reachable.add(node_id)
            pending.extend(adjacency.get(node_id, []))
    return reachable


def _cycle_nodes(adjacency: Mapping[str, list[str]]) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            cycles.add(node_id)
            return
        if node_id in visited:
            return
        visiting.add(node_id)
        for target_id in adjacency.get(node_id, []):
            if target_id in visiting:
                cycles.update({node_id, target_id})
            else:
                visit(target_id)
        visiting.discard(node_id)
        visited.add(node_id)

    for node_id in adjacency:
        visit(node_id)
    return cycles
