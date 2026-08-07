"""Definições de nós de state machine para Logic Graph."""
from __future__ import annotations

from engine.logic.metadata import NodeDefinition, PinDefinition


class CreateStateMachineNode(NodeDefinition):
    """Cria uma nova state machine."""

    __node_definition__ = NodeDefinition(
        id="create_state_machine",
        title="Criar State Machine",
        category="StateManagement",
        description="Cria uma nova máquina de estados com estado inicial",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("machine_id", "ID da Máquina", "STRING", default_value="sm_1"),
            PinDefinition("initial_state", "Estado Inicial", "STRING", default_value="idle"),
        ],
        pins_output=[
            PinDefinition("exec_created", "Criado", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("machine_id_out", "ID da Máquina", "STRING"),
            PinDefinition("initial_state_out", "Estado Inicial", "STRING"),
        ]
    )


class AddTransitionNode(NodeDefinition):
    """Adiciona uma transição entre estados."""

    __node_definition__ = NodeDefinition(
        id="add_transition",
        title="Adicionar Transição",
        category="StateManagement",
        description="Define uma transição entre dois estados",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("machine_id", "ID da Máquina", "STRING", default_value=""),
            PinDefinition("from_state", "De", "STRING", default_value="idle"),
            PinDefinition("to_state", "Para", "STRING", default_value="walking"),
            PinDefinition("condition", "Condição", "STRING", default_value="always"),  # always, on_key, on_event
        ],
        pins_output=[
            PinDefinition("exec_success", "Sucesso", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )


class ChangeStateNode(NodeDefinition):
    """Muda o estado atual."""

    __node_definition__ = NodeDefinition(
        id="change_state",
        title="Mudar Estado",
        category="StateManagement",
        description="Muda o estado atual da máquina de estados",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("machine_id", "ID da Máquina", "STRING", default_value=""),
            PinDefinition("state", "Novo Estado", "STRING", default_value="walking"),
            PinDefinition("force", "Forçar?", "BOOL", default_value=False),  # Ignorar verificação
        ],
        pins_output=[
            PinDefinition("exec_changed", "Mudado", "EXEC"),
            PinDefinition("exec_invalid_transition", "Transição Inválida", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("previous_state", "Estado Anterior", "STRING"),
            PinDefinition("new_state", "Novo Estado", "STRING"),
        ]
    )


class GetStateNode(NodeDefinition):
    """Retorna o estado atual."""

    __node_definition__ = NodeDefinition(
        id="get_state",
        title="Obter Estado",
        category="StateManagement",
        description="Obtém o estado atual da máquina de estados",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("machine_id", "ID da Máquina", "STRING", default_value=""),
        ],
        pins_output=[
            PinDefinition("exec_got_state", "Obtido", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("state", "Estado Atual", "STRING"),
        ]
    )


class IsInStateNode(NodeDefinition):
    """Verifica se está em um estado."""

    __node_definition__ = NodeDefinition(
        id="is_in_state",
        title="Está em Estado?",
        category="StateManagement",
        description="Verifica se a máquina está em um estado específico",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("machine_id", "ID da Máquina", "STRING", default_value=""),
            PinDefinition("state", "Estado a Verificar", "STRING", default_value="idle"),
        ],
        pins_output=[
            PinDefinition("exec_in_state", "Está", "EXEC"),
            PinDefinition("exec_not_in_state", "Não Está", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )
