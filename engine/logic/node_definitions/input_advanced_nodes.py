"""Definições de nós de input avançado para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class DetectTouchNode(NodeDefinition):
    """Detecta toque em uma área."""

    __node_definition__ = NodeDefinition(
        id="detect_touch",
        title_key="Detectar Toque",
        category_key="Input",
        description_key="Detecta toque do usuário em uma área específica",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="x", label_key="X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="y", label_key="Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="width", label_key="Largura", pin_type=PinType.FLOAT, default_value=100.0),
            PinDefinition(id="height", label_key="Altura", pin_type=PinType.FLOAT, default_value=100.0),
        ],
        outputs=[
            PinDefinition(id="exec_touched", label_key="Tocado", pin_type=PinType.EXEC),
            PinDefinition(id="exec_no_touch", label_key="Sem Toque", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="touch_x", label_key="Toque X", pin_type=PinType.FLOAT),
            PinDefinition(id="touch_y", label_key="Toque Y", pin_type=PinType.FLOAT),
        ]
    )


class DetectSwipeNode(NodeDefinition):
    """Detecta swipe (deslize)."""

    __node_definition__ = NodeDefinition(
        id="detect_swipe",
        title_key="Detectar Swipe",
        category_key="Input",
        description_key="Detecta gesto de deslize na tela",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="direction", label_key="Direção", pin_type=PinType.STRING, default_value="right"),  # right, left, up, down
            PinDefinition(id="min_distance", label_key="Distância Mínima", pin_type=PinType.FLOAT, default_value=50.0),
        ],
        outputs=[
            PinDefinition(id="exec_swiped", label_key="Deslizou", pin_type=PinType.EXEC),
            PinDefinition(id="exec_no_swipe", label_key="Sem Deslize", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="swipe_distance", label_key="Distância", pin_type=PinType.FLOAT),
        ]
    )


class DetectPinchNode(NodeDefinition):
    """Detecta pinça (zoom)."""

    __node_definition__ = NodeDefinition(
        id="detect_pinch",
        title_key="Detectar Pinça",
        category_key="Input",
        description_key="Detecta gesto de pinça (zoom) na tela",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="type", label_key="Tipo", pin_type=PinType.STRING, default_value="out"),  # in (zoom out), out (zoom in)
        ],
        outputs=[
            PinDefinition(id="exec_pinched", label_key="Pinçado", pin_type=PinType.EXEC),
            PinDefinition(id="exec_no_pinch", label_key="Sem Pinça", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="pinch_scale", label_key="Escala", pin_type=PinType.FLOAT),
        ]
    )


class IsKeyPressedNode(NodeDefinition):
    """Verifica se tecla está pressionada."""

    __node_definition__ = NodeDefinition(
        id="is_key_pressed",
        title_key="Tecla Pressionada?",
        category_key="Input",
        description_key="Verifica se uma tecla está sendo pressionada AGORA",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="key", label_key="Tecla", pin_type=PinType.STRING, default_value="space"),
        ],
        outputs=[
            PinDefinition(id="exec_pressed", label_key="Pressionada", pin_type=PinType.EXEC),
            PinDefinition(id="exec_not_pressed", label_key="Não Pressionada", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )


class WaitKeyReleaseNode(NodeDefinition):
    """Aguarda até uma tecla ser liberada."""

    __node_definition__ = NodeDefinition(
        id="wait_key_release",
        title_key="Aguardar Liberação de Tecla",
        category_key="Input",
        description_key="Aguarda até uma tecla ser liberada ou timeout",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="key", label_key="Tecla", pin_type=PinType.STRING, default_value="space"),
            PinDefinition(id="timeout", label_key="Timeout (s)", pin_type=PinType.FLOAT, default_value=10.0),
        ],
        outputs=[
            PinDefinition(id="exec_released", label_key="Liberada", pin_type=PinType.EXEC),
            PinDefinition(id="exec_waiting", label_key="Aguardando", pin_type=PinType.EXEC),
            PinDefinition(id="exec_timeout", label_key="Timeout", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )
