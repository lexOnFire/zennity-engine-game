"""Definições de nós de câmera avançada para Logic Graph."""
from __future__ import annotations

from engine.logic.metadata import NodeDefinition, PinDefinition


class CameraShakeNode(NodeDefinition):
    """Sacode a câmera."""

    __node_definition__ = NodeDefinition(
        id="camera_shake",
        title="Câmera Sacode",
        category="Camera",
        description="Sacode a câmera para criar efeito de impacto",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("duration", "Duração (s)", "FLOAT", default_value=0.5),
            PinDefinition("intensity", "Intensidade", "FLOAT", default_value=5.0),
            PinDefinition("frequency", "Frequência", "FLOAT", default_value=10.0),
        ],
        pins_output=[
            PinDefinition("exec_shaking", "Sacolejando", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )


class CameraFollowNode(NodeDefinition):
    """Câmera segue um objeto."""

    __node_definition__ = NodeDefinition(
        id="camera_follow",
        title="Câmera Segue",
        category="Camera",
        description="A câmera segue suavemente um objeto",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("target", "Alvo", "STRING", default_value=""),
            PinDefinition("smooth_time", "Suavidade", "FLOAT", default_value=0.3),
        ],
        pins_output=[
            PinDefinition("exec_following", "Seguindo", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )


class CameraStopFollowNode(NodeDefinition):
    """Para de seguir."""

    __node_definition__ = NodeDefinition(
        id="camera_stop_follow",
        title="Câmera Parar de Seguir",
        category="Camera",
        description="Para de seguir o alvo",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        pins_output=[
            PinDefinition("exec_success", "Sucesso", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )


class CameraLookAtNode(NodeDefinition):
    """Câmera olha para uma posição."""

    __node_definition__ = NodeDefinition(
        id="camera_look_at",
        title="Câmera Olha Para",
        category="Camera",
        description="A câmera se move para olhar para uma posição específica",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("x", "X", "FLOAT", default_value=0.0),
            PinDefinition("y", "Y", "FLOAT", default_value=0.0),
            PinDefinition("duration", "Duração (s)", "FLOAT", default_value=1.0),
        ],
        pins_output=[
            PinDefinition("exec_looking", "Olhando", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )


class CameraSetZoomNode(NodeDefinition):
    """Define o zoom da câmera."""

    __node_definition__ = NodeDefinition(
        id="camera_set_zoom",
        title="Câmera Zoom",
        category="Camera",
        description="Define o nível de zoom da câmera",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("zoom", "Zoom", "FLOAT", default_value=1.0),
            PinDefinition("duration", "Duração (s)", "FLOAT", default_value=0.5),
        ],
        pins_output=[
            PinDefinition("exec_success", "Sucesso", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("current_zoom", "Zoom Atual", "FLOAT"),
        ]
    )
