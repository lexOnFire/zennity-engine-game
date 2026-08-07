"""Definições de nós de input avançado para Logic Graph."""
from __future__ import annotations

from engine.logic.metadata import NodeDefinition, PinDefinition


class DetectTouchNode(NodeDefinition):
    """Detecta toque em uma área."""

    __node_definition__ = NodeDefinition(
        id="detect_touch",
        title="Detectar Toque",
        category="Input",
        description="Detecta toque do usuário em uma área específica",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("x", "X", "FLOAT", default_value=0.0),
            PinDefinition("y", "Y", "FLOAT", default_value=0.0),
            PinDefinition("width", "Largura", "FLOAT", default_value=100.0),
            PinDefinition("height", "Altura", "FLOAT", default_value=100.0),
        ],
        pins_output=[
            PinDefinition("exec_touched", "Tocado", "EXEC"),
            PinDefinition("exec_no_touch", "Sem Toque", "EXEC"),
            PinDefinition("touch_x", "Toque X", "FLOAT"),
            PinDefinition("touch_y", "Toque Y", "FLOAT"),
        ]
    )


class DetectSwipeNode(NodeDefinition):
    """Detecta swipe (deslize)."""

    __node_definition__ = NodeDefinition(
        id="detect_swipe",
        title="Detectar Swipe",
        category="Input",
        description="Detecta gesto de deslize na tela",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("direction", "Direção", "STRING", default_value="right"),  # right, left, up, down
            PinDefinition("min_distance", "Distância Mínima", "FLOAT", default_value=50.0),
        ],
        pins_output=[
            PinDefinition("exec_swiped", "Deslizou", "EXEC"),
            PinDefinition("exec_no_swipe", "Sem Deslize", "EXEC"),
            PinDefinition("swipe_distance", "Distância", "FLOAT"),
        ]
    )


class DetectPinchNode(NodeDefinition):
    """Detecta pinça (zoom)."""

    __node_definition__ = NodeDefinition(
        id="detect_pinch",
        title="Detectar Pinça",
        category="Input",
        description="Detecta gesto de pinça (zoom) na tela",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("type", "Tipo", "STRING", default_value="out"),  # in (zoom out), out (zoom in)
        ],
        pins_output=[
            PinDefinition("exec_pinched", "Pinçado", "EXEC"),
            PinDefinition("exec_no_pinch", "Sem Pinça", "EXEC"),
            PinDefinition("pinch_scale", "Escala", "FLOAT"),
        ]
    )


class IsKeyPressedNode(NodeDefinition):
    """Verifica se tecla está pressionada."""

    __node_definition__ = NodeDefinition(
        id="is_key_pressed",
        title="Tecla Pressionada?",
        category="Input",
        description="Verifica se uma tecla está sendo pressionada AGORA",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("key", "Tecla", "STRING", default_value="space"),
        ],
        pins_output=[
            PinDefinition("exec_pressed", "Pressionada", "EXEC"),
            PinDefinition("exec_not_pressed", "Não Pressionada", "EXEC"),
        ]
    )


class WaitKeyReleaseNode(NodeDefinition):
    """Aguarda até uma tecla ser liberada."""

    __node_definition__ = NodeDefinition(
        id="wait_key_release",
        title="Aguardar Liberação de Tecla",
        category="Input",
        description="Aguarda até uma tecla ser liberada ou timeout",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("key", "Tecla", "STRING", default_value="space"),
            PinDefinition("timeout", "Timeout (s)", "FLOAT", default_value=10.0),
        ],
        pins_output=[
            PinDefinition("exec_released", "Liberada", "EXEC"),
            PinDefinition("exec_waiting", "Aguardando", "EXEC"),
            PinDefinition("exec_timeout", "Timeout", "EXEC"),
        ]
    )
