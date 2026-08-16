"""Testes funcionais e de runtime para o Custom Script Node (Pure Data)."""
from __future__ import annotations

import json
from engine.logic.graph_asset import normalize_logic_graph, node_port_definitions
from engine.logic.runtime.core import LogicGraphRuntime


def test_custom_script_calculate_damage():
    """Testa o nó Calculate Damage do MVP (base_damage * multiplier -> damage)."""
    graph_data = {
        "nodes": [
            {
                "id": "calc_1",
                "type": "custom_script",
                "title": "Calculate Damage",
                "properties": {
                    "inputs": [
                        {"name": "base_damage", "type": "number", "default": 10.0},
                        {"name": "multiplier", "type": "number", "default": 2.5},
                    ],
                    "outputs": [
                        {"name": "damage", "type": "number"},
                    ],
                    "script": (
                        "base = ctx.get_input('base_damage')\n"
                        "mult = ctx.get_input('multiplier')\n"
                        "ctx.set_output('damage', base * mult)"
                    ),
                },
            }
        ],
        "edges": [],
    }

    runtime = LogicGraphRuntime(graph_data)
    result = runtime._evaluate_output("calc_1", "damage", None, 0.0, set())
    assert result == 25.0


def test_custom_script_multi_output_coherent_evaluation():
    """Testa múltiplos outputs avaliados coherentemente no mesmo nó."""
    graph_data = {
        "nodes": [
            {
                "id": "multi_calc",
                "type": "custom_script",
                "title": "Math Multi",
                "properties": {
                    "inputs": [
                        {"name": "a", "type": "number", "default": 10.0},
                        {"name": "b", "type": "number", "default": 3.0},
                    ],
                    "outputs": [
                        {"name": "sum", "type": "number"},
                        {"name": "difference", "type": "number"},
                    ],
                    "script": (
                        "a = ctx.get_input('a')\n"
                        "b = ctx.get_input('b')\n"
                        "ctx.set_output('sum', a + b)\n"
                        "ctx.set_output('difference', a - b)"
                    ),
                },
            }
        ],
        "edges": [],
    }

    runtime = LogicGraphRuntime(graph_data)
    sum_val = runtime._evaluate_output("multi_calc", "sum", None, 0.0, set())
    diff_val = runtime._evaluate_output("multi_calc", "difference", None, 0.0, set())

    assert sum_val == 13.0
    assert diff_val == 7.0


def test_custom_script_preserves_zero_false_empty_string():
    """Testa que 0, False e '' não são mascarados por fallbacks/defaults falsos."""
    graph_data = {
        "nodes": [
            {
                "id": "zero_false_node",
                "type": "custom_script",
                "title": "Falsy Test",
                "properties": {
                    "inputs": [
                        {"name": "num", "type": "number", "default": 0},
                        {"name": "flag", "type": "bool", "default": False},
                        {"name": "txt", "type": "text", "default": ""},
                    ],
                    "outputs": [
                        {"name": "num_out", "type": "number"},
                        {"name": "flag_out", "type": "bool"},
                        {"name": "txt_out", "type": "text"},
                    ],
                    "script": (
                        "n = ctx.get_input('num', 999)\n"
                        "f = ctx.get_input('flag', True)\n"
                        "t = ctx.get_input('txt', 'fallback')\n"
                        "ctx.set_output('num_out', n)\n"
                        "ctx.set_output('flag_out', f)\n"
                        "ctx.set_output('txt_out', t)"
                    ),
                },
            }
        ],
        "edges": [],
    }

    runtime = LogicGraphRuntime(graph_data)
    assert runtime._evaluate_output("zero_false_node", "num_out", None, 0.0, set()) == 0
    assert runtime._evaluate_output("zero_false_node", "flag_out", None, 0.0, set()) is False
    assert runtime._evaluate_output("zero_false_node", "txt_out", None, 0.0, set()) == ""


def test_custom_script_save_and_reopen_roundtrip():
    """Testa serialização, normalização e recarregamento sem perda de dados."""
    original_graph = {
        "nodes": [
            {
                "id": "custom_node_save_test",
                "type": "custom_script",
                "title": "Saved Node",
                "properties": {
                    "inputs": [{"name": "x", "type": "number", "default": 5.0}],
                    "outputs": [{"name": "doubled", "type": "number"}],
                    "script": "ctx.set_output('doubled', ctx.get_input('x') * 2)",
                },
            }
        ],
        "edges": [],
    }

    # Normaliza e simula roundtrip em JSON
    normalized = normalize_logic_graph(original_graph)
    json_str = json.dumps(normalized)
    loaded_graph = json.loads(json_str)

    # Reavalia após carregamento
    runtime = LogicGraphRuntime(loaded_graph)
    val = runtime._evaluate_output("custom_node_save_test", "doubled", None, 0.0, set())
    assert val == 10.0

    # Valida extração de portas
    ports = node_port_definitions(loaded_graph["nodes"][0])
    assert ports["inputs"] == [("x", "number")]
    assert ports["outputs"] == [("doubled", "number")]
