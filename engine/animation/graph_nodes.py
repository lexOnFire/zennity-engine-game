"""Definições de Nós do Graph Framework para Animator Controllers e Blend Trees."""
from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class AnimationStateNode:
    """Nó do Graph Framework que representa um estado de animação."""

    __node_definition__ = NodeDefinition(
        id="animation.state",
        title_key="node.animation.state",
        category_key="Animation",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
            PinDefinition(id="clip", pin_type=PinType.STRING),
            PinDefinition(id="speed", pin_type=PinType.FLOAT, default_value=1.0),
        ],
        outputs=[
            PinDefinition(id="out", pin_type=PinType.EXEC),
        ],
    )


class AnimatorParameterNode:
    """Nó do Graph Framework que representa um parâmetro do Animator Controller."""

    __node_definition__ = NodeDefinition(
        id="animation.parameter",
        title_key="node.animation.parameter",
        category_key="Animation",
        inputs=[
            PinDefinition(id="name", pin_type=PinType.STRING),
            PinDefinition(id="type", pin_type=PinType.STRING, default_value="bool"),
        ],
        outputs=[
            PinDefinition(id="value", pin_type=PinType.BOOL),
        ],
    )


class BlendTree1DNode:
    """Nó do Graph Framework que representa uma Blend Tree 1D."""

    __node_definition__ = NodeDefinition(
        id="animation.blend_tree_1d",
        title_key="node.animation.blend_tree_1d",
        category_key="Animation",
        inputs=[
            PinDefinition(id="parameter", pin_type=PinType.FLOAT),
            PinDefinition(id="clip_a", pin_type=PinType.STRING),
            PinDefinition(id="clip_b", pin_type=PinType.STRING),
        ],
        outputs=[
            PinDefinition(id="blended_clip", pin_type=PinType.STRING),
        ],
    )
