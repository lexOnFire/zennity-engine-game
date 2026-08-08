"""Definições de nós de câmera avançada para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class CameraShakeNode(NodeDefinition):
    """Sacode a câmera."""

    __node_definition__ = NodeDefinition(
        id="camera_shake",
        title_key="Câmera Sacode",
        category_key="Camera",
        description_key="Sacode a câmera para criar efeito de impacto",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="duration", label_key="Duração (s)", pin_type=PinType.FLOAT, default_value=0.5),
            PinDefinition(id="intensity", label_key="Intensidade", pin_type=PinType.FLOAT, default_value=5.0),
            PinDefinition(id="frequency", label_key="Frequência", pin_type=PinType.FLOAT, default_value=10.0),
        ],
        outputs=[
            PinDefinition(id="exec_shaking", label_key="Sacolejando", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )


class CameraFollowNode(NodeDefinition):
    """Câmera segue um objeto."""

    __node_definition__ = NodeDefinition(
        id="camera_follow",
        title_key="Câmera Segue",
        category_key="Camera",
        description_key="A câmera segue suavemente um objeto",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Alvo", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="smooth_time", label_key="Suavidade", pin_type=PinType.FLOAT, default_value=0.3),
        ],
        outputs=[
            PinDefinition(id="exec_following", label_key="Seguindo", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )


class CameraStopFollowNode(NodeDefinition):
    """Para de seguir."""

    __node_definition__ = NodeDefinition(
        id="camera_stop_follow",
        title_key="Câmera Parar de Seguir",
        category_key="Camera",
        description_key="Para de seguir o alvo",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )


class CameraLookAtNode(NodeDefinition):
    """Câmera olha para uma posição."""

    __node_definition__ = NodeDefinition(
        id="camera_look_at",
        title_key="Câmera Olha Para",
        category_key="Camera",
        description_key="A câmera se move para olhar para uma posição específica",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="x", label_key="X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="y", label_key="Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="duration", label_key="Duração (s)", pin_type=PinType.FLOAT, default_value=1.0),
        ],
        outputs=[
            PinDefinition(id="exec_looking", label_key="Olhando", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )


class CameraSetZoomNode(NodeDefinition):
    """Define o zoom da câmera."""

    __node_definition__ = NodeDefinition(
        id="camera_set_zoom",
        title_key="Câmera Zoom",
        category_key="Camera",
        description_key="Define o nível de zoom da câmera",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="zoom", label_key="Zoom", pin_type=PinType.FLOAT, default_value=1.0),
            PinDefinition(id="duration", label_key="Duração (s)", pin_type=PinType.FLOAT, default_value=0.5),
        ],
        outputs=[
            PinDefinition(id="exec_success", label_key="Sucesso", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="current_zoom", label_key="Zoom Atual", pin_type=PinType.FLOAT),
        ]
    )
