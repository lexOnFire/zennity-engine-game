"""Definições de nós de state machine para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class CreateStateMachineNode(NodeDefinition):
    """Cria uma nova state machine."""

    __node_definition__ = NodeDefinition(
        id="create_state_machine",
        title_key="Criar State Machine",
        category_key="StateManagement",
        description_key="Cria uma nova máquina de estados com estado inicial",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="machine_id", label_key="ID da Máquina", pin_type=PinType.STRING, default_value="sm_1"),
            PinDefinition(id="initial_state", label_key="Estado Inicial", pin_type=PinType.STRING, default_value="idle"),
        ],
        outputs=[
            PinDefinition(id="exec_created", label_key="Criado", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="machine_id", label_key="ID da Máquina", pin_type=PinType.STRING),
            PinDefinition(id="current_state", label_key="Estado Inicial", pin_type=PinType.STRING),
        ]
    )


class AddTransitionNode(NodeDefinition):
    """Adiciona uma transição entre estados."""

    __node_definition__ = NodeDefinition(
        id="add_transition",
        title_key="Adicionar Transição",
        category_key="StateManagement",
        description_key="Define uma transição entre dois estados",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="machine_id", label_key="ID da Máquina", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="from_state", label_key="De", pin_type=PinType.STRING, default_value="idle"),
            PinDefinition(id="to_state", label_key="Para", pin_type=PinType.STRING, default_value="walking"),
            PinDefinition(id="condition", label_key="Condição", pin_type=PinType.STRING, default_value="always"),  # always, on_key, on_event
        ],
        outputs=[
            PinDefinition(id="next", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )


class ChangeStateNode(NodeDefinition):
    """Muda o estado atual."""

    __node_definition__ = NodeDefinition(
        id="change_state",
        title_key="Mudar Estado",
        category_key="StateManagement",
        description_key="Muda o estado atual da máquina de estados",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="machine_id", label_key="ID da Máquina", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="state", label_key="Novo Estado", pin_type=PinType.STRING, default_value="walking"),
            PinDefinition(id="force", label_key="Forçar?", pin_type=PinType.BOOL, default_value=False),  # Ignorar verificação
        ],
        outputs=[
            PinDefinition(id="exec_changed", label_key="Mudado", pin_type=PinType.EXEC),
            PinDefinition(id="exec_invalid_transition", label_key="Transição Inválida", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="previous_state", label_key="Estado Anterior", pin_type=PinType.STRING),
            PinDefinition(id="new_state", label_key="Novo Estado", pin_type=PinType.STRING),
        ]
    )


class GetStateNode(NodeDefinition):
    """Retorna o estado atual."""

    __node_definition__ = NodeDefinition(
        id="get_state",
        title_key="Obter Estado",
        category_key="StateManagement",
        description_key="Obtém o estado atual da máquina de estados",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="machine_id", label_key="ID da Máquina", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="exec_got_state", label_key="Obtido", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="state", label_key="Estado Atual", pin_type=PinType.STRING),
        ]
    )


class IsInStateNode(NodeDefinition):
    """Verifica se está em um estado."""

    __node_definition__ = NodeDefinition(
        id="is_in_state",
        title_key="Está em Estado?",
        category_key="StateManagement",
        description_key="Verifica se a máquina está em um estado específico",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="machine_id", label_key="ID da Máquina", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="state", label_key="Estado a Verificar", pin_type=PinType.STRING, default_value="idle"),
        ],
        outputs=[
            PinDefinition(id="exec_in_state", label_key="Está", pin_type=PinType.EXEC),
            PinDefinition(id="exec_not_in_state", label_key="Não Está", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )
