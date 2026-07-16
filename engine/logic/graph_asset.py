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

try:
    from .blackboard import normalize_variable_definitions
except ImportError:  # Runtime autocontido exportado.
    from .logic_blackboard import normalize_variable_definitions


LOGIC_GRAPH_FORMAT = "zennity.logic_graph"
LOGIC_GRAPH_VERSION = 1

NODE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "event_start": {"title": "Ao iniciar", "category": "Eventos", "properties": {}},
    "event_update": {"title": "A cada frame", "category": "Eventos", "properties": {}},
    "event_custom": {"title": "Ao receber evento", "category": "Eventos", "properties": {"name": "evento"}},
    "event_collision_enter": {"title": "Ao colidir", "category": "Eventos", "properties": {}},
    "event_collision_exit": {"title": "Ao sair da colisão", "category": "Eventos", "properties": {}},
    "event_trigger_enter": {"title": "Ao entrar na área", "category": "Eventos", "properties": {}},
    "event_trigger_exit": {"title": "Ao sair da área", "category": "Eventos", "properties": {}},
    "event_timer": {"title": "Após um tempo", "category": "Eventos", "properties": {"seconds": 1.0, "repeat": False}},
    "self_object": {"title": "Este objeto", "category": "Objetos", "properties": {}},
    "find_tag": {"title": "Procurar por Tag", "category": "Objetos", "properties": {"tag": "Player"}},
    "input_axis": {"title": "Ler movimento", "category": "Movimento", "properties": {"negative": "A", "positive": "D"}},
    "move": {"title": "Mover", "category": "Movimento", "properties": {"speed": 200.0}},
    "jump": {"title": "Pular", "category": "Movimento", "properties": {"force": 420.0}},
    "get_position": {"title": "Ler posição", "category": "Posição", "properties": {}},
    "move_by": {"title": "Mover continuamente", "category": "Posição", "properties": {"x": 100.0, "y": 0.0}},
    "if_else": {"title": "If / Else", "category": "Lógica", "properties": {"condition": True}},
    "sequence": {"title": "Sequência", "category": "Lógica", "properties": {"outputs": 2}},
    "and": {"title": "AND", "category": "Lógica", "properties": {}},
    "or": {"title": "OR", "category": "Lógica", "properties": {}},
    "not": {"title": "NÃO", "category": "Lógica", "properties": {}},
    "key_pressed": {"title": "Tecla pressionada", "category": "Condição", "properties": {"key": "SPACE"}},
    "is_grounded": {"title": "Está no chão", "category": "Condição", "properties": {}},
    "compare_number": {"title": "Comparar número", "category": "Condição", "properties": {"operator": ">", "value": 0.0}},
    "play_animation": {"title": "Tocar animação", "category": "Ação", "properties": {"state": "Idle"}},
    "play_animation_asset": {"title": "Tocar arquivo de animação", "category": "Ação", "properties": {"path": ""}},
    "stop_animation": {"title": "Parar animação", "category": "Ação", "properties": {}},
    "play_sound": {"title": "Tocar som", "category": "Ação", "properties": {"path": ""}},
    "set_sprite": {"title": "Trocar imagem do objeto", "category": "Ação", "properties": {"path": ""}},
    "set_hud": {"title": "Atualizar HUD", "category": "Ação", "properties": {"text": "Texto"}},
    "emit_event": {"title": "Emitir evento", "category": "Ação", "properties": {"name": "evento", "payload": None}},
    "set_position": {"title": "Definir posição", "category": "Ação", "properties": {"x": 0.0, "y": 0.0}},
    "rotate": {"title": "Girar", "category": "Ação", "properties": {"degrees": 90.0}},
    "set_active": {"title": "Ativar / Desativar", "category": "Ação", "properties": {"active": True}},
    "destroy_object": {"title": "Destruir objeto", "category": "Ação", "properties": {}},
    "log_message": {"title": "Mostrar no Console", "category": "Ação", "properties": {"text": "Mensagem"}},
    "subgraph_start": {"title": "Início do subgrafo", "category": "Subgrafos", "properties": {}},
    "subgraph_input": {"title": "Entrada do subgrafo", "category": "Subgrafos", "properties": {"name": "entrada", "type": "number", "default": 0.0}},
    "subgraph_return": {"title": "Retorno do subgrafo", "category": "Subgrafos", "properties": {"name": "resultado", "type": "number"}},
    "call_subgraph": {"title": "Executar subgrafo", "category": "Subgrafos", "properties": {"path": "", "inputs": [], "outputs": []}},
    "get_variable": {"title": "Ler variável", "category": "Variáveis", "properties": {"scope": "object", "name": "value"}},
    "set_variable": {"title": "Definir variável", "category": "Variáveis", "properties": {"scope": "object", "name": "value", "value": 0}},
    "number_value": {"title": "Número", "category": "Variáveis", "properties": {"value": 0.0}},
    "bool_value": {"title": "Verdadeiro / Falso", "category": "Variáveis", "properties": {"value": True}},
    "text_value": {"title": "Texto", "category": "Variáveis", "properties": {"value": "Texto"}},
    "add_number": {"title": "Somar", "category": "Matemática", "properties": {"a": 0.0, "b": 0.0}},
    "subtract_number": {"title": "Subtrair", "category": "Matemática", "properties": {"a": 0.0, "b": 0.0}},
    "multiply_number": {"title": "Multiplicar", "category": "Matemática", "properties": {"a": 1.0, "b": 1.0}},
    "divide_number": {"title": "Dividir", "category": "Matemática", "properties": {"a": 1.0, "b": 1.0}},
    "absolute_number": {"title": "Valor absoluto", "category": "Matemática", "properties": {"value": 0.0}},
    "clamp_number": {"title": "Limitar número", "category": "Matemática", "properties": {"value": 0.0, "minimum": 0.0, "maximum": 1.0}},
    "random_number": {"title": "Número aleatório", "category": "Matemática", "properties": {"minimum": 0.0, "maximum": 1.0}},
    "delta_time": {"title": "Tempo do frame", "category": "Matemática", "properties": {}},
    "join_text": {"title": "Juntar textos", "category": "Texto", "properties": {"a": "", "b": ""}},
    "to_text": {"title": "Converter para texto", "category": "Texto", "properties": {"value": ""}},
}

# Portas são metadados de edição e permanecem separadas das propriedades dos
# nós. Grafos antigos continuam válidos porque os nomes padrão são ``in`` e
# ``next``, exatamente como antes desta infraestrutura visual.
NODE_PORT_DEFINITIONS: dict[str, dict[str, list[tuple[str, str]]]] = {
    "event_start": {"inputs": [], "outputs": [("next", "flow")]},
    "event_update": {"inputs": [], "outputs": [("next", "flow")]},
    "event_custom": {"inputs": [], "outputs": [("next", "flow"), ("payload", "any")]},
    "event_collision_enter": {"inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_collision_exit": {"inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_trigger_enter": {"inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_trigger_exit": {"inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_timer": {"inputs": [], "outputs": [("next", "flow")]},
    "self_object": {"inputs": [], "outputs": [("object", "object")]},
    "find_tag": {"inputs": [("in", "flow")], "outputs": [("next", "flow"), ("object", "object")]},
    "input_axis": {"inputs": [("in", "flow")], "outputs": [("next", "flow"), ("value", "number")]},
    "move": {"inputs": [("in", "flow"), ("value", "number")], "outputs": [("next", "flow")]},
    "jump": {"inputs": [("in", "flow"), ("force", "number")], "outputs": [("next", "flow")]},
    "get_position": {"inputs": [("target", "object")], "outputs": [("x", "number"), ("y", "number")]},
    "move_by": {"inputs": [("in", "flow"), ("target", "object"), ("x", "number"), ("y", "number")], "outputs": [("next", "flow")]},
    "if_else": {"inputs": [("in", "flow"), ("condition", "bool")], "outputs": [("true", "flow"), ("false", "flow")]},
    "sequence": {"inputs": [("in", "flow")], "outputs": [("then_0", "flow"), ("then_1", "flow"), ("next", "flow")]},
    "and": {"inputs": [("a", "bool"), ("b", "bool")], "outputs": [("value", "bool")]},
    "or": {"inputs": [("a", "bool"), ("b", "bool")], "outputs": [("value", "bool")]},
    "not": {"inputs": [("value", "bool")], "outputs": [("value", "bool")]},
    "key_pressed": {"inputs": [("in", "flow")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "is_grounded": {"inputs": [("in", "flow")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "compare_number": {"inputs": [("in", "flow"), ("value", "number")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "play_animation": {"inputs": [("in", "flow"), ("state", "text")], "outputs": [("next", "flow")]},
    "play_animation_asset": {"inputs": [("in", "flow"), ("path", "text")], "outputs": [("next", "flow")]},
    "stop_animation": {"inputs": [("in", "flow")], "outputs": [("next", "flow")]},
    "play_sound": {"inputs": [("in", "flow"), ("path", "text")], "outputs": [("next", "flow")]},
    "set_sprite": {"inputs": [("in", "flow"), ("target", "object"), ("path", "text")], "outputs": [("next", "flow")]},
    "set_hud": {"inputs": [("in", "flow"), ("text", "text")], "outputs": [("next", "flow")]},
    "emit_event": {"inputs": [("in", "flow"), ("payload", "any")], "outputs": [("next", "flow")]},
    "set_position": {"inputs": [("in", "flow"), ("target", "object"), ("x", "number"), ("y", "number")], "outputs": [("next", "flow")]},
    "rotate": {"inputs": [("in", "flow"), ("target", "object"), ("degrees", "number")], "outputs": [("next", "flow")]},
    "set_active": {"inputs": [("in", "flow"), ("target", "object"), ("active", "bool")], "outputs": [("next", "flow")]},
    "destroy_object": {"inputs": [("in", "flow"), ("target", "object")], "outputs": []},
    "log_message": {"inputs": [("in", "flow"), ("text", "text")], "outputs": [("next", "flow")]},
    "subgraph_start": {"inputs": [], "outputs": [("next", "flow")]},
    "subgraph_input": {"inputs": [], "outputs": [("value", "any")]},
    "subgraph_return": {"inputs": [("in", "flow"), ("value", "any")], "outputs": []},
    "call_subgraph": {"inputs": [("in", "flow")], "outputs": [("next", "flow")]},
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


def node_port_definitions(node_type: str | Mapping[str, Any]) -> dict[str, list[tuple[str, str]]]:
    """Retorna cópias das portas de um tipo, com fallback compatível."""
    node = node_type if isinstance(node_type, Mapping) else None
    type_name = str(node.get("type", "")) if node is not None else str(node_type)
    definition = NODE_PORT_DEFINITIONS.get(type_name)
    if definition is None:
        return {"inputs": [("in", "flow")], "outputs": [("next", "flow")]}
    ports = {
        "inputs": list(definition.get("inputs", [])),
        "outputs": list(definition.get("outputs", [])),
    }
    if node is None:
        return ports
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}
    value_type = _safe_port_type(properties.get("type", "any"))
    if type_name == "subgraph_input":
        ports["outputs"] = [("value", value_type)]
    elif type_name == "subgraph_return":
        ports["inputs"] = [("in", "flow"), ("value", value_type)]
    elif type_name == "call_subgraph":
        ports["inputs"].extend(_declared_interface_ports(properties.get("inputs")))
        ports["outputs"].extend(_declared_interface_ports(properties.get("outputs")))
    return ports


def subgraph_interface(data: Mapping[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    """Deriva a interface pública a partir dos nós de entrada e retorno."""
    graph = normalize_logic_graph(data)
    inputs: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    for node in graph["nodes"]:
        properties = node.get("properties", {})
        if node["type"] == "subgraph_input":
            inputs.append({
                "name": str(properties.get("name", "entrada")).strip(),
                "type": _safe_port_type(properties.get("type", "any")),
                "default": deepcopy(properties.get("default")),
            })
        elif node["type"] == "subgraph_return":
            outputs.append({
                "name": str(properties.get("name", "resultado")).strip(),
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
    result["enabled"] = bool(source.get("enabled", True))
    raw_target = source.get("target", {})
    if isinstance(raw_target, Mapping):
        target_type = str(raw_target.get("type", "name")).lower()
        result["target"] = {
            "type": target_type if target_type in {"name", "tag"} else "name",
            "value": str(raw_target.get("value", "Player")).strip() or "Player",
        }
    result["variables"] = normalize_variable_definitions(source.get("variables", {}))
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
    result["debug"]["breakpoints"] = [node_id for node_id in result["debug"]["breakpoints"] if node_id in node_ids]
    result["debug"]["breakpoint_conditions"] = {
        node_id: expression
        for node_id, expression in result["debug"]["breakpoint_conditions"].items()
        if node_id in node_ids
    }

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
    event_nodes = [
        node for node in graph["nodes"]
        if node["type"].startswith("event_") or node["type"] == "subgraph_start"
    ]
    if not event_nodes:
        issues.append({"level": "warning", "message": "Adicione Ao iniciar, A cada frame ou Ao receber evento para executar o grafo."})
    connected = {edge["from_node"] for edge in graph["edges"]} | {edge["to_node"] for edge in graph["edges"]}
    connected_inputs = {(edge["to_node"], edge.get("to_port", "in")) for edge in graph["edges"]}
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    for node in graph["nodes"]:
        if node["type"] in {"event_custom", "emit_event"} and not str(node.get("properties", {}).get("name", "")).strip():
            issues.append({"level": "error", "node": node["id"], "message": "Informe o nome do evento."})
        if node["type"] in {"subgraph_input", "subgraph_return"} and not str(node.get("properties", {}).get("name", "")).strip():
            issues.append({"level": "error", "node": node["id"], "message": "Informe o nome da porta do subgrafo."})
        if node["type"] == "call_subgraph" and not str(node.get("properties", {}).get("path", "")).strip():
            issues.append({"level": "error", "node": node["id"], "message": "Escolha o arquivo do subgrafo."})
        if node["type"] in {"set_sprite", "play_animation_asset", "play_sound"}:
            has_path = bool(str(node.get("properties", {}).get("path", "")).strip())
            if not has_path and (node["id"], "path") not in connected_inputs:
                issues.append({"level": "warning", "node": node["id"], "message": "Vincule um asset do projeto a este bloco."})
        if node["id"] not in connected and len(graph["nodes"]) > 1:
            issues.append({"level": "warning", "node": node["id"], "message": f"Nó desconectado: {node['title']}"})
    interface = subgraph_interface(graph)
    for interface_side, definitions in (("entrada", interface["inputs"]), ("saída", interface["outputs"])):
        names = [str(definition.get("name", "")).strip() for definition in definitions]
        for name in names:
            if name in {"in", "next"}:
                issues.append({"level": "error", "message": f"'{name}' é um nome reservado para porta de {interface_side}."})
            elif name and names.count(name) > 1:
                message = f"Porta de {interface_side} duplicada: {name}"
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
            issues.append({"level": "error", "node": source["id"], "message": f"Saída inexistente: {from_port}"})
        elif target_type is None:
            issues.append({"level": "error", "node": target["id"], "message": f"Entrada inexistente: {to_port}"})
        elif source_type != target_type and "any" not in {source_type, target_type}:
            issues.append({"level": "error", "node": target["id"], "message": f"Tipos incompatíveis: {source_type} → {target_type}"})
        input_key = (target["id"], str(to_port))
        if input_key in occupied_inputs:
            issues.append({"level": "error", "node": target["id"], "message": f"Entrada conectada mais de uma vez: {to_port}"})
        occupied_inputs.add(input_key)
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
