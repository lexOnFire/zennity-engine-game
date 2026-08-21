"""
Integration tests for Player Facing Direction & Directional Combat Flow.
Phase 13 Item 13.1-G Non-Vacuity Suite.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.logic.graph_asset import load_logic_graph, normalize_logic_graph
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.event_bus import LogicEventBus
from engine.logic.blackboard import BlackboardStore


class DummyTarget:
    def __init__(self, name: str, tag: str, x: float, y: float):
        self.name = name
        self.tag = tag
        self.x = x
        self.y = y
        self.active = True


class MockCombatGameHost:
    def __init__(self, player_x: float = 100.0, player_y: float = 100.0, axis_val: float = 0.0):
        self.name = "Player"
        self.x = player_x
        self.y = player_y
        self.axis_val = axis_val
        self.objects: dict[str, dict] = {
            "Player": {"name": "Player", "tag": "Player", "x": self.x, "y": self.y, "active": True}
        }
        self.entities: list[DummyTarget] = []

    def add_target(self, name: str, tag: str, x: float, y: float) -> DummyTarget:
        t = DummyTarget(name, tag, x, y)
        self.entities.append(t)
        self.objects[name] = {"name": name, "tag": tag, "x": x, "y": y, "active": True}
        return t

    @property
    def _world(self) -> dict[str, dict]:
        return self.objects

    def axis(self, neg: str, pos: str) -> float:
        return float(self.axis_val)

    def move(self, dx: float) -> None:
        self.x += dx
        self.objects["Player"]["x"] = self.x

    def move_y(self, dy: float) -> None:
        self.y += dy
        self.objects["Player"]["y"] = self.y

    def key_pressed(self, k: str) -> bool:
        return k.upper() == "SPACE"


def _build_player_runtime(store: BlackboardStore, bus: LogicEventBus):
    g_move = normalize_logic_graph(load_logic_graph(Path("Assets/Logic/PlayerMovementLogic.zlogic")))
    g_combat = normalize_logic_graph(load_logic_graph(Path("Assets/Logic/PlayerCombatLogic.zlogic")))
    rt_move = LogicGraphRuntime(g_move, store, "Player", bus)
    rt_combat = LogicGraphRuntime(g_combat, store, "Player", bus)
    return rt_move, rt_combat


def test_a_left_movement_writes_facing_negative():
    """TEST A: Moving left writes facing_x = -1.0."""
    store = BlackboardStore()
    bus = LogicEventBus()
    rt_move, _ = _build_player_runtime(store, bus)
    game = MockCombatGameHost(axis_val=-1.0)
    rt_move.start(game)
    rt_move.update(game, 0.016)

    assert store.get("object", "facing_x", "Player") == -1.0


def test_b_right_movement_writes_facing_positive():
    """TEST B: Moving right from an initially left-facing state writes facing_x = +1.0."""
    store = BlackboardStore()
    bus = LogicEventBus()
    rt_move, _ = _build_player_runtime(store, bus)
    game = MockCombatGameHost(axis_val=1.0)
    rt_move.start(game)
    # Força estado anterior para esquerda
    store.set("object", "facing_x", -1.0, "Player")
    assert store.get("object", "facing_x", "Player") == -1.0

    # Movimenta para a direita
    rt_move.update(game, 0.016)
    assert store.get("object", "facing_x", "Player") == 1.0


def test_c_idle_preserves_last_facing_direction():
    """TEST C: Stopping (axis=0) preserves the previous facing direction."""
    store = BlackboardStore()
    bus = LogicEventBus()
    rt_move, _ = _build_player_runtime(store, bus)

    # 1. Move para a esquerda
    game = MockCombatGameHost(axis_val=-1.0)
    rt_move.start(game)
    rt_move.update(game, 0.016)
    assert store.get("object", "facing_x", "Player") == -1.0

    # 2. Para (idle, axis=0)
    game.axis_val = 0.0
    rt_move.update(game, 0.016)
    assert store.get("object", "facing_x", "Player") == -1.0


def test_d_attack_left_deals_damage_to_enemy_at_left():
    """TEST D: Moving left and attacking hits enemy at left."""
    store = BlackboardStore()
    bus = LogicEventBus()
    rt_move, rt_combat = _build_player_runtime(store, bus)

    received_damage = []
    bus.subscribe("enemy_damage", lambda e: received_damage.append(e.payload))

    game = MockCombatGameHost(player_x=100.0, axis_val=-1.0)
    game.add_target("Enemy", "Enemy", x=60.0, y=100.0)

    rt_move.start(game)
    rt_combat.start(game)

    # Frame 1: Move left
    rt_move.update(game, 0.016)
    # Frame 2: Attack
    rt_combat.update(game, 0.016)
    bus.dispatch()

    assert received_damage == [25.0]


def test_e_attack_right_deals_damage_to_enemy_at_right():
    """TEST E: Facing right and attacking hits enemy at right."""
    store = BlackboardStore()
    bus = LogicEventBus()
    rt_move, rt_combat = _build_player_runtime(store, bus)

    received_damage = []
    bus.subscribe("enemy_damage", lambda e: received_damage.append(e.payload))

    game = MockCombatGameHost(player_x=100.0, axis_val=1.0)
    game.add_target("Enemy", "Enemy", x=140.0, y=100.0)

    rt_move.start(game)
    rt_combat.start(game)

    # Força orientação prévia para esquerda para testar transição
    store.set("object", "facing_x", -1.0, "Player")

    # Frame 1: Move right
    rt_move.update(game, 0.016)
    # Frame 2: Attack
    rt_combat.update(game, 0.016)
    bus.dispatch()

    assert received_damage == [25.0]


def test_f_backwards_attack_blocked_negative_control():
    """TEST F: Attacking while facing left does NOT hit enemy behind player at right."""
    store = BlackboardStore()
    bus = LogicEventBus()
    rt_move, rt_combat = _build_player_runtime(store, bus)

    received_damage = []
    bus.subscribe("enemy_damage", lambda e: received_damage.append(e.payload))

    game = MockCombatGameHost(player_x=100.0, axis_val=-1.0)
    # Inimigo está atrás do player (à direita)
    game.add_target("Enemy", "Enemy", x=140.0, y=100.0)

    rt_move.start(game)
    rt_combat.start(game)

    # Move left
    rt_move.update(game, 0.016)
    # Attack
    rt_combat.update(game, 0.016)
    bus.dispatch()

    assert received_damage == []


def test_g_boss_attack_left_and_right():
    """TEST G: Player attacks boss on left and right correctly."""
    # 1. Boss on left
    store1 = BlackboardStore()
    bus1 = LogicEventBus()
    rt_move1, rt_combat1 = _build_player_runtime(store1, bus1)
    boss_damage_left = []
    bus1.subscribe("boss_damage", lambda e: boss_damage_left.append(e.payload))

    game1 = MockCombatGameHost(player_x=100.0, axis_val=-1.0)
    game1.add_target("Boss", "Boss", x=50.0, y=100.0)
    rt_move1.start(game1)
    rt_combat1.start(game1)
    rt_move1.update(game1, 0.016)
    rt_combat1.update(game1, 0.016)
    bus1.dispatch()
    assert boss_damage_left == [25.0]

    # 2. Boss on right
    store2 = BlackboardStore()
    bus2 = LogicEventBus()
    rt_move2, rt_combat2 = _build_player_runtime(store2, bus2)
    boss_damage_right = []
    bus2.subscribe("boss_damage", lambda e: boss_damage_right.append(e.payload))

    game2 = MockCombatGameHost(player_x=100.0, axis_val=1.0)
    game2.add_target("Boss", "Boss", x=150.0, y=100.0)
    store2.set("object", "facing_x", -1.0, "Player")
    rt_move2.start(game2)
    rt_combat2.start(game2)
    rt_move2.update(game2, 0.016)
    rt_combat2.update(game2, 0.016)
    bus2.dispatch()
    assert boss_damage_right == [25.0]