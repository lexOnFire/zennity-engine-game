"""Definições de nós de física para Logic Graph."""
from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class ModifyRigidbodyNode:
    """Modifica propriedades de Rigidbody em runtime."""

    __node_definition__ = NodeDefinition(
        id="modify_rigidbody",
        title_key="Modificar Rigidbody",
        category_key="Physics",
        description_key="Altera velocidade, gravidade, massa de Rigidbody",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
            PinDefinition(id="property", label_key="Propriedade", pin_type=PinType.STRING, default_value="velocity_x"),
            PinDefinition(id="value", label_key="Novo Valor", pin_type=PinType.FLOAT, default_value=0.0),
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
            PinDefinition(id="property", label_key="Propriedade", pin_type=PinType.STRING, default_value="enabled"),
            PinDefinition(id="value", label_key="Novo Valor", pin_type=PinType.STRING, default_value="true"),
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
            PinDefinition(id="force_x", label_key="Força X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="force_y", label_key="Força Y", pin_type=PinType.FLOAT, default_value=100.0),
            PinDefinition(id="force_mode", label_key="Modo", pin_type=PinType.STRING, default_value="impulse"),
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )
