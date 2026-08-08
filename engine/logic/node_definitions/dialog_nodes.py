"""Definições de nós de diálogo para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition


class ShowDialogNode(NodeDefinition):
    """Mostra um diálogo com opções."""

    __node_definition__ = NodeDefinition(
        id="show_dialog",
        title_key="Mostrar Diálogo",
        category_key="Dialog",
        description_key="Mostra um diálogo com texto e opções para o player escolher",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("dialog_id", "ID do Diálogo", "STRING", default_value="dialog_1"),
            PinDefinition("character", "Personagem", "STRING", default_value="NPC"),
            PinDefinition("text", "Texto", "STRING", default_value="Olá!"),
            PinDefinition("options", "Opções", "ARRAY", default_value=[]),
        ],
        outputs=[
            PinDefinition("exec_showing", "Mostrando", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("dialog_id_out", "ID", "STRING"),
            PinDefinition("is_showing", "Exibindo?", "BOOL"),
        ]
    )


class WaitDialogChoiceNode(NodeDefinition):
    """Aguarda o player escolher uma opção."""

    __node_definition__ = NodeDefinition(
        id="wait_dialog_choice",
        title_key="Aguardar Escolha",
        category_key="Dialog",
        description_key="Aguarda até o player escolher uma opção de diálogo",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("dialog_id", "ID do Diálogo", "STRING", default_value="dialog_1"),
        ],
        outputs=[
            PinDefinition("exec_chosen", "Escolhido", "EXEC"),
            PinDefinition("exec_waiting", "Aguardando", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("choice_index", "Índice", "INT"),
            PinDefinition("chosen_text", "Texto Escolhido", "STRING"),
        ]
    )


class SetDialogChoiceNode(NodeDefinition):
    """Define a escolha do player (uso interno)."""

    __node_definition__ = NodeDefinition(
        id="set_dialog_choice",
        title_key="Definir Escolha",
        category_key="Dialog",
        description_key="Define qual opção o player escolheu (para uso interno)",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("dialog_id", "ID do Diálogo", "STRING", default_value="dialog_1"),
            PinDefinition("choice_index", "Índice", "INT", default_value=0),
        ],
        outputs=[
            PinDefinition("exec_success", "Sucesso", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )


class CloseDialogNode(NodeDefinition):
    """Fecha um diálogo ativo."""

    __node_definition__ = NodeDefinition(
        id="close_dialog",
        title_key="Fechar Diálogo",
        category_key="Dialog",
        description_key="Fecha um diálogo ativo",

        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("dialog_id", "ID do Diálogo", "STRING", default_value="dialog_1"),
        ],
        outputs=[
            PinDefinition("exec_success", "Sucesso", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )
