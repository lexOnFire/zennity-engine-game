"""Definições de nós de física para Logic Graph."""
from engine.core.metadata import NodeDefinition, PinDefinition


class ModifyRigidbodyNode:
    """Modifica propriedades de Rigidbody em runtime."""

    __node_definition__ = NodeDefinition(
        id="modify_rigidbody",
        title_key="Modificar Rigidbody",
        category_key="Physics",
        description_key="Altera velocidade, gravidade, massa de Rigidbody",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("target", "Target", "STRING", default_value="player"),
            PinDefinition("property", "Propriedade", "STRING", default_value="velocity_x"),
            PinDefinition("value", "Novo Valor", "FLOAT", default_value=0.0),
        ],
        outputs=[
            PinDefinition("exec_success", "Sucesso", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )


class ModifyColliderNode:
    """Modifica propriedades de Collider em runtime."""

    __node_definition__ = NodeDefinition(
        id="modify_collider",
        title_key="Modificar Collider",
        category_key="Physics",
        description_key="Ativa/desativa ou altera tamanho de Collider",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("target", "Target", "STRING", default_value="player"),
            PinDefinition("property", "Propriedade", "STRING", default_value="enabled"),
            PinDefinition("value", "Novo Valor", "STRING", default_value="true"),
        ],
        outputs=[
            PinDefinition("exec_success", "Sucesso", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )


class ApplyForceNode:
    """Aplica força a um Rigidbody."""

    __node_definition__ = NodeDefinition(
        id="apply_force",
        title_key="Aplicar Força",
        category_key="Physics",
        description_key="Aplica impulso ou força contínua a um Rigidbody",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("target", "Target", "STRING", default_value="player"),
            PinDefinition("force_x", "Força X", "FLOAT", default_value=0.0),
            PinDefinition("force_y", "Força Y", "FLOAT", default_value=100.0),
            PinDefinition("force_mode", "Modo", "STRING", default_value="impulse"),
        ],
        outputs=[
            PinDefinition("exec_success", "Sucesso", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )
