"""Definições de nós de pathfinding para Logic Graph."""
from __future__ import annotations

from engine.logic.metadata import NodeDefinition, PinDefinition


class FindPathNode(NodeDefinition):
    """Encontra caminho entre dois pontos."""

    __node_definition__ = NodeDefinition(
        id="find_path",
        title="Encontrar Caminho",
        category="Navigation",
        description="Encontra um caminho navegável entre dois pontos",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("start_x", "Início X", "FLOAT", default_value=0.0),
            PinDefinition("start_y", "Início Y", "FLOAT", default_value=0.0),
            PinDefinition("end_x", "Fim X", "FLOAT", default_value=100.0),
            PinDefinition("end_y", "Fim Y", "FLOAT", default_value=100.0),
            PinDefinition("grid_size", "Tamanho Grid", "FLOAT", default_value=32.0),
        ],
        pins_output=[
            PinDefinition("exec_found", "Encontrado", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("path_id", "ID do Caminho", "STRING"),
            PinDefinition("path_length", "Comprimento", "INT"),
        ]
    )


class FollowPathNode(NodeDefinition):
    """Segue um caminho."""

    __node_definition__ = NodeDefinition(
        id="follow_path",
        title="Seguir Caminho",
        category="Navigation",
        description="Segue um caminho ponto a ponto",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("path_id", "ID do Caminho", "STRING", default_value=""),
            PinDefinition("speed", "Velocidade", "FLOAT", default_value=100.0),
            PinDefinition("target", "Alvo", "STRING", default_value=""),
        ],
        pins_output=[
            PinDefinition("exec_following", "Seguindo", "EXEC"),
            PinDefinition("exec_finished", "Terminou", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("current_waypoint", "Waypoint Atual", "INT"),
            PinDefinition("next_x", "Próximo X", "FLOAT"),
            PinDefinition("next_y", "Próximo Y", "FLOAT"),
        ]
    )


class StopPathNode(NodeDefinition):
    """Para de seguir um caminho."""

    __node_definition__ = NodeDefinition(
        id="stop_path",
        title="Parar Caminho",
        category="Navigation",
        description="Para de seguir um caminho",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("path_id", "ID do Caminho", "STRING", default_value=""),
        ],
        pins_output=[
            PinDefinition("exec_stopped", "Parado", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
        ]
    )


class DistanceToPointNode(NodeDefinition):
    """Calcula distância entre dois pontos."""

    __node_definition__ = NodeDefinition(
        id="distance_to_point",
        title="Distância para Ponto",
        category="Navigation",
        description="Calcula a distância Euclidiana entre dois pontos",

        pins_input=[
            PinDefinition("exec", "Exec", "EXEC"),
            PinDefinition("x1", "Ponto 1 X", "FLOAT", default_value=0.0),
            PinDefinition("y1", "Ponto 1 Y", "FLOAT", default_value=0.0),
            PinDefinition("x2", "Ponto 2 X", "FLOAT", default_value=100.0),
            PinDefinition("y2", "Ponto 2 Y", "FLOAT", default_value=100.0),
        ],
        pins_output=[
            PinDefinition("exec_calculated", "Calculado", "EXEC"),
            PinDefinition("exec_failure", "Falha", "EXEC"),
            PinDefinition("distance", "Distância", "FLOAT"),
        ]
    )
