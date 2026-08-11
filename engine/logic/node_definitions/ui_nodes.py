"""Definições de nós de UI para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class BindUIToBlackboardNode(NodeDefinition):
    """Vincula UI ao quadro negro."""

    __node_definition__ = NodeDefinition(
        id="bind_ui_to_blackboard",
        title_key="Vincular UI ao Blackboard",
        category_key="UI",
        description_key="Vincula um elemento de UI a um valor no blackboard",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="widget_id", label_key="ID Widget", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="variable", label_key="Variável", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="next", label_key="Pronto", pin_type=PinType.EXEC),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="widget_id", label_key="ID Widget", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="value", label_key="Valor", pin_type=PinType.FLOAT, default_value=0.5),
        ],
        outputs=[
            PinDefinition(id="next", label_key="Pronto", pin_type=PinType.EXEC),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="widget_id", label_key="ID Widget", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="text", label_key="Texto", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="next", label_key="Pronto", pin_type=PinType.EXEC),
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
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="widget_id", label_key="ID Widget", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="visible", label_key="Visível", pin_type=PinType.BOOL, default_value=True),
        ],
        outputs=[
            PinDefinition(id="next", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )
