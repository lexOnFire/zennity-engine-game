"""Definições de nós de componentes para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition


class AddComponentNode(NodeDefinition):
    """Adiciona um componente ao objeto."""

    __node_definition__ = NodeDefinition(
        id="add_component",
        title_key="Adicionar Componente",
        category_key="Components",
        description_key="Adiciona um componente ao objeto",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("component_type", "Tipo", "STRING", default_value=""),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("component_type", "Tipo", "STRING", default_value=""),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
        ]
    )
