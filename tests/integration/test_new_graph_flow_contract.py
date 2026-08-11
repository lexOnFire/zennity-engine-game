"""Phase 9.5B Stage 1 — HARD REQUIREMENT (brief item 20).

A graph authored from **today's palette definitions** must execute end to end.

This is the exact reproduction of the Phase 9.5A P0: the palette advertised
`exec_done`, every executor returned `next`, and `core._follow` matched port
names by exact string, so a freshly authored graph died silently at the first
node.  No pre-existing asset is used here -- the graph is built from the pins
the palette actually offers right now.
"""
from __future__ import annotations

import pytest

from engine.logic.graph_asset import normalize_logic_graph
from engine.logic.node_definitions import NODE_DEFINITIONS
from engine.logic.runtime import LogicGraphRuntime


class ProbeGame:
    """Minimal host exposing what the nodes under test need."""

    name = "player"

    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.logged: list[str] = []
        self.keys: set[str] = set()

    # movement
    def move_by(self, dx, dy):
        self.x += float(dx)
        self.y += float(dy)

    def log(self, message):
        self.logged.append(str(message))

    # input
    def axis(self, *_a, **_k):
        return 1.0

    def is_key_pressed(self, key):
        return str(key) in self.keys

    def key_pressed(self, key):
        return str(key) in self.keys

    def key_held(self, key):
        return str(key) in self.keys


def exec_output_pins(node_id: str) -> list[str]:
    """The exec output pins the palette shows for this node, today."""
    entry = NODE_DEFINITIONS[node_id]
    return [p[0] for p in entry["outputs"] if p[1] == "flow"]


def first_exec_output(node_id: str) -> str:
    pins = exec_output_pins(node_id)
    assert pins, f"{node_id} declares no exec output"
    return pins[0]


def exec_input_pin(node_id: str) -> str:
    entry = NODE_DEFINITIONS[node_id]
    flow_in = [p[0] for p in entry["inputs"] if p[1] == "flow"]
    return flow_in[0] if flow_in else "exec"


# ---------------------------------------------------------------------------
def test_graph_authored_from_the_current_palette_runs_to_the_last_node():
    """event_update -> input_axis -> move_by, wired with palette pin names."""
    nodes = [
        {"id": "n_update", "type": "event_update"},
        {"id": "n_axis", "type": "input_axis", "properties": {"axis": "horizontal"}},
        {"id": "n_move", "type": "move_by", "properties": {"x": 5.0, "y": 0.0}},
        {"id": "n_log", "type": "log_message", "properties": {"text": "moved"}},
    ]
    # Wire using exactly the pin ids the palette exposes -- no hand-picked names.
    edges = [
        {"from": "n_update", "from_port": first_exec_output("event_update"),
         "to": "n_axis", "to_port": exec_input_pin("input_axis")},
        {"from": "n_axis", "from_port": first_exec_output("input_axis"),
         "to": "n_move", "to_port": exec_input_pin("move_by")},
        {"from": "n_move", "from_port": first_exec_output("move_by"),
         "to": "n_log", "to_port": exec_input_pin("log_message")},
    ]

    graph = normalize_logic_graph(
        {"format": "zennity.logic", "name": "authored", "nodes": nodes, "edges": edges}
    )

    runtime = LogicGraphRuntime(graph)
    game = ProbeGame()
    runtime.start(game)
    runtime.update(game, 0.016)

    assert "n_log" in runtime.executed_nodes, (
        "flow did not reach the last node -- the palette and the runtime still "
        f"disagree. executed={runtime.executed_nodes}"
    )
    assert game.logged == ["moved"]


def test_saving_and_reloading_an_authored_graph_preserves_execution():
    """Author -> normalise (save) -> normalise again (load) -> still runs."""
    nodes = [
        {"id": "s", "type": "event_update"},
        {"id": "m", "type": "move_by", "properties": {"x": 3.0, "y": 0.0}},
    ]
    edges = [{"from": "s", "from_port": first_exec_output("event_update"),
              "to": "m", "to_port": exec_input_pin("move_by")}]

    saved = normalize_logic_graph(
        {"format": "zennity.logic", "name": "roundtrip", "nodes": nodes, "edges": edges})
    reloaded = normalize_logic_graph(saved)

    runtime = LogicGraphRuntime(reloaded)
    game = ProbeGame()
    runtime.start(game)
    runtime.update(game, 1.0)   # move_by scales by dt

    assert "m" in runtime.executed_nodes
    assert game.x == pytest.approx(3.0)


@pytest.mark.parametrize("node_id", [
    "move_by", "input_axis", "set_variable", "play_animation",
    "raycast", "set_ui_text", "scene.load_scene", "add_number",
])
def test_required_palette_nodes_expose_a_usable_contract(node_id):
    """Brief item 19: the pins shown must be the pins the runtime accepts."""
    assert node_id in NODE_DEFINITIONS, f"{node_id} missing from the palette"
    entry = NODE_DEFINITIONS[node_id]
    assert entry["inputs"] or entry["outputs"], f"{node_id} has no pins at all"

    # No node may still advertise the pre-Stage-1 spellings.
    declared = {p[0] for p in entry["outputs"]}
    assert "exec_done" not in declared, f"{node_id} still declares exec_done"
    assert "exec_success" not in declared, f"{node_id} still declares exec_success"


def test_no_palette_node_declares_a_legacy_exec_port():
    """The next/exec_done split is gone architecturally, not case by case."""
    from engine.logic.port_aliases import EXEC_PORT_ALIASES

    offenders = []
    for node_id, entry in NODE_DEFINITIONS.items():
        for pin_id, pin_type in entry.get("outputs", []) or []:
            if pin_type == "flow" and pin_id in EXEC_PORT_ALIASES:
                offenders.append(f"{node_id}.{pin_id}")
    assert not offenders, f"legacy exec ports still declared: {offenders}"


def test_branch_nodes_expose_both_outcomes():
    """key_pressed used to declare only the positive branch."""
    for node_id, expected in (
        ("is_grounded", {"grounded", "airborne"}),
        ("key_held", {"held", "released"}),
        ("key_pressed", {"exec_pressed", "exec_not_pressed"}),
    ):
        declared = {p[0] for p in NODE_DEFINITIONS[node_id]["outputs"] if p[1] == "flow"}
        assert expected <= declared, f"{node_id} declares {declared}, expected {expected}"
