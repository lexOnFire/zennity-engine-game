"""Definições de nós de animação para Logic Graph."""
from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class AnimateValueNode:
    """Anima um valor de A para B com easing."""

    __node_definition__ = NodeDefinition(
        id="animate_value",
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


class WaitUntilConditionNode:
    """Aguarda até uma condição ser verdadeira."""

    __node_definition__ = NodeDefinition(
        id="wait_until_condition",
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
