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


# Phase 5B.2: Collision/Trigger Event Nodes (EVENT SOURCE)
class OnCollisionEnterNode:
    """Triggered when two colliders start colliding."""

    __node_definition__ = NodeDefinition(
        id="on_collision_enter",
        title_key="On Collision Enter",
        category_key="Physics/Events",
        description_key="Fires when collision starts",

        inputs=[],

        outputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="self_object", label_key="Self Object", pin_type=PinType.OBJECT),
            PinDefinition(id="other_object", label_key="Other Object", pin_type=PinType.OBJECT),
            PinDefinition(id="self_collider", label_key="Self Collider", pin_type=PinType.OBJECT),
            PinDefinition(id="other_collider", label_key="Other Collider", pin_type=PinType.OBJECT),
        ]
    )


class OnCollisionExitNode:
    """Triggered when two colliders stop colliding."""

    __node_definition__ = NodeDefinition(
        id="on_collision_exit",
        title_key="On Collision Exit",
        category_key="Physics/Events",
        description_key="Fires when collision ends",

        inputs=[],

        outputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="self_object", label_key="Self Object", pin_type=PinType.OBJECT),
            PinDefinition(id="other_object", label_key="Other Object", pin_type=PinType.OBJECT),
            PinDefinition(id="self_collider", label_key="Self Collider", pin_type=PinType.OBJECT),
            PinDefinition(id="other_collider", label_key="Other Collider", pin_type=PinType.OBJECT),
        ]
    )


class OnTriggerEnterNode:
    """Triggered when an object enters a trigger collider."""

    __node_definition__ = NodeDefinition(
        id="on_trigger_enter",
        title_key="On Trigger Enter",
        category_key="Physics/Events",
        description_key="Fires when trigger is entered",

        inputs=[],

        outputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="self_object", label_key="Self Object", pin_type=PinType.OBJECT),
            PinDefinition(id="other_object", label_key="Other Object", pin_type=PinType.OBJECT),
            PinDefinition(id="self_collider", label_key="Self Collider", pin_type=PinType.OBJECT),
            PinDefinition(id="other_collider", label_key="Other Collider", pin_type=PinType.OBJECT),
        ]
    )


class OnTriggerExitNode:
    """Triggered when an object exits a trigger collider."""

    __node_definition__ = NodeDefinition(
        id="on_trigger_exit",
        title_key="On Trigger Exit",
        category_key="Physics/Events",
        description_key="Fires when trigger is exited",

        inputs=[],

        outputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="self_object", label_key="Self Object", pin_type=PinType.OBJECT),
            PinDefinition(id="other_object", label_key="Other Object", pin_type=PinType.OBJECT),
            PinDefinition(id="self_collider", label_key="Self Collider", pin_type=PinType.OBJECT),
            PinDefinition(id="other_collider", label_key="Other Collider", pin_type=PinType.OBJECT),
        ]
    )


# Phase 5B.3: Raycast Query
class RaycastNode:
    """Cast a ray and check for collisions."""

    __node_definition__ = NodeDefinition(
        id="raycast",
        title_key="Raycast",
        category_key="Physics/Queries",
        description_key="Cast a ray and get nearest hit",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="origin_x", label_key="Origin X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="origin_y", label_key="Origin Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="direction_x", label_key="Direction X", pin_type=PinType.FLOAT, default_value=1.0),
            PinDefinition(id="direction_y", label_key="Direction Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="max_distance", label_key="Max Distance", pin_type=PinType.FLOAT, default_value=999.0),
            PinDefinition(id="ignore_self", label_key="Ignore Self", pin_type=PinType.BOOL, default_value=True),
            PinDefinition(id="include_triggers", label_key="Include Triggers", pin_type=PinType.BOOL, default_value=False),
            # Phase 5B.4: Layer mask filtering
            PinDefinition(id="layer_mask", label_key="Layer Mask", pin_type=PinType.INT, default_value=4294967295),
        ],

        outputs=[
            PinDefinition(id="exec_hit", label_key="Hit", pin_type=PinType.EXEC),
            PinDefinition(id="exec_no_hit", label_key="No Hit", pin_type=PinType.EXEC),
            PinDefinition(id="hit_object", label_key="Hit Object", pin_type=PinType.OBJECT),
            PinDefinition(id="hit_point_x", label_key="Hit Point X", pin_type=PinType.FLOAT),
            PinDefinition(id="hit_point_y", label_key="Hit Point Y", pin_type=PinType.FLOAT),
            PinDefinition(id="hit_distance", label_key="Hit Distance", pin_type=PinType.FLOAT),
            PinDefinition(id="hit_normal_x", label_key="Hit Normal X", pin_type=PinType.FLOAT),
            PinDefinition(id="hit_normal_y", label_key="Hit Normal Y", pin_type=PinType.FLOAT),
        ]
    )


# Phase 5B.4: Collision Layer/Mask Getters
class GetCollisionLayerNode:
    """Get collider's collision layer."""

    __node_definition__ = NodeDefinition(
        id="get_collision_layer",
        title_key="Get Collision Layer",
        category_key="Physics/Layers",
        description_key="Returns collider's collision layer",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value=""),
        ],

        outputs=[
            PinDefinition(id="value", label_key="Layer", pin_type=PinType.INT),
        ]
    )


class GetCollisionMaskNode:
    """Get collider's collision mask."""

    __node_definition__ = NodeDefinition(
        id="get_collision_mask",
        title_key="Get Collision Mask",
        category_key="Physics/Layers",
        description_key="Returns collider's collision mask",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value=""),
        ],

        outputs=[
            PinDefinition(id="value", label_key="Mask", pin_type=PinType.INT),
        ]
    )


class SetCollisionLayerNode:
    """Set collider's collision layer."""

    __node_definition__ = NodeDefinition(
        id="set_collision_layer",
        title_key="Set Collision Layer",
        category_key="Physics/Layers",
        description_key="Set collider's collision layer",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="value", label_key="Layer", pin_type=PinType.INT, default_value=1),
        ],

        outputs=[
            PinDefinition(id="exec_success", label_key="Success", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Failure", pin_type=PinType.EXEC),
        ]
    )


class SetCollisionMaskNode:
    """Set collider's collision mask."""

    __node_definition__ = NodeDefinition(
        id="set_collision_mask",
        title_key="Set Collision Mask",
        category_key="Physics/Layers",
        description_key="Set collider's collision mask",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="value", label_key="Mask", pin_type=PinType.INT, default_value=4294967295),
        ],

        outputs=[
            PinDefinition(id="exec_success", label_key="Success", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Failure", pin_type=PinType.EXEC),
        ]
    )
