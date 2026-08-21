"""The shipping game must be losable, winnable, and able to leave its end screens.

PHASE 13 item 13.1-D.

Three wiring defects made the shipping loop impossible to complete, and none of
them was visible in the graphs themselves -- every graph involved validates
clean. They were all in *who is connected to whom*:

* ``PlayerHealthLogic`` was bound to the Player in Level 2 but not in Level 1,
  so the Level 1 player could attack and never be hurt.
* ``BossHealthLogic`` displayed the boss's health and handled its death, but had
  no damage intake at all -- ``boss_damage`` was emitted by the player and
  consumed by nobody, so the boss was invulnerable and Victory unreachable.
* ``VictoryLogic`` was bound to nothing, and named a target (``Player``) that
  does not exist in ``Victory.zscene``.

These tests exercise the real composition rather than reading the JSON: scenes
go through ``hydrate_logic_graphs`` -- the same function the viewport uses -- and
the graphs run in a real ``LogicGraphRuntime`` over a shared event bus. Reading
the files would have passed while the game stayed broken, which is how the
defects survived this long.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from editor.runtime.viewport_asset_hydration import hydrate_logic_graphs
from engine.logic.blackboard import BlackboardStore
from engine.logic.event_bus import LogicEventBus
from engine.logic.runtime import LogicGraphRuntime


# ---------------------------------------------------------------------------
# Composition helpers
# ---------------------------------------------------------------------------

class _HostObject:
    """A scene object with the component lookup the physics nodes expect."""

    def __init__(self, data: dict) -> None:
        self.data = data
        self.name = data.get("name", "")
        from engine.physics.collider import BoxCollider

        self._collider = BoxCollider(width=32.0, height=32.0)

    def get_component(self, component_type):
        from engine.physics.collider import BoxCollider

        return self._collider if component_type is BoxCollider else None


class _Game:
    """The host surface the bound graphs drive.

    Every graph on an object runs, not just the one under test, because that is
    the composition the game has -- a Player runs movement, combat and health
    together, and this is where a second health owner would show up. Movement
    and AI graphs reach for host state this harness has no reason to model
    (``axis``, sprite lookups), so unknown attributes resolve to an inert stub
    rather than raising and taking the health pipeline down with them.

    ``load_scene`` and ``find_object`` are real: the assertions depend on them.
    """

    def __init__(self, objects: dict[str, dict]) -> None:
        self.objects = objects
        self.loaded_scenes: list[str] = []
        self._world = {}
        self._hosts: dict[str, _HostObject] = {}

    def load_scene(self, path: str) -> None:
        self.loaded_scenes.append(str(path))

    def find_object(self, name: str):
        """Return a host object with the component surface the graphs use.

        ``modify_collider`` -- on the boss's death path -- asks the target for a
        real collider component, so a plain dict would make the death chain stop
        one node short of loading Victory. The scene objects do declare
        colliders, so the harness materialises one.
        """
        data = self.objects.get(str(name))
        if data is None:
            return None
        if str(name) not in self._hosts:
            self._hosts[str(name)] = _HostObject(data)
        return self._hosts[str(name)]

    def key_pressed(self, key: str) -> bool:
        return False

    def __getattr__(self, name: str):
        # Only reached for attributes the harness does not define.
        def _inert(*args, **kwargs):
            return 0.0
        return _inert


def _scene_objects(scene: str) -> dict[str, dict]:
    """Hydrate a shipping scene exactly as the viewport does."""
    data = json.loads((PROJECT_ROOT / "Assets" / "Scenes" / f"{scene}.zscene").read_text(encoding="utf-8"))
    objects = {obj["name"]: json.loads(json.dumps(obj)) for obj in data["objects"]}
    hydrate_logic_graphs(objects, PROJECT_ROOT)
    return objects


def _graph_paths(obj: dict) -> list[str]:
    return [
        str(entry["path"])
        for entry in (obj.get("logic_graphs") or [])
        if isinstance(entry, dict) and entry.get("path")
    ]


def _graph_names(obj: dict) -> set[str]:
    return {Path(path).stem for path in _graph_paths(obj)}


class _Composed:
    """One object's bound graphs, running on a shared bus and blackboard."""

    def __init__(self, scene: str, object_name: str) -> None:
        self.objects = _scene_objects(scene)
        self.obj = self.objects[object_name]
        self.name = object_name
        self.game = _Game(self.objects)
        self.bus = LogicEventBus()
        self.blackboard = BlackboardStore()
        self.runtimes: list[LogicGraphRuntime] = []

        for entry in self.obj.get("logic_graphs") or []:
            graph = entry.get("graph") if isinstance(entry, dict) else None
            if not isinstance(graph, dict):
                continue
            runtime = LogicGraphRuntime(graph, self.blackboard, object_name, event_bus=self.bus)
            runtime.configure_variables(
                {name: {"type": "number", "scope": "object", "default": value}
                 for name, value in (self.obj.get("variables") or {}).items()}
            )
            runtime.start(self.game)
            self.runtimes.append(runtime)

        # One warm-up frame. A custom event that arrives before the graph has
        # seen a frame is queued instead of run, because the runtime needs a
        # host reference to execute against; ticking once here means emit()
        # behaves the same as it does mid-game.
        self.tick()

    def variable(self, name: str):
        return self.blackboard.values_for_object(self.name).get(name)

    def set_variable(self, name: str, value) -> None:
        self.blackboard.set("object", name, value, self.name)

    def emit(self, event: str, payload) -> None:
        self.bus.emit(event, payload=payload)

    def tick(self, times: int = 1, dt: float = 0.016) -> None:
        """One frame: deliver queued events, then advance every graph.

        ``LogicEventBus.emit`` only queues; ``dispatch`` is what hands events to
        subscribers, and the game calls it once per frame. Ticking without it
        leaves the queue untouched and every damage test silently measures
        nothing.
        """
        for _ in range(times):
            self.bus.dispatch()
            for runtime in self.runtimes:
                runtime.update(self.game, dt)


# ---------------------------------------------------------------------------
# A / B -- the player can be hurt, and dying ends the run
# ---------------------------------------------------------------------------

def test_a_player_takes_damage_in_level1() -> None:
    """Level 1's player must lose health when something attacks it."""
    player = _Composed("Level1", "Player")
    player.set_variable("health", 100)

    player.emit("player_damage", 25)
    player.tick()

    assert player.variable("health") == 75, (
        "player_damage reached nobody: the Level 1 player has "
        f"{sorted(_graph_names(player.obj))} bound and cannot be hurt"
    )


def test_b_player_death_loads_game_over() -> None:
    """Health at or below zero has to end the run."""
    player = _Composed("Level1", "Player")
    player.set_variable("health", 20)

    player.emit("player_damage", 25)
    player.tick(times=3)

    assert player.variable("health") <= 0
    assert any("GameOver" in scene for scene in player.game.loaded_scenes), (
        f"the player died and nothing loaded GameOver: {player.game.loaded_scenes}"
    )


def test_b_negative_a_living_player_never_loads_game_over() -> None:
    """The death path must not fire while the player is still alive."""
    player = _Composed("Level1", "Player")
    player.set_variable("health", 100)

    player.emit("player_damage", 25)
    player.tick(times=3)

    assert player.variable("health") > 0
    assert not any("GameOver" in scene for scene in player.game.loaded_scenes)


# ---------------------------------------------------------------------------
# C / D -- the boss can be hurt, and killing it wins
# ---------------------------------------------------------------------------

def test_c_boss_takes_damage_in_level2() -> None:
    """boss_damage must reach the graph that owns the boss's health."""
    boss = _Composed("Level2", "Boss")
    boss.set_variable("health", 500)

    boss.emit("boss_damage", 25)
    boss.tick()

    assert boss.variable("health") == 475, (
        "boss_damage reached nobody: the boss owns "
        f"{sorted(_graph_names(boss.obj))} and cannot be hurt"
    )


def test_c_negative_enemy_damage_does_not_hurt_the_boss() -> None:
    """The boss answers to boss_damage only; enemy_damage belongs to enemies."""
    boss = _Composed("Level2", "Boss")
    boss.set_variable("health", 500)

    boss.emit("enemy_damage", 25)
    boss.tick()

    assert boss.variable("health") == 500


def test_d_boss_death_wins_the_game() -> None:
    """Killing the boss must mark it defeated and go to Victory."""
    boss = _Composed("Level2", "Boss")
    boss.set_variable("health", 20)

    boss.emit("boss_damage", 25)
    boss.tick(times=3)

    assert boss.variable("health") <= 0
    assert boss.blackboard.get("project", "boss_defeated", boss.name) is True, (
        "the boss died without setting boss_defeated"
    )
    assert any("Victory" in scene for scene in boss.game.loaded_scenes), (
        f"the boss died and nothing loaded Victory: {boss.game.loaded_scenes}"
    )


def test_d_negative_boss_damage_does_not_hurt_the_player() -> None:
    """boss_damage is aimed at the boss; it must not drain the player."""
    player = _Composed("Level2", "Player")
    player.set_variable("health", 100)

    player.emit("boss_damage", 25)
    player.tick()

    assert player.variable("health") == 100


# ---------------------------------------------------------------------------
# E -- the victory screen owns its logic
# ---------------------------------------------------------------------------

def test_e_victory_canvas_owns_victory_logic() -> None:
    """Victory's Canvas must run VictoryLogic, and only that."""
    objects = _scene_objects("Victory")
    canvas = objects["Canvas"]
    names = _graph_names(canvas)

    assert "VictoryLogic" in names, f"Victory's Canvas runs {sorted(names)}"
    assert "CanvasLogic" not in names, (
        "CanvasLogic is a scratch graph (set_hud text='teste'); an explicit "
        "binding on the Canvas must stop it being auto-attached to a shipping scene"
    )


def test_e_victory_logic_targets_an_object_that_exists() -> None:
    """A graph's declared target has to name something in its own scene."""
    graph = json.loads((PROJECT_ROOT / "Assets" / "Logic" / "VictoryLogic.zlogic").read_text(encoding="utf-8"))
    scene = json.loads((PROJECT_ROOT / "Assets" / "Scenes" / "Victory.zscene").read_text(encoding="utf-8"))

    target = str((graph.get("target") or {}).get("value", ""))
    names = {obj.get("name") for obj in scene.get("objects", [])}

    assert target == "Canvas"
    assert target in names, f"VictoryLogic targets {target!r}; Victory has {sorted(names)}"


# ---------------------------------------------------------------------------
# F -- exactly one owner, so damage is applied exactly once
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "scene, object_name, event, start, expected",
    [
        ("Level1", "Player", "player_damage", 100, 75),
        ("Level2", "Player", "player_damage", 100, 75),
        ("Level2", "Boss", "boss_damage", 500, 475),
    ],
)
def test_f_damage_is_applied_exactly_once(scene, object_name, event, start, expected) -> None:
    """Two graphs owning one health value would silently double every hit."""
    composed = _Composed(scene, object_name)
    composed.set_variable("health", start)

    composed.emit(event, 25)
    composed.tick()

    assert composed.variable("health") == expected, (
        f"{object_name} in {scene} went {start} -> {composed.variable('health')}; "
        f"{sorted(_graph_names(composed.obj))} are bound"
    )


# ---------------------------------------------------------------------------
# G -- the emitter side of the boss pipeline
# ---------------------------------------------------------------------------

def test_g_level2_player_can_attack() -> None:
    """Without PlayerCombatLogic in Level 2, boss_damage is never emitted."""
    objects = _scene_objects("Level2")
    names = _graph_names(objects["Player"])

    assert names == {"PlayerMovementLogic", "PlayerHealthLogic", "PlayerCombatLogic"}, (
        f"Level 2's player runs {sorted(names)}"
    )


def test_g_the_boss_pipeline_has_an_emitter_and_a_listener() -> None:
    """One emitter, one listener -- measured across every shipping graph."""
    emitters: list[str] = []
    listeners: list[str] = []
    for path in sorted((PROJECT_ROOT / "Assets" / "Logic").rglob("*.zlogic")):
        graph = json.loads(path.read_text(encoding="utf-8"))
        for node in graph.get("nodes", []):
            name = (node.get("properties") or {}).get("name")
            if name != "boss_damage":
                continue
            if node.get("type") == "emit_event":
                emitters.append(path.name)
            elif node.get("type") == "event_custom":
                listeners.append(path.name)

    assert emitters == ["PlayerCombatLogic.zlogic"]
    assert listeners == ["BossHealthLogic.zlogic"]


def test_g_level1_player_runs_the_full_set() -> None:
    """Level 1 gains health without losing what it already had."""
    objects = _scene_objects("Level1")
    names = _graph_names(objects["Player"])

    assert names == {"PlayerMovementLogic", "PlayerCombatLogic", "PlayerHealthLogic"}, (
        f"Level 1's player runs {sorted(names)}"
    )
