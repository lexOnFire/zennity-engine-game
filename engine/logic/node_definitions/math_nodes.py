"""Definições canônicas dos nós de matemática do Logic Graph.

Phase 9.5B Stage 1.

Antes desta fase, aritmética funcionava em runtime mas **não existia na paleta**:
sete avaliadores (`add_number`, `subtract_number`, `multiply_number`,
`divide_number`, `clamp_number`, `absolute_number`, `random_number`) estavam
registrados sem nenhuma definição, então não podiam ser criados visualmente.
Era a maior lacuna de autoria encontrada na auditoria 9.5A.

Convenção de IDs
----------------
Os ids permanecem `add_number`, `multiply_number`, ... porque é o que os
avaliadores já registram e o que assets antigos podem referenciar.  O namespace
`math.*` documentado em `docs/PHASE9_5B_STAGE1_NODE_CONTRACTS.md` é a direção
futura; migrá-lo agora exigiria tocar o dispatcher e está fora do escopo do
Stage 1.  **Um id canônico por operação** -- nada de `add_number` + `math.add` +
`number_add` coexistindo.

Todos são PURE_DATA: sem pinos de execução, resolvidos sob demanda.
"""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType

_CATEGORY = "Math"


def _binary(node_id: str, title: str, description: str) -> NodeDefinition:
    """Operação binária a/b -> result (contrato lido pelos avaliadores)."""
    return NodeDefinition(
        id=node_id,
        title_key=title,
        category_key=_CATEGORY,
        description_key=description,
        execution_model="pure_data",
        inputs=[
            PinDefinition(id="a", label_key="A", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="b", label_key="B", pin_type=PinType.FLOAT, default_value=0.0),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Resultado", pin_type=PinType.FLOAT),
        ],
    )


class AddNumberNode:
    """Soma dois números."""

    __node_definition__ = _binary("add_number", "Somar", "Soma A + B")


class SubtractNumberNode:
    """Subtrai dois números."""

    __node_definition__ = _binary("subtract_number", "Subtrair", "Subtrai A - B")


class MultiplyNumberNode:
    """Multiplica dois números."""

    __node_definition__ = _binary("multiply_number", "Multiplicar", "Multiplica A × B")


class DivideNumberNode:
    """Divide dois números."""

    __node_definition__ = _binary("divide_number", "Dividir", "Divide A ÷ B")


class AbsoluteNumberNode:
    """Valor absoluto."""

    __node_definition__ = NodeDefinition(
        id="absolute_number",
        title_key="Valor Absoluto",
        category_key=_CATEGORY,
        description_key="Devolve o valor sem sinal",
        execution_model="pure_data",
        inputs=[
            PinDefinition(id="value", label_key="Valor", pin_type=PinType.FLOAT, default_value=0.0),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Resultado", pin_type=PinType.FLOAT),
        ],
    )


class ClampNumberNode:
    """Limita um número a um intervalo."""

    __node_definition__ = NodeDefinition(
        id="clamp_number",
        title_key="Limitar (Clamp)",
        category_key=_CATEGORY,
        description_key="Mantém o valor entre mínimo e máximo",
        execution_model="pure_data",
        inputs=[
            PinDefinition(id="value", label_key="Valor", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="minimum", label_key="Mínimo", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="maximum", label_key="Máximo", pin_type=PinType.FLOAT, default_value=1.0),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Resultado", pin_type=PinType.FLOAT),
        ],
    )


class RandomNumberNode:
    """Número aleatório num intervalo."""

    __node_definition__ = NodeDefinition(
        id="random_number",
        title_key="Número Aleatório",
        category_key=_CATEGORY,
        description_key="Sorteia um valor entre mínimo e máximo",
        execution_model="pure_data",
        inputs=[
            PinDefinition(id="minimum", label_key="Mínimo", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="maximum", label_key="Máximo", pin_type=PinType.FLOAT, default_value=1.0),
        ],
        outputs=[
            PinDefinition(id="value", label_key="Resultado", pin_type=PinType.FLOAT),
        ],
    )
