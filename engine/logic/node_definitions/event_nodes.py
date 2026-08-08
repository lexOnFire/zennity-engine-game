"""Definições de nós de eventos para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition


class CompareNumberNode(NodeDefinition):
    """Compara dois números."""

    __node_definition__ = NodeDefinition(
        id="compare_number",
        title_key="Comparar Número",
        category_key="Logic",
        description_key="Compara dois números e executa ramo baseado no resultado",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("a", "A", "FLOAT", default_value=0.0),
            PinDefinition("b", "B", "FLOAT", default_value=0.0),
            PinDefinition("operation", "Operação", "STRING", default_value="=="),
        ],
        outputs=[
            PinDefinition("true", "Verdadeiro", "EXEC"),
            PinDefinition("false", "Falso", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("a", "A", "STRING", default_value=""),
            PinDefinition("b", "B", "STRING", default_value=""),
            PinDefinition("operation", "Operação", "STRING", default_value="=="),
        ],
        outputs=[
            PinDefinition("true", "Verdadeiro", "EXEC"),
            PinDefinition("false", "Falso", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("key", "Tecla", "STRING", default_value="space"),
        ],
        outputs=[
            PinDefinition("exec_pressed", "Pressionado", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("key", "Tecla", "STRING", default_value="space"),
        ],
        outputs=[
            PinDefinition("held", "Pressionada", "EXEC"),
            PinDefinition("released", "Liberada", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("grounded", "No Chão", "EXEC"),
            PinDefinition("airborne", "No Ar", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("axis", "Eixo", "STRING", default_value="horizontal"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
            PinDefinition("value", "Valor", "FLOAT"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("positive_key", "Tecla Positiva", "STRING", default_value="d"),
            PinDefinition("negative_key", "Tecla Negativa", "STRING", default_value="a"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
            PinDefinition("value", "Valor", "FLOAT"),
        ]
    )
