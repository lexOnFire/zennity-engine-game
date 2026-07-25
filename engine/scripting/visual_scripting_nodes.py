"""Nós de Visual Scripting integrados ao Graph Framework e MetadataManager da Zennity Engine."""
from __future__ import annotations
from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class EventOnStartNode:
    """Nó de Evento OnStart (Início do jogo)."""

    __node_definition__ = NodeDefinition(
        id="vs.event_on_start",
        title_key="node.vs.event_on_start",
        category_key="Visual Scripting/Events",
        inputs=[],
        outputs=[
            PinDefinition(id="out", pin_type=PinType.EXEC),
        ],
    )


class EventOnUpdateNode:
    """Nó de Evento OnUpdate (Cada frame)."""

    __node_definition__ = NodeDefinition(
        id="vs.event_on_update",
        title_key="node.vs.event_on_update",
        category_key="Visual Scripting/Events",
        inputs=[],
        outputs=[
            PinDefinition(id="out", pin_type=PinType.EXEC),
            PinDefinition(id="delta_time", pin_type=PinType.FLOAT),
        ],
    )


class IfElseNode:
    """Nó de Controle de Fluxo If / Else."""

    __node_definition__ = NodeDefinition(
        id="vs.if_else",
        title_key="node.vs.if_else",
        category_key="Visual Scripting/Control",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
            PinDefinition(id="condition", pin_type=PinType.BOOL, default_value=True),
        ],
        outputs=[
            PinDefinition(id="true", pin_type=PinType.EXEC),
            PinDefinition(id="false", pin_type=PinType.EXEC),
        ],
    )


class SetPositionNode:
    """Nó de Ação para alterar a posição do Transform."""

    __node_definition__ = NodeDefinition(
        id="vs.set_position",
        title_key="node.vs.set_position",
        category_key="Visual Scripting/Actions",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
            PinDefinition(id="position", pin_type=PinType.VECTOR3),
        ],
        outputs=[
            PinDefinition(id="out", pin_type=PinType.EXEC),
        ],
    )


class LogMessageNode:
    """Nó de Ação para imprimir mensagens no Console."""

    __node_definition__ = NodeDefinition(
        id="vs.log_message",
        title_key="node.vs.log_message",
        category_key="Visual Scripting/Actions",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
            PinDefinition(id="message", pin_type=PinType.STRING, default_value="Hello Zennity!"),
        ],
        outputs=[
            PinDefinition(id="out", pin_type=PinType.EXEC),
        ],
    )
