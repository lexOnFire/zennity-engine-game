"""Tests for Player logic graph binding, removal, and WASD movement behavior.

Validates that:
- Player without logic_assets/LogicGraph component DOES NOT move with WASD input
- Player with PlayerMovement_wasd.zlogic moves with WASD input
- Removing LogicGraph component + logic_assets disables movement
- benchmark_gameplay_compat does not mask absence of zlogic by moving player
"""
from pathlib import Path
from engine.logic.runtime import LogicGraphRuntime
from engine.logic.blackboard import BlackboardStore
from engine.logic.event_bus import LogicEventBus
from editor.runtime.viewport_asset_hydration import hydrate_logic_graphs
from editor.runtime.benchmark_gameplay_compat import update_benchmark_gameplay
from editor.runtime.viewport_logic_api import PlayLogicAPI

PROJECT_ROOT = Path.cwd()


def test_player_without_logic_assets_does_not_move_with_wasd_input() -> None:
    objects = {
        "Player": {
            "name": "Player",
            "x": 100.0,
            "y": 100.0,
            "w": 40.0,
            "h": 40.0,
            "logic_assets": [],
            "components": {"items": []},
            "editor_data": {},
        }
    }
    # Hydrate logic graphs
    hydrate_logic_graphs(objects, PROJECT_ROOT)

    # Player must have 0 logic graphs attached
    player = objects["Player"]
    assert len(player.get("logic_graphs", [])) == 0

    # Simulate 10 frames of WASD input
    input_state = {"right": True, "down": True, "left": False, "up": False}
    player["_input"] = input_state

    for _ in range(10):
        update_benchmark_gameplay(objects, 1 / 60)

    # Position must remain unchanged (no movement)
    assert player["x"] == 100.0
    assert player["y"] == 100.0


def test_player_with_wasd_logic_moves_with_wasd_input() -> None:
    objects = {
        "Player": {
            "name": "Player",
            "x": 100.0,
            "y": 100.0,
            "w": 40.0,
            "h": 40.0,
            "logic_assets": ["Assets/Logic/PlayerMovement_wasd.zlogic"],
            "components": {"items": []},
        }
    }
    hydrate_logic_graphs(objects, PROJECT_ROOT)

    player = objects["Player"]
    graphs = player.get("logic_graphs", [])
    assert len(graphs) == 1
    assert graphs[0]["graph"]["enabled"] is True

    # Instantiate runtime for the logic graph
    blackboard = BlackboardStore()
    event_bus = LogicEventBus()
    runtime = LogicGraphRuntime(
        graphs[0]["graph"], blackboard, "Player", event_bus, lambda path: {}
    )
    events_queue: list[dict] = []
    api = PlayLogicAPI("Player", player, events_queue, objects, None, {}, PROJECT_ROOT)

    input_state = {"right": True, "down": False, "left": False, "up": False}
    dt = 1 / 60

    # Run frame updates
    for _ in range(10):
        api.begin_frame(input_state)
        runtime.update(api, dt)
        update_benchmark_gameplay(objects, dt)

    # Position X should have increased due to WASD right input
    assert player["x"] > 100.0


def test_removing_logic_graph_disables_player_movement() -> None:
    # 1. Start with Player that has logic attached
    objects = {
        "Player": {
            "name": "Player",
            "x": 100.0,
            "y": 100.0,
            "w": 40.0,
            "h": 40.0,
            "logic_assets": ["Assets/Logic/PlayerMovement_wasd.zlogic"],
        }
    }
    hydrate_logic_graphs(objects, PROJECT_ROOT)
    assert len(objects["Player"].get("logic_graphs", [])) == 1

    # 2. Simulate user removing logic graph from Inspector
    player = objects["Player"]
    player["logic_assets"] = []
    player["components"] = {"items": []}
    player["editor_data"] = {}

    # Re-hydrate after removal
    hydrate_logic_graphs(objects, PROJECT_ROOT)
    assert len(player.get("logic_graphs", [])) == 0

    # 3. Simulate input & benchmark update
    start_x, start_y = player["x"], player["y"]
    input_state = {"right": True, "up": True}
    player["_input"] = input_state

    for _ in range(10):
        update_benchmark_gameplay(objects, 1 / 60)

    # Player position must NOT change
    assert player["x"] == start_x
    assert player["y"] == start_y


def test_benchmark_gameplay_compat_does_not_mask_absence_of_zlogic() -> None:
    objects = {
        "Player": {
            "name": "Player",
            "x": 50.0,
            "y": 50.0,
            "w": 40.0,
            "h": 40.0,
            "_input": {"right": True, "down": True},
        }
    }
    # Direct benchmark update without logic runtime
    update_benchmark_gameplay(objects, 0.1)

    # Position X and Y must remain unchanged by benchmark_gameplay_compat
    assert objects["Player"]["x"] == 50.0
    assert objects["Player"]["y"] == 50.0
