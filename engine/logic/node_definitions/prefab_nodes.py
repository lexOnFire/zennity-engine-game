"""Definições de nós de prefab para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition


class CreateObjectNode(NodeDefinition):
    """Cria um novo objeto."""

    __node_definition__ = NodeDefinition(
        id="create_object",
        title_key="Criar Objeto",
        category_key="Objects",
        description_key="Cria um novo objeto na cena",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("prefab_path", "Caminho Prefab", "STRING", default_value=""),
            PinDefinition("x", "X", "FLOAT", default_value=0.0),
            PinDefinition("y", "Y", "FLOAT", default_value=0.0),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
            PinDefinition("object", "Objeto", "OBJECT"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("path", "Caminho", "STRING", default_value=""),
            PinDefinition("x", "X", "FLOAT", default_value=0.0),
            PinDefinition("y", "Y", "FLOAT", default_value=0.0),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
            PinDefinition("instance", "Instância", "OBJECT"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("x", "X", "FLOAT", default_value=0.0),
            PinDefinition("y", "Y", "FLOAT", default_value=0.0),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
            PinDefinition("clone", "Clone", "OBJECT"),
        ]
    )
