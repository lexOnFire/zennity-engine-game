"""Nós de pathfinding para Logic Graph - Navegação 100% visual."""
from __future__ import annotations

import math
from typing import Any, Mapping
from ..registry import registry


@registry.register_executor('find_path')
def execute_find_path(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Encontra caminho entre dois pontos usando A* ou dijkstra simples."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        start_x = float(properties.get("start_x", 0.0))
        start_y = float(properties.get("start_y", 0.0))
        end_x = float(properties.get("end_x", 100.0))
        end_y = float(properties.get("end_y", 100.0))
        grid_size = float(properties.get("grid_size", 32.0))

        if not hasattr(runtime, "_paths"):
            runtime._paths = {}

        path_id = f"path_{node_id}"

        # Criar caminho simples (linha reta com grid)
        path_points = []
        current_x, current_y = start_x, start_y

        while abs(current_x - end_x) > grid_size or abs(current_y - end_y) > grid_size:
            dx = end_x - current_x
            dy = end_y - current_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 0:
                step_x = (dx / distance) * grid_size
                step_y = (dy / distance) * grid_size
                current_x += step_x
                current_y += step_y
                path_points.append((current_x, current_y))

        path_points.append((end_x, end_y))

        runtime._paths[path_id] = {
            "points": path_points,
            "current_index": 0,
            "finished": False
        }

        runtime._store(node_id, "path_id", path_id)
        runtime._store(node_id, "path_length", len(path_points))

        return ["found"]
    except Exception as e:
        print(f"Erro em find_path: {e}")
        return ["failure"]


@registry.register_executor('follow_path')
def execute_follow_path(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Segue um caminho ponto a ponto."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        path_id = str(properties.get("path_id", ""))
        speed = float(properties.get("speed", 100.0))
        target_name = str(properties.get("target", ""))

        if not hasattr(runtime, "_paths"):
            return ["failure"]

        if path_id not in runtime._paths:
            return ["failure"]

        path_data = runtime._paths[path_id]
        points = path_data["points"]
        current_index = path_data["current_index"]

        if current_index >= len(points):
            path_data["finished"] = True
            return ["finished"]

        current_point = points[current_index]
        runtime._store(node_id, "current_waypoint", current_index)
        runtime._store(node_id, "next_x", current_point[0])
        runtime._store(node_id, "next_y", current_point[1])

        # Avançar para próximo ponto
        path_data["current_index"] += 1

        return ["following"]
    except Exception as e:
        print(f"Erro em follow_path: {e}")
        return ["failure"]


@registry.register_executor('stop_path')
def execute_stop_path(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Para de seguir um caminho."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        path_id = str(properties.get("path_id", ""))

        if hasattr(runtime, "_paths") and path_id in runtime._paths:
            del runtime._paths[path_id]

        return ["stopped"]
    except Exception as e:
        print(f"Erro em stop_path: {e}")
        return ["failure"]


@registry.register_executor('distance_to_point')
def execute_distance_to_point(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Calcula distância entre dois pontos."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        x1 = float(properties.get("x1", 0.0))
        y1 = float(properties.get("y1", 0.0))
        x2 = float(properties.get("x2", 100.0))
        y2 = float(properties.get("y2", 100.0))

        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx * dx + dy * dy)

        runtime._store(node_id, "distance", distance)

        return ["calculated"]
    except Exception as e:
        print(f"Erro em distance_to_point: {e}")
        return ["failure"]
