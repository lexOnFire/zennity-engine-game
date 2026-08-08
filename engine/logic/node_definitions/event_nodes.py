"""Definições de nós de eventos para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class CompareNumberNode(NodeDefinition):
    """Compara dois números."""

    __node_definition__ = NodeDefinition(
        id="compare_number",
        title_key="Comparar Número",
        category_key="Logic",
        description_key="Compara dois números e executa ramo baseado no resultado",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="a", label_key="A", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="b", label_key="B", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="operation", label_key="Operação", pin_type=PinType.STRING, default_value="=="),
        ],
        outputs=[
            PinDefinition(id="true", label_key="Verdadeiro", pin_type=PinType.EXEC),
            PinDefinition(id="false", label_key="Falso", pin_type=PinType.EXEC),
        ]
    )


class CompareTextNode(NodeDefinition):
    """Compara dois textos."""

    __node_definition__ = NodeDefinition(
        id="compare_text",
        title_key="Comparar Texto",
        category_key="Logic",
        description_key="Compara dois textos e executa ramo baseado no resultado",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="a", label_key="A", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="b", label_key="B", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="operation", label_key="Operação", pin_type=PinType.STRING, default_value="=="),
        ],
        outputs=[
            PinDefinition(id="true", label_key="Verdadeiro", pin_type=PinType.EXEC),
            PinDefinition(id="false", label_key="Falso", pin_type=PinType.EXEC),
        ]
    )


class KeyPressedNode(NodeDefinition):
    """Detecta pressão de tecla."""

    __node_definition__ = NodeDefinition(
        id="key_pressed",
        title_key="Tecla Pressionada",
        category_key="Input",
        description_key="Dispara quando uma tecla é pressionada",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="key", label_key="Tecla", pin_type=PinType.STRING, default_value="space"),
        ],
        outputs=[
            PinDefinition(id="exec_pressed", label_key="Pressionado", pin_type=PinType.EXEC),
        ]
    )


class KeyHeldNode(NodeDefinition):
    """Detecta se tecla está pressionada."""

    __node_definition__ = NodeDefinition(
        id="key_held",
        title_key="Tecla Pressionada (Contínuo)",
        category_key="Input",
        description_key="Verifica se uma tecla está continuamente pressionada",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="key", label_key="Tecla", pin_type=PinType.STRING, default_value="space"),
        ],
        outputs=[
            PinDefinition(id="held", label_key="Pressionada", pin_type=PinType.EXEC),
            PinDefinition(id="released", label_key="Liberada", pin_type=PinType.EXEC),
        ]
    )


class IsGroundedNode(NodeDefinition):
    """Verifica se objeto está no chão."""

    __node_definition__ = NodeDefinition(
        id="is_grounded",
        title_key="No Chão",
        category_key="Physics",
        description_key="Verifica se o objeto está em contato com o chão",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="grounded", label_key="No Chão", pin_type=PinType.EXEC),
            PinDefinition(id="airborne", label_key="No Ar", pin_type=PinType.EXEC),
        ]
    )


class InputAxisNode(NodeDefinition):
    """Lê entrada de eixo."""

    __node_definition__ = NodeDefinition(
        id="input_axis",
        title_key="Eixo de Entrada",
        category_key="Input",
        description_key="Lê o valor de um eixo de entrada",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="axis", label_key="Eixo", pin_type=PinType.STRING, default_value="horizontal"),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
            PinDefinition(id="value", label_key="Valor", pin_type=PinType.FLOAT),
        ]
    )


class ReadKeyAxisNode(NodeDefinition):
    """Lê eixo de teclado."""

    __node_definition__ = NodeDefinition(
        id="read_key_axis",
        title_key="Eixo de Teclado",
        category_key="Input",
        description_key="Lê o valor de um eixo baseado em teclas",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="positive_key", label_key="Tecla Positiva", pin_type=PinType.STRING, default_value="d"),
            PinDefinition(id="negative_key", label_key="Tecla Negativa", pin_type=PinType.STRING, default_value="a"),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
            PinDefinition(id="value", label_key="Valor", pin_type=PinType.FLOAT),
        ]
    )
