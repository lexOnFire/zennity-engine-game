"""Testes de unidade e integração para assets .znode (D2.4)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.logic.custom_node_asset import (
    CUSTOM_NODE_FORMAT,
    CUSTOM_NODE_FORMAT_VERSION,
    load_custom_node_asset,
    save_custom_node_asset,
    validate_custom_node_asset,
)
from engine.logic.custom_node_registry import CustomNodeRegistry
from engine.logic.runtime.core import LogicGraphRuntime


def test_custom_node_asset_save_and_load(tmp_path: Path):
    """Testa salvamento e carregamento determinístico de um asset .znode."""
    node_file = tmp_path / "Assets" / "Logic" / "CustomNodes" / "calculate_damage.znode"
    data = {
        "node_id": "calculate_damage",
        "title": "Calculate Damage",
        "category": "Custom",
        "execution_model": "pure_data",
        "inputs": [
            {"name": "base", "type": "number", "default": 10.0},
            {"name": "mult", "type": "number", "default": 2.0},
        ],
        "outputs": [
            {"name": "damage", "type": "number"},
        ],
        "script": "ctx.set_output('damage', ctx.get_input('base') * ctx.get_input('mult'))",
    }

    save_custom_node_asset(node_file, data)
    assert node_file.exists()

    loaded = load_custom_node_asset(node_file)
    assert loaded["format"] == CUSTOM_NODE_FORMAT
    assert loaded["format_version"] == CUSTOM_NODE_FORMAT_VERSION
    assert loaded["node_id"] == "calculate_damage"
    assert loaded["title"] == "Calculate Damage"
    assert len(loaded["inputs"]) == 2
    assert len(loaded["outputs"]) == 1


def test_custom_node_builtin_collision_rejected(tmp_path: Path):
    """Testa que colisão de node_id com built-in (ex: compare_number ou move_by) é rejeitada."""
    data = {
        "node_id": "compare_number",
        "title": "My Compare Number",
        "category": "Custom",
        "execution_model": "pure_data",
        "inputs": [],
        "outputs": [],
        "script": "",
    }
    valid, err = validate_custom_node_asset(data)
    assert valid is False
    assert "Colisão de node_id" in err


def test_custom_node_duplicate_id_collision_handled(tmp_path: Path):
    """Testa que se dois assets tiverem o mesmo node_id, ambos são isolados pelo registry."""
    custom_dir = tmp_path / "Assets" / "Logic" / "CustomNodes"
    custom_dir.mkdir(parents=True, exist_ok=True)

    data1 = {
        "node_id": "calc_dup",
        "title": "Calc One",
        "category": "Custom",
        "execution_model": "pure_data",
        "inputs": [],
        "outputs": [],
        "script": "",
    }
    data2 = {
        "node_id": "calc_dup",
        "title": "Calc Two",
        "category": "Custom",
        "execution_model": "pure_data",
        "inputs": [],
        "outputs": [],
        "script": "",
    }

    save_custom_node_asset(custom_dir / "calc_one.znode", data1)
    save_custom_node_asset(custom_dir / "calc_two.znode", data2)

    registry = CustomNodeRegistry(tmp_path)
    registry.refresh()

    assert "calc_dup" not in registry.nodes
    assert "calc_dup" in registry.conflicts
    assert len(registry.conflicts["calc_dup"]) == 2


def test_custom_node_snapshot_semantics(tmp_path: Path):
    """Testa snapshot semantics: alterar o .znode NÃO afeta instâncias existentes no grafo."""
    custom_dir = tmp_path / "Assets" / "Logic" / "CustomNodes"
    custom_dir.mkdir(parents=True, exist_ok=True)
    znode_path = custom_dir / "damage_scale.znode"

    # Versão 1: result = a * 2
    save_custom_node_asset(
        znode_path,
        {
            "node_id": "damage_scale",
            "title": "Damage Scale",
            "execution_model": "pure_data",
            "inputs": [{"name": "a", "type": "number", "default": 5.0}],
            "outputs": [{"name": "result", "type": "number"}],
            "script": "ctx.set_output('result', ctx.get_input('a') * 2.0)",
        },
    )

    registry = CustomNodeRegistry(tmp_path)
    registry.refresh()

    # Instancia nó no grafo
    inst1 = registry.instantiate_node_data("damage_scale", "node_inst_1")

    # Versão 2: result = a * 10
    save_custom_node_asset(
        znode_path,
        {
            "node_id": "damage_scale",
            "title": "Damage Scale",
            "execution_model": "pure_data",
            "inputs": [{"name": "a", "type": "number", "default": 5.0}],
            "outputs": [{"name": "result", "type": "number"}],
            "script": "ctx.set_output('result', ctx.get_input('a') * 10.0)",
        },
    )
    registry.refresh()

    # Instancia segundo nó após mudança no asset
    inst2 = registry.instantiate_node_data("damage_scale", "node_inst_2")

    # Executa ambos em runtime
    graph = {"nodes": [inst1, inst2], "edges": []}
    runtime = LogicGraphRuntime(graph)

    res1 = runtime._evaluate_output("node_inst_1", "result", None, 0.0, set())
    res2 = runtime._evaluate_output("node_inst_2", "result", None, 0.0, set())

    assert res1 == 10.0  # Continua usando * 2
    assert res2 == 50.0  # Usa o novo * 10


def test_existing_instance_survives_znode_deletion(tmp_path: Path):
    """Testa que deletar o arquivo .znode não quebra a execução de grafos que contêm o nó."""
    custom_dir = tmp_path / "Assets" / "Logic" / "CustomNodes"
    custom_dir.mkdir(parents=True, exist_ok=True)
    znode_path = custom_dir / "temp_calc.znode"

    save_custom_node_asset(
        znode_path,
        {
            "node_id": "temp_calc",
            "title": "Temp Calc",
            "execution_model": "pure_data",
            "inputs": [{"name": "val", "type": "number", "default": 42.0}],
            "outputs": [{"name": "out", "type": "number"}],
            "script": "ctx.set_output('out', ctx.get_input('val') + 8.0)",
        },
    )

    registry = CustomNodeRegistry(tmp_path)
    registry.refresh()
    instance = registry.instantiate_node_data("temp_calc", "inst_survivor")

    # Deleta o arquivo .znode do disco
    znode_path.unlink()
    registry.refresh()
    assert "temp_calc" not in registry.nodes

    # Executa o grafo com a instância existente
    graph = {"nodes": [instance], "edges": []}
    runtime = LogicGraphRuntime(graph)
    val = runtime._evaluate_output("inst_survivor", "out", None, 0.0, set())
    assert val == 50.0


def test_action_reusable_custom_node(tmp_path: Path):
    """Testa asset .znode no modo Action com fluxo."""
    custom_dir = tmp_path / "Assets" / "Logic" / "CustomNodes"
    custom_dir.mkdir(parents=True, exist_ok=True)
    znode_path = custom_dir / "validate_positive.znode"

    save_custom_node_asset(
        znode_path,
        {
            "node_id": "validate_positive",
            "title": "Validate Positive",
            "execution_model": "action",
            "inputs": [{"name": "value", "type": "number", "default": 10.0}],
            "outputs": [{"name": "normalized", "type": "number"}],
            "script": (
                "val = ctx.get_input('value', 0)\n"
                "if val < 0:\n"
                "    ctx.emit('failure')\n"
                "else:\n"
                "    ctx.set_output('normalized', val)\n"
                "    ctx.emit('next')"
            ),
        },
    )

    registry = CustomNodeRegistry(tmp_path)
    registry.refresh()
    inst = registry.instantiate_node_data("validate_positive", "act_pos")

    graph = {"nodes": [inst], "edges": []}
    runtime = LogicGraphRuntime(graph)
    node = runtime.nodes["act_pos"]
    next_ports = runtime._execute(node, None, 0.0)

    assert next_ports == ["next"]
    assert runtime.values[("act_pos", "normalized")] == 10.0
