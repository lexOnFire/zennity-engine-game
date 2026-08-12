"""Definições de nós de animação para Logic Graph."""
from engine.core.metadata import NodeDefinition, PinDefinition, PinType


# Phase 6B.2: Animator Action Nodes
class PlayAnimationNode:
    """Toca uma animação no Animator."""

    __node_definition__ = NodeDefinition(
        id="play_animation",
        title_key="Play Animation",
        category_key="Animation",
        description_key="Toca uma animação específica no Animator do target",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
            # PHASE 9 recovery item 4.2: the authoring property is ``state``,
            # not ``animation_name``. Every saved node uses it -- Idle, Jump,
            # Run, PlayerAttack, 4 of 4 -- and none uses animation_name. The
            # legacy name is migrated at load time by _RENAMED_NODE_PROPERTIES,
            # so it is compatibility, not a second authorable field.
            #
            # The default is empty on purpose. It used to be "idle", and the
            # normalizer seeded that over a legacy graph's real animation name.
            PinDefinition(id="state", label_key="Estado", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="force", label_key="Force", pin_type=PinType.BOOL, default_value=False),
        ],
        outputs=[
            # "next" is the engine's one name for "this succeeded, continue".
            PinDefinition(id="next", label_key="Pronto", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Failure", pin_type=PinType.EXEC),
            PinDefinition(id="animation", label_key="Animation", pin_type=PinType.STRING),
        ]
    )


class PauseAnimationNode:
    """Pausa a animação em execução."""

    __node_definition__ = NodeDefinition(
        id="pause_animation",
        title_key="Pause Animation",
        category_key="Animation",
        description_key="Pausa a animação do Animator do target",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Success", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Failure", pin_type=PinType.EXEC),
        ]
    )


class StopAnimationNode:
    """Para a animação em execução."""

    __node_definition__ = NodeDefinition(
        id="stop_animation",
        title_key="Stop Animation",
        category_key="Animation",
        description_key="Para a animação do Animator do target",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
        ],
        outputs=[
            PinDefinition(id="next", label_key="Pronto", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Failure", pin_type=PinType.EXEC),
            # The executor already stores this; it was simply never declared.
            PinDefinition(id="stopped", label_key="Parada", pin_type=PinType.BOOL),
        ]
    )


# Phase 6B.2: Animator Getter Nodes (Pure Data)
class GetCurrentAnimationNode:
    """Obtém o nome da animação em execução."""

    __node_definition__ = NodeDefinition(
        id="get_current_animation",
        title_key="Get Current Animation",
        category_key="Animation/Getters",
        description_key="Retorna o nome da animação em execução",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Animation", pin_type=PinType.STRING),
        ]
    )


class GetCurrentFrameNode:
    """Obtém o índice do frame atual."""

    __node_definition__ = NodeDefinition(
        id="get_current_frame",
        title_key="Get Current Frame",
        category_key="Animation/Getters",
        description_key="Retorna o índice do frame atual (0-based)",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Frame Index", pin_type=PinType.INT),
        ]
    )


class GetAnimationTimeNode:
    """Obtém o tempo decorrido da animação."""

    __node_definition__ = NodeDefinition(
        id="get_animation_time",
        title_key="Get Animation Time",
        category_key="Animation/Getters",
        description_key="Retorna o tempo decorrido da animação em segundos",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Time (seconds)", pin_type=PinType.FLOAT),
        ]
    )


class GetIsPlayingNode:
    """Verifica se a animação está tocando."""

    __node_definition__ = NodeDefinition(
        id="get_is_playing",
        title_key="Get Is Playing",
        category_key="Animation/Getters",
        description_key="Retorna se uma animação está tocando",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Is Playing", pin_type=PinType.BOOL),
        ]
    )


# Phase 6B.2: Animator Parameter Node
class AnimatorParameterNode:
    """Modifica um parâmetro do Animator (bool, float, int, trigger)."""

    __node_definition__ = NodeDefinition(
        id="animator_parameter",
        title_key="Animator Parameter",
        category_key="Animation",
        description_key="Define um parâmetro booleano, float, inteiro ou trigger no Animator",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
            PinDefinition(id="parameter_name", label_key="Parameter", pin_type=PinType.STRING, default_value="speed"),
            PinDefinition(id="parameter_type", label_key="Type", pin_type=PinType.STRING, default_value="float"),
            PinDefinition(id="value", label_key="Value", pin_type=PinType.STRING, default_value="1.0"),
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Success", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Failure", pin_type=PinType.EXEC),
        ]
    )


# Phase 6B.2: Utility Nodes
class AnimateValueNode:
    """Anima um valor de A para B com easing."""

    __node_definition__ = NodeDefinition(
        id="animate_value",
        # PHASE 9 recovery item 3, revalidated on this branch: no executor, no
        # evaluator, and 0 uses across every shipping .zlogic. Stage 1 declared
        # the same thing. Marked rather than deleted -- the definition documents
        # an intent that was never implemented -- and the flag is what makes the
        # validator report it as deprecated instead of as a missing runtime.
        deprecated=True,
        title_key="Animar Valor (Lerp)",
        category_key="Animation",
        description_key="Anima uma propriedade de A para B com duração e easing",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
            PinDefinition(id="property", label_key="Propriedade", pin_type=PinType.STRING, default_value="x"),
            PinDefinition(id="from_value", label_key="De", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="to_value", label_key="Para", pin_type=PinType.FLOAT, default_value=100.0),
            PinDefinition(id="duration", label_key="Duração (s)", pin_type=PinType.FLOAT, default_value=1.0),
            PinDefinition(id="easing", label_key="Easing", pin_type=PinType.STRING, default_value="linear"),
        ],
        outputs=[
            PinDefinition(id="exec_animating", label_key="Animando", pin_type=PinType.EXEC),
            PinDefinition(id="exec_finished", label_key="Fim", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="value", label_key="Valor Atual", pin_type=PinType.FLOAT),
            PinDefinition(id="progress", label_key="Progresso (0-1)", pin_type=PinType.FLOAT),
        ]
    )


# Phase 6B.4: Animator Controller Nodes
class AnimatorSetTriggerNode:
    """Define um trigger do Animator Controller."""

    __node_definition__ = NodeDefinition(
        id="animator_set_trigger",
        title_key="Set Animator Trigger",
        category_key="Animation",
        description_key="Define um trigger nomeado no Animator Controller",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
            PinDefinition(id="trigger_name", label_key="Trigger", pin_type=PinType.STRING, default_value="attack"),
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Success", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Failure", pin_type=PinType.EXEC),
        ]
    )


class AnimatorGetParameterNode:
    """Obtém um parâmetro do Animator Controller."""

    __node_definition__ = NodeDefinition(
        id="animator_get_parameter",
        title_key="Get Animator Parameter",
        category_key="Animation/Getters",
        description_key="Obtém valor de um parâmetro do Animator Controller",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
            PinDefinition(id="parameter_name", label_key="Parameter", pin_type=PinType.STRING, default_value="speed"),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Value", pin_type=PinType.STRING),  # ANY would be better if available
        ]
    )


class GetAnimatorStateNode:
    """Obtém o estado atual do Animator Controller."""

    __node_definition__ = NodeDefinition(
        id="get_animator_state",
        title_key="Get Animator State",
        category_key="Animation/Getters",
        description_key="Retorna o estado atual (idle, run, attack, etc)",

        inputs=[
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
        ],
        outputs=[
            PinDefinition(id="value", label_key="State", pin_type=PinType.STRING),
        ]
    )


# Phase 6B.3: Animation Event Nodes
class OnAnimationEventNode:
    """Dispara quando um evento específico ocorre em uma animação."""

    __node_definition__ = NodeDefinition(
        id="on_animation_event",
        title_key="On Animation Event",
        category_key="Animation/Events",
        description_key="Dispara quando uma animação atinge um evento nomeado",

        inputs=[],  # No exec input
        outputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="owner_object", label_key="Owner", pin_type=PinType.STRING),
            PinDefinition(id="animation_name", label_key="Animation", pin_type=PinType.STRING),
            PinDefinition(id="event_name", label_key="Event Name", pin_type=PinType.STRING),
            PinDefinition(id="frame_index", label_key="Frame", pin_type=PinType.INT),
            PinDefinition(id="elapsed_time", label_key="Time", pin_type=PinType.FLOAT),
        ]
    )


class OnAnimationFinishedNode:
    """Dispara quando uma animação não-loop termina."""

    __node_definition__ = NodeDefinition(
        id="on_animation_finished",
        title_key="On Animation Finished",
        category_key="Animation/Events",
        description_key="Dispara quando uma animação não-loop chega ao fim",

        inputs=[],  # No exec input
        outputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="owner_object", label_key="Owner", pin_type=PinType.STRING),
            PinDefinition(id="animation_name", label_key="Animation", pin_type=PinType.STRING),
            PinDefinition(id="elapsed_time", label_key="Time", pin_type=PinType.FLOAT),
        ]
    )


class WaitUntilConditionNode:
    """Aguarda até uma condição ser verdadeira."""

    __node_definition__ = NodeDefinition(
        id="wait_until_condition",
        # Same evidence as animate_value: no runtime of any kind, 0 asset uses.
        deprecated=True,
        title_key="Aguardar Até Condição",
        category_key="Flow",
        description_key="Pausa execução até condição ser verdadeira ou timeout",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="condition_type", label_key="Tipo Condição", pin_type=PinType.STRING, default_value="variable_equals"),
            PinDefinition(id="variable_name", label_key="Variável", pin_type=PinType.STRING, default_value="hp"),
            PinDefinition(id="expected_value", label_key="Valor Esperado", pin_type=PinType.STRING, default_value="0"),
            PinDefinition(id="target", label_key="Target", pin_type=PinType.STRING, default_value="player"),
            PinDefinition(id="property", label_key="Propriedade", pin_type=PinType.STRING, default_value="health"),
            PinDefinition(id="operator", label_key="Operador", pin_type=PinType.STRING, default_value="=="),
            PinDefinition(id="timeout", label_key="Timeout (s)", pin_type=PinType.FLOAT, default_value=30.0),
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="exec_timeout", label_key="Timeout", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="exec_waiting", label_key="Aguardando", pin_type=PinType.EXEC),
            PinDefinition(id="elapsed_time", label_key="Tempo Decorrido", pin_type=PinType.FLOAT),
        ]
    )
