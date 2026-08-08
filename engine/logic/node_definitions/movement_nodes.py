"""Definições de nós de movimento para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition


class MoveNode(NodeDefinition):
    """Move o objeto em uma direção."""

    __node_definition__ = NodeDefinition(
        id="move",
        title_key="Mover",
        category_key="Movement",
        description_key="Move o objeto em uma direção específica",
        inputs=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("direction_x", "Direção X", "FLOAT", default_value=1.0),
            PinDefinition("direction_y", "Direção Y", "FLOAT", default_value=0.0),
            PinDefinition("speed", "Velocidade", "FLOAT", default_value=100.0),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("delta_x", "Delta X", "FLOAT", default_value=0.0),
            PinDefinition("delta_y", "Delta Y", "FLOAT", default_value=0.0),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("force", "Força", "FLOAT", default_value=500.0),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("axis", "Eixo", "STRING", default_value="x"),
            PinDefinition("min", "Mínimo", "FLOAT", default_value=0.0),
            PinDefinition("max", "Máximo", "FLOAT", default_value=100.0),
            PinDefinition("speed", "Velocidade", "FLOAT", default_value=50.0),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("velocity_x", "Velocidade X", "FLOAT", default_value=0.0),
            PinDefinition("velocity_y", "Velocidade Y", "FLOAT", default_value=0.0),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("velocity_x", "Velocidade X", "FLOAT", default_value=0.0),
            PinDefinition("velocity_y", "Velocidade Y", "FLOAT", default_value=0.0),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
            PinDefinition("velocity_x", "Velocidade X", "FLOAT"),
            PinDefinition("velocity_y", "Velocidade Y", "FLOAT"),
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
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
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
            PinDefinition("exec", "Exec", "EXEC"),
        ],
        outputs=[
            PinDefinition("exec_done", "Pronto", "EXEC"),
        ]
    )
