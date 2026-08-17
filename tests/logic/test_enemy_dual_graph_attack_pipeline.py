"""An enemy runs both of its graphs, and it still hurts the player.

PHASE 12 post-close hotfix H1.

Item 19 gave ``EnemyAttackLogic`` a working attack: it reads ``cooldown_timer``,
counts it up by 0.016 a frame, fires when it reaches ``attack_cooldown``, emits
``player_damage``, and resets the timer to zero. Its own tests prove all of
that, and they pass.

They pass because they build the enemy out of one graph. Level2 builds it out of
two. ``EnemyAILogic`` kept a legacy attack chain of its own -- reading the same
``cooldown_timer``, comparing it against the same ``attack_cooldown``, and
resetting it with a real ``set_variable`` -- left over from before the damage
pipeline existed. That chain was inert only because its own increment was a
phantom node. Item 19 started feeding the timer from the other graph, which woke
it up.

Both graphs then owned one variable, and the resolver orders graphs by casefolded
path, so ``EnemyAILogic`` runs first, deterministically. It consumed the
threshold and zeroed the timer before ``EnemyAttackLogic`` ever evaluated it:

    300 frames, player in range, 0 damage, health 100 -> 100

The fix removes the duplicate chain, leaving one owner. This file is the gate
that would have caught it: every test here composes the enemy the way the scene
composes it, because that was the exact gap -- a total gameplay failure crossed
item 19, phase 10, phase 11 and phase 12 with a green suite.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.logic.blackboard import BlackboardStore
from engine.logic.event_bus import LogicEventBus
from engine.logic.graph_asset import load_logic_graph, normalize_logic_graph
from engine.logic.runtime import LogicGraphRuntime

REPO_ROOT = Path(__file__).resolve().parents[2]
LOGIC = REPO_ROOT / "Assets" / "Logic"

#: The order the runtime actually builds these in. ``AssetRepository.assets()``
#: sorts by casefolded path, so it is alphabetical rather than the order the
#: scene lists -- ``EnemyAILogic`` before ``EnemyAttackLogic``, deterministically.
SCENE_ORDER = ("EnemyAILogic", "EnemyAttackLogic")

#: Live values from Level2's enemies.
ENEMY = {
    "health": 60, "max_health": 60, "move_speed": 70,
    "attack_damage": 10, "attack_range": 40, "detection_range": 400,
    "attack_cooldown": 1.0, "cooldown_timer": 1.0,
}
PLAYER = {"health": 100, "max_health": 100}

#: ``attack_cooldown`` / 0.016, plus the frame that fires and resets.
COOLDOWN_TICKS = 64


def graph(name: str) -> dict:
    return normalize_logic_graph(load_logic_graph(LOGIC / f"{name}.zlogic"))


# ---------------------------------------------------------------------------
# Harness -- mirrors viewport_session_orchestrator.update_logic
# ---------------------------------------------------------------------------


class _Animator:
    def __init__(self) -> None:
        self.parameters: dict[str, object] = {}

    def set_parameter(self, name: str, value: object) -> None:
        self.parameters[str(name)] = value

    def get_parameter(self, name: str, default: object = None) -> object:
        return self.parameters.get(str(name), default)


class _Object:
    def __init__(self, x: float, y: float, name: str) -> None:
        self.x = float(x)
        self.y = float(y)
        self.name = name
        self.tag = name
        self.rigidbody = None
        self.components: list = []
        self.animator = _Animator()

    def get_component(self, _component_type):
        return self.animator

    def move(self, delta_x: float, delta_y: float = 0.0) -> None:
        self.x += float(delta_x)
        self.y += float(delta_y)


class _Api(_Object):
    def __init__(self, position: tuple[float, float], name: str, player: _Object | None) -> None:
        super().__init__(position[0], position[1], name)
        self._player = player
        self.progress: dict[str, tuple[float, float]] = {}

    def _lookup(self, wanted: str):
        return self._player if str(wanted).lower() == "player" else self

    find = _lookup
    find_object = _lookup
    find_by_tag = _lookup

    def set_ui_progress(self, widget: str, value: float, maximum: float) -> None:
        self.progress[str(widget)] = (float(value), float(maximum))


class Enemy:
    """One enemy carrying a list of graphs, plus the player's health graph.

    ``pin`` holds the enemy still, and does so before *every* graph, not once
    per frame: the AI graph moves the enemy before the attack graph measures
    the distance, so an enemy parked one unit outside attack range steps in and
    attacks within the same frame. That is correct behaviour, and it is exactly
    why a range gate has to be tested with the enemy unable to move.
    """

    def __init__(self, graphs: tuple[str, ...] = SCENE_ORDER, *, distance: float = 20.0,
                 pin: bool = True, player: bool = True, **overrides) -> None:
        self.store = BlackboardStore()
        self.bus = LogicEventBus()
        self.pin = pin
        for key, value in {**ENEMY, **{k: v for k, v in overrides.items() if k in ENEMY}}.items():
            self.store.set("object", key, value, "Enemy")
        player_vars = dict(PLAYER)
        if "player_health" in overrides:
            player_vars["health"] = overrides["player_health"]
        for key, value in player_vars.items():
            self.store.set("object", key, value, "Player")

        self.player_object = _Object(distance, 0.0, "Player") if player else None
        self.enemy_api = _Api((0.0, 0.0), "Enemy", self.player_object)
        self.player_api = _Api((distance, 0.0), "Player", self.player_object)
        self.names = tuple(graphs)
        self.runtimes = [LogicGraphRuntime(graph(n), self.store, "Enemy", self.bus)
                         for n in self.names]
        self.health_runtime = LogicGraphRuntime(
            graph("PlayerHealthLogic"), self.store, "Player", self.bus)
        self.health_runtime.start(self.player_api)
        self.damage_events: list[object] = []
        self.bus.subscribe("player_damage", lambda event: self.damage_events.append(event.payload))
        self.hit_frames: list[int] = []
        self.frame = 0

    def timer(self) -> float:
        return self.store.get("object", "cooldown_timer", "Enemy")

    def health(self) -> float:
        return self.store.get("object", "health", "Player")

    def tick(self, count: int = 1, dt: float = 1.0 / 60.0) -> "Enemy":
        for _ in range(count):
            before = self.health()
            for runtime in self.runtimes:
                if self.pin:
                    self.enemy_api.x, self.enemy_api.y = 0.0, 0.0
                runtime.update(self.enemy_api, dt)
                self.bus.dispatch()
            self.health_runtime.update(self.player_api, dt)
            self.bus.dispatch()
            if self.health() != before:
                self.hit_frames.append(self.frame)
            self.frame += 1
        return self


# ---------------------------------------------------------------------------
# The defect, in the composition the scene uses
# ---------------------------------------------------------------------------


def test_an_enemy_with_both_graphs_damages_the_player():
    """The regression this hotfix exists for.

    Against ad488324 this is 0 damage over 300 frames with the player standing
    in range the whole time.
    """
    enemy = Enemy(player_health=100000).tick(300)
    assert enemy.damage_events, "the enemy dealt no damage at all"
    assert enemy.health() < 100000


def test_both_graphs_deal_the_same_damage_as_the_attack_graph_alone():
    """Adding the AI graph must not change how hard the enemy hits."""
    alone = Enemy(("EnemyAttackLogic",), player_health=100000).tick(300)
    both = Enemy(SCENE_ORDER, player_health=100000).tick(300)
    assert both.damage_events == alone.damage_events


def test_the_ai_graph_does_not_steal_the_cooldown():
    """The mechanism, not just the symptom: the timer must survive the AI graph.

    Before the fix ``EnemyAILogic`` reset ``cooldown_timer`` to zero the moment
    it reached the threshold, one graph ahead of the graph that owns it.
    """
    enemy = Enemy(player_health=100000)
    for _ in range(COOLDOWN_TICKS - 2):
        enemy.tick()
        assert enemy.timer() > 0 or enemy.frame <= 1, (
            f"timer was zeroed on frame {enemy.frame} without an attack")


@pytest.mark.parametrize("order", [SCENE_ORDER, tuple(reversed(SCENE_ORDER))])
def test_the_result_does_not_depend_on_graph_order(order: tuple[str, ...]):
    enemy = Enemy(order, player_health=100000).tick(300)
    assert len(enemy.damage_events) >= 4, f"{order} produced {len(enemy.damage_events)} hits"


def test_order_does_not_change_the_number_of_hits():
    forward = Enemy(SCENE_ORDER, player_health=100000).tick(300)
    reverse = Enemy(tuple(reversed(SCENE_ORDER)), player_health=100000).tick(300)
    assert len(forward.damage_events) == len(reverse.damage_events)


# ---------------------------------------------------------------------------
# Ownership, asserted structurally
# ---------------------------------------------------------------------------


def test_the_ai_graph_has_no_cooldown_writer():
    writers = {str(n.get("properties", {}).get("name", ""))
               for n in graph("EnemyAILogic")["nodes"] if str(n["type"]) == "set_variable"}
    assert "cooldown_timer" not in writers


def test_the_ai_graph_has_no_increment_phantom():
    types = {str(n["type"]) for n in graph("EnemyAILogic")["nodes"]}
    assert "variable.increment" not in types


def test_the_ai_graph_does_not_decide_attacks():
    ids = {str(n["id"]) for n in graph("EnemyAILogic")["nodes"]}
    for removed in ("get_attack_cooldown", "get_cooldown_timer", "margin_cooldown",
                    "check_can_attack", "set_attack_trigger", "reset_cooldown_timer",
                    "decrease_cooldown_timer"):
        assert removed not in ids, f"{removed} is still in EnemyAILogic"


def test_the_ai_graph_never_emits_damage():
    types = {str(n["type"]) for n in graph("EnemyAILogic")["nodes"]}
    assert "emit_event" not in types


def test_the_attack_graph_is_the_only_cooldown_owner():
    attack = graph("EnemyAttackLogic")
    writers = [n for n in attack["nodes"]
               if str(n["type"]) == "set_variable"
               and str(n.get("properties", {}).get("name", "")) == "cooldown_timer"]
    assert len(writers) == 2, "increment and reset both live here"
    emitters = {str(n["properties"]["name"]) for n in attack["nodes"]
                if str(n["type"]) == "emit_event"}
    assert emitters == {"player_damage"}


def test_the_scene_still_gives_the_enemy_both_graphs():
    """The fix removes a chain, not a graph: the AI graph stays attached."""
    scene = json.loads((REPO_ROOT / "Assets" / "Scenes" / "Level2.zscene").read_text(encoding="utf-8"))
    enemies = [o for o in scene["objects"]
               if "Assets/Logic/EnemyAILogic.zlogic" in (o.get("logic_assets") or [])]
    assert enemies
    for enemy in enemies:
        assert "Assets/Logic/EnemyAttackLogic.zlogic" in enemy["logic_assets"]


# ---------------------------------------------------------------------------
# Cooldown, counting up
# ---------------------------------------------------------------------------


def test_the_first_attack_is_immediate():
    """``cooldown_timer`` is seeded at ``attack_cooldown``, so the enemy is
    already armed when it arrives. Existing contract, unchanged here."""
    assert Enemy().tick().health() == PLAYER["health"] - ENEMY["attack_damage"]


def test_an_attack_resets_the_timer_to_zero():
    """Exactly zero: the increment sits on ``check_can_attack``'s false branch,
    so the frame that attacks does not also tick the timer forward."""
    enemy = Enemy().tick()
    assert enemy.timer() == 0.0


def test_the_timer_counts_up_at_the_authored_rate():
    """Direction matters: a countdown here would look like a working cooldown
    on the first attack and then never fire again."""
    enemy = Enemy(cooldown_timer=0.0).tick(10)
    assert enemy.timer() == pytest.approx(0.16, abs=1e-6)
    assert enemy.timer() > 0, "the timer must count UP"


def test_the_gap_between_hits_is_the_authored_cooldown():
    enemy = Enemy(player_health=100000).tick(COOLDOWN_TICKS * 4)
    gaps = {b - a for a, b in zip(enemy.hit_frames, enemy.hit_frames[1:])}
    assert gaps == {COOLDOWN_TICKS}, gaps


def test_one_cycle_is_one_hit():
    enemy = Enemy(player_health=100000).tick(COOLDOWN_TICKS * 3)
    assert len(enemy.damage_events) == 3, enemy.hit_frames


def test_every_hit_costs_the_authored_damage():
    enemy = Enemy(player_health=100000).tick(COOLDOWN_TICKS * 4)
    assert set(enemy.damage_events) == {float(ENEMY["attack_damage"])}


# ---------------------------------------------------------------------------
# Range, target, movement
# ---------------------------------------------------------------------------


def test_out_of_range_a_held_enemy_deals_nothing():
    """Held still, so the range gate is the only thing under test."""
    enemy = Enemy(distance=ENEMY["attack_range"] + 1.0).tick(COOLDOWN_TICKS * 3)
    assert enemy.damage_events == []
    assert enemy.health() == PLAYER["health"]


def test_an_enemy_just_outside_range_steps_in_and_attacks():
    """The other half of the same fact, asserted rather than left implicit.

    A free enemy one unit outside attack range closes that unit during the AI
    graph's turn and is inside range by the time the attack graph measures. The
    range gate is not a shield against an enemy that can walk.
    """
    enemy = Enemy(distance=ENEMY["attack_range"] + 1.0, pin=False).tick()
    assert enemy.damage_events == [float(ENEMY["attack_damage"])]


def test_a_missing_target_deals_nothing_and_does_not_raise():
    enemy = Enemy(player=False).tick(COOLDOWN_TICKS * 3)
    assert enemy.damage_events == []
    assert enemy.health() == PLAYER["health"]


def test_the_enemy_still_chases():
    """Movement regression: the excision must not touch the chase chain."""
    enemy = Enemy(distance=200.0, pin=False)
    start = enemy.enemy_api.x
    enemy.tick(30)
    assert enemy.enemy_api.x > start, "the enemy stopped chasing"


def test_the_enemy_still_stops_inside_attack_range():
    enemy = Enemy(distance=20.0, pin=False)
    enemy.tick(30)
    assert enemy.enemy_api.x == pytest.approx(0.0), "the enemy should hold position in range"


def test_the_enemy_ignores_a_player_beyond_detection_range():
    enemy = Enemy(distance=ENEMY["detection_range"] + 100.0, pin=False)
    enemy.tick(30)
    assert enemy.enemy_api.x == pytest.approx(0.0)
    assert enemy.damage_events == []
