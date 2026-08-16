"""Suíte integrada de teste e validação de fechamento da PRE-PHASE 10 (Item D3)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.logic.blackboard import BlackboardStore
from engine.logic.custom_node_asset import (
    load_custom_node_asset,
    save_custom_node_asset,
    validate_custom_node_asset,
)
from engine.logic.custom_node_registry import CustomNodeRegistry
from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    create_logic_node,
    default_logic_graph,
    node_port_definitions,
    normalize_logic_graph,
)
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.runtime.custom_script_sandbox import (
    ALLOWED_BUILTINS,
    validate_custom_script,
)


def test_d3_pure_data_end_to_end():
    """Seção 5: Pure Data End-to-End no Runtime."""
    graph = {
        "nodes": [
            {
                "id": "calc_pure",
                "type": "custom_script",
                "properties": {
                    "execution_model": "pure_data",
                    "inputs": [
                        {"name": "base_damage", "type": "number", "default": 10.0},
                        {"name": "multiplier", "type": "number", "default": 2.5},
                    ],
                    "outputs": [{"name": "damage", "type": "number"}],
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

    runtime = LogicGraphRuntime(graph)
    res = runtime._evaluate_output("calc_pure", "damage", None, 0.0, set())
    assert res == 25.0


def test_d3_pure_data_multi_output_coherent_evaluation():
    """Seção 6: Pure Data Multi-Output com 1 execução por passagem coerente."""
    graph = {
        "nodes": [
            {
                "id": "multi_out_node",
                "type": "custom_script",
                "properties": {
                    "execution_model": "pure_data",
                    "inputs": [
                        {"name": "a", "type": "number", "default": 10.0},
                        {"name": "b", "type": "number", "default": 3.0},
                    ],
                    "outputs": [
                        {"name": "sum", "type": "number"},
                        {"name": "difference", "type": "number"},
                        {"name": "product", "type": "number"},
                    ],
                    "script": (
                        "a = ctx.get_input('a')\n"
                        "b = ctx.get_input('b')\n"
                        "ctx.set_output('sum', a + b)\n"
                        "ctx.set_output('difference', a - b)\n"
                        "ctx.set_output('product', a * b)"
                    ),
                },
            }
        ],
        "edges": [],
    }

    runtime = LogicGraphRuntime(graph)
    s = runtime._evaluate_output("multi_out_node", "sum", None, 0.0, set())
    d = runtime._evaluate_output("multi_out_node", "difference", None, 0.0, set())
    p = runtime._evaluate_output("multi_out_node", "product", None, 0.0, set())

    assert s == 13.0
    assert d == 7.0
    assert p == 30.0


def test_d3_falsy_values_gate():
    """Seção 7: Preservação exata de valores falsy (0, 0.0, False, '')."""
    graph = {
        "nodes": [
            {
                "id": "falsy_node",
                "type": "custom_script",
                "properties": {
                    "execution_model": "pure_data",
                    "inputs": [
                        {"name": "zero_int", "type": "number", "default": 0},
                        {"name": "zero_flt", "type": "number", "default": 0.0},
                        {"name": "bool_f", "type": "bool", "default": False},
                        {"name": "empty_s", "type": "text", "default": ""},
                    ],
                    "outputs": [
                        {"name": "out_0i", "type": "number"},
                        {"name": "out_0f", "type": "number"},
                        {"name": "out_bf", "type": "bool"},
                        {"name": "out_es", "type": "text"},
                    ],
                    "script": (
                        "ctx.set_output('out_0i', ctx.get_input('zero_int', 99))\n"
                        "ctx.set_output('out_0f', ctx.get_input('zero_flt', 99.0))\n"
                        "ctx.set_output('out_bf', ctx.get_input('bool_f', True))\n"
                        "ctx.set_output('out_es', ctx.get_input('empty_s', 'fallback'))"
                    ),
                },
            }
        ],
        "edges": [],
    }

    runtime = LogicGraphRuntime(graph)
    assert runtime._evaluate_output("falsy_node", "out_0i", None, 0.0, set()) == 0
    assert runtime._evaluate_output("falsy_node", "out_0f", None, 0.0, set()) == 0.0
    assert runtime._evaluate_output("falsy_node", "out_bf", None, 0.0, set()) is False
    assert runtime._evaluate_output("falsy_node", "out_es", None, 0.0, set()) == ""


def test_d3_action_script_pipelines():
    """Seções 8, 9, 10, 11, 12, 13: Action Script Success, Default Next, Failure, Exception, Multiple Emit."""
    # Action Success
    g_success = {
        "nodes": [
            {
                "id": "act_success",
                "type": "custom_script",
                "properties": {
                    "execution_model": "action",
                    "inputs": [{"name": "damage", "type": "number", "default": 25.0}],
                    "outputs": [{"name": "result", "type": "number"}],
                    "script": "ctx.set_output('result', ctx.get_input('damage') * 2)\nctx.emit('next')",
                },
            }
        ],
        "edges": [],
    }
    r_success = LogicGraphRuntime(g_success)
    assert r_success._execute(r_success.nodes["act_success"], None, 0.0) == ["next"]
    assert r_success.values[("act_success", "result")] == 50.0

    # Action Default Next
    g_def = {
        "nodes": [
            {
                "id": "act_def",
                "type": "custom_script",
                "properties": {
                    "execution_model": "action",
                    "inputs": [{"name": "damage", "type": "number", "default": 15.0}],
                    "outputs": [{"name": "result", "type": "number"}],
                    "script": "ctx.set_output('result', ctx.get_input('damage'))",
                },
            }
        ],
        "edges": [],
    }
    r_def = LogicGraphRuntime(g_def)
    assert r_def._execute(r_def.nodes["act_def"], None, 0.0) == ["next"]

    # Action Explicit Failure
    g_fail = {
        "nodes": [
            {
                "id": "act_fail",
                "type": "custom_script",
                "properties": {
                    "execution_model": "action",
                    "inputs": [{"name": "val", "type": "number", "default": -5.0}],
                    "outputs": [],
                    "script": "if ctx.get_input('val') < 0: ctx.emit('failure')",
                },
            }
        ],
        "edges": [],
    }
    r_fail = LogicGraphRuntime(g_fail)
    assert r_fail._execute(r_fail.nodes["act_fail"], None, 0.0) == ["failure"]

    # Action Runtime Exception (Div Zero) -> failure
    g_exc = {
        "nodes": [
            {
                "id": "act_exc",
                "type": "custom_script",
                "properties": {
                    "execution_model": "action",
                    "inputs": [],
                    "outputs": [],
                    "script": "x = 10 / 0",
                },
            }
        ],
        "edges": [],
    }
    r_exc = LogicGraphRuntime(g_exc)
    assert r_exc._execute(r_exc.nodes["act_exc"], None, 0.0) == ["failure"]


def test_d3_ast_security_matrix():
    """Seção 14: Matriz completa de segurança AST."""
    forbidden_snippets = [
        "import os",
        "from os import system",
        "eval('1+1')",
        "exec('x=1')",
        "open('file.txt')",
        "__import__('os')",
        "x = ().__class__",
        "x = object.__subclasses__",
        "x = getattr(ctx, 'outputs')",
        "setattr(ctx, 'foo', 1)",
        "while True: pass",
        "f = lambda: 1",
        "class X: pass",
        "def evil(): pass",
    ]

    for snippet in forbidden_snippets:
        valid, err = validate_custom_script(snippet, {"in"}, {"out"}, execution_model="pure_data")
        assert valid is False, f"Snippet permitido indevidamente: {snippet}"


def test_d3_blackboard_and_custom_script_integration():
    """Seções 19, 20, 21: Integração Blackboard + Custom Script (Object Scope Isolation)."""
    graph = {
        "nodes": [
            {
                "id": "evt",
                "type": "event_start",
                "properties": {},
            },
            {
                "id": "get_hp",
                "type": "get_variable",
                "properties": {"name": "health", "scope": "object"},
            },
            {
                "id": "calc_dmg",
                "type": "custom_script",
                "properties": {
                    "execution_model": "action",
                    "inputs": [{"name": "hp_in", "type": "number", "default": 0}],
                    "outputs": [{"name": "dmg_out", "type": "number"}],
                    "script": "ctx.set_output('dmg_out', ctx.get_input('hp_in') - 20)\nctx.emit('next')",
                },
            },
            {
                "id": "set_hp",
                "type": "set_variable",
                "properties": {"name": "health", "scope": "object"},
            },
        ],
        "edges": [
            {"from_node": "evt", "from_port": "next", "to_node": "calc_dmg", "to_port": "in"},
            {"from_node": "get_hp", "from_port": "value", "to_node": "calc_dmg", "to_port": "hp_in"},
            {"from_node": "calc_dmg", "from_port": "next", "to_node": "set_hp", "to_port": "in"},
            {"from_node": "calc_dmg", "from_port": "dmg_out", "to_node": "set_hp", "to_port": "value"},
        ],
        "variables": {"health": {"type": "number", "scope": "object", "default": 100.0}},
    }

    store = BlackboardStore()
    store.set("object", "health", 100.0, "Enemy_1")
    store.set("object", "health", 50.0, "Enemy_2")

    # Executa Enemy_1 (100 -> 80)
    rt1 = LogicGraphRuntime(graph, store, "Enemy_1")
    rt1.start(None)
    assert store.get("object", "health", "Enemy_1") == 80.0

    # Executa Enemy_2 (50 -> 30)
    rt2 = LogicGraphRuntime(graph, store, "Enemy_2")
    rt2.start(None)
    assert store.get("object", "health", "Enemy_2") == 30.0


def test_d3_reusable_znode_lifecycle(tmp_path: Path):
    """Seções 24 a 37: Ciclo completo do .znode (Export, Discovery, Normalizer, Snapshot Semantics, Delete)."""
    custom_dir = tmp_path / "Assets" / "Logic" / "CustomNodes"
    custom_dir.mkdir(parents=True, exist_ok=True)
    znode_path = custom_dir / "stat_calculator.znode"

    # Export / Save
    save_custom_node_asset(
        znode_path,
        {
            "node_id": "stat_calculator",
            "title": "Stat Calculator",
            "category": "Custom",
            "execution_model": "pure_data",
            "inputs": [{"name": "lvl", "type": "number", "default": 1.0}],
            "outputs": [{"name": "stat", "type": "number"}],
            "script": "ctx.set_output('stat', ctx.get_input('lvl') * 15.0)",
        },
    )

    registry = CustomNodeRegistry(tmp_path)
    registry.refresh()
    assert "stat_calculator" in registry.nodes

    # Instanciação no grafo
    inst1 = registry.instantiate_node_data("stat_calculator", "inst_1")
    graph = default_logic_graph("IntegrationGraph")
    graph["nodes"] = [inst1]

    # Normalização
    norm_graph = normalize_logic_graph(graph)
    assert len(norm_graph["nodes"]) == 1
    assert norm_graph["nodes"][0]["properties"]["custom_asset_id"] == "stat_calculator"

    # Execução
    rt = LogicGraphRuntime(norm_graph)
    assert rt._evaluate_output("inst_1", "stat", None, 0.0, set()) == 15.0
