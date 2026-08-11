"""Definições de nós de controle de fluxo para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class IfElseNode(NodeDefinition):
    """Ramificação condicional."""

    __node_definition__ = NodeDefinition(
        id="if_else",
        title_key="Se/Senão",
        category_key="Flow",
        description_key="Executa diferentes ramos baseado em uma condição",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="condition", label_key="Condição", pin_type=PinType.BOOL, default_value=False),
        ],
        outputs=[
            PinDefinition(id="true", label_key="Verdadeiro", pin_type=PinType.EXEC),
            PinDefinition(id="false", label_key="Falso", pin_type=PinType.EXEC),
            PinDefinition(id="value", label_key="Condição", pin_type=PinType.BOOL),
        ]
    )


class RestartSceneNode(NodeDefinition):
    """Reinicia a cena atual."""

    __node_definition__ = NodeDefinition(
        id="restart_scene",
        execution_model="terminal",
        title_key="Reiniciar Cena",
        category_key="Flow",
        description_key="Reinicia a cena atual",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
        ]
    )


class OnceNode(NodeDefinition):
    """Executa apenas uma vez."""

    __node_definition__ = NodeDefinition(
        id="once",
        title_key="Uma Vez",
        category_key="Flow",
        description_key="Permite que o ramo execute apenas uma vez",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="next", label_key="Próximo", pin_type=PinType.EXEC),
            PinDefinition(id="blocked", label_key="Bloqueado", pin_type=PinType.EXEC),
        ]
    )


class CooldownNode(NodeDefinition):
    """Espera tempo antes de permitir próxima execução."""

    __node_definition__ = NodeDefinition(
        id="cooldown",
        title_key="Cooldown",
        category_key="Flow",
        description_key="Aguarda um tempo de espera antes de permitir execução novamente",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="seconds", label_key="Segundos", pin_type=PinType.FLOAT, default_value=1.0),
        ],
        outputs=[
            PinDefinition(id="next", label_key="Próximo", pin_type=PinType.EXEC),
            PinDefinition(id="blocked", label_key="Bloqueado", pin_type=PinType.EXEC),
        ]
    )
