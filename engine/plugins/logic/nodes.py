"""Declarative Node definitions for Logic Plugin."""
from engine.graphs.registry import register_node
from engine.core.metadata.pin import PinDefinition, PinType

@register_node(
    id="logic.events.start",
    name="Start Event",
    category="Events",
    description="Triggered when the object enters the scene or game starts.",
    color="#FF4040",
    outputs=[PinDefinition("exec", PinType.EXEC, hide_label=True)]
)
class LogicStartEventNode:
    pass

@register_node(
    id="logic.events.update",
    name="Update Event",
    category="Events",
    description="Triggered every frame.",
    color="#FF4040",
    outputs=[
        PinDefinition("exec", PinType.EXEC, hide_label=True),
        PinDefinition("dt", PinType.FLOAT, "Delta Time")
    ]
)
class LogicUpdateEventNode:
    pass

@register_node(
    id="logic.movement.move",
    name="Move Object",
    category="Movement",
    description="Moves the object in the given direction.",
    color="#00AEEF",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("direction", PinType.VECTOR2),
        PinDefinition("speed", PinType.FLOAT, default_value=1.0)
    ],
    outputs=[PinDefinition("exec", PinType.EXEC)]
)
class LogicMoveNode:
    pass

@register_node(
    id="logic.misc.log",
    name="Log Message",
    category="Misc",
    description="Logs a message to the console.",
    color="#808080",
    inputs=[
        PinDefinition("exec", PinType.EXEC),
        PinDefinition("message", PinType.STRING)
    ],
    outputs=[PinDefinition("exec", PinType.EXEC)]
)
class LogicLogNode:
    pass
