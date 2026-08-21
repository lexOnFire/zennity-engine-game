"""
Integration tests for Guard Interaction and Gate Progression Pipeline.
Phase 13 Item 13.1-K Non-Vacuity Suite.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pytest

from engine.logic.graph_asset import load_logic_graph, normalize_logic_graph
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.event_bus import LogicEventBus
from engine.logic.blackboard import BlackboardStore


class MockGameObject:
    def __init__(self, name: str, tag: str):
        self.name = name
        self.tag = tag
        self.destroyed = False
        self.sounds_played: list[str] = []
        self.ui_texts: dict[str, str] = {}

    def play_sound(self, path: str) -> None:
        self.sounds_played.append(path)

    def destroy(self, target: Any = None) -> None:
        self.destroyed = True

    def set_ui_text(self, element: str, text: str) -> None:
        self.ui_texts[element] = text


def _build_runtime(graph_path: str, store: BlackboardStore, bus: LogicEventBus, object_key: str):
    graph = normalize_logic_graph(load_logic_graph(Path(graph_path)))
    rt = LogicGraphRuntime(graph, store, object_key, bus)
    return rt


def test_a_player_without_key_does_not_open_gate():
    """TEST A (Negative Control): Player interacts with Guard when has_key=False -> gate_opened is not emitted and Door stays locked."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("project", "has_key", False, "")
    store.set("object", "locked", True, "Door")

    rt_guard = _build_runtime("Assets/Logic/GuardInteractionLogic.zlogic", store, bus, "Guard")
    rt_door = _build_runtime("Assets/Logic/DoorLogic.zlogic", store, bus, "Door")

    guard = MockGameObject("Guard", "NPC")
    door = MockGameObject("Door", "Door")
    player = MockGameObject("Player", "Player")

    rt_guard.start(guard)
    rt_door.start(door)

    # Interação com o Guard sem a chave
    rt_guard.trigger_event("event_trigger_enter", guard, 0.016, player)
    bus.dispatch()

    assert store.get("object", "locked", "Door") is True
    assert door.destroyed is False
    assert len(door.sounds_played) == 0


def test_b_player_with_key_emits_gate_opened():
    """TEST B: Player interacts with Guard when has_key=True -> emits gate_opened and opens Door."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("project", "has_key", True, "")
    store.set("object", "locked", True, "Door")

    rt_guard = _build_runtime("Assets/Logic/GuardInteractionLogic.zlogic", store, bus, "Guard")
    rt_door = _build_runtime("Assets/Logic/DoorLogic.zlogic", store, bus, "Door")

    guard = MockGameObject("Guard", "NPC")
    door = MockGameObject("Door", "Door")
    player = MockGameObject("Player", "Player")

    rt_guard.start(guard)
    rt_door.start(door)

    # Interação do Player tendo a chave
    rt_guard.trigger_event("event_trigger_enter", guard, 0.016, player)
    bus.dispatch()

    assert store.get("object", "locked", "Door") is False
    assert door.destroyed is True
    assert "door_open" in door.sounds_played


def test_c_non_player_interaction_does_not_open_gate():
    """TEST C (Negative Control): Non-player object (e.g. Enemy) enters Guard trigger with has_key=True -> gate_opened is NOT emitted."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("project", "has_key", True, "")
    store.set("object", "locked", True, "Door")

    rt_guard = _build_runtime("Assets/Logic/GuardInteractionLogic.zlogic", store, bus, "Guard")
    rt_door = _build_runtime("Assets/Logic/DoorLogic.zlogic", store, bus, "Door")

    guard = MockGameObject("Guard", "NPC")
    door = MockGameObject("Door", "Door")
    enemy = MockGameObject("Enemy", "Enemy")

    rt_guard.start(guard)
    rt_door.start(door)

    # Inimigo entra no trigger do Guard
    rt_guard.trigger_event("event_trigger_enter", guard, 0.016, enemy)
    bus.dispatch()

    assert store.get("object", "locked", "Door") is True
    assert door.destroyed is False
    assert len(door.sounds_played) == 0


def test_d_full_progression_key_to_guard_to_door():
    """TEST D (Full Progression Chain): Player collects Key -> project.has_key=True -> Player interacts with Guard -> Door unlocks and is destroyed."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("project", "has_key", False, "")
    store.set("object", "locked", True, "Door")

    rt_key = _build_runtime("Assets/Logic/KeyCollectionLogic.zlogic", store, bus, "Key")
    rt_guard = _build_runtime("Assets/Logic/GuardInteractionLogic.zlogic", store, bus, "Guard")
    rt_door = _build_runtime("Assets/Logic/DoorLogic.zlogic", store, bus, "Door")

    key_host = MockGameObject("Key", "Key")
    guard = MockGameObject("Guard", "NPC")
    door = MockGameObject("Door", "Door")
    player = MockGameObject("Player", "Player")

    rt_key.start(key_host)
    rt_guard.start(guard)
    rt_door.start(door)

    # 1. Player tenta falar com Guard antes de ter a chave
    rt_guard.trigger_event("event_trigger_enter", guard, 0.016, player)
    bus.dispatch()
    assert store.get("object", "locked", "Door") is True
    assert door.destroyed is False

    # 2. Player coleta a chave
    rt_key.trigger_event("event_trigger_enter", key_host, 0.016, player)
    bus.dispatch()
    assert store.get("project", "has_key", "") is True
    assert key_host.destroyed is True

    # 3. Player retorna e interage com o Guard
    rt_guard.trigger_event("event_trigger_enter", guard, 0.016, player)
    bus.dispatch()

    # 4. Porta destrancada e passagem liberada
    assert store.get("object", "locked", "Door") is False
    assert door.destroyed is True
    assert "door_open" in door.sounds_played


def test_e_single_emission_idempotency():
    """TEST E: Exactly one gate_opened event is emitted per valid interaction."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("project", "has_key", True, "")
    store.set("object", "locked", True, "Door")

    rt_guard = _build_runtime("Assets/Logic/GuardInteractionLogic.zlogic", store, bus, "Guard")
    rt_door = _build_runtime("Assets/Logic/DoorLogic.zlogic", store, bus, "Door")

    guard = MockGameObject("Guard", "NPC")
    door = MockGameObject("Door", "Door")
    player = MockGameObject("Player", "Player")

    rt_guard.start(guard)
    rt_door.start(door)

    rt_guard.trigger_event("event_trigger_enter", guard, 0.016, player)
    bus.dispatch()

    assert store.get("object", "locked", "Door") is False
    assert door.destroyed is True
    assert door.sounds_played == ["door_open"]


def test_f_repeated_interaction_safety():
    """TEST F: Subsequent interactions after door is already opened do not break state or cause duplications."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("project", "has_key", True, "")
    store.set("object", "locked", True, "Door")

    rt_guard = _build_runtime("Assets/Logic/GuardInteractionLogic.zlogic", store, bus, "Guard")
    rt_door = _build_runtime("Assets/Logic/DoorLogic.zlogic", store, bus, "Door")

    guard = MockGameObject("Guard", "NPC")
    door = MockGameObject("Door", "Door")
    player = MockGameObject("Player", "Player")

    rt_guard.start(guard)
    rt_door.start(door)

    # Primeira interação válida
    rt_guard.trigger_event("event_trigger_enter", guard, 0.016, player)
    bus.dispatch()

    # Segunda interação
    rt_guard.trigger_event("event_trigger_enter", guard, 0.016, player)
    bus.dispatch()

    assert store.get("object", "locked", "Door") is False
    assert door.destroyed is True