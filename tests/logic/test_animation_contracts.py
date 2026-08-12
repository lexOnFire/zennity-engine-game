"""play_animation and stop_animation: one owner, one contract, one executor.

PHASE 9 recovery item 4.2.

Both nodes were declared twice -- ``actions_nodes`` and ``animation_nodes`` --
with different pins, and each had two executors. The measured effect on a real
shipping asset was that ``play_animation`` did nothing an author could predict:

* the author saved ``state='PlayerAttack'``;
* normalization seeded ``animation_name='idle'`` from the losing declaration's
  default;
* the winning executor read ``animation_name``, so the author's value was
  ignored;
* it returned ``failure``, a port the resolved contract did not declare, so the
  flow after the node stopped dead.

``animation_nodes`` wins: it resolves the real Animator component through
``target`` and has a failure path. What ``actions_nodes`` held was a thinner
parallel implementation that assumed the game object *was* the animator.

``state`` is the authoring property, from asset evidence: 4 saved nodes use it
with real values, 0 use ``animation_name``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    load_logic_graph,
    normalize_logic_graph,
    save_logic_graph,
)
from engine.logic.node_definitions import definition_owner, duplicate_definition_conflicts
from engine.logic.node_system import load_runtime_node_modules
from engine.logic.runtime.registry import registry

REPO_ROOT = Path(__file__).resolve().parents[2]
ANIMATION_NODES = ("play_animation", "stop_animation")


@pytest.fixture(scope="module", autouse=True)
def runtime_loaded():
    load_runtime_node_modules()


# ---------------------------------------------------------------------------
# Split brain
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("node_id", ANIMATION_NODES)
def test_the_split_brain_is_resolved(node_id: str):
    """One definition, one owner, one executor -- checked, not assumed."""
    assert definition_owner(node_id) == "animation_nodes"
    assert not [c for c in duplicate_definition_conflicts() if c[0] == node_id]
    assert registry.executors[node_id].__module__ == (
        "engine.logic.runtime.nodes.animation_nodes"
    )


@pytest.mark.parametrize("node_id", ANIMATION_NODES)
def test_actions_nodes_no_longer_declares_or_implements_it(node_id: str):
    import engine.logic.node_definitions.actions_nodes as definitions
    import engine.logic.runtime.nodes.actions_nodes as runtime_module

    for module in (definitions, runtime_module):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert f'"{node_id}"' not in source and f"'{node_id}'" not in source, (
            f"{module.__name__} still names {node_id}"
        )


def test_no_duplicate_definitions_remain_anywhere():
    assert duplicate_definition_conflicts() == []


def test_the_known_duplicate_debt_is_empty():
    """Item 4.1 recorded these two as scheduled; the schedule is now met."""
    from engine.logic.node_definitions import KNOWN_DUPLICATE_DEFINITIONS

    assert set(KNOWN_DUPLICATE_DEFINITIONS) == set()


# ---------------------------------------------------------------------------
# The contract
# ---------------------------------------------------------------------------

def test_play_animation_declares_the_canonical_contract():
    schema = NODE_PORT_DEFINITIONS["play_animation"]
    assert [name for name, _kind in schema["inputs"]] == ["exec", "target", "state", "force"]
    assert [name for name, _kind in schema["outputs"]] == ["next", "exec_failure", "animation"]


def test_stop_animation_declares_the_canonical_contract():
    schema = NODE_PORT_DEFINITIONS["stop_animation"]
    assert [name for name, _kind in schema["inputs"]] == ["exec", "target"]
    assert [name for name, _kind in schema["outputs"]] == ["next", "exec_failure", "stopped"]


@pytest.mark.parametrize("node_id", ANIMATION_NODES)
def test_no_stale_explicit_contract_overrides_the_declaration(node_id: str):
    """The declaration is the source of truth, not a snapshot beside it."""
    from engine.logic.node_definitions.catalogue import _EXPLICIT_PORT_CONTRACTS

    assert node_id not in _EXPLICIT_PORT_CONTRACTS, (
        f"{node_id} still has an explicit port contract; it would override "
        "animation_nodes' declaration exactly as before"
    )


@pytest.mark.parametrize("node_id", ANIMATION_NODES)
def test_the_definition_and_the_port_schema_agree(node_id: str):
    entry, schema = NODE_DEFINITIONS[node_id], NODE_PORT_DEFINITIONS[node_id]
    assert [tuple(p) for p in entry["inputs"]] == [tuple(p) for p in schema["inputs"]]
    assert [tuple(p) for p in entry["outputs"]] == [tuple(p) for p in schema["outputs"]]


@pytest.mark.parametrize("node_id", ANIMATION_NODES)
def test_the_executor_returns_only_declared_ports(node_id: str):
    """Ports the executor returns must exist on the node, or flow dies there."""
    import inspect
    import re

    source = inspect.getsource(registry.executors[node_id])
    returned = set(re.findall(r'return \["([a-z_]+)"\]', source))
    declared = {name for name, kind in NODE_PORT_DEFINITIONS[node_id]["outputs"]
                if kind in ("flow", "exec")}
    assert returned, "no return ports found; the scan is broken"
    assert returned <= declared, (
        f"{node_id} executor returns {sorted(returned - declared)}, "
        f"which the contract does not declare (declares {sorted(declared)})"
    )


# ---------------------------------------------------------------------------
# state vs animation_name
# ---------------------------------------------------------------------------

def _asset_property_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in REPO_ROOT.rglob("*.zlogic"):
        if ".git" in path.parts:
            continue
        for node in json.loads(path.read_text(encoding="utf-8")).get("nodes", []):
            if str(node.get("type")) != "play_animation":
                continue
            for name in (node.get("properties") or {}):
                counts[name] = counts.get(name, 0) + 1
    return counts


def test_the_assets_justify_state_being_canonical():
    counts = _asset_property_counts()
    assert counts.get("state", 0) > 0, "no saved node uses state; the decision needs re-checking"
    assert counts.get("animation_name", 0) == 0, (
        f"assets now save animation_name {counts['animation_name']} time(s); "
        "the canonical property was chosen from asset usage"
    )


def test_animation_name_is_not_a_second_authorable_property():
    properties = NODE_DEFINITIONS["play_animation"]["properties"]
    assert "state" in properties
    assert "animation_name" not in properties, (
        "animation_name is exposed as an authorable field beside state; it is "
        "load-time compatibility, not a competing property"
    )


def test_a_legacy_animation_name_becomes_state():
    """The historical bug: the seeded default won over the author's value."""
    graph = {
        "format": "zennity.logic_graph", "version": 1, "name": "LegacyProperty",
        "nodes": [{"id": "n", "type": "play_animation", "position": [0.0, 0.0],
                   "properties": {"animation_name": "Run", "target": "Player"}}],
        "edges": [],
    }
    properties = normalize_logic_graph(graph)["nodes"][0]["properties"]
    assert properties["state"] == "Run", properties
    assert properties.get("animation_name") is None, (
        "animation_name survived the migration and would shadow state"
    )


def test_a_saved_state_is_never_overwritten_by_a_default():
    graph = {
        "format": "zennity.logic_graph", "version": 1, "name": "SavedState",
        "nodes": [{"id": "n", "type": "play_animation", "position": [0.0, 0.0],
                   "properties": {"state": "PlayerAttack"}}],
        "edges": [],
    }
    assert normalize_logic_graph(graph)["nodes"][0]["properties"]["state"] == "PlayerAttack"


def test_the_shipping_assets_keep_their_state_values():
    for path in sorted(REPO_ROOT.rglob("*.zlogic")):
        if ".git" in path.parts:
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        saved = {
            str(node["id"]): (node.get("properties") or {}).get("state")
            for node in raw.get("nodes", [])
            if str(node.get("type")) == "play_animation"
        }
        if not saved:
            continue
        normalized = {
            str(node["id"]): node["properties"].get("state")
            for node in normalize_logic_graph(load_logic_graph(path))["nodes"]
            if node["type"] == "play_animation"
        }
        for node_id, value in saved.items():
            assert normalized.get(node_id) == value, f"{path.name}:{node_id}"


# ---------------------------------------------------------------------------
# Properties and save/reopen
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("node_id", ANIMATION_NODES)
def test_every_data_pin_is_authorable(node_id: str):
    entry = NODE_DEFINITIONS[node_id]
    data_inputs = {name for name, kind in entry["inputs"] if kind not in ("flow", "exec")}
    missing = data_inputs - set(entry.get("properties", {}))
    assert not missing, f"{node_id} data pins with no editable default: {sorted(missing)}"


def test_play_animation_survives_save_and_reopen(tmp_path: Path):
    graph = {
        "format": "zennity.logic_graph", "version": 1, "name": "AnimRoundTrip",
        "nodes": [{"id": "n", "type": "play_animation", "position": [0.0, 0.0],
                   "properties": {"state": "Run", "target": "Hero", "force": True}}],
        "edges": [],
    }
    destination = tmp_path / "AnimRoundTrip.zlogic"
    save_logic_graph(destination, normalize_logic_graph(graph))
    reopened = normalize_logic_graph(load_logic_graph(destination))["nodes"][0]["properties"]
    assert reopened["state"] == "Run"
    assert reopened["target"] == "Hero"
    assert reopened["force"] is True


def test_a_legacy_graph_is_saved_with_the_canonical_property(tmp_path: Path):
    graph = {
        "format": "zennity.logic_graph", "version": 1, "name": "LegacySave",
        "nodes": [{"id": "n", "type": "play_animation", "position": [0.0, 0.0],
                   "properties": {"animation_name": "Run"}}],
        "edges": [],
    }
    destination = tmp_path / "LegacySave.zlogic"
    save_logic_graph(destination, normalize_logic_graph(graph))
    written = json.loads(destination.read_text(encoding="utf-8"))["nodes"][0]["properties"]
    assert written["state"] == "Run"
    assert "animation_name" not in written


# ---------------------------------------------------------------------------
# Runtime roundtrip
# ---------------------------------------------------------------------------

@pytest.fixture
def animator():
    from engine.animation.animator import Animator
    from engine.animation.clip import AnimationClip

    instance = Animator()
    for name in ("Run", "Idle"):
        instance.add_clip(AnimationClip(name=name, frames=[], fps=10.0))
    return instance


class _Player:
    def __init__(self, animator, name="Hero"):
        self.name = name
        self._animator = animator

    def get_component(self, component_type):
        from engine.animation.animator import Animator

        return self._animator if component_type is Animator else None


class _Game:
    def __init__(self, player):
        self._player = player

    def find_object(self, name):
        if self._player is not None and name == self._player.name:
            return self._player
        return None


def _run(graph: dict, game) -> list[str]:
    """Drive the real executor through the real normalizer."""
    from engine.logic.runtime import LogicGraphRuntime

    normalized = normalize_logic_graph(graph)
    node = normalized["nodes"][0]
    runtime = LogicGraphRuntime(normalized)
    return registry.executors[node["type"]](runtime, node, game, 1.0 / 60.0)


def _graph(node_type: str, properties: dict) -> dict:
    return {
        "format": "zennity.logic_graph", "version": 1, "name": "RuntimeRoundTrip",
        "nodes": [{"id": "n", "type": node_type, "position": [0.0, 0.0],
                   "properties": properties}],
        "edges": [],
    }


def test_play_animation_reaches_the_animator(animator):
    game = _Game(_Player(animator))
    ports = _run(_graph("play_animation", {"state": "Run", "target": "Hero"}), game)
    assert animator.current_clip == "Run"
    assert ports == ["next"]


def test_a_legacy_property_still_reaches_the_animator(animator):
    """End to end: the value the author saved is the one that plays."""
    game = _Game(_Player(animator))
    ports = _run(_graph("play_animation", {"animation_name": "Run", "target": "Hero"}), game)
    assert animator.current_clip == "Run"
    assert ports == ["next"]


def test_force_is_passed_through(animator):
    game = _Game(_Player(animator))
    _run(_graph("play_animation", {"state": "Run", "target": "Hero"}), game)
    played: list[tuple[str, bool]] = []
    animator.play = lambda name, force=False: played.append((name, force))
    _run(_graph("play_animation", {"state": "Idle", "target": "Hero", "force": True}), game)
    assert played == [("Idle", True)]


def test_a_missing_animator_takes_the_failure_port(animator):
    ports = _run(_graph("play_animation", {"state": "Run", "target": "Ghost"}), _Game(None))
    assert ports == ["exec_failure"]
    assert animator.current_clip is None


def test_an_unknown_clip_takes_the_failure_port(animator):
    game = _Game(_Player(animator))
    assert _run(_graph("play_animation", {"state": "Nope", "target": "Hero"}), game) == [
        "exec_failure"
    ]


def test_an_empty_state_takes_the_failure_port(animator):
    game = _Game(_Player(animator))
    assert _run(_graph("play_animation", {"state": "", "target": "Hero"}), game) == [
        "exec_failure"
    ]


def test_stop_animation_stops_the_animator(animator):
    game = _Game(_Player(animator))
    _run(_graph("play_animation", {"state": "Run", "target": "Hero"}), game)
    assert animator.current_clip == "Run"

    ports = _run(_graph("stop_animation", {"target": "Hero"}), game)
    assert ports == ["next"]


def test_stop_animation_fails_without_an_animator():
    assert _run(_graph("stop_animation", {"target": "Ghost"}), _Game(None)) == ["exec_failure"]
