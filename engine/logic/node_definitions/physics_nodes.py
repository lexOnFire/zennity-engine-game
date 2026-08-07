"""Definições de nós de física para Logic Graph."""
from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class ModifyRigidbodyNode:
    """Modifica propriedades de Rigidbody em runtime."""

    __node_definition__ = NodeDefinition(
        id="modify_rigidbody",
        title_key="Modificar Rigidbody",
        category_key="Logic/Physics",
        description_key="Altera velocidade, gravidade, massa e outras propriedades de Rigidbody.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target (objeto)", pin_type=PinType.STRING, default_value="player"),
            PinDefinition(id="property", label_key="Propriedade", pin_type=PinType.STRING, default_value="velocity_x"),
            PinDefinition(id="value", label_key="Novo Valor", pin_type=PinType.FLOAT, default_value=0.0),
        ],
        outputs=[
            PinDefinition(id="success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="failure", label_key="Erro", pin_type=PinType.EXEC),
        ],
        tags=["física", "rigidbody", "velocidade", "gravidade"],
    )


class ModifyColliderNode:
    """Modifica propriedades de Collider em runtime."""

    __node_definition__ = NodeDefinition(
        id="modify_collider",
        title_key="Modificar Collider",
        category_key="Logic/Physics",
        description_key="Ativa/desativa, altera tamanho ou trigger de Collider.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target (objeto)", pin_type=PinType.STRING, default_value="player"),
            PinDefinition(id="property", label_key="Propriedade", pin_type=PinType.STRING, default_value="enabled"),
            PinDefinition(id="value", label_key="Novo Valor", pin_type=PinType.STRING, default_value="true"),
        ],
        outputs=[
            PinDefinition(id="success", label_key="Sucesso", pin_type=PipType.EXEC),
            PinDefinition(id="failure", label_key="Erro", pin_type=PipType.EXEC),
        ],
        tags=["física", "collider", "trigger", "colisor"],
    )


class ApplyForceNode:
    """Aplica força a um Rigidbody."""

    __node_definition__ = NodeDefinition(
        id="apply_force",
        title_key="Aplicar Força",
        category_key="Logic/Physics",
        description_key="Aplica impulso ou força contínua a um Rigidbody.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target (objeto)", pin_type=PinType.STRING, default_value="player"),
            PinDefinition(id="force_x", label_key="Força X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="force_y", label_key="Força Y", pin_type=PipType.FLOAT, default_value=100.0),
            PinDefinition(id="force_mode", label_key="Modo", pin_type=PipType.STRING, default_value="impulse"),
        ],
        outputs=[
            PinDefinition(id="success", label_key="Sucesso", pin_type=PipType.EXEC),
            PinDefinition(id="failure", label_key="Erro", pin_type=PipType.EXEC),
        ],
        tags=["física", "força", "impulso", "movimento"],
    )
