"""Definições de nós de UI para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition


class BindUIToBlackboardNode(NodeDefinition):
    """Vincula UI ao quadro negro."""

    __node_definition__ = NodeDefinition(
        id="bind_ui_to_blackboard",
        title_key="Vincular UI ao Blackboard",
        category_key="UI",
        description_key="Vincula um elemento de UI a um valor no blackboard",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("widget_id", "ID Widget", "STRING", default_value=""),
            PinDefinition("variable", "Variável", "STRING", default_value=""),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
        ]
    )


class SetUIProgressBarNode(NodeDefinition):
    """Define valor da barra de progresso."""

    __node_definition__ = NodeDefinition(
        id="set_ui_progress_bar",
        title_key="Definir Barra de Progresso",
        category_key="UI",
        description_key="Define o valor de uma barra de progresso",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("widget_id", "ID Widget", "STRING", default_value=""),
            PinDefinition("value", "Valor", "FLOAT", default_value=0.5),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
        ]
    )


class SetUITextNode(NodeDefinition):
    """Define texto de um widget."""

    __node_definition__ = NodeDefinition(
        id="set_ui_text",
        title_key="Definir Texto UI",
        category_key="UI",
        description_key="Define o texto de um widget de texto",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("widget_id", "ID Widget", "STRING", default_value=""),
            PinDefinition("text", "Texto", "STRING", default_value=""),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
        ]
    )


class SetUIVisibleNode(NodeDefinition):
    """Define visibilidade de widget."""

    __node_definition__ = NodeDefinition(
        id="set_ui_visible",
        title_key="Definir Visibilidade UI",
        category_key="UI",
        description_key="Define se um widget é visível ou não",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("widget_id", "ID Widget", "STRING", default_value=""),
            PinDefinition("visible", "Visível", "BOOL", default_value=True),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
        ]
    )
