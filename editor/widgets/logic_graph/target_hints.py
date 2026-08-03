"""Target hint calculation for Logic Graph node items."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def refresh_target_hints(graph: dict[str, Any], node_items: dict[str, Any]) -> None:
    """Update visible hints explaining which object each node targets."""
    creators = {"create_object", "create_prefab", "clone_object"}
    nodes = {str(node.get("id")): node for node in graph.get("nodes", [])}
    flow_next: dict[str, list[str]] = {}
    explicit_targets: set[str] = set()
    for edge in graph.get("edges", []):
        source_id = str(edge.get("from_node", ""))
        target_id = str(edge.get("to_node", ""))
        source_item = node_items.get(source_id)
        source_port = source_item.output_ports.get(str(edge.get("from_port", "next"))) if source_item else None
        kind = source_port.data_type if source_port is not None else str(edge.get("kind", "flow"))
        if kind == "flow":
            flow_next.setdefault(source_id, []).append(target_id)
        if kind == "object" and str(edge.get("to_port", "")) == "target":
            explicit_targets.add(target_id)

    implicit_sources = _implicit_target_sources(nodes, flow_next, creators)
    graph_target = str(graph.get("target", {}).get("value", "Player"))
    for node_id, item in node_items.items():
        node_type = str(nodes.get(node_id, {}).get("type", ""))
        if node_type in creators:
            item.set_target_hint(f"NOVO ALVO → {_created_target_name(node_type, nodes[node_id])}", False)
            continue
        if "target" not in item.input_ports:
            item.set_target_hint()
            continue
        if node_id in explicit_targets:
            item.set_target_hint("ALVO → referência conectada", False)
            continue
        labels = implicit_sources.get(node_id, set())
        if len(labels) == 1:
            item.set_target_hint(f"ALVO IMPLÍCITO → {next(iter(labels))}", True)
        elif len(labels) > 1:
            item.set_target_hint("ALVO IMPLÍCITO → depende do fluxo", True)
        else:
            item.set_target_hint(f"ALVO ATUAL → {graph_target}", False)


def _implicit_target_sources(
    nodes: dict[str, dict[str, Any]],
    flow_next: dict[str, list[str]],
    creators: set[str],
) -> dict[str, set[str]]:
    implicit_sources: dict[str, set[str]] = {}

    def spread(source_id: str, label: str) -> None:
        pending = list(flow_next.get(source_id, []))
        visited: set[str] = set()
        while pending:
            node_id = pending.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            implicit_sources.setdefault(node_id, set()).add(label)
            if str(nodes.get(node_id, {}).get("type", "")) in creators:
                continue
            pending.extend(flow_next.get(node_id, []))

    for node_id, node in nodes.items():
        node_type = str(node.get("type", ""))
        properties = node.get("properties", {})
        if node_type == "create_object":
            spread(node_id, str(properties.get("name", "NovoObjeto")))
        elif node_type == "create_prefab":
            label = Path(str(properties.get("path", "Prefab"))).stem or "Prefab"
            spread(node_id, label)
        elif node_type == "clone_object":
            spread(node_id, str(properties.get("name", "Cópia")) or "Cópia")
        elif node_type == "event_object_created":
            spread(node_id, "objeto recém-criado")
    return implicit_sources


def _created_target_name(node_type: str, node: dict[str, Any]) -> str:
    properties = node.get("properties", {})
    if node_type == "create_prefab":
        return Path(str(properties.get("path", ""))).stem or "Prefab"
    return str(properties.get("name", "")) or "Nova instância"
