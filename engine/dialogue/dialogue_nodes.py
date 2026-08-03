"""Nós de Dialogue Graph integrados ao Graph Framework e MetadataManager da Zennity Engine."""
from __future__ import annotations
from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class DialogueNode:
    """Nó de Texto de Diálogo com locutor e fala."""

    __node_definition__ = NodeDefinition(
        id="dialogue.speech",
        title_key="node.dialogue.speech",
        category_key="Dialogue",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
            PinDefinition(id="speaker", pin_type=PinType.STRING, default_value="NPC"),
            PinDefinition(id="text", pin_type=PinType.STRING, default_value="Olá!"),
        ],
        outputs=[
            PinDefinition(id="out", pin_type=PinType.EXEC),
        ],
    )


class ChoiceNode:
    """Nó de Opções de Escolha do Diálogo."""

    __node_definition__ = NodeDefinition(
        id="dialogue.choice",
        title_key="node.dialogue.choice",
        category_key="Dialogue",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
            PinDefinition(id="prompt", pin_type=PinType.STRING, default_value="Escolha:"),
        ],
        outputs=[
            PinDefinition(id="option_1", pin_type=PinType.EXEC),
            PinDefinition(id="option_2", pin_type=PinType.EXEC),
        ],
    )


class ConditionNode:
    """Nó de Condição para ramificar falas."""

    __node_definition__ = NodeDefinition(
        id="dialogue.condition",
        title_key="node.dialogue.condition",
        category_key="Dialogue",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
            PinDefinition(id="condition_var", pin_type=PinType.STRING),
        ],
        outputs=[
            PinDefinition(id="true", pin_type=PinType.EXEC),
            PinDefinition(id="false", pin_type=PinType.EXEC),
        ],
    )


class EndNode:
    """Nó de Encerramento do Diálogo."""

    __node_definition__ = NodeDefinition(
        id="dialogue.end",
        title_key="node.dialogue.end",
        category_key="Dialogue",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
        ],
        outputs=[],
    )


class DialogueEventNode:
    """Nó para disparar eventos durante o diálogo."""

    __node_definition__ = NodeDefinition(
        id="dialogue.event",
        title_key="node.dialogue.event",
        category_key="Dialogue",
        inputs=[
            PinDefinition(id="in", pin_type=PinType.EXEC),
            PinDefinition(id="event_name", pin_type=PinType.STRING),
        ],
        outputs=[
            PinDefinition(id="out", pin_type=PinType.EXEC),
        ],
    )
