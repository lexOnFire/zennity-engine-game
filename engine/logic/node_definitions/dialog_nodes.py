"""Definições de nós de diálogo para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class ShowDialogNode(NodeDefinition):
    """Mostra um diálogo com opções."""

    __node_definition__ = NodeDefinition(
        id="show_dialog",
        title_key="Mostrar Diálogo",
        category_key="Dialog",
        description_key="Mostra um diálogo com texto e opções para o player escolher",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="dialog_id", label_key="ID do Diálogo", pin_type=PinType.STRING, default_value="dialog_1"),
            PinDefinition(id="character", label_key="Personagem", pin_type=PinType.STRING, default_value="NPC"),
            PinDefinition(id="text", label_key="Texto", pin_type=PinType.STRING, default_value="Olá!"),
            PinDefinition("options", "Opções", "ARRAY", default_value=[]),
        ],
        outputs=[
            PinDefinition(id="exec_showing", label_key="Mostrando", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="dialog_id_out", label_key="ID", pin_type=PinType.STRING),
            PinDefinition(id="is_showing", label_key="Exibindo?", pin_type=PinType.BOOL),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="dialog_id", label_key="ID do Diálogo", pin_type=PinType.STRING, default_value="dialog_1"),
        ],
        outputs=[
            PinDefinition(id="exec_chosen", label_key="Escolhido", pin_type=PinType.EXEC),
            PinDefinition(id="exec_waiting", label_key="Aguardando", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="choice_index", label_key="Índice", pin_type=PinType.INT),
            PinDefinition(id="chosen_text", label_key="Texto Escolhido", pin_type=PinType.STRING),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="dialog_id", label_key="ID do Diálogo", pin_type=PinType.STRING, default_value="dialog_1"),
            PinDefinition(id="choice_index", label_key="Índice", pin_type=PinType.INT, default_value=0),
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="dialog_id", label_key="ID do Diálogo", pin_type=PinType.STRING, default_value="dialog_1"),
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )
