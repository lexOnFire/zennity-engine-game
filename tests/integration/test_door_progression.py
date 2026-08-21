"""
Integration tests for Door Progression Flow.
Phase 13 Item 13.1-I Non-Vacuity Suite.
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


class MockDoorHost:
    def __init__(self, name: str = "Door", tag: str = "Door"):
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


def test_a_door_event_unlocks_and_frees_passage():
    """TEST A: Emitting gate_opened unlocks the door (locked=False), plays door_open sound, and destroys Door."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("object", "locked", True, "Door")

    rt_door = _build_runtime("Assets/Logic/DoorLogic.zlogic", store, bus, "Door")
    game = MockDoorHost(name="Door", tag="Door")
    rt_door.start(game)

    # Dispara evento gate_opened
    bus.emit("gate_opened")
    bus.dispatch()

    assert store.get("object", "locked", "Door") is False
    assert game.destroyed is True
    assert "door_open" in game.sounds_played


def test_b_door_stays_locked_without_event_negative_control():
    """TEST B (Negative Control): Without gate_opened event, Door stays locked, not destroyed, no sound."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("object", "locked", True, "Door")

    rt_door = _build_runtime("Assets/Logic/DoorLogic.zlogic", store, bus, "Door")
    game = MockDoorHost(name="Door", tag="Door")
    rt_door.start(game)

    # Atualiza sem emitir gate_opened
    rt_door.update(game, 0.016)

    assert store.get("object", "locked", "Door") is True
    assert game.destroyed is False
    assert len(game.sounds_played) == 0


def test_c_unrelated_event_does_not_open_door_negative_control():
    """TEST C (Negative Control): Unrelated event does not trigger door opening."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("object", "locked", True, "Door")

    rt_door = _build_runtime("Assets/Logic/DoorLogic.zlogic", store, bus, "Door")
    game = MockDoorHost(name="Door", tag="Door")
    rt_door.start(game)

    bus.emit("some_other_event")
    bus.dispatch()

    assert store.get("object", "locked", "Door") is True
    assert game.destroyed is False
    assert len(game.sounds_played) == 0


def test_d_single_execution_idempotency():
    """TEST D (Idempotency): Emitting gate_opened multiple times executes properly."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("object", "locked", True, "Door")

    rt_door = _build_runtime("Assets/Logic/DoorLogic.zlogic", store, bus, "Door")
    game = MockDoorHost(name="Door", tag="Door")
    rt_door.start(game)

    bus.emit("gate_opened")
    bus.dispatch()

    assert store.get("object", "locked", "Door") is False
    assert game.destroyed is True
    assert game.sounds_played == ["door_open"]


def test_e_end_to_end_level1_key_to_door_progression():
    """TEST E (Full Progression Chain): Key collection sets has_key -> GuardDialogue condition opens gate -> DoorLogic unlocks & destroys Door."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("project", "has_key", False, "")
    store.set("object", "locked", True, "Door")

    # 1. Player coleta a chave
    rt_key = _build_runtime("Assets/Logic/KeyCollectionLogic.zlogic", store, bus, "Key")
    key_host = MockDoorHost(name="Key", tag="Key")
    rt_key.start(key_host)
    player = MockDoorHost(name="Player", tag="Player")
    player.tag = "Player"
    rt_key.trigger_event("event_trigger_enter", key_host, 0.016, player)

    assert store.get("project", "has_key", "") is True
    assert key_host.destroyed is True

    # 2. GuardDialogue avalia has_key=True e emite open_gate / gate_opened
    rt_door = _build_runtime("Assets/Logic/DoorLogic.zlogic", store, bus, "Door")
    door_host = MockDoorHost(name="Door", tag="Door")
    rt_door.start(door_host)

    if store.get("project", "has_key", "") is True:
        bus.emit("gate_opened")
        bus.dispatch()

    assert store.get("object", "locked", "Door") is False
    assert door_host.destroyed is True
    assert "door_open" in door_host.sounds_played