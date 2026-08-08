"""Definições de nós diversos para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition


class SetVariableNode(NodeDefinition):
    """Define uma variável."""

    __node_definition__ = NodeDefinition(
        id="set_variable",
        title_key="Definir Variável",
        category_key="Variables",
        description_key="Define o valor de uma variável",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("value", "Valor", "ANY", default_value=None),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
            PinDefinition("value", "Valor", "ANY"),
        ]
    )


class GetVariableNode(NodeDefinition):
    """Obtém valor de uma variável."""

    __node_definition__ = NodeDefinition(
        id="get_variable",
        title_key="Obter Variável",
        category_key="Variables",
        description_key="Obtém o valor de uma variável",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
            PinDefinition("value", "Valor", "ANY"),
        ]
    )


class CallSubgraphNode(NodeDefinition):
    """Chama um subgrafo."""

    __node_definition__ = NodeDefinition(
        id="call_subgraph",
        title_key="Chamar Subgrafo",
        category_key="Graphs",
        description_key="Chama outro grafo como uma subfunção",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )


class SubgraphReturnNode(NodeDefinition):
    """Retorna do subgrafo."""

    __node_definition__ = NodeDefinition(
        id="subgraph_return",
        title_key="Retornar Subgrafo",
        category_key="Graphs",
        description_key="Retorna um valor do subgrafo para o chamador",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("value", "Valor", "ANY", default_value=None),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
            PinDefinition("value", "Valor", "ANY"),
        ]
    )


class SequenceNode(NodeDefinition):
    """Executa múltiplas saídas em sequência."""

    __node_definition__ = NodeDefinition(
        id="sequence",
        title_key="Sequência",
        category_key="Flow",
        description_key="Executa múltiplas ramos um após o outro",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("then_0", "Então 1", "EXEC"),
            PinDefinition("then_1", "Então 2", "EXEC"),
            PinDefinition("next", "Próximo", "EXEC"),
        ]
    )


class SetHudNode(NodeDefinition):
    """Define texto no HUD."""

    __node_definition__ = NodeDefinition(
        id="set_hud",
        title_key="Definir HUD",
        category_key="UI",
        description_key="Define um texto no HUD (Head Up Display)",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("text", "Texto", "STRING", default_value="Texto"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
        ]
    )


class EmitEventNode(NodeDefinition):
    """Emite um evento customizado."""

    __node_definition__ = NodeDefinition(
        id="emit_event",
        title_key="Emitir Evento",
        category_key="Events",
        description_key="Emite um evento customizado que outros objetos podem escutar",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("payload", "Dados", "ANY", default_value=None),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
        ]
    )
