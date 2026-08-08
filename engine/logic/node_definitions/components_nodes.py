"""Definições de nós de componentes para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class AddComponentNode(NodeDefinition):
    """Adiciona um componente ao objeto."""

    __node_definition__ = NodeDefinition(
        id="add_component",
        title_key="Adicionar Componente",
        category_key="Components",
        description_key="Adiciona um componente ao objeto",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="component_type", label_key="Tipo", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class RemoveComponentNode(NodeDefinition):
    """Remove um componente do objeto."""

    __node_definition__ = NodeDefinition(
        id="remove_component",
        title_key="Remover Componente",
        category_key="Components",
        description_key="Remove um componente do objeto",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="component_type", label_key="Tipo", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )
