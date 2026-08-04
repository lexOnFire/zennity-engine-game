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
        self._persistent: dict[str, Any] = {}
        self._started = False

    def start(self, game: Any) -> None:
        self._started = True
        self.current_state = self.root or "Empty"

    def stop(self, game: Any) -> None:
        self._started = False
        self._memory.clear()
        self._persistent.clear()

    def update(self, game: Any, dt: float) -> bool:
        if not self._started:
            self.start(game)
        previous = self.current_state
        if not self.root:
            return False
        status = self._tick(self.root, game, max(0.0, float(dt)))
        if status != "running":
            self._memory.clear()
        self._log_execution(game, self.current_state, status)
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
        if kind == "bt.repeat":
            return self._repeat(node_id, node, game, dt)
        if kind == "bt.cooldown":
            return self._cooldown(node_id, node, game, dt)
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
        if kind == "bt.target_in_range":
            target = game.find(str(self._input(node, "target", "Player")))
            return "success" if target is not None and game.distance_to(target) <= max(0.0, self._number(node, "distance", 150.0)) else "failure"
        if kind == "bt.parameter_condition":
            return "success" if self._parameter_matches(node) else "failure"
        if kind == "bt.chase":
            return self._chase(node, game, dt)
        if kind == "bt.patrol":
            return self._patrol(node_id, node, game, dt)
        if kind == "bt.attack":
            return self._attack(node, game)
        if kind == "bt.play_animation":
            animation = str(self._input(node, "animation", "Idle"))
            animator = getattr(game, "animator", None)
            if animator is not None and hasattr(animator, "play"):
                animator.play(animation)
            elif hasattr(game, "play_animation"):
                game.play_animation(animation)
            else:
                return "failure"
            return "success"
        return "failure"

    def _repeat(self, node_id: str, node: Mapping[str, Any], game: Any, dt: float) -> str:
        children = self.children.get(node_id, [])
        if not children:
            return "failure"
        result = self._tick(children[0], game, dt)
        if result == "running":
            return result
        self._clear_subtree_memory(children[0])
        completed = int(self._memory.get((node_id, "count"), 0)) + 1
        count = max(0, int(self._number(node, "count", 0)))
        if count and completed >= count:
            self._memory.pop((node_id, "count"), None)
            return "success" if result == "success" else "failure"
        self._memory[(node_id, "count")] = completed
        return "running"

    def _cooldown(self, node_id: str, node: Mapping[str, Any], game: Any, dt: float) -> str:
        remaining = max(0.0, float(self._persistent.get(node_id, 0.0)) - dt)
        self._persistent[node_id] = remaining
        if remaining > 0.0:
            return "failure"
        children = self.children.get(node_id, [])
        if not children:
            return "failure"
        result = self._tick(children[0], game, dt)
        if result == "success":
            self._persistent[node_id] = max(0.0, self._number(node, "seconds", 1.0))
            self._clear_subtree_memory(children[0])
        return result

    def _clear_subtree_memory(self, node_id: str) -> None:
        self._memory.pop(node_id, None)
        for key in tuple(self._memory):
            if isinstance(key, tuple) and key[0] == node_id:
                self._memory.pop(key, None)
        for child in self.children.get(node_id, []):
            self._clear_subtree_memory(child)

    def _chase(self, node: Mapping[str, Any], game: Any, dt: float) -> str:
        target = game.find(str(self._input(node, "target", "Player")))
        if target is None:
            return "failure"
        distance = game.distance_to(target)
        if distance <= max(0.0, self._number(node, "stop_distance", 48.0)):
            return "success"
        return self._move_towards(game, target.x, target.y, self._number(node, "speed", 120.0), dt)

    def _patrol(self, node_id: str, node: Mapping[str, Any], game: Any, dt: float) -> str:
        endpoint = int(self._persistent.get((node_id, "endpoint"), 0))
        point = self._point(self._input(node, "point_b" if endpoint else "point_a", "0,0"))
        if point is None:
            return "failure"
        if math.hypot(point[0] - game.x, point[1] - game.y) <= 1.0:
            endpoint = 1 - endpoint
            self._persistent[(node_id, "endpoint")] = endpoint
            point = self._point(self._input(node, "point_b" if endpoint else "point_a", "0,0"))
            if point is None:
                return "failure"
        self._move_towards(game, point[0], point[1], self._number(node, "speed", 80.0), dt)
        return "running"

    def _attack(self, node: Mapping[str, Any], game: Any) -> str:
        target = game.find(str(self._input(node, "target", "Player")))
        if target is None or game.distance_to(target) > max(0.0, self._number(node, "range", 64.0)):
            return "failure"
        damage = max(0.0, self._number(node, "damage", 10.0))
        obj = getattr(target, "obj", None)
        if isinstance(obj, dict):
            health_key = "health" if "health" in obj else "vida" if "vida" in obj else "health"
            obj[health_key] = max(0.0, float(obj.get(health_key, 100.0)) - damage)
        elif hasattr(target, "health"):
            target.health = max(0.0, float(target.health) - damage)
        else:
            return "failure"
        return "success"

    def _parameter_matches(self, node: Mapping[str, Any]) -> bool:
        current = self.parameters.get(str(self._input(node, "parameter", "")))
        expected: Any = self._input(node, "value", "true")
        if isinstance(expected, str):
            lowered = expected.strip().casefold()
            if lowered in {"true", "false"}:
                expected = lowered == "true"
            else:
                try:
                    expected = float(expected)
                except ValueError:
                    pass
        operator = str(self._input(node, "operator", "==")).strip()
        if operator == "==": return current == expected
        if operator == "!=": return current != expected
        try:
            left, right = float(current), float(expected)
            return {">": left > right, ">=": left >= right, "<": left < right, "<=": left <= right}.get(operator, False)
        except (TypeError, ValueError):
            return False

    def _is_reactive(self, node: Mapping[str, Any], kind: str) -> bool:
        """
        Um composite reativo reavalia os filhos desde o primeiro a cada tick;
        um com memória retoma no filho que ficou "running".

        BUG FIX: o composite SEMPRE tinha memória, então um filho que retorna
        "running" para sempre (bt.patrol, bt.chase) prendia o pai nele
        permanentemente -- uma árvore como
        ``selector[sequence[target_in_range, chase], patrol]`` nunca voltava a
        testar a perseguição depois de entrar em patrulha, tornando o padrão
        mais comum de IA impossível de montar.

        Defaults: ``bt.selector`` é reativo (é o nó de prioridade -- um ramo
        mais prioritário precisa poder interromper um irmão preso em
        "running"); ``bt.sequence`` mantém memória (reavaliar do início
        re-executaria ações já concluídas e com efeito colateral, como
        ``bt.attack``). A property ``reactive`` sobrescreve os dois casos.
        """
        raw = self._input(node, "reactive", kind == "bt.selector")
        if isinstance(raw, str):
            return raw.strip().casefold() in {"1", "true", "verdadeiro", "sim", "yes", "on"}
        return bool(raw)

    def _tick_composite(self, node_id: str, kind: str, game: Any, dt: float) -> str:
        children = self.children.get(node_id, [])
        if not children:
            return "success" if kind == "bt.sequence" else "failure"
        reactive = self._is_reactive(self.nodes[node_id], kind)
        previous_running = self._memory.get(node_id)
        index = 0 if reactive else int(previous_running or 0)
        while index < len(children):
            result = self._tick(children[index], game, dt)
            if result == "running":
                if reactive and previous_running is not None and int(previous_running) != index:
                    # Trocou de ramo: aborta o que estava rodando para que ele
                    # recomece do zero quando/se voltar a ser escolhido.
                    self._clear_subtree_memory(children[int(previous_running)])
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
    def _move_towards(game: Any, target_x: float, target_y: float, speed: float, dt: float) -> str:
        dx, dy = target_x - game.x, target_y - game.y
        distance = math.hypot(dx, dy)
        if distance <= 1.0:
            return "success"
        step = min(distance, max(0.0, speed) * dt)
        if step <= 0.0:
            return "failure"
        game.move(dx / distance * step, dy / distance * step)
        game.override_physics_axis("x")
        game.override_physics_axis("y")
        return "running"

    @staticmethod
    def _point(value: Any) -> tuple[float, float] | None:
        try:
            if isinstance(value, Mapping):
                return float(value.get("x", 0.0)), float(value.get("y", 0.0))
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                return float(value[0]), float(value[1])
            parts = str(value).replace(";", ",").split(",")
            return (float(parts[0]), float(parts[1])) if len(parts) >= 2 else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _input(node: Mapping[str, Any], name: str, default: Any) -> Any:
        # Current graph editor persists inspector values as ``properties``;
        # older assets and exported runtimes may still use ``inputs``.
        for field in ("properties", "inputs"):
            values = node.get(field, {})
            if isinstance(values, Mapping) and name in values:
                return values[name]
        return default

    def _number(self, node: Mapping[str, Any], name: str, default: float) -> float:
        try:
            return float(self._input(node, name, default))
        except (TypeError, ValueError):
            return default

    def _log_execution(self, game: Any, node_id: str, status: str) -> None:
        """Registra qual nó está sendo executado e seu status."""
        if node_id not in self.nodes:
            return
        node = self.nodes[node_id]
        node_type = str(node.get("type", "")).replace("bt.", "").upper()
        props = node.get("properties", {})
        target_info = ""
        if "target" in props:
            target_info = f" → {props['target']}"
        elif "target_pos" in props:
            target_info = f" @ {props['target_pos']}"
        status_emoji = {"running": "⏳", "success": "✓", "failure": "✗"}.get(status, "?")
        message = f"{status_emoji} {node_type}{target_info}"
        if hasattr(game, "log"):
            game.log("INFO", message)
        elif hasattr(game, "_log"):
            game._log("INFO", message)
