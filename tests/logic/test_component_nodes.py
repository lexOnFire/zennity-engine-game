from engine.logic.graph_asset import create_logic_node, node_port_definitions
from engine.logic.runtime.nodes.components_nodes import (
    COMPONENT_NODE_TYPES,
    execute_add_component,
)
from engine.runtime.runtime_world import RuntimeWorld


class _Target:
    def __init__(self) -> None:
        self.calls = []

    def add_component(self, component, properties) -> None:
        self.calls.append((component, dict(properties)))


class _Runtime:
    def __init__(self, target) -> None:
        self.target = target

    def _read_target(self, *_args):
        return self.target


def test_every_inspector_component_has_an_explicit_graph_node() -> None:
    assert set(COMPONENT_NODE_TYPES) == {
        "add_sprite_renderer", "add_animator", "add_rigidbody",
        "add_box_collider", "add_circle_collider", "add_camera",
        "add_audio_source", "add_ui_canvas", "add_ui_text",
        "add_ui_image", "add_ui_button",
    }
    for node_type in COMPONENT_NODE_TYPES:
        node = create_logic_node(node_type)
        ports = node_port_definitions(node)
        assert node["category"] == "Components"
        assert ("in", "flow") in ports["inputs"]
        assert ("target", "object") in ports["inputs"]
        assert ("next", "flow") in ports["outputs"]


def test_explicit_component_nodes_execute_with_their_visible_properties() -> None:
    target = _Target()
    runtime = _Runtime(target)

    for node_type, component in COMPONENT_NODE_TYPES.items():
        node = create_logic_node(node_type)
        assert execute_add_component(runtime, node, object(), 0.0) == ["next"]
        assert target.calls[-1] == (component, node["properties"])


def test_runtime_world_applies_graph_components_to_viewport_schema() -> None:
    obj = {"name": "Player"}

    RuntimeWorld.add_component(
        obj, "SpriteRenderer",
        {"texture": "Assets/player.png", "color": "#ff8040", "sort_order": 3},
    )
    RuntimeWorld.add_component(obj, "CircleCollider", {"radius": 12})
    RuntimeWorld.add_component(obj, "UIButton", {"text": "Play"})

    assert obj["renderer_enabled"] is False
    assert obj["texture"] == "Assets/player.png"
    assert obj["color"] == (255, 128, 64)
    assert obj["sort_order"] == 3
    assert obj["collider"] == {"radius": 12, "type": "circle"}
    assert obj["ui"]["type"] == "button"
    assert obj["ui"]["text"] == "Play"
