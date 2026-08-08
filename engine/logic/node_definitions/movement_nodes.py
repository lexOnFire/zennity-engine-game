"""Definições de nós de movimento para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class MoveNode(NodeDefinition):
    """Move o objeto em uma direção."""

    __node_definition__ = NodeDefinition(
        id="move",
        title_key="Mover",
        category_key="Movement",
        description_key="Move o objeto em uma direção específica",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="direction_x", label_key="Direção X", pin_type=PinType.FLOAT, default_value=1.0),
            PinDefinition(id="direction_y", label_key="Direção Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="speed", label_key="Velocidade", pin_type=PinType.FLOAT, default_value=100.0),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class MoveByNode(NodeDefinition):
    """Move o objeto por uma distância."""

    __node_definition__ = NodeDefinition(
        id="move_by",
        title_key="Mover Por",
        category_key="Movement",
        description_key="Move o objeto por um deslocamento específico",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="delta_x", label_key="Delta X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="delta_y", label_key="Delta Y", pin_type=PinType.FLOAT, default_value=0.0),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class JumpNode(NodeDefinition):
    """Faz o objeto pular."""

    __node_definition__ = NodeDefinition(
        id="jump",
        title_key="Pular",
        category_key="Movement",
        description_key="Aplica uma força de pulo ao objeto",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="force", label_key="Força", pin_type=PinType.FLOAT, default_value=500.0),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class PatrolAxisNode(NodeDefinition):
    """Patrulha entre dois pontos."""

    __node_definition__ = NodeDefinition(
        id="patrol_axis",
        title_key="Patrulhar",
        category_key="Movement",
        description_key="Move o objeto para frente e para trás entre limites",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="axis", label_key="Eixo", pin_type=PinType.STRING, default_value="x"),
            PinDefinition(id="min", label_key="Mínimo", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="max", label_key="Máximo", pin_type=PinType.FLOAT, default_value=100.0),
            PinDefinition(id="speed", label_key="Velocidade", pin_type=PinType.FLOAT, default_value=50.0),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class StartContinuousMotionNode(NodeDefinition):
    """Inicia movimento contínuo."""

    __node_definition__ = NodeDefinition(
        id="start_continuous_motion",
        title_key="Iniciar Movimento Contínuo",
        category_key="Movement",
        description_key="Inicia um movimento contínuo do objeto",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="velocity_x", label_key="Velocidade X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="velocity_y", label_key="Velocidade Y", pin_type=PinType.FLOAT, default_value=0.0),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class StopContinuousMotionNode(NodeDefinition):
    """Para movimento contínuo."""

    __node_definition__ = NodeDefinition(
        id="stop_continuous_motion",
        title_key="Parar Movimento Contínuo",
        category_key="Movement",
        description_key="Para o movimento contínuo do objeto",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class UpdateContinuousMotionNode(NodeDefinition):
    """Atualiza movimento contínuo."""

    __node_definition__ = NodeDefinition(
        id="update_continuous_motion",
        title_key="Atualizar Movimento Contínuo",
        category_key="Movement",
        description_key="Atualiza a velocidade do movimento contínuo",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="velocity_x", label_key="Velocidade X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="velocity_y", label_key="Velocidade Y", pin_type=PinType.FLOAT, default_value=0.0),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class GetContinuousMotionNode(NodeDefinition):
    """Obtém velocidade contínua atual."""

    __node_definition__ = NodeDefinition(
        id="get_continuous_motion",
        title_key="Obter Movimento Contínuo",
        category_key="Movement",
        description_key="Obtém a velocidade atual do movimento contínuo",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
            PinDefinition(id="velocity_x", label_key="Velocidade X", pin_type=PinType.FLOAT),
            PinDefinition(id="velocity_y", label_key="Velocidade Y", pin_type=PinType.FLOAT),
        ]
    )


class PauseContinuousMotionNode(NodeDefinition):
    """Pausa movimento contínuo."""

    __node_definition__ = NodeDefinition(
        id="pause_continuous_motion",
        title_key="Pausar Movimento Contínuo",
        category_key="Movement",
        description_key="Pausa temporariamente o movimento contínuo",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )


class ResumeContinuousMotionNode(NodeDefinition):
    """Retoma movimento contínuo."""

    __node_definition__ = NodeDefinition(
        id="resume_continuous_motion",
        title_key="Retomar Movimento Contínuo",
        category_key="Movement",
        description_key="Retoma o movimento contínuo pausado",
        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
        ],
        outputs=[
            PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC),
        ]
    )
