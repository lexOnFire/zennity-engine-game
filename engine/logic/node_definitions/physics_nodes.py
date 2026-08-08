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


# Phase 5B.1: Getter nodes (pure data)
class GetRigidBodyVelocityXNode:
    """Get RigidBody velocity X component."""

    __node_definition__ = NodeDefinition(
        id="get_rigidbody_velocity_x",
        title_key="Get Velocity X",
        category_key="Physics/Getters",
        description_key="Returns RigidBody velocity X component",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Velocity X", pin_type=PinType.FLOAT),
        ]
    )


class GetRigidBodyVelocityYNode:
    """Get RigidBody velocity Y component."""

    __node_definition__ = NodeDefinition(
        id="get_rigidbody_velocity_y",
        title_key="Get Velocity Y",
        category_key="Physics/Getters",
        description_key="Returns RigidBody velocity Y component",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Velocity Y", pin_type=PinType.FLOAT),
        ]
    )


class GetRigidBodyMassNode:
    """Get RigidBody mass."""

    __node_definition__ = NodeDefinition(
        id="get_rigidbody_mass",
        title_key="Get Mass",
        category_key="Physics/Getters",
        description_key="Returns RigidBody mass",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Mass", pin_type=PinType.FLOAT),
        ]
    )


class GetRigidBodyGravityScaleNode:
    """Get RigidBody gravity scale."""

    __node_definition__ = NodeDefinition(
        id="get_rigidbody_gravity_scale",
        title_key="Get Gravity Scale",
        category_key="Physics/Getters",
        description_key="Returns RigidBody gravity scale",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Gravity Scale", pin_type=PinType.FLOAT),
        ]
    )


class GetRigidBodyUseGravityNode:
    """Get RigidBody use gravity flag."""

    __node_definition__ = NodeDefinition(
        id="get_rigidbody_use_gravity",
        title_key="Get Use Gravity",
        category_key="Physics/Getters",
        description_key="Returns RigidBody use gravity flag",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Use Gravity", pin_type=PinType.BOOL),
        ]
    )


class GetRigidBodyIsKinematicNode:
    """Get RigidBody kinematic flag."""

    __node_definition__ = NodeDefinition(
        id="get_rigidbody_is_kinematic",
        title_key="Get Is Kinematic",
        category_key="Physics/Getters",
        description_key="Returns RigidBody kinematic flag",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Is Kinematic", pin_type=PinType.BOOL),
        ]
    )
