"""Runtime direto para documentos visuais ``Behavior Tree``."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping


class BehaviorGraphRunner:
    """Executa o mesmo ``zennity.generic_graph`` editado na aba Behavior Tree."""

    def __init__(self, graph: Mapping[str, Any], project_root: str | Path = ".") -> None:
        if str(graph.get("format", "")) != "zennity.generic_graph":
            raise ValueError("Formato de Behavior Tree visual inválido.")
        if str(graph.get("category", "")).casefold() != "behavior tree":
            raise ValueError("O documento não pertence à categoria Behavior Tree.")
        self.graph = dict(graph)
        self.project_root = Path(project_root).resolve()
        self.nodes = {
            str(node.get("id")): dict(node)
            for node in graph.get("nodes", [])
            if isinstance(node, Mapping) and node.get("id")
        }
        self.children: dict[str, list[str]] = {}
        incoming: set[str] = set()
        edges = [edge for edge in graph.get("edges", []) if isinstance(edge, Mapping)]
        for edge in sorted(edges, key=lambda item: str(item.get("source_port", ""))):
            source = str(edge.get("source_node", ""))
            target = str(edge.get("target_node", ""))
            if source in self.nodes and target in self.nodes:
                self.children.setdefault(source, []).append(target)
                incoming.add(target)
        roots = [node_id for node_id in self.nodes if node_id not in incoming]
        self.root = roots[0] if roots else (next(iter(self.nodes), ""))
        self.parameters: dict[str, Any] = {}
        self.current_state = "Idle"
        self._memory: dict[str, Any] = {}
        self._started = False

    def start(self, game: Any) -> None:
        self._started = True
        self.current_state = self.root or "Empty"

    def stop(self, game: Any) -> None:
        self._started = False
        self._memory.clear()

    def update(self, game: Any, dt: float) -> bool:
        if not self._started:
            self.start(game)
        previous = self.current_state
        if not self.root:
            return False
        status = self._tick(self.root, game, max(0.0, float(dt)))
        if status != "running":
            self._memory.clear()
        return previous != self.current_state

    def play(self, state: str, game: Any) -> bool:
        if state not in self.nodes:
            return False
        self.root = state
        self._memory.clear()
        self.current_state = state
        return True

    def set_bool(self, name: str, value: bool) -> None:
        self.parameters[str(name)] = bool(value)

    def set_float(self, name: str, value: float) -> None:
        self.parameters[str(name)] = float(value)

    def trigger(self, name: str) -> None:
        self.parameters[str(name)] = True

    def _tick(self, node_id: str, game: Any, dt: float) -> str:
        node = self.nodes[node_id]
        kind = str(node.get("type", ""))
        self.current_state = node_id
        if kind in {"bt.sequence", "bt.selector"}:
            return self._tick_composite(node_id, kind, game, dt)
        if kind == "bt.inverter":
            children = self.children.get(node_id, [])
            if not children:
                return "failure"
            result = self._tick(children[0], game, dt)
            return {"success": "failure", "failure": "success"}.get(result, result)
        if kind == "bt.wait":
            duration = max(0.0, self._number(node, "duration", 1.0))
            elapsed = float(self._memory.get(node_id, 0.0)) + dt
            self._memory[node_id] = elapsed
            if elapsed < duration:
                return "running"
            self._memory.pop(node_id, None)
            return "success"
        if kind == "bt.move_to":
            return self._move_to(node, game, dt)
        return "failure"

    def _tick_composite(self, node_id: str, kind: str, game: Any, dt: float) -> str:
        children = self.children.get(node_id, [])
        if not children:
            return "success" if kind == "bt.sequence" else "failure"
        index = int(self._memory.get(node_id, 0))
        while index < len(children):
            result = self._tick(children[index], game, dt)
            if result == "running":
                self._memory[node_id] = index
                return result
            if kind == "bt.sequence" and result == "failure":
                self._memory.pop(node_id, None)
                return result
            if kind == "bt.selector" and result == "success":
                self._memory.pop(node_id, None)
                return result
            index += 1
        self._memory.pop(node_id, None)
        return "success" if kind == "bt.sequence" else "failure"

    def _move_to(self, node: Mapping[str, Any], game: Any, dt: float) -> str:
        target = self._input(node, "target_pos", "")
        target_x: float
        target_y: float
        if isinstance(target, str):
            other = game.find(target)
            if other is not None:
                target_x, target_y = other.x, other.y
            else:
                parts = target.replace(";", ",").split(",")
                if len(parts) < 2:
                    return "failure"
                try:
                    target_x, target_y = float(parts[0]), float(parts[1])
                except ValueError:
                    return "failure"
        elif isinstance(target, Mapping):
            target_x, target_y = float(target.get("x", 0.0)), float(target.get("y", 0.0))
        elif isinstance(target, (list, tuple)) and len(target) >= 2:
            target_x, target_y = float(target[0]), float(target[1])
        else:
            return "failure"
        dx, dy = target_x - game.x, target_y - game.y
        distance = math.hypot(dx, dy)
        if distance <= 1.0:
            game.x, game.y = target_x, target_y
            return "success"
        step = min(distance, max(0.0, self._number(node, "speed", 5.0)) * dt)
        if step <= 0.0:
            return "failure"
        game.move(dx / distance * step, dy / distance * step)
        game.override_physics_axis("x")
        game.override_physics_axis("y")
        return "running"

    @staticmethod
    def _input(node: Mapping[str, Any], name: str, default: Any) -> Any:
        values = node.get("inputs", {})
        return values.get(name, default) if isinstance(values, Mapping) else default

    def _number(self, node: Mapping[str, Any], name: str, default: float) -> float:
        try:
            return float(self._input(node, name, default))
        except (TypeError, ValueError):
            return default
