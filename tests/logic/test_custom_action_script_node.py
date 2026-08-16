"""Testes para Action Custom Script Node (Flow, Failure, Falsy, Data Outputs e Chains) — D2.3."""
from __future__ import annotations

import json
import pytest
from engine.logic.graph_asset import normalize_logic_graph, node_port_definitions
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.runtime.custom_script_sandbox import validate_custom_script


def test_custom_action_script_success_and_next():
    """Seção 19: Testa execução Action com sucesso e emissão de 'next'."""
    graph_data = {
        "nodes": [
            {
                "id": "action_1",
                "type": "custom_script",
                "title": "Action Success",
                "properties": {
                    "execution_model": "action",
                    "inputs": [
                        {"name": "damage", "type": "number", "default": 25.0},
                        {"name": "multiplier", "type": "number", "default": 2.0},
                    ],
                    "outputs": [
                        {"name": "result", "type": "number"},
                    ],
                    "script": (
                        "dmg = ctx.get_input('damage')\n"
                        "mult = ctx.get_input('multiplier')\n"
                        "ctx.set_output('result', dmg * mult)\n"
                        "ctx.emit('next')"
                    ),
                },
            }
        ],
        "edges": [],
    }

    runtime = LogicGraphRuntime(graph_data)
    node = runtime.nodes["action_1"]
    next_ports = runtime._execute(node, None, 0.0)

    assert next_ports == ["next"]
    assert runtime.values[("action_1", "result")] == 50.0


def test_custom_action_script_explicit_failure():
    """Seção 20: Testa execução Action com condicional emitindo 'failure'."""
    script = (
        "val = ctx.get_input('value', 0)\n"
        "if val < 0:\n"
        "    ctx.emit('failure')\n"
        "else:\n"
        "    ctx.emit('next')"
    )

    def create_graph(val):
        return {
            "nodes": [
                {
                    "id": "action_cond",
                    "type": "custom_script",
                    "title": "Condition Action",
                    "properties": {
                        "execution_model": "action",
                        "inputs": [{"name": "value", "type": "number", "default": val}],
                        "outputs": [],
                        "script": script,
                    },
                }
            ],
            "edges": [],
        }

    # Caso value = 10 -> next
    runtime_pos = LogicGraphRuntime(create_graph(10))
    assert runtime_pos._execute(runtime_pos.nodes["action_cond"], None, 0.0) == ["next"]

    # Caso value = -1 -> failure
    runtime_neg = LogicGraphRuntime(create_graph(-1))
    assert runtime_neg._execute(runtime_neg.nodes["action_cond"], None, 0.0) == ["failure"]


def test_custom_action_script_default_next_when_no_emit():
    """Seção 21: Testa que se o script Action não chamar ctx.emit, assume 'next' por padrão."""
    graph_data = {
        "nodes": [
            {
                "id": "action_no_emit",
                "type": "custom_script",
                "title": "No Emit Action",
                "properties": {
                    "execution_model": "action",
                    "inputs": [{"name": "val", "type": "number", "default": 5}],
                    "outputs": [{"name": "out", "type": "number"}],
                    "script": "ctx.set_output('out', ctx.get_input('val') + 1)",
                },
            }
        ],
        "edges": [],
    }

    runtime = LogicGraphRuntime(graph_data)
    node = runtime.nodes["action_no_emit"]
    next_ports = runtime._execute(node, None, 0.0)

    assert next_ports == ["next"]
    assert runtime.values[("action_no_emit", "out")] == 6


def test_custom_action_script_runtime_exception_routes_to_failure():
    """Seção 22: Testa que exceções em runtime desviam para 'failure' e não quebram o runtime."""
    graph_data = {
        "nodes": [
            {
                "id": "action_div_zero",
                "type": "custom_script",
                "title": "Div Zero Action",
                "properties": {
                    "execution_model": "action",
                    "inputs": [{"name": "val", "type": "number", "default": 0}],
                    "outputs": [{"name": "out", "type": "number"}],
                    "script": (
                        "val = ctx.get_input('val')\n"
                        "res = 10 / val\n"
                        "ctx.set_output('out', res)\n"
                        "ctx.emit('next')"
                    ),
                },
            }
        ],
        "edges": [],
    }

    runtime = LogicGraphRuntime(graph_data)
    node = runtime.nodes["action_div_zero"]
    # 10 / 0 deve ser capturado com segurança e retornar ['failure']
    next_ports = runtime._execute(node, None, 0.0)
    assert next_ports == ["failure"]


def test_custom_action_script_invalid_flow_rejected():
    """Seção 23: Testa que ctx.emit com porta inválida ('banana') falha na validação AST."""
    script = "ctx.emit('banana')"
    valid, err = validate_custom_script(script, [], [], execution_model="action")
    assert valid is False
    assert "inválida" in err


def test_custom_action_script_multiple_emit_rejected():
    """Seção 24: Testa que múltiplas chamadas concorrentes a ctx.emit no mesmo script são rejeitadas."""
    graph_data = {
        "nodes": [
            {
                "id": "action_multi_emit",
                "type": "custom_script",
                "title": "Multi Emit Action",
                "properties": {
                    "execution_model": "action",
                    "inputs": [],
                    "outputs": [],
                    "script": "ctx.emit('next')\nctx.emit('failure')",
                },
            }
        ],
        "edges": [],
    }

    runtime = LogicGraphRuntime(graph_data)
    node = runtime.nodes["action_multi_emit"]
    # Múltipla emissão é tratada como erro de execução e desvia para failure
    next_ports = runtime._execute(node, None, 0.0)
    assert next_ports == ["failure"]


def test_custom_action_script_falsy_values_preserved():
    """Seção 25: Testa preservação exata de valores 0, False e '' em nós Action."""
    graph_data = {
        "nodes": [
            {
                "id": "action_falsy",
                "type": "custom_script",
                "properties": {
                    "execution_model": "action",
                    "inputs": [
                        {"name": "n", "type": "number", "default": 0},
                        {"name": "b", "type": "bool", "default": False},
                        {"name": "s", "type": "text", "default": ""},
                    ],
                    "outputs": [
                        {"name": "out_n", "type": "number"},
                        {"name": "out_b", "type": "bool"},
                        {"name": "out_s", "type": "text"},
                    ],
                    "script": (
                        "n = ctx.get_input('n', 99)\n"
                        "b = ctx.get_input('b', True)\n"
                        "s = ctx.get_input('s', 'default')\n"
                        "ctx.set_output('out_n', n)\n"
                        "ctx.set_output('out_b', b)\n"
                        "ctx.set_output('out_s', s)\n"
                        "ctx.emit('next')"
                    ),
                },
            }
        ],
        "edges": [],
    }

    runtime = LogicGraphRuntime(graph_data)
    node = runtime.nodes["action_falsy"]
    runtime._execute(node, None, 0.0)

    assert runtime.values[("action_falsy", "out_n")] == 0
    assert runtime.values[("action_falsy", "out_b")] is False
    assert runtime.values[("action_falsy", "out_s")] == ""


def test_custom_action_script_chain_execution():
    """Seção 26: Testa encadeamento de fluxo: event_start -> custom_script (action) -> set_variable."""
    graph_data = {
        "nodes": [
            {
                "id": "evt_start",
                "type": "event_start",
                "properties": {},
            },
            {
                "id": "action_step",
                "type": "custom_script",
                "properties": {
                    "execution_model": "action",
                    "inputs": [{"name": "factor", "type": "number", "default": 4.0}],
                    "outputs": [{"name": "calculated", "type": "number"}],
                    "script": "ctx.set_output('calculated', ctx.get_input('factor') * 10)\nctx.emit('next')",
                },
            },
            {
                "id": "set_var",
                "type": "set_variable",
                "properties": {"name": "total", "scope": "object"},
            },
        ],
        "edges": [
            {"from_node": "evt_start", "from_port": "next", "to_node": "action_step", "to_port": "in"},
            {"from_node": "action_step", "from_port": "next", "to_node": "set_var", "to_port": "in"},
            {"from_node": "action_step", "from_port": "calculated", "to_node": "set_var", "to_port": "value"},
        ],
        "variables": {"total": {"type": "number", "scope": "object", "default": 0}},
    }

    runtime = LogicGraphRuntime(graph_data)
    runtime.start(None)

    assert "action_step" in runtime.executed_nodes
    assert "set_var" in runtime.executed_nodes
    assert runtime.variables["total"] == 40.0


def test_custom_action_script_failure_chain():
    """Seção 27: Testa failure chain onde erro no script ativa exclusivamente o branch failure."""
    graph_data = {
        "nodes": [
            {
                "id": "evt_start",
                "type": "event_start",
                "properties": {},
            },
            {
                "id": "action_fail_step",
                "type": "custom_script",
                "properties": {
                    "execution_model": "action",
                    "inputs": [],
                    "outputs": [],
                    "script": "x = 1 / 0\nctx.emit('next')",
                },
            },
            {
                "id": "on_success",
                "type": "set_variable",
                "properties": {"name": "status", "scope": "object", "value": "OK"},
            },
            {
                "id": "on_failure",
                "type": "set_variable",
                "properties": {"name": "status", "scope": "object", "value": "FAILED"},
            },
        ],
        "edges": [
            {"from_node": "evt_start", "from_port": "next", "to_node": "action_fail_step", "to_port": "in"},
            {"from_node": "action_fail_step", "from_port": "next", "to_node": "on_success", "to_port": "in"},
            {"from_node": "action_fail_step", "from_port": "failure", "to_node": "on_failure", "to_port": "in"},
        ],
        "variables": {"status": {"type": "text", "scope": "object", "default": "PENDING"}},
    }

    runtime = LogicGraphRuntime(graph_data)
    runtime.start(None)

    assert "on_success" not in runtime.executed_nodes
    assert "on_failure" in runtime.executed_nodes
    assert runtime.variables["status"] == "FAILED"


def test_custom_action_script_data_output_and_flow():
    """Seção 28: Testa que data outputs calculados continuam disponíveis para consumidores downstream."""
    graph_data = {
        "nodes": [
            {
                "id": "evt_start",
                "type": "event_start",
                "properties": {},
            },
            {
                "id": "action_calc",
                "type": "custom_script",
                "properties": {
                    "execution_model": "action",
                    "inputs": [{"name": "base", "type": "number", "default": 100.0}],
                    "outputs": [{"name": "final", "type": "number"}],
                    "script": "ctx.set_output('final', ctx.get_input('base') + 50.0)\nctx.emit('next')",
                },
            },
            {
                "id": "set_var",
                "type": "set_variable",
                "properties": {"name": "result_var", "scope": "object"},
            },
        ],
        "edges": [
            {"from_node": "evt_start", "from_port": "next", "to_node": "action_calc", "to_port": "in"},
            {"from_node": "action_calc", "from_port": "next", "to_node": "set_var", "to_port": "in"},
            {"from_node": "action_calc", "from_port": "final", "to_node": "set_var", "to_port": "value"},
        ],
        "variables": {"result_var": {"type": "number", "scope": "object", "default": 0}},
    }

    runtime = LogicGraphRuntime(graph_data)
    runtime.start(None)

    assert runtime.variables["result_var"] == 150.0


def test_custom_action_script_save_and_reopen():
    """Seção 29: Testa serialização e reabertura de grafo com Action Custom Script."""
    original_graph = {
        "nodes": [
            {
                "id": "saved_action_node",
                "type": "custom_script",
                "title": "Saved Action",
                "properties": {
                    "execution_model": "action",
                    "inputs": [{"name": "spd", "type": "number", "default": 12.5}],
                    "outputs": [{"name": "dist", "type": "number"}],
                    "script": "ctx.set_output('dist', ctx.get_input('spd') * 2.0)\nctx.emit('next')",
                },
            }
        ],
        "edges": [],
    }

    normalized = normalize_logic_graph(original_graph)
    json_str = json.dumps(normalized)
    loaded_graph = json.loads(json_str)

    runtime = LogicGraphRuntime(loaded_graph)
    node = runtime.nodes["saved_action_node"]
    assert runtime._execute(node, None, 0.0) == ["next"]
    assert runtime.values[("saved_action_node", "dist")] == 25.0

    ports = node_port_definitions(loaded_graph["nodes"][0])
    assert ports["inputs"] == [("in", "flow"), ("spd", "number")]
    assert ports["outputs"] == [("next", "flow"), ("failure", "flow"), ("dist", "number")]
