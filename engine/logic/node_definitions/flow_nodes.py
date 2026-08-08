"""Definições de nós de controle de fluxo para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition


class IfElseNode(NodeDefinition):
    """Ramificação condicional."""

    __node_definition__ = NodeDefinition(
        id="if_else",
        title_key="Se/Senão",
        category_key="Flow",
        description_key="Executa diferentes ramos baseado em uma condição",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("condition", "Condição", "BOOL", default_value=False),
        ],
        outputs=[
            PinDefinition("true", "Verdadeiro", "EXEC"),
            PinDefinition("false", "Falso", "EXEC"),
        ]
    )


class RestartSceneNode(NodeDefinition):
    """Reinicia a cena atual."""

    __node_definition__ = NodeDefinition(
        id="restart_scene",
        title_key="Reiniciar Cena",
        category_key="Flow",
        description_key="Reinicia a cena atual",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("next", "Próximo", "EXEC"),
            PinDefinition("blocked", "Bloqueado", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("seconds", "Segundos", "FLOAT", default_value=1.0),
        ],
        outputs=[
            PinDefinition("next", "Próximo", "EXEC"),
            PinDefinition("blocked", "Bloqueado", "EXEC"),
        ]
    )
