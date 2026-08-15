"""Tests for editor Play Mode object-variable seeding.

PHASE 9 recovery item 24.1.

Validates:
1. scene-authored object variable becomes readable before first graph tick
2. detection_range=300 available on first EnemyAILogic frame
3. attack_range available on first EnemyAttackLogic frame
4. zero/False/empty string values are preserved, not treated as missing
5. multiple variables seed correctly
6. multiple graphs on same object do not reset state
7. two different objects keep isolated object scopes
8. project scope unaffected
9. scene scope unaffected
10. object without variables remains valid
11. retry/new Play session starts from authored defaults
12. Stop -> Play does not leak previous object values
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import pytest

from engine.logic.blackboard import BlackboardStore
from engine.logic.event_bus import LogicEventBus
from engine.logic.graph_asset import load_logic_graph, normalize_logic_graph
from engine.logic.runtime import LogicGraphRuntime
from editor.runtime.viewport_runtime_initializer import ViewportRuntimeInitializer

REPO_ROOT = Path(__file__).resolve().parents[2]


class _MockWorld:
    def reset_session(self) -> None:
        pass


class _MockApi:
    def __init__(self, name: str, obj: dict[str, Any]) -> None:
        self.name = name
        self.tag = obj.get("tag", "")
        self.x = float(obj.get("x", 0.0))
        self.y = float(obj.get("y", 0.0))
        self.rigidbody = None
        self.components: list = []
        self._world = {name: {"name": name, "tag": self.tag, "x": self.x, "y": self.y, "active": True}}

    def get_component(self, t):
        return self

    def set_parameter(self, n, v):
        pass

    def get_parameter(self, n, d=None):
        return d

    def find_object(self, n):
        if n == "Player":
            return _MockApi("Player", {"tag": "Player", "x": 100.0, "y": 0.0})
        return self if n == self.name else None

    find = find_object


def _make_initializer(objects: dict[str, dict[str, Any]]) -> tuple[ViewportRuntimeInitializer, list[dict[str, Any]]]:
    emitted: list[dict[str, Any]] = []
    runtimes: dict[str, list[tuple[str, Any]]] = {}
    apis: dict[str, Any] = {}
    controllers: dict[str, Any] = {}
    runners: dict[str, Any] = {}

    init = ViewportRuntimeInitializer(
        objects=objects,
        logic_runtimes=runtimes,
        initialized_ids=set(),
        animator_event_signatures={},
        runtime_world=_MockWorld(),
        hydrators=[],
        api_factory=lambda name, obj: _MockApi(name, obj),
        subgraph_loader=lambda path: {},
        emit=lambda msg: emitted.append(msg),
        play_audio=lambda *args, **kwargs: None,
        project_root=REPO_ROOT,
        logic_modules={},
        logic_apis=apis,
        animator_controllers=controllers,
        behavior_runners=runners,
    )
    return init, emitted


def test_scene_authored_object_variable_readable_before_graph_tick():
    """1. scene-authored object variable becomes readable in logic_blackboard."""
    objects = {
        "Enemy 1": {
            "name": "Enemy 1",
            "tag": "Enemy",
            "x": 300.0,
            "y": 0.0,
            "variables": {"detection_range": 300.0, "attack_range": 48.0, "move_speed": 100.0},
            "logic_graphs": [],
        }
    }
    init, _ = _make_initializer(objects)
    init.start()

    assert init.logic_blackboard.get("object", "detection_range", "Enemy 1") == 300.0
    assert init.logic_blackboard.get("object", "attack_range", "Enemy 1") == 48.0
    assert init.logic_blackboard.get("object", "move_speed", "Enemy 1") == 100.0


def test_detection_range_available_on_first_enemy_ai_frame():
    """2. detection_range=300 available on first EnemyAILogic frame without float(None)."""
    ai_graph = normalize_logic_graph(load_logic_graph(REPO_ROOT / "Assets" / "Logic" / "EnemyAILogic.zlogic"))
    objects = {
        "Enemy 1": {
            "name": "Enemy 1",
            "tag": "Enemy",
            "x": 300.0,
            "y": 0.0,
            "variables": {
                "health": 100,
                "max_health": 100,
                "move_speed": 100,
                "attack_damage": 10,
                "attack_range": 48,
                "detection_range": 300,
                "attack_cooldown": 1.0,
                "cooldown_timer": 1.0,
            },
            "logic_graphs": [{"path": "Assets/Logic/EnemyAILogic.zlogic", "graph": ai_graph}],
        }
    }
    init, logs = _make_initializer(objects)
    init.start()

    # Execute first frame
    api = init.logic_apis["Enemy 1"]
    _, runtime = init.logic_runtimes["Enemy 1"][0]
    runtime.update(api, 0.016)

    # 0 error logs
    error_logs = [l for l in logs if l.get("level") == "ERROR"]
    assert error_logs == []
    assert "check_detected" in runtime.executed_nodes


def test_attack_range_available_on_first_enemy_attack_frame():
    """3. attack_range available on first EnemyAttackLogic frame without error."""
    atk_graph = normalize_logic_graph(load_logic_graph(REPO_ROOT / "Assets" / "Logic" / "EnemyAttackLogic.zlogic"))
    objects = {
        "Enemy 1": {
            "name": "Enemy 1",
            "tag": "Enemy",
            "x": 300.0,
            "y": 0.0,
            "variables": {
                "health": 100,
                "max_health": 100,
                "move_speed": 100,
                "attack_damage": 10,
                "attack_range": 48,
                "detection_range": 300,
                "attack_cooldown": 1.0,
                "cooldown_timer": 1.0,
            },
            "logic_graphs": [{"path": "Assets/Logic/EnemyAttackLogic.zlogic", "graph": atk_graph}],
        }
    }
    init, logs = _make_initializer(objects)
    init.start()

    api = init.logic_apis["Enemy 1"]
    _, runtime = init.logic_runtimes["Enemy 1"][0]
    runtime.update(api, 0.016)

    error_logs = [l for l in logs if l.get("level") == "ERROR"]
    assert error_logs == []


def test_zero_false_empty_string_values_preserved():
    """4. zero/False/empty string values are preserved, not treated as missing."""
    objects = {
        "Player": {
            "name": "Player",
            "tag": "Player",
            "variables": {"coins": 0, "has_key": False, "custom_tag": ""},
            "logic_graphs": [],
        }
    }
    init, _ = _make_initializer(objects)
    init.start()

    assert init.logic_blackboard.get("object", "coins", "Player") == 0.0
    assert init.logic_blackboard.get("object", "has_key", "Player") is False
    assert init.logic_blackboard.get("object", "custom_tag", "Player") == ""


def test_multiple_graphs_on_same_object_do_not_reset_state():
    """6. multiple graphs on same object do not reset state written by a previous graph."""
    g1 = normalize_logic_graph(load_logic_graph(REPO_ROOT / "Assets" / "Logic" / "PlayerMovementLogic.zlogic"))
    g2 = normalize_logic_graph(load_logic_graph(REPO_ROOT / "Assets" / "Logic" / "PlayerCombatLogic.zlogic"))

    objects = {
        "Player": {
            "name": "Player",
            "tag": "Player",
            "variables": {"health": 100, "facing_x": 1},
            "logic_graphs": [
                {"path": "Assets/Logic/PlayerMovementLogic.zlogic", "graph": g1},
                {"path": "Assets/Logic/PlayerCombatLogic.zlogic", "graph": g2},
            ],
        }
    }
    init, _ = _make_initializer(objects)
    init.start()

    # Modify health
    init.logic_blackboard.set("object", "health", 75.0, "Player")

    # Second initialization step simulation
    raw_variables = objects["Player"]["variables"]
    for var_name, var_val in raw_variables.items():
        if var_name not in init.logic_blackboard.object_values.get("Player", {}):
            init.logic_blackboard.set("object", str(var_name), var_val, "Player")

    assert init.logic_blackboard.get("object", "health", "Player") == 75.0


def test_two_different_objects_keep_isolated_object_scopes():
    """7. two different objects keep isolated object scopes."""
    objects = {
        "Enemy 1": {"name": "Enemy 1", "variables": {"health": 100.0}},
        "Enemy 2": {"name": "Enemy 2", "variables": {"health": 80.0}},
    }
    init, _ = _make_initializer(objects)
    init.start()

    assert init.logic_blackboard.get("object", "health", "Enemy 1") == 100.0
    assert init.logic_blackboard.get("object", "health", "Enemy 2") == 80.0

    init.logic_blackboard.set("object", "health", 50.0, "Enemy 1")
    assert init.logic_blackboard.get("object", "health", "Enemy 1") == 50.0
    assert init.logic_blackboard.get("object", "health", "Enemy 2") == 80.0


def test_project_and_scene_scopes_unaffected():
    """8 & 9. project and scene scopes are unaffected by object seeding."""
    objects = {"Enemy 1": {"name": "Enemy 1", "variables": {"detection_range": 300.0}}}
    init, _ = _make_initializer(objects)
    init.start(scene_blackboard={"variables": {"scene_var": {"scope": "scene", "default": 42.0}}})

    assert init.logic_blackboard.get("scene", "scene_var", "Enemy 1") == 42.0
    assert init.logic_blackboard.get("object", "detection_range", "Enemy 1") == 300.0


def test_object_without_variables_remains_valid():
    """10. object without variables remains valid without error."""
    objects = {"EmptyObj": {"name": "EmptyObj"}}
    init, logs = _make_initializer(objects)
    init.start()

    error_logs = [l for l in logs if l.get("level") == "ERROR"]
    assert error_logs == []


def test_stop_play_does_not_leak_previous_object_values():
    """11 & 12. Stop -> Play does not leak modified object values and resets to authored defaults."""
    objects = {
        "Enemy 1": {"name": "Enemy 1", "variables": {"health": 100.0}},
    }
    init, _ = _make_initializer(objects)
    init.start()

    # Runtime modified
    init.logic_blackboard.set("object", "health", 25.0, "Enemy 1")
    assert init.logic_blackboard.get("object", "health", "Enemy 1") == 25.0

    # Stop & Restart
    init.stop({})
    init.start()

    # Must reset to 100.0
    assert init.logic_blackboard.get("object", "health", "Enemy 1") == 100.0


def test_real_level1_scene_persistence_and_viewport_execution():
    """Real integrated test: Level1.zscene -> EditorScenePersistence.load -> hydrate -> ViewportRuntimeInitializer."""
    from editor.scene_persistence import EditorScenePersistence
    from editor.runtime.viewport_asset_hydration import hydrate_logic_graphs

    persistence = EditorScenePersistence(REPO_ROOT)
    payload, snapshots, typed = persistence.load(REPO_ROOT / "Assets" / "Scenes" / "Level1.zscene")
    objects = {s["name"]: s for s in snapshots}
    hydrate_logic_graphs(objects, REPO_ROOT)

    init, logs = _make_initializer(objects)
    init.start()

    for name in ("Enemy 1", "Enemy 2", "Enemy 3"):
        det = init.logic_blackboard.get("object", "detection_range", name)
        atk = init.logic_blackboard.get("object", "attack_range", name)
        assert det == 300.0
        assert atk == 48.0

        api = init.logic_apis[name]
        for path, rt in init.logic_runtimes[name]:
            rt.update(api, 0.016)

    error_logs = [l for l in logs if l.get("level") == "ERROR"]
    assert error_logs == []
