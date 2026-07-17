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
    from .prefab_asset import parameter_port, port_type
except ImportError:
    from engine.prefabs.prefab_asset import parameter_port, port_type

try:
    from .blackboard import normalize_variable_definitions
except ImportError:  # Runtime autocontido exportado.
    from .logic_blackboard import normalize_variable_definitions


LOGIC_GRAPH_FORMAT = "zennity.logic_graph"
LOGIC_GRAPH_VERSION = 1

UNIQUE_EVENT_TYPES = {
    "event_start", "event_update", "event_collision_enter", "event_collision_exit",
    "event_trigger_enter", "event_trigger_exit", "event_object_created",
}

NODE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "event_start": {"title": "Ao iniciar", "category": "Eventos", "properties": {}},
    "event_update": {"title": "A cada frame", "category": "Eventos", "properties": {}},
    "event_custom": {"title": "Ao receber evento", "category": "Eventos", "properties": {"name": "evento"}},
    "event_collision_enter": {"title": "Ao colidir", "category": "Eventos", "properties": {}},
    "event_collision_exit": {"title": "Ao sair da colisão", "category": "Eventos", "properties": {}},
    "event_trigger_enter": {"title": "Ao entrar na área", "category": "Eventos", "properties": {}},
    "event_trigger_exit": {"title": "Ao sair da área", "category": "Eventos", "properties": {}},
    "event_timer": {"title": "Após um tempo", "category": "Eventos", "properties": {"seconds": 1.0, "repeat": False}},
    "event_key_pressed": {"title": "Ao apertar tecla (uma vez)", "category": "Eventos", "properties": {"key": "D"}},
    "event_object_created": {"title": "Ao objeto ser criado", "category": "Eventos", "properties": {}},
    "self_object": {"title": "Este objeto", "category": "Objetos", "properties": {}},
    "find_tag": {"title": "Procurar por Tag", "category": "Objetos", "properties": {"tag": "Player"}},
    "get_tag": {"title": "Ler Tag do objeto", "category": "Objetos", "properties": {}},
    "get_prefab_parameter": {
        "title": "Ler parâmetro do Prefab", "category": "Objetos",
        "properties": {"name": "speed", "type": "number", "default": 0.0},
    },
    "create_object": {
        "title": "Criar objeto",
        "category": "Objetos",
        "properties": {
            "name": "NovoObjeto", "x": 0.0, "y": 0.0,
            "width": 64.0, "height": 64.0, "color": "#58a6ff",
            "texture": "", "tag": "Untagged", "relative": False,
            "inherit_source": True, "inherit_logic": False,
            "lifetime": 0.0, "max_instances": 0, "max_distance": 0.0,
            "use_pool": False,
        },
    },
    "create_prefab": {
        "title": "Criar Prefab", "category": "Objetos",
        "properties": {
            "path": "", "override_position": True, "x": 0.0, "y": 0.0, "relative": False,
            "override_rotation": False, "rotation": 0.0,
            "override_scale": False, "width": 64.0, "height": 64.0,
            "include_camera": False, "include_audio": False, "include_logic": False,
            "parameters": {}, "exposed_properties": [],
            "lifetime": 0.0, "max_instances": 0, "max_distance": 0.0,
            "use_pool": True,
        },
    },
    "clone_object": {
        "title": "Clonar objeto", "category": "Objetos",
        "properties": {
            "name": "", "lifetime": 0.0, "max_instances": 0,
            "max_distance": 0.0, "use_pool": False,
        },
    },
    "add_component": {"title": "Adicionar componente", "category": "Objetos", "properties": {"component": "BoxCollider", "properties": {"type": "box"}}},
    "remove_component": {"title": "Remover componente", "category": "Objetos", "properties": {"component": "BoxCollider"}},
    "input_axis": {"title": "Ler movimento", "category": "Movimento", "properties": {"negative": "A", "positive": "D"}},
    "move": {"title": "Mover", "category": "Movimento", "properties": {"speed": 200.0}},
    "jump": {"title": "Pular", "category": "Movimento", "properties": {"force": 420.0}},
    "get_position": {"title": "Ler posição", "category": "Posição", "properties": {}},
    "move_by": {"title": "Mover continuamente", "category": "Posição", "properties": {"x": 100.0, "y": 0.0}},
    "start_continuous_motion": {
        "title": "Iniciar movimento permanente", "category": "Posição",
        "properties": {
            "movement": "Movement", "x": 100.0, "y": 0.0,
            "space": "global", "acceleration": 0.0, "deceleration": 0.0,
        },
    },
    "update_continuous_motion": {
        "title": "Alterar movimento permanente", "category": "Posição",
        "properties": {"movement": "Movement", "x": 100.0, "y": 0.0, "acceleration": 0.0},
    },
    "pause_continuous_motion": {
        "title": "Pausar movimento permanente", "category": "Posição",
        "properties": {"movement": "Movement"},
    },
    "resume_continuous_motion": {
        "title": "Continuar movimento permanente", "category": "Posição",
        "properties": {"movement": "Movement"},
    },
    "stop_continuous_motion": {
        "title": "Parar movimento permanente", "category": "Posição",
        "properties": {"movement": "", "smooth": False},
    },
    "get_continuous_motion": {
        "title": "Consultar movimento permanente", "category": "Posição",
        "properties": {"movement": "Movement"},
    },
    "patrol_axis": {"title": "Patrulhar entre limites", "category": "Posição", "properties": {"axis": "Y", "minimum": -100.0, "maximum": 100.0, "speed": 100.0}},
    "if_else": {"title": "If / Else", "category": "Lógica", "properties": {"condition": True}},
    "sequence": {"title": "Sequência", "category": "Lógica", "properties": {"outputs": 2}},
    "once": {"title": "Executar uma vez", "category": "Lógica", "properties": {}},
    "cooldown": {"title": "Intervalo / Cooldown", "category": "Lógica", "properties": {"seconds": 1.0}},
    "and": {"title": "AND", "category": "Lógica", "properties": {}},
    "or": {"title": "OR", "category": "Lógica", "properties": {}},
    "not": {"title": "NÃO", "category": "Lógica", "properties": {}},
    "key_pressed": {"title": "Tecla apertada agora?", "category": "Condição", "properties": {"key": "SPACE"}},
    "key_held": {"title": "Tecla está segurada?", "category": "Condição", "properties": {"key": "SPACE"}},
    "is_grounded": {"title": "Está no chão", "category": "Condição", "properties": {}},
    "compare_number": {"title": "Comparar número", "category": "Condição", "properties": {"operator": ">", "value": 0.0}},
    "compare_text": {"title": "Comparar texto", "category": "Condição", "properties": {"operator": "==", "value": "Texto"}},
    "play_animation": {"title": "Tocar animação", "category": "Ação", "properties": {"state": "Idle"}},
    "play_animation_asset": {"title": "Tocar arquivo de animação", "category": "Ação", "properties": {"path": ""}},
    "stop_animation": {"title": "Parar animação", "category": "Ação", "properties": {}},
    "play_sound": {"title": "Tocar som", "category": "Ação", "properties": {"path": ""}},
    "set_sprite": {"title": "Trocar imagem do objeto", "category": "Ação", "properties": {"path": ""}},
    "start_texture_scroll": {
        "title": "Iniciar fundo rolante",
        "category": "Ação",
        "properties": {
            "path": "", "speed_x": 0.0, "speed_y": 80.0,
            "repeat_x": False, "repeat_y": True, "parallax": 1.0,
            "send_to_background": True,
        },
    },
    "stop_texture_scroll": {"title": "Parar fundo rolante", "category": "Ação", "properties": {"reset": False}},
    "set_hud": {"title": "Atualizar HUD", "category": "Ação", "properties": {"text": "Texto"}},
    "emit_event": {"title": "Emitir evento", "category": "Ação", "properties": {"name": "evento", "payload": None}},
    "set_position": {"title": "Definir posição", "category": "Ação", "properties": {"x": 0.0, "y": 0.0}},
    "rotate": {"title": "Girar", "category": "Ação", "properties": {"degrees": 90.0}},
    "set_active": {"title": "Ativar / Desativar", "category": "Ação", "properties": {"active": True}},
    "destroy_object": {"title": "Destruir objeto", "category": "Ação", "properties": {}},
    "destroy_after_time": {"title": "Destruir depois de um tempo", "category": "Ação", "properties": {"seconds": 2.0}},
    "restart_scene": {"title": "Reiniciar cena", "category": "Ação", "properties": {}},
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
    "event_key_pressed": {"inputs": [], "outputs": [("next", "flow")]},
    "event_object_created": {"inputs": [], "outputs": [("next", "flow"), ("object", "object")]},
    "self_object": {"inputs": [], "outputs": [("object", "object")]},
    "find_tag": {"inputs": [("in", "flow")], "outputs": [("next", "flow"), ("object", "object")]},
    "get_tag": {"inputs": [("target", "object")], "outputs": [("value", "text")]},
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
    "if_else": {"inputs": [("in", "flow"), ("condition", "bool")], "outputs": [("true", "flow"), ("false", "flow")]},
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
    "compare_text": {"inputs": [("in", "flow"), ("value", "text")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "play_animation": {"inputs": [("in", "flow"), ("state", "text")], "outputs": [("next", "flow")]},
    "play_animation_asset": {"inputs": [("in", "flow"), ("path", "text")], "outputs": [("next", "flow")]},
    "stop_animation": {"inputs": [("in", "flow")], "outputs": [("next", "flow")]},
    "play_sound": {"inputs": [("in", "flow"), ("path", "text")], "outputs": [("next", "flow")]},
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
        "category": str(definition.get("category", "Personalizado")),
        "position": [float(position[0]), float(position[1])],
        "editor": {"collapsed": False, "width": 210.0, "height": 0.0},
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
            "title": str(raw_group.get("title", "Grupo")).strip() or "Grupo",
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
            "text": str(raw_comment.get("text", "Comentário")),
            "position": [_safe_float(position[0]), _safe_float(position[1])],
            "width": max(160.0, min(720.0, _safe_float(raw_comment.get("width", 260.0)) or 260.0)),
            "color": str(raw_comment.get("color", "#6b5b2f")),
        })
    result["editor"] = {"groups": groups, "comments": comments}
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
            raw_editor = raw_node.get("editor", {})
            if not isinstance(raw_editor, Mapping):
                raw_editor = {}
            editor_width = max(170.0, min(520.0, _safe_float(raw_editor.get("width", 210.0)) or 210.0))
            editor_height = max(0.0, min(720.0, _safe_float(raw_editor.get("height", 0.0))))
            nodes.append({
                "id": node_id,
                "type": node_type,
                "title": str(raw_node.get("title", definition.get("title", node_type))),
                "category": str(raw_node.get("category", definition.get("category", "Personalizado"))),
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
                "order": _safe_int(raw_edge.get("order", edge_index), edge_index),
            })
    result["edges"] = edges
    return result


def _event_identity(node: Mapping[str, Any]) -> tuple[str, str] | None:
    node_type = str(node.get("type", ""))
    if node_type in UNIQUE_EVENT_TYPES:
        return node_type, ""
    if node_type == "event_custom":
        return node_type, str(node.get("properties", {}).get("name", "evento")).strip().casefold()
    if node_type == "event_key_pressed":
        return node_type, str(node.get("properties", {}).get("key", "D")).strip().casefold()
    return None


def consolidate_logic_events(data: Mapping[str, Any] | None) -> tuple[dict[str, Any], int]:
    """Unifica eventos equivalentes e preserva todas as ramificações de saída."""
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
    """Insere uma receita reutilizando eventos únicos que já existem no grafo."""
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
    event_identities: dict[tuple[str, str], str] = {}
    for node in graph["nodes"]:
        identity = _event_identity(node)
        if identity is not None and identity in event_identities:
            issues.append({"level": "warning", "node": node["id"], "message": "Evento duplicado: conecte as ações ao evento existente."})
        elif identity is not None:
            event_identities[identity] = str(node["id"])
        if node["type"] in {"event_custom", "emit_event"} and not str(node.get("properties", {}).get("name", "")).strip():
            issues.append({"level": "error", "node": node["id"], "message": "Informe o nome do evento."})
        if node["type"] in {"subgraph_input", "subgraph_return"} and not str(node.get("properties", {}).get("name", "")).strip():
            issues.append({"level": "error", "node": node["id"], "message": "Informe o nome da porta do subgrafo."})
        if node["type"] == "call_subgraph" and not str(node.get("properties", {}).get("path", "")).strip():
            issues.append({"level": "error", "node": node["id"], "message": "Escolha o arquivo do subgrafo."})
        if node["type"] == "create_prefab":
            prefab_properties = node.get("properties", {})
            prefab_path = str(prefab_properties.get("path", "")).strip()
            if not prefab_path:
                issues.append({"level": "error", "node": node["id"], "message": "Escolha o arquivo .zprefab."})
            elif Path(prefab_path).suffix.lower() != ".zprefab":
                issues.append({"level": "error", "node": node["id"], "message": "O arquivo escolhido precisa ser .zprefab."})
            if bool(prefab_properties.get("override_scale", False)):
                try:
                    valid_size = (
                        float(prefab_properties.get("width", 0.0)) > 0.0
                        and float(prefab_properties.get("height", 0.0)) > 0.0
                    )
                except (TypeError, ValueError):
                    valid_size = False
                if not valid_size:
                    issues.append({"level": "error", "node": node["id"], "message": "Largura e altura do Prefab precisam ser maiores que zero."})
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
                            "level": "warning", "node": node["id"],
                            "message": f"Parâmetro não exposto pelo Prefab: {parameter_name}",
                        })
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
            issues.append({"level": "error", "node": source["id"], "edge": edge["id"], "message": f"Saída inexistente: {from_port}"})
        elif target_type is None:
            issues.append({"level": "error", "node": target["id"], "edge": edge["id"], "message": f"Entrada inexistente: {to_port}"})
        elif source_type != target_type and "any" not in {source_type, target_type}:
            issues.append({"level": "error", "node": target["id"], "edge": edge["id"], "message": f"Tipos incompatíveis: {source_type} → {target_type}"})
        input_key = (target["id"], str(to_port))
        if input_key in occupied_inputs:
            issues.append({"level": "error", "node": target["id"], "message": f"Entrada conectada mais de uma vez: {to_port}"})
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
                "message": f"Fluxo inalcançável a partir de um evento: {node['title']}",
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
            "message": "Ciclo de execução detectado; use Intervalo/Cooldown para evitar repetição perigosa.",
        })
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
