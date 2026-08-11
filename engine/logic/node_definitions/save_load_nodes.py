"""Definições de nós de Save/Load para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class SaveGameNode(NodeDefinition):
    """Salva o jogo em um slot."""

    __node_definition__ = NodeDefinition(
        id="save_game",
        title_key="Salvar Jogo",
        category_key="Persistence",
        description_key="Salva o estado atual do jogo em um slot de save",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="slot_name", label_key="Nome do Slot", pin_type=PinType.STRING, default_value="save_slot_1"),
            PinDefinition(id="include_scene", label_key="Incluir Cena?", pin_type=PinType.BOOL, default_value=True),
        ],
        outputs=[
            PinDefinition(id="exec_saved", label_key="Salvo", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="slot_name", label_key="Slot", pin_type=PinType.STRING),
            PinDefinition(id="saved", label_key="Foi Salvo?", pin_type=PinType.BOOL),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="slot_name", label_key="Nome do Slot", pin_type=PinType.STRING, default_value="save_slot_1"),
        ],
        outputs=[
            PinDefinition(id="exec_loaded", label_key="Carregado", pin_type=PinType.EXEC),
            PinDefinition(id="exec_no_save", label_key="Sem Save", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="slot_name", label_key="Slot", pin_type=PinType.STRING),
            PinDefinition(id="loaded", label_key="Foi Carregado?", pin_type=PinType.BOOL),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="slot_name", label_key="Nome do Slot", pin_type=PinType.STRING, default_value="save_slot_1"),
        ],
        outputs=[
            PinDefinition(id="exec_deleted", label_key="Deletado", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="slot_name", label_key="Nome do Slot", pin_type=PinType.STRING, default_value="save_slot_1"),
        ],
        outputs=[
            PinDefinition(id="exec_exists", label_key="Existe", pin_type=PinType.EXEC),
            PinDefinition(id="exec_not_exists", label_key="Não Existe", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )
