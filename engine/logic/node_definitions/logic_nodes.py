"""Definições canônicas dos nós booleanos e de texto do Logic Graph.

Phase 9.5B Stage 1.  Como os nós de matemática, `and`/`or`/`not` e
`join_text`/`to_text` já executavam mas não existiam na paleta, então lógica
booleana era inautorável visualmente.

Todos são PURE_DATA: sem pinos de execução, resolvidos sob demanda pelos
avaliadores em ``engine/logic/runtime/nodes/misc_nodes.py`` e ``string_nodes.py``.
"""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class AndNode:
    """E lógico."""

    __node_definition__ = NodeDefinition(
        id="and",
        title_key="E (AND)",
        category_key="Logic",
        description_key="Verdadeiro somente se A e B forem verdadeiros",
        execution_model="pure_data",
        inputs=[
            PinDefinition(id="a", label_key="A", pin_type=PinType.BOOL, default_value=False),
            PinDefinition(id="b", label_key="B", pin_type=PinType.BOOL, default_value=False),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Resultado", pin_type=PinType.BOOL),
        ],
    )


class OrNode:
    """OU lógico."""

    __node_definition__ = NodeDefinition(
        id="or",
        title_key="OU (OR)",
        category_key="Logic",
        description_key="Verdadeiro se A ou B for verdadeiro",
        execution_model="pure_data",
        inputs=[
            PinDefinition(id="a", label_key="A", pin_type=PinType.BOOL, default_value=False),
            PinDefinition(id="b", label_key="B", pin_type=PinType.BOOL, default_value=False),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Resultado", pin_type=PinType.BOOL),
        ],
    )


class NotNode:
    """Negação lógica."""

    __node_definition__ = NodeDefinition(
        id="not",
        title_key="NÃO (NOT)",
        category_key="Logic",
        description_key="Inverte um valor booleano",
        execution_model="pure_data",
        inputs=[
            PinDefinition(id="value", label_key="Valor", pin_type=PinType.BOOL, default_value=False),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Resultado", pin_type=PinType.BOOL),
        ],
    )


class JoinTextNode:
    """Concatena dois textos."""

    __node_definition__ = NodeDefinition(
        id="join_text",
        title_key="Juntar Texto",
        category_key="Text",
        description_key="Concatena A e B",
        execution_model="pure_data",
        inputs=[
            PinDefinition(id="a", label_key="A", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="b", label_key="B", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Resultado", pin_type=PinType.STRING),
        ],
    )


class ToTextNode:
    """Converte um valor para texto."""

    __node_definition__ = NodeDefinition(
        id="to_text",
        title_key="Converter em Texto",
        category_key="Text",
        description_key="Converte qualquer valor para texto",
        execution_model="pure_data",
        inputs=[
            PinDefinition(id="value", label_key="Valor", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Resultado", pin_type=PinType.STRING),
        ],
    )


class DeltaTimeNode:
    """Tempo do frame."""

    __node_definition__ = NodeDefinition(
        id="delta_time",
        title_key="Delta Time",
        category_key="Values",
        description_key="Segundos decorridos desde o frame anterior",
        execution_model="pure_data",
        inputs=[],
        outputs=[
            PinDefinition(id="value", label_key="Delta", pin_type=PinType.FLOAT),
        ],
    )
