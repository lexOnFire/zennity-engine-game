"""
Integration tests for Collectibles (Coin & Key) Progression Flow.
Phase 13 Item 13.1-H Non-Vacuity Suite.
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


class MockCollectibleHost:
    def __init__(self, name: str = "Coin", tag: str = "Coin"):
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


def test_a_player_collects_coin_increments_count_and_destroys():
    """TEST A: Player collecting Coin increments coins count from 0 to 1, plays sound, destroys coin."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("project", "coins", 0, "")

    rt_coin = _build_runtime("Assets/Logic/CoinCollectionLogic.zlogic", store, bus, "Coin")
    game = MockCollectibleHost(name="Coin", tag="Coin")
    rt_coin.start(game)

    # Dispara trigger enter pelo Player
    player = MockGameObject("Player", "Player")
    rt_coin.trigger_event("event_trigger_enter", game, 0.016, player)

    assert store.get("project", "coins", "") == 1
    assert game.destroyed is True
    assert "pickup_coin" in game.sounds_played


def test_b_non_player_collides_with_coin_negative_control():
    """TEST B (Negative Control): Non-player (e.g. Enemy) colliding with Coin does NOT collect it."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("project", "coins", 0, "")

    rt_coin = _build_runtime("Assets/Logic/CoinCollectionLogic.zlogic", store, bus, "Coin")
    game = MockCollectibleHost(name="Coin", tag="Coin")
    rt_coin.start(game)

    # Dispara trigger enter por um Enemy
    enemy = MockGameObject("Enemy", "Enemy")
    rt_coin.trigger_event("event_trigger_enter", game, 0.016, enemy)

    assert store.get("project", "coins", "") == 0
    assert game.destroyed is False
    assert len(game.sounds_played) == 0


def test_c_player_collects_key_sets_has_key_and_destroys():
    """TEST C: Player collecting Key sets project variable has_key=True, plays sound, destroys key."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("project", "has_key", False, "")

    rt_key = _build_runtime("Assets/Logic/KeyCollectionLogic.zlogic", store, bus, "Key")
    game = MockCollectibleHost(name="Key", tag="Key")
    rt_key.start(game)

    # Dispara trigger enter pelo Player
    player = MockGameObject("Player", "Player")
    rt_key.trigger_event("event_trigger_enter", game, 0.016, player)

    assert store.get("project", "has_key", "") is True
    assert game.destroyed is True
    assert "pickup_key" in game.sounds_played


def test_d_non_player_collides_with_key_negative_control():
    """TEST D (Negative Control): Non-player colliding with Key does NOT collect it."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("project", "has_key", False, "")

    rt_key = _build_runtime("Assets/Logic/KeyCollectionLogic.zlogic", store, bus, "Key")
    game = MockCollectibleHost(name="Key", tag="Key")
    rt_key.start(game)

    # Dispara trigger enter por um Enemy
    enemy = MockGameObject("Enemy", "Enemy")
    rt_key.trigger_event("event_trigger_enter", game, 0.016, enemy)

    assert store.get("project", "has_key", "") is False
    assert game.destroyed is False
    assert len(game.sounds_played) == 0


def test_e_multiple_coins_accumulation_positive_control():
    """TEST E (Positive Control): Collecting multiple coins sequentially accumulates coins correctly."""
    store = BlackboardStore()
    bus = LogicEventBus()
    store.set("project", "coins", 0, "")

    player = MockGameObject("Player", "Player")

    # Coin 1
    rt1 = _build_runtime("Assets/Logic/CoinCollectionLogic.zlogic", store, bus, "Coin")
    g1 = MockCollectibleHost(name="Coin", tag="Coin")
    rt1.start(g1)
    rt1.trigger_event("event_trigger_enter", g1, 0.016, player)
    assert store.get("project", "coins", "") == 1

    # Coin 2
    rt2 = _build_runtime("Assets/Logic/CoinCollectionLogic.zlogic", store, bus, "Coin")
    g2 = MockCollectibleHost(name="Coin", tag="Coin")
    rt2.start(g2)
    rt2.trigger_event("event_trigger_enter", g2, 0.016, player)
    assert store.get("project", "coins", "") == 2

    # Coin 3
    rt3 = _build_runtime("Assets/Logic/CoinCollectionLogic.zlogic", store, bus, "Coin")
    g3 = MockCollectibleHost(name="Coin", tag="Coin")
    rt3.start(g3)
    rt3.trigger_event("event_trigger_enter", g3, 0.016, player)
    assert store.get("project", "coins", "") == 3