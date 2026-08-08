"""Definições de nós de Save/Load para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition


class SaveGameNode(NodeDefinition):
    """Salva o jogo em um slot."""

    __node_definition__ = NodeDefinition(
        id="save_game",
        title_key="Salvar Jogo",
        category_key="Persistence",
        description_key="Salva o estado atual do jogo em um slot de save",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("slot_name", "Nome do Slot", "STRING", default_value="save_slot_1"),
            PinDefinition("include_scene", "Incluir Cena?", "BOOL", default_value=True),
        ],
        outputs=[
            PinDefinition("exec_saved", "Salvo", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("slot_name_out", "Slot", "STRING"),
            PinDefinition("saved", "Foi Salvo?", "BOOL"),
        ]
    )


class LoadGameNode(NodeDefinition):
    """Carrega o jogo de um slot."""

    __node_definition__ = NodeDefinition(
        id="load_game",
        title_key="Carregar Jogo",
        category_key="Persistence",
        description_key="Carrega o estado do jogo de um slot de save",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("slot_name", "Nome do Slot", "STRING", default_value="save_slot_1"),
        ],
        outputs=[
            PinDefinition("exec_loaded", "Carregado", "EXEC"),
            PinDefinition("exec_no_save", "Sem Save", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("slot_name_out", "Slot", "STRING"),
            PinDefinition("loaded", "Foi Carregado?", "BOOL"),
        ]
    )


class DeleteSaveNode(NodeDefinition):
    """Deleta um save slot."""

    __node_definition__ = NodeDefinition(
        id="delete_save",
        title_key="Deletar Save",
        category_key="Persistence",
        description_key="Deleta um save slot",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("slot_name", "Nome do Slot", "STRING", default_value="save_slot_1"),
        ],
        outputs=[
            PinDefinition("exec_deleted", "Deletado", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )


class HasSaveNode(NodeDefinition):
    """Verifica se um save existe."""

    __node_definition__ = NodeDefinition(
        id="has_save",
        title_key="Tem Save?",
        category_key="Persistence",
        description_key="Verifica se um save slot existe",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("slot_name", "Nome do Slot", "STRING", default_value="save_slot_1"),
        ],
        outputs=[
            PinDefinition("exec_exists", "Existe", "EXEC"),
            PinDefinition("exec_not_exists", "Não Existe", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )
