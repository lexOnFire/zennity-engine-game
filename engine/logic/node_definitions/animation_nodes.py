"""Definições de nós de animação para Logic Graph."""
from engine.logic.metadata import NodeDefinition, PinDefinition


class AnimateValueNode:
    """Anima um valor de A para B com easing."""

    __node_definition__ = NodeDefinition(
        id="animate_value",
        title="Animar Valor (Lerp)",
        category="Animation",
        description="Anima uma propriedade de A para B com duração e easing",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("target", "Target", "STRING", default_value="player"),
            PinDefinition("property", "Propriedade", "STRING", default_value="x"),
            PinDefinition("from_value", "De", "FLOAT", default_value=0.0),
            PinDefinition("to_value", "Para", "FLOAT", default_value=100.0),
            PinDefinition("duration", "Duração (s)", "FLOAT", default_value=1.0),
            PinDefinition("easing", "Easing", "STRING", default_value="linear"),
        ],
        pins_output=[
            PinDefinition("exec_animating", "Animando", "EXEC"),
            PinDefinition("exec_finished", "Fim", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("value", "Valor Atual", "FLOAT"),
            PinDefinition("progress", "Progresso (0-1)", "FLOAT"),
        ]
    )


class WaitUntilConditionNode:
    """Aguarda até uma condição ser verdadeira."""

    __node_definition__ = NodeDefinition(
        id="wait_until_condition",
        title="Aguardar Até Condição",
        category="Flow",
        description="Pausa execução até condição ser verdadeira ou timeout",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("condition_type", "Tipo Condição", "STRING", default_value="variable_equals"),
            PinDefinition("variable_name", "Variável", "STRING", default_value="hp"),
            PinDefinition("expected_value", "Valor Esperado", "STRING", default_value="0"),
            PinDefinition("target", "Target", "STRING", default_value="player"),
            PinDefinition("property", "Propriedade", "STRING", default_value="health"),
            PinDefinition("operator", "Operador", "STRING", default_value="=="),
            PinDefinition("timeout", "Timeout (s)", "FLOAT", default_value=30.0),
        ],
        pins_output=[
            PinDefinition("exec_success", "Sucesso", "EXEC"),
            PinDefinition("exec_timeout", "Timeout", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("exec_waiting", "Aguardando", "EXEC"),
            PinDefinition("elapsed_time", "Tempo Decorrido", "FLOAT"),
        ]
    )
