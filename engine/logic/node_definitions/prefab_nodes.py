"""Definições de nós de prefab para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class CreateObjectNode(NodeDefinition):
    """Cria um novo objeto."""

    __node_definition__ = NodeDefinition(
        id="create_object",
        title_key="Criar Objeto",
        category_key="Objects",
        description_key="Cria um novo objeto na cena",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="prefab_path", label_key="Caminho Prefab", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="x", label_key="X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="y", label_key="Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="source", label_key="Origem", pin_type=PinType.OBJECT),
        ],
        outputs=[
            PinDefinition(id="next", label_key="Pronto", pin_type=PinType.EXEC),
            PinDefinition(id="limit_reached", label_key="Limite Atingido", pin_type=PinType.EXEC),
            PinDefinition(id="object", label_key="Objeto", pin_type=PinType.OBJECT),
        ]
    )


class CreatePrefabNode(NodeDefinition):
    """Cria um prefab."""

    __node_definition__ = NodeDefinition(
        id="create_prefab",
        title_key="Criar Prefab",
        category_key="Objects",
        description_key="Instancia um prefab na cena",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="path", label_key="Caminho", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="x", label_key="X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="y", label_key="Y", pin_type=PinType.FLOAT, default_value=0.0),
        ],
        outputs=[
            PinDefinition(id="next", label_key="Pronto", pin_type=PinType.EXEC),
            PinDefinition(id="limit_reached", label_key="Limite Atingido", pin_type=PinType.EXEC),
            PinDefinition(id="object", label_key="Instância", pin_type=PinType.OBJECT),
            PinDefinition(id="parameters", label_key="Parâmetros", pin_type=PinType.STRING),
        ]
    )


class CloneObjectNode(NodeDefinition):
    """Clona um objeto."""

    __node_definition__ = NodeDefinition(
        id="clone_object",
        title_key="Clonar Objeto",
        category_key="Objects",
        description_key="Cria uma cópia de um objeto existente",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="x", label_key="X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="y", label_key="Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="name", label_key="Nome", pin_type=PinType.STRING),
        ],
        outputs=[
            PinDefinition(id="next", label_key="Pronto", pin_type=PinType.EXEC),
            PinDefinition(id="limit_reached", label_key="Limite Atingido", pin_type=PinType.EXEC),
            PinDefinition(id="object", label_key="Clone", pin_type=PinType.OBJECT),
        ]
    )
