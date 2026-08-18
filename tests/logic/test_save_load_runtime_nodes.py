"""Testes dos nós de runtime de Save/Load integrados ao SaveManager (Pre-Phase 13 Sprint R2)."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import pytest

from engine.core.save_manager import SaveManager
from engine.logic.runtime.nodes.save_load_nodes import (
    execute_delete_save,
    execute_has_save,
    execute_load_game,
    execute_save_game,
)


def test_save_load_persistent_roundtrip(tmp_path: Path):
    """Valida ciclo completo de save, has_save, load e delete_save com persistência real em disco."""
    sm = SaveManager(save_directory=tmp_path)
    game = SimpleNamespace(save_manager=sm, current_scene=SimpleNamespace(name="Level1"))
    runtime_a = SimpleNamespace(
        _variables={"player_hp": 100, "coins": 42},
        _state_machines={"combat": "IDLE"},
        _stored={},
        _store=lambda nid, k, v: runtime_a._stored.setdefault(nid, {}).__setitem__(k, v),
    )

    # 1. Salvar jogo no slot_1
    save_node = {"id": "save_node", "properties": {"slot_name": "slot_1", "include_scene": True}}
    save_ports = execute_save_game(runtime_a, save_node, game, 0.016)
    assert save_ports == ["exec_saved"]

    # Confirma existência de arquivo real no disco
    save_file = tmp_path / "slot_1.json"
    assert save_file.exists()

    # 2. has_save retorna exec_exists
    has_node = {"id": "has_node", "properties": {"slot_name": "slot_1"}}
    assert execute_has_save(runtime_a, has_node, game, 0.016) == ["exec_exists"]

    # 3. Carregar em uma nova instância limpa de runtime (Cross-Runtime Persistence)
    runtime_b = SimpleNamespace(
        _variables={},
        _state_machines={},
        _stored={},
        _store=lambda nid, k, v: runtime_b._stored.setdefault(nid, {}).__setitem__(k, v),
    )
    load_node = {"id": "load_node", "properties": {"slot_name": "slot_1"}}
    load_ports = execute_load_game(runtime_b, load_node, game, 0.016)
    assert load_ports == ["exec_loaded"]

    # Confirma que os dados foram restaurados corretamente
    assert runtime_b._variables["player_hp"] == 100
    assert runtime_b._variables["coins"] == 42
    assert runtime_b._state_machines["combat"] == "IDLE"

    # 4. delete_save remove o arquivo
    del_node = {"id": "del_node", "properties": {"slot_name": "slot_1"}}
    assert execute_delete_save(runtime_b, del_node, game, 0.016) == ["exec_deleted"]
    assert not save_file.exists()
    assert execute_has_save(runtime_b, has_node, game, 0.016) == ["exec_not_exists"]


def test_save_path_traversal_protection(tmp_path: Path):
    """Valida que tentativas de path traversal (ex: '../outside') são rejeitadas com exec_failure."""
    sm = SaveManager(save_directory=tmp_path)
    game = SimpleNamespace(save_manager=sm)
    runtime = SimpleNamespace(
        _variables={"secret": 123},
        _stored={},
        _store=lambda nid, k, v: None,
    )

    bad_save_node = {"id": "n1", "properties": {"slot_name": "../hacked"}}
    assert execute_save_game(runtime, bad_save_node, game, 0.016) == ["exec_failure"]
    assert not (tmp_path.parent / "hacked.json").exists()


def test_load_corrupted_file_fails(tmp_path: Path):
    """Valida que arquivo de save corrompido retorna exec_failure e não altera o runtime."""
    sm = SaveManager(save_directory=tmp_path)
    game = SimpleNamespace(save_manager=sm)
    runtime = SimpleNamespace(_variables={"initial": 1}, _stored={}, _store=lambda n, k, v: None)

    # Cria arquivo JSON corrompido
    corrupt_file = tmp_path / "corrupt_slot.json"
    corrupt_file.write_text("{ corrupt json ...", encoding="utf-8")

    load_node = {"id": "n1", "properties": {"slot_name": "corrupt_slot"}}
    assert execute_load_game(runtime, load_node, game, 0.016) == ["exec_failure"]
    assert runtime._variables == {"initial": 1}
