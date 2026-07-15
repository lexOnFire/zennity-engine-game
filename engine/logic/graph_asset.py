"""Formato persistente dos grafos visuais de lógica.

Este módulo é deliberadamente independente de Qt e Pygame. O editor cuida da
aparência, enquanto o runtime futuro poderá executar o mesmo documento.
"""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping


LOGIC_GRAPH_FORMAT = "zennity.logic_graph"
LOGIC_GRAPH_VERSION = 1

NODE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "event_start": {"title": "Ao iniciar", "category": "Eventos", "properties": {}},
    "event_update": {"title": "A cada frame", "category": "Eventos", "properties": {}},
    "self_object": {"title": "Este objeto", "category": "Objetos", "properties": {}},
    "find_tag": {"title": "Procurar por Tag", "category": "Objetos", "properties": {"tag": "Player"}},
    "input_axis": {"title": "Ler movimento", "category": "Movimento", "properties": {"negative": "A", "positive": "D"}},
    "move": {"title": "Mover", "category": "Movimento", "properties": {"speed": 200.0}},
    "jump": {"title": "Pular", "category": "Movimento", "properties": {"force": 420.0}},
    "if_else": {"title": "If / Else", "category": "Lógica", "properties": {"condition": True}},
    "sequence": {"title": "Sequência", "category": "Lógica", "properties": {"outputs": 2}},
    "and": {"title": "AND", "category": "Lógica", "properties": {}},
    "or": {"title": "OR", "category": "Lógica", "properties": {}},
    "key_pressed": {"title": "Tecla pressionada", "category": "Condição", "properties": {"key": "SPACE"}},
    "is_grounded": {"title": "Está no chão", "category": "Condição", "properties": {}},
    "compare_number": {"title": "Comparar número", "category": "Condição", "properties": {"operator": ">", "value": 0.0}},
    "play_animation": {"title": "Tocar animação", "category": "Ação", "properties": {"state": "Idle"}},
    "play_sound": {"title": "Tocar som", "category": "Ação", "properties": {"path": ""}},
    "set_hud": {"title": "Atualizar HUD", "category": "Ação", "properties": {"text": "Texto"}},
    "get_variable": {"title": "Ler variável", "category": "Variáveis", "properties": {"name": "value"}},
    "set_variable": {"title": "Definir variável", "category": "Variáveis", "properties": {"name": "value", "value": 0}},
}


def default_logic_graph(name: str = "NewLogic") -> dict[str, Any]:
    return {
        "format": LOGIC_GRAPH_FORMAT,
        "version": LOGIC_GRAPH_VERSION,
        "name": str(name).strip() or "NewLogic",
        "target": {"type": "name", "value": "Player"},
        "variables": {},
        "nodes": [],
        "edges": [],
    }


def create_logic_node(node_type: str, position: tuple[float, float] = (0.0, 0.0)) -> dict[str, Any]:
    definition = NODE_DEFINITIONS.get(str(node_type), {})
    return {
        "id": uuid.uuid4().hex,
        "type": str(node_type),
        "title": str(definition.get("title", node_type)),
        "category": str(definition.get("category", "Personalizado")),
        "position": [float(position[0]), float(position[1])],
        "properties": deepcopy(definition.get("properties", {})),
    }


def normalize_logic_graph(data: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(data or {})
    result = default_logic_graph(str(source.get("name", "NewLogic")))
    raw_target = source.get("target", {})
    if isinstance(raw_target, Mapping):
        target_type = str(raw_target.get("type", "name")).lower()
        result["target"] = {
            "type": target_type if target_type in {"name", "tag"} else "name",
            "value": str(raw_target.get("value", "Player")).strip() or "Player",
        }
    variables = source.get("variables", {})
    result["variables"] = deepcopy(variables) if isinstance(variables, Mapping) else {}

    nodes: list[dict[str, Any]] = []
    node_ids: set[str] = set()
    raw_nodes = source.get("nodes", [])
    if isinstance(raw_nodes, list):
        for index, raw_node in enumerate(raw_nodes):
            if not isinstance(raw_node, Mapping):
                continue
            node_type = str(raw_node.get("type", "custom")).strip() or "custom"
            definition = NODE_DEFINITIONS.get(node_type, {})
            node_id = str(raw_node.get("id", "")).strip() or uuid.uuid4().hex
            if node_id in node_ids:
                node_id = uuid.uuid4().hex
            node_ids.add(node_id)
            position = raw_node.get("position", [80.0 + (index % 4) * 230.0, 80.0 + (index // 4) * 130.0])
            if not isinstance(position, (list, tuple)) or len(position) < 2:
                position = [80.0, 80.0]
            properties = deepcopy(definition.get("properties", {}))
            raw_properties = raw_node.get("properties", {})
            if isinstance(raw_properties, Mapping):
                properties.update(deepcopy(raw_properties))
            nodes.append({
                "id": node_id,
                "type": node_type,
                "title": str(raw_node.get("title", definition.get("title", node_type))),
                "category": str(raw_node.get("category", definition.get("category", "Personalizado"))),
                "position": [_safe_float(position[0]), _safe_float(position[1])],
                "properties": properties,
            })
    result["nodes"] = nodes

    edges: list[dict[str, Any]] = []
    raw_edges = source.get("edges", [])
    if isinstance(raw_edges, list):
        for raw_edge in raw_edges:
            if not isinstance(raw_edge, Mapping):
                continue
            source_node = str(raw_edge.get("from_node", ""))
            target_node = str(raw_edge.get("to_node", ""))
            if source_node not in node_ids or target_node not in node_ids or source_node == target_node:
                continue
            edges.append({
                "id": str(raw_edge.get("id", "")).strip() or uuid.uuid4().hex,
                "from_node": source_node,
                "from_port": str(raw_edge.get("from_port", "next")),
                "to_node": target_node,
                "to_port": str(raw_edge.get("to_port", "in")),
                "kind": str(raw_edge.get("kind", "flow")),
            })
    result["edges"] = edges
    return result


def validate_logic_graph(data: Mapping[str, Any] | None) -> list[dict[str, str]]:
    graph = normalize_logic_graph(data)
    issues: list[dict[str, str]] = []
    if not graph["nodes"]:
        issues.append({"level": "warning", "message": "O grafo não possui nós."})
        return issues
    if not str(graph.get("target", {}).get("value", "")).strip():
        issues.append({"level": "error", "message": "Escolha o objeto alvo do grafo."})
    event_nodes = [node for node in graph["nodes"] if node["type"].startswith("event_")]
    if not event_nodes:
        issues.append({"level": "warning", "message": "Adicione Ao iniciar ou A cada frame para executar o grafo."})
    connected = {edge["from_node"] for edge in graph["edges"]} | {edge["to_node"] for edge in graph["edges"]}
    for node in graph["nodes"]:
        if node["id"] not in connected and len(graph["nodes"]) > 1:
            issues.append({"level": "warning", "node": node["id"], "message": f"Nó desconectado: {node['title']}"})
    return issues


def load_logic_graph(path: str | Path) -> dict[str, Any]:
    graph_path = Path(path)
    raw = json.loads(graph_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("O Logic Graph deve conter um objeto JSON.")
    if raw.get("format", LOGIC_GRAPH_FORMAT) != LOGIC_GRAPH_FORMAT:
        raise ValueError("Formato de Logic Graph não reconhecido.")
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
