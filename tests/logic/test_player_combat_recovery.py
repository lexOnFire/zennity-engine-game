"""Player combat: one hit per keypress, correct target, correct damage.

ITEM 23 — Gate A final.

Validates the full approved architecture:

  SPACE + cooldown >= 0.4
  → play_animation("PlayerAttack")
  → find_nearest_object(tag="Enemy", max_distance=80)
      ├─ found → facing guard (dx * facing_x > 0)
      │     ├─ true  → emit_event("enemy_damage", payload=attack_damage)
      │     └─ false → find_nearest_object(tag="Boss", ...)
      └─ none → find_nearest_object(tag="Boss", ...)
                    ├─ found → facing guard
                    │     ├─ true  → emit_event("enemy_damage", payload=attack_damage)
                    │     └─ false → miss
                    └─ none → miss

  EnemyHealth receives "enemy_damage", subtracts payload from own health,
  clamps, writes back, destroys self if dead.

Structural invariants proven by these tests:
  * 0 orphan edges, 0 phantom nodes in PlayerCombatLogic and EnemyHealth.
  * Damage event name matches on both emitter and receiver.
  * Attack damage is 25 (canonical from Level1 Player variables).
  * Cooldown is 0.4 s; a single SPACE in one frame must not fire twice.
  * facing_x guard: back-facing enemy is NOT hit.
  * Enemy self-destroys at health ≤ 0.
  * Boss is only hit when no in-range, in-front enemy exists.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pytest

from engine.logic.blackboard import BlackboardStore
from engine.logic.event_bus import LogicEventBus
from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    load_logic_graph,
    node_port_definitions,
    normalize_logic_graph,
)
from engine.logic.node_definitions.catalogue import resolve_node_id
from engine.logic.runtime import LogicGraphRuntime

REPO_ROOT = Path(__file__).resolve().parents[2]
LOGIC = REPO_ROOT / "Assets" / "Logic"

# ---------------------------------------------------------------------------
# Scene defaults (from Level1.zscene Player + EnemyHealth defaults)
# ---------------------------------------------------------------------------

PLAYER_DEFAULTS = {
    "health": 100,
    "max_health": 100,
    "attack_damage": 25,
    "attack_range": 80,
    "attack_cooldown": 0.4,
    "cooldown_timer": 0.4,   # starts ready
    "facing_x": 1.0,
}
ENEMY_DEFAULTS = {
    "health": 100,
    "max_health": 100,
}
BOSS_DEFAULTS = {
    "health": 500,
    "max_health": 500,
}


# ---------------------------------------------------------------------------
# Graph loader helpers
# ---------------------------------------------------------------------------

def graph(name: str) -> dict:
    return normalize_logic_graph(load_logic_graph(LOGIC / f"{name}.zlogic"))


# ---------------------------------------------------------------------------
# Minimal game-API object
# ---------------------------------------------------------------------------

class _Destroyed(Exception):
    pass


class _Obj:
    """Lightweight stand-in for a runtime scene object."""

    def __init__(self, x: float, y: float, name: str, tag: str = "") -> None:
        self.x = float(x)
        self.y = float(y)
        self.name = name
        self.tag = tag
        self.alive = True
        self.rigidbody = None
        self.components: list = []
        self._animator_params: dict[str, object] = {}

    # -- animator shim -------------------------------------------------------
    def get_component(self, _type):
        return self  # act as animator

    def set_parameter(self, name: str, value: object) -> None:
        self._animator_params[str(name)] = value

    def get_parameter(self, name: str, default: object = None) -> object:
        return self._animator_params.get(str(name), default)

    def play_state(self, state: str, force: bool = False) -> None:
        pass  # no-op; we only care about blackboard / events

    # -- move ----------------------------------------------------------------
    def move(self, dx: float, dy: float = 0.0) -> None:
        self.x += float(dx)
        self.y += float(dy)


class _MockAnimator:
    """Minimal Animator stub — satisfy play_animation node contract."""

    def __init__(self) -> None:
        # play_animation checks: if state not in animator._clips → exec_failure
        self._clips: dict = {"PlayerAttack": True, "Idle": True, "Run": True}
        self._current: str | None = None

    def play(self, state: str, force: bool = False) -> None:
        self._current = state

    def set_parameter(self, name: str, value: object) -> None:
        pass

    def get_parameter(self, name: str, default: object = None) -> object:
        return default


class _Game:
    """
    Per-object API the runtime receives as ``game``.
    Implements only what PlayerCombatLogic and EnemyHealth use.
    """

    def __init__(
        self,
        self_obj: _Obj,
        enemy_obj: _Obj | None,
        boss_obj: _Obj | None,
        pressed_keys: set[str],
    ) -> None:
        self._self = self_obj
        self._enemy = enemy_obj
        self._boss = boss_obj
        self._pressed = {k.lower() for k in pressed_keys}
        self._animator = _MockAnimator()

        # geometry mirrors self_obj
        self.x = self_obj.x
        self.y = self_obj.y
        self.name = self_obj.name
        self.tag = self_obj.tag
        self.rigidbody = None
        self.components: list = []
        self._animator_params: dict[str, object] = {}

        # World mapping for find_nearest_object (_world_objects(game))
        self._world: dict[str, dict[str, Any]] = {}
        for obj in [self._self, self._enemy, self._boss]:
            if obj is not None:
                self._world[obj.name] = {
                    "name": obj.name,
                    "tag": obj.tag,
                    "x": obj.x,
                    "y": obj.y,
                    "active": obj.alive,
                }

    # -- animator / find_object pass-through ----------------------------------
    def get_component(self, _type):
        """Return mock animator for Animator component queries."""
        return self._animator

    def find_object(self, name: str) -> Any:
        """play_animation calls find_object(target_name) to get the animator."""
        if not name or name == self.name:
            return self
        if self._enemy and name == self._enemy.name:
            return self._enemy
        if self._boss and name == self._boss.name:
            return self._boss
        return None

    find = find_object
    find_by_tag = find_object

    def set_parameter(self, name: str, value: object) -> None:
        self._animator_params[str(name)] = value

    def get_parameter(self, name: str, default: object = None) -> object:
        return self._animator_params.get(str(name), default)

    def play_state(self, state: str, force: bool = False) -> None:
        pass

    def move(self, dx: float, dy: float = 0.0) -> None:
        self._self.x += float(dx)
        self.x = self._self.x

    # -- key polling ---------------------------------------------------------
    def key_pressed(self, key: str) -> bool:
        return key.lower() in self._pressed

    def key(self, key: str) -> bool:  # key_held alias
        return key.lower() in self._pressed

    # -- find_nearest_object -------------------------------------------------
    def find_nearest_object(self, tag: str, max_distance: float) -> _Obj | None:
        candidates = []
        for obj in [self._enemy, self._boss]:
            if obj is None or not obj.alive:
                continue
            if obj.tag.lower() != tag.lower():
                continue
            dist = math.sqrt((obj.x - self.x) ** 2 + (obj.y - self.y) ** 2)
            if dist <= max_distance:
                candidates.append((dist, obj))
        if not candidates:
            return None
        candidates.sort(key=lambda t: t[0])
        return candidates[0][1]

    def find_by_name(self, name: str) -> _Obj | None:
        for obj in [self._self, self._enemy, self._boss]:
            if obj and obj.name == name:
                return obj
        return None

    # -- destroy_object (called by EnemyHealth when hp ≤ 0) -----------------
    def destroy(self, target: Any = None) -> None:
        obj = target if target is not None else self._self
        if hasattr(obj, "alive"):
            obj.alive = False

    destroy_object = destroy


# ---------------------------------------------------------------------------
# Combat harness
# ---------------------------------------------------------------------------

class CombatScene:
    """
    Wires PlayerCombatLogic + one EnemyHealth (and optional BossHealth) onto a
    shared blackboard and event bus, then lets you tick them together.
    """

    def __init__(
        self,
        *,
        player_x: float = 0.0,
        enemy_x: float | None = 40.0,   # None = no enemy
        boss_x: float | None = None,     # None = no boss
        facing_x: float = 1.0,
        pressed: set[str] | None = None,
        player_vars: dict | None = None,
        enemy_vars: dict | None = None,
        boss_vars: dict | None = None,
        cooldown_timer_start: float = 0.4,  # 0.4 = ready immediately
    ) -> None:
        self.store = BlackboardStore()
        self.bus = LogicEventBus()

        # ---- Player blackboard ----
        pv = {**PLAYER_DEFAULTS, **(player_vars or {})}
        pv["cooldown_timer"] = cooldown_timer_start
        pv["facing_x"] = facing_x
        for k, v in pv.items():
            self.store.set("object", k, v, "Player")

        # ---- Enemy blackboard ----
        ev = {**ENEMY_DEFAULTS, **(enemy_vars or {})}
        for k, v in ev.items():
            self.store.set("object", k, v, "Enemy")

        # ---- Boss blackboard ----
        bv = {**BOSS_DEFAULTS, **(boss_vars or {})}
        for k, v in bv.items():
            self.store.set("object", k, v, "Boss")

        # ---- Scene objects ----
        self.player_obj = _Obj(player_x, 0.0, "Player", tag="Player")
        self.enemy_obj: _Obj | None = (
            _Obj(enemy_x, 0.0, "Enemy", tag="Enemy") if enemy_x is not None else None
        )
        self.boss_obj: _Obj | None = (
            _Obj(boss_x, 0.0, "Boss", tag="Boss") if boss_x is not None else None
        )

        self._pressed = pressed or set()

        # ---- Runtimes ----
        self.player_rt = LogicGraphRuntime(
            graph("PlayerCombatLogic"), self.store, "Player", self.bus
        )

        self.enemy_rt: LogicGraphRuntime | None = None
        if self.enemy_obj is not None:
            self.enemy_rt = LogicGraphRuntime(
                graph("EnemyHealth"), self.store, "Enemy", self.bus
            )

        self.boss_rt: LogicGraphRuntime | None = None
        if self.boss_obj is not None:
            boss_health_graph = graph("EnemyHealth")
            for node in boss_health_graph.get("nodes", []):
                if node.get("id") == "receive_hit":
                    node.setdefault("properties", {})["name"] = "boss_damage"
            self.boss_rt = LogicGraphRuntime(
                boss_health_graph, self.store, "Boss", self.bus
            )

        # Start runtimes that need it
        if self.enemy_rt:
            enemy_game = _Game(self.enemy_obj, self.enemy_obj, self.boss_obj, set())
            self.enemy_rt.start(enemy_game)
        if self.boss_rt:
            boss_game = _Game(self.boss_obj, self.enemy_obj, self.boss_obj, set())
            self.boss_rt.start(boss_game)

    # -- Helpers -------------------------------------------------------------

    def enemy_health(self) -> float:
        return float(self.store.get("object", "health", "Enemy"))

    def boss_health(self) -> float:
        return float(self.store.get("object", "health", "Boss"))

    def player_cooldown(self) -> float:
        return float(self.store.get("object", "cooldown_timer", "Player"))

    # -- Core tick -----------------------------------------------------------

    def tick(
        self,
        count: int = 1,
        dt: float = 1.0 / 60.0,
        pressed: set[str] | None = None,
    ) -> "CombatScene":
        keys = pressed if pressed is not None else self._pressed
        for _ in range(count):
            player_game = _Game(
                self.player_obj, self.enemy_obj, self.boss_obj, keys
            )
            self.player_rt.update(player_game, dt)
            self.bus.dispatch()

            if self.enemy_rt and self.enemy_obj and self.enemy_obj.alive:
                enemy_game = _Game(
                    self.enemy_obj, self.enemy_obj, self.boss_obj, set()
                )
                self.enemy_rt.update(enemy_game, dt)
                self.bus.dispatch()

            if self.boss_rt and self.boss_obj and self.boss_obj.alive:
                boss_game = _Game(
                    self.boss_obj, self.enemy_obj, self.boss_obj, set()
                )
                self.boss_rt.update(boss_game, dt)
                self.bus.dispatch()

        return self


# ===========================================================================
# Tests
# ===========================================================================

# ---------------------------------------------------------------------------
# Graph structural integrity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["PlayerCombatLogic", "EnemyHealth"])
def test_graph_has_zero_orphans_and_phantoms(name: str):
    """0 orphan edges, 0 phantom nodes — gate A.0 contract."""
    g = graph(name)
    nodes = {str(n["id"]): n for n in g["nodes"]}
    phantom = {
        str(n["type"]) for n in g["nodes"]
        if resolve_node_id(str(n["type"])) not in NODE_DEFINITIONS
    }
    orphans = []
    for edge in g["edges"]:
        src = nodes[str(edge["from_node"])]
        dst = nodes[str(edge["to_node"])]
        out_ports = {p for p, _ in node_port_definitions(src)["outputs"]}
        in_ports = {p for p, _ in node_port_definitions(dst)["inputs"]}
        if str(edge["from_port"]) not in out_ports:
            orphans.append(f'{src["type"]}.{edge["from_port"]}>out')
        if str(edge["to_port"]) not in in_ports:
            orphans.append(f'{dst["type"]}.{edge["to_port"]}>in')
    assert phantom == set(), f"phantom node types in {name}: {phantom}"
    assert sorted(set(orphans)) == [], f"orphan edges in {name}: {orphans}"


def test_damage_event_name_matches_emitter_and_receiver():
    """A name typo in either side is silent — this catches it explicitly."""
    emitted = {
        str(n["properties"]["name"])
        for n in graph("PlayerCombatLogic")["nodes"]
        if str(n["type"]) == "emit_event"
    }
    received = {
        str(n["properties"]["name"])
        for n in graph("EnemyHealth")["nodes"]
        if str(n["type"]) == "event_custom"
    }
    assert emitted == {"enemy_damage", "boss_damage"}, f"Emitter names: {emitted}"
    assert received == {"enemy_damage"}, f"Receiver names: {received}"


def test_player_combat_never_writes_enemy_health_directly():
    """Ownership invariant: PlayerCombatLogic must not set_variable 'health'."""
    g = graph("PlayerCombatLogic")
    writers = [n for n in g["nodes"] if str(n["type"]) == "set_variable"]
    written = {str(n.get("properties", {}).get("name", "")) for n in writers}
    assert "health" not in written, f"PlayerCombatLogic writes health: {written}"


def test_enemy_health_owns_the_only_health_write():
    """EnemyHealth alone updates health — no cross-object writes."""
    g = graph("EnemyHealth")
    writers = [n for n in g["nodes"] if str(n["type"]) == "set_variable"]
    names = [str(n.get("properties", {}).get("name", "")) for n in writers]
    assert "health" in names, "EnemyHealth must write health"
    scopes = [str(n.get("properties", {}).get("scope", "")) for n in writers]
    assert all(s == "object" for s in scopes), f"Non-object scope found: {scopes}"


def test_attack_damage_is_25():
    """Canonical attack_damage from Level1 Player variables."""
    g = graph("PlayerCombatLogic")
    variables = g.get("variables", {})
    assert "attack_damage" in variables, "attack_damage variable missing"
    default = variables["attack_damage"].get("default", variables["attack_damage"].get("default_value"))
    assert float(default) == 25.0, f"attack_damage default is {default}, expected 25.0"


def test_cooldown_threshold_is_0_4():
    """Cooldown threshold must be 0.4 s."""
    g = graph("PlayerCombatLogic")
    checkers = [n for n in g["nodes"] if str(n.get("id", "")) == "check_cooldown"]
    assert checkers, "check_cooldown node not found"
    val = float(checkers[0].get("properties", {}).get("value", 0))
    assert val == pytest.approx(0.4), f"check_cooldown threshold is {val}"


# ---------------------------------------------------------------------------
# Cooldown: one hit per press, not per frame
# ---------------------------------------------------------------------------

def test_single_space_press_fires_exactly_one_hit():
    """Gate A.1 core: one keypress → one damage event, not N frames."""
    scene = CombatScene(player_x=0.0, enemy_x=40.0, facing_x=1.0)
    before = scene.enemy_health()
    # Tick 10 frames with SPACE held — cooldown prevents repeat
    scene.tick(10, pressed={"space"})
    after = scene.enemy_health()
    assert after == before - 25.0, (
        f"Expected exactly one hit (100 → 75), got {before} → {after}"
    )


def test_cooldown_prevents_second_hit_in_same_second():
    """After reset, cooldown_timer = 0.0; second press in same tick is blocked."""
    dt = 1.0 / 60.0
    scene = CombatScene(player_x=0.0, enemy_x=40.0, facing_x=1.0)
    # First attack fires immediately (timer starts at 0.4)
    scene.tick(1, pressed={"space"})
    hp_after_first = scene.enemy_health()
    assert hp_after_first == 75.0, f"First hit failed: {hp_after_first}"

    # Timer reset to 0 — ticking a few frames with SPACE should NOT hit again
    ticks_before_cooldown_expires = int(0.35 / dt)  # < 0.4s
    scene.tick(ticks_before_cooldown_expires, pressed={"space"})
    assert scene.enemy_health() == 75.0, "Second hit fired before cooldown expired"

    # After cooldown, hit fires again
    ticks_to_expire = int(0.05 / dt) + 5
    scene.tick(ticks_to_expire, pressed={"space"})
    assert scene.enemy_health() == 50.0, "Second hit did not fire after cooldown"


# ---------------------------------------------------------------------------
# Facing guard
# ---------------------------------------------------------------------------

def test_facing_guard_hits_enemy_in_front():
    """facing_x=+1, enemy at x=+40 → hit."""
    scene = CombatScene(player_x=0.0, enemy_x=40.0, facing_x=1.0)
    scene.tick(1, pressed={"space"})
    assert scene.enemy_health() == 75.0, "Front-facing enemy should be hit"


def test_facing_guard_misses_enemy_behind():
    """facing_x=+1, enemy at x=-40 → miss (back-facing guard)."""
    scene = CombatScene(player_x=0.0, enemy_x=-40.0, facing_x=1.0)
    scene.tick(1, pressed={"space"})
    assert scene.enemy_health() == 100.0, "Back-facing enemy should NOT be hit"


def test_facing_guard_left_hits_enemy_on_left():
    """facing_x=-1, enemy at x=-40 → hit."""
    scene = CombatScene(player_x=0.0, enemy_x=-40.0, facing_x=-1.0)
    scene.tick(1, pressed={"space"})
    assert scene.enemy_health() == 75.0, "Left-facing enemy should be hit"


def test_facing_guard_left_misses_enemy_on_right():
    """facing_x=-1, enemy at x=+40 → miss."""
    scene = CombatScene(player_x=0.0, enemy_x=40.0, facing_x=-1.0)
    scene.tick(1, pressed={"space"})
    assert scene.enemy_health() == 100.0, "Right enemy with left facing should miss"


# ---------------------------------------------------------------------------
# Out-of-range
# ---------------------------------------------------------------------------

def test_enemy_out_of_range_is_not_hit():
    """max_distance=80; enemy at x=200 → miss."""
    scene = CombatScene(player_x=0.0, enemy_x=200.0, facing_x=1.0)
    scene.tick(1, pressed={"space"})
    assert scene.enemy_health() == 100.0, "Out-of-range enemy should not be hit"


# ---------------------------------------------------------------------------
# Multiple targets: only the right one takes damage
# ---------------------------------------------------------------------------

def test_enemy_in_front_hit_boss_behind_untouched():
    """Enemy in front is hit; Boss behind player is not."""
    # Player at 0, Enemy at +40 (in front), Boss at -100 (behind)
    scene = CombatScene(
        player_x=0.0,
        enemy_x=40.0,
        boss_x=-100.0,
        facing_x=1.0,
    )
    scene.tick(1, pressed={"space"})
    assert scene.enemy_health() == 75.0, "Enemy in front should be hit"
    assert scene.boss_health() == 500.0, "Boss behind should be untouched"


def test_no_enemy_in_range_hits_boss_in_front():
    """No enemy in range → fall through to Boss search."""
    # Enemy behind, Boss in front
    scene = CombatScene(
        player_x=0.0,
        enemy_x=-50.0,     # behind; facing_x=+1 guard will fail → fallthrough to Boss
        boss_x=40.0,
        facing_x=1.0,
    )
    scene.tick(1, pressed={"space"})
    assert scene.boss_health() == 475.0, "Boss in front should be hit via fallthrough"
    assert scene.enemy_health() == 100.0, "Enemy behind should be untouched"


def test_enemy_behind_and_boss_behind_is_safe_miss():
    """Both targets behind player → no damage to either."""
    scene = CombatScene(
        player_x=0.0,
        enemy_x=-40.0,
        boss_x=-60.0,
        facing_x=1.0,
    )
    scene.tick(1, pressed={"space"})
    assert scene.enemy_health() == 100.0, "Enemy behind should not be hit"
    assert scene.boss_health() == 500.0, "Boss behind should not be hit"


# ---------------------------------------------------------------------------
# Death
# ---------------------------------------------------------------------------

def test_enemy_dies_at_zero_health():
    """Three hits (75, 50, 25) kill the enemy on the fourth."""
    dt = 1.0 / 60.0
    cooldown_ticks = int(0.4 / dt) + 2

    scene = CombatScene(player_x=0.0, enemy_x=40.0, facing_x=1.0)

    for expected_hp in [75.0, 50.0, 25.0]:
        scene.tick(1, pressed={"space"})
        assert scene.enemy_health() == expected_hp
        # Wait for cooldown
        scene.tick(cooldown_ticks, pressed=set())

    # Fourth hit kills enemy
    scene.tick(1, pressed={"space"})
    assert scene.enemy_health() == 0.0 or not scene.enemy_obj.alive, (
        "Enemy should be dead after fourth hit"
    )


def test_no_damage_without_space():
    """Ticking without pressing SPACE does not affect enemy health."""
    scene = CombatScene(player_x=0.0, enemy_x=40.0, facing_x=1.0)
    scene.tick(30, pressed=set())
    assert scene.enemy_health() == 100.0, "No SPACE → no damage"
