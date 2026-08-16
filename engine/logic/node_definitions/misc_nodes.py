"""Definições de nós diversos para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class SetVariableNode(NodeDefinition):
    """Define uma variável."""

    __node_definition__ = NodeDefinition(
        id="set_variable",
        title_key="Definir Variável",
        category_key="Variables",
        description_key="Define o valor de uma variável",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            # ANY, not STRING: a variable holds whatever the graph puts in it,
            # and the shipping assets feed this pin numbers. The declaration
            # said STRING while the removed override said "any" -- the override
            # was carrying a truth the pin vocabulary could not express.
            PinDefinition(id="value", label_key="Valor", pin_type=PinType.ANY, default_value=None),
        ],
        outputs=[
            # ``next``, not ``exec_done``: 12 flow edges across the shipping
            # assets are wired to ``next`` and none to any other spelling. The
            # declaration said ``exec_done`` and a _EXPLICIT_PORT_CONTRACTS
            # entry silently overrode it, so this file never described the node
            # the editor actually showed. No ``value`` output: nothing
            # evaluates it, so it was a pin no author could ever read.
            PinDefinition(id="next", label_key="Próximo", pin_type=PinType.EXEC),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
            PinDefinition(id="value", label_key="Valor", pin_type=PinType.STRING),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="value", label_key="Valor", pin_type=PinType.STRING, default_value=None),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
            PinDefinition(id="value", label_key="Valor", pin_type=PinType.STRING),
        ]
    )


class SequenceNode(NodeDefinition):
    """Executa múltiplas saídas em sequência."""

    __node_definition__ = NodeDefinition(
        id="sequence",
        # PHASE 9 recovery item 3: the pin family this node expands at runtime
        # (then_0, then_1, ...). Declared here, on the node that owns it, so
        # DYNAMIC_PORT_NODES stops being a second table describing the same
        # fact -- the catalogue now derives it from the declarations.
        dynamic_exec_prefixes=("then_",),
        title_key="Sequência",
        category_key="Flow",
        description_key="Executa múltiplas ramos um após o outro",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="then_0", label_key="Então 1", pin_type=PinType.EXEC),
            PinDefinition(id="then_1", label_key="Então 2", pin_type=PinType.EXEC),
            PinDefinition(id="next", label_key="Próximo", pin_type=PinType.EXEC),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="text", label_key="Texto", pin_type=PinType.STRING, default_value="Texto"),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="payload", label_key="Dados", pin_type=PinType.STRING, default_value=None),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class CustomScriptNode(NodeDefinition):
    """Nó de script Python customizado avaliado como Pure Data."""

    __node_definition__ = NodeDefinition(
        id="custom_script",
        title_key="Script Customizado",
        category_key="Custom",
        description_key="Executa lógica em Python restrito sobre entradas e saídas de dados",
        execution_model="pure_data",
        inputs=[],
        outputs=[],
    )
