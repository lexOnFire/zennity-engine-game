"""Nó de Behavior Tree integrados ao Graph Framework e MetadataManager da Zennity Engine."""
from __future__ import annotations
from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class BTSelectorNode:
    """Nó Seletor (Fallback) da Behavior Tree."""

    __node_definition__ = NodeDefinition(
        id="bt.selector",
        title_key="node.bt.selector",
        category_key="Behavior Tree/Composite",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="out_1", pin_type=PinType.EXEC),
            PinDefinition(id="out_2", pin_type=PinType.EXEC),
        ],
    )


class BTSequenceNode:
    """Nó Sequência da Behavior Tree."""

    __node_definition__ = NodeDefinition(
        id="bt.sequence",
        title_key="node.bt.sequence",
        category_key="Behavior Tree/Composite",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="out_1", pin_type=PinType.EXEC),
            PinDefinition(id="out_2", pin_type=PinType.EXEC),
        ],
    )


class BTInverterNode:
    """Nó Decorador Inversor da Behavior Tree."""

    __node_definition__ = NodeDefinition(
        id="bt.inverter",
        title_key="node.bt.inverter",
        category_key="Behavior Tree/Decorator",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="child", pin_type=PinType.EXEC),
        ],
    )


class BTWaitNode:
    """Nó de Ação de Espera da Behavior Tree."""

    __node_definition__ = NodeDefinition(
        id="bt.wait",
        title_key="node.bt.wait",
        category_key="Behavior Tree/Action",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
            PinDefinition(id="duration", pin_type=PinType.FLOAT, default_value=1.0),
        ],
        outputs=[
            PinDefinition(id="out", pin_type=PinType.EXEC),
        ],
    )


class BTMoveToNode:
    """Nó de Ação MoveTo da Behavior Tree."""

    __node_definition__ = NodeDefinition(
        id="bt.move_to",
        title_key="node.bt.move_to",
        category_key="Behavior Tree/Action",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
            PinDefinition(id="target_pos", pin_type=PinType.VECTOR3),
            PinDefinition(id="speed", pin_type=PinType.FLOAT, default_value=5.0),
        ],
        outputs=[
            PinDefinition(id="out", pin_type=PinType.EXEC),
        ],
    )
