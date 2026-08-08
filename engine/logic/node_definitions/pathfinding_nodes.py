"""Definições de nós de pathfinding para Logic Graph."""
from __future__ import annotations

from engine.core.metadata import NodeDefinition, PinDefinition, PinType


class FindPathNode(NodeDefinition):
    """Encontra caminho entre dois pontos."""

    __node_definition__ = NodeDefinition(
        id="find_path",
        title_key="Encontrar Caminho",
        category_key="Navigation",
        description_key="Encontra um caminho navegável entre dois pontos",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="start_x", label_key="Início X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="start_y", label_key="Início Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="end_x", label_key="Fim X", pin_type=PinType.FLOAT, default_value=100.0),
            PinDefinition(id="end_y", label_key="Fim Y", pin_type=PinType.FLOAT, default_value=100.0),
            PinDefinition(id="grid_size", label_key="Tamanho Grid", pin_type=PinType.FLOAT, default_value=32.0),
        ],
        outputs=[
            PinDefinition(id="exec_found", label_key="Encontrado", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="path_id", label_key="ID do Caminho", pin_type=PinType.STRING),
            PinDefinition(id="path_length", label_key="Comprimento", pin_type=PinType.INT),
        ]
    )


class FollowPathNode(NodeDefinition):
    """Segue um caminho."""

    __node_definition__ = NodeDefinition(
        id="follow_path",
        title_key="Seguir Caminho",
        category_key="Navigation",
        description_key="Segue um caminho ponto a ponto",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="path_id", label_key="ID do Caminho", pin_type=PinType.STRING, default_value=""),
            PinDefinition(id="speed", label_key="Velocidade", pin_type=PinType.FLOAT, default_value=100.0),
            PinDefinition(id="target", label_key="Alvo", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="exec_following", label_key="Seguindo", pin_type=PinType.EXEC),
            PinDefinition(id="exec_finished", label_key="Terminou", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="current_waypoint", label_key="Waypoint Atual", pin_type=PinType.INT),
            PinDefinition(id="next_x", label_key="Próximo X", pin_type=PinType.FLOAT),
            PinDefinition(id="next_y", label_key="Próximo Y", pin_type=PinType.FLOAT),
        ]
    )


class StopPathNode(NodeDefinition):
    """Para de seguir um caminho."""

    __node_definition__ = NodeDefinition(
        id="stop_path",
        title_key="Parar Caminho",
        category_key="Navigation",
        description_key="Para de seguir um caminho",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="path_id", label_key="ID do Caminho", pin_type=PinType.STRING, default_value=""),
        ],
        outputs=[
            PinDefinition(id="exec_stopped", label_key="Parado", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
        ]
    )


class DistanceToPointNode(NodeDefinition):
    """Calcula distância entre dois pontos."""

    __node_definition__ = NodeDefinition(
        id="distance_to_point",
        title_key="Distância para Ponto",
        category_key="Navigation",
        description_key="Calcula a distância Euclidiana entre dois pontos",

        inputs=[
            PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC),
            PinDefinition(id="x1", label_key="Ponto 1 X", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="y1", label_key="Ponto 1 Y", pin_type=PinType.FLOAT, default_value=0.0),
            PinDefinition(id="x2", label_key="Ponto 2 X", pin_type=PinType.FLOAT, default_value=100.0),
            PinDefinition(id="y2", label_key="Ponto 2 Y", pin_type=PinType.FLOAT, default_value=100.0),
        ],
        outputs=[
            PinDefinition(id="exec_calculated", label_key="Calculado", pin_type=PinType.EXEC),
            PinDefinition(id="exec_failure", label_key="Falha", pin_type=PinType.EXEC),
            PinDefinition(id="distance", label_key="Distância", pin_type=PinType.FLOAT),
        ]
    )
