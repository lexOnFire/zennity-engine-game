"""Registry extensível de executores de nós do Logic Graph."""
from __future__ import annotations

from typing import Any, Callable, Mapping, Protocol


class LogicNodeRuntime(Protocol):
    values: dict[Any, Any]
    def _evaluate_output(self, node_id: str, port: str, game: Any, dt: float, resolving: set) -> Any: ...
    def _read_input(self, node_id: str, port: str, default: Any, game: Any, dt: float, resolving: set) -> Any: ...
    def _condition(self, value: Any) -> bool: ...
    def _store(self, node_id: str, port: str, value: Any) -> None: ...


NodeHandler = Callable[[LogicNodeRuntime, Mapping[str, Any], Any, float], list[str]]


class LogicNodeHandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, NodeHandler] = {}

    def register(self, node_type: str, handler: NodeHandler, *, replace: bool = False) -> None:
        key = str(node_type)
        if key in self._handlers and not replace:
            raise ValueError(f"Handler já registrado: {key}")
        self._handlers[key] = handler

    def get(self, node_type: str) -> NodeHandler | None:
        return self._handlers.get(str(node_type))

    @property
    def node_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))


def default_logic_handlers() -> LogicNodeHandlerRegistry:
    registry = LogicNodeHandlerRegistry()

    def evaluate_next(runtime: LogicNodeRuntime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
        runtime._evaluate_output(str(node["id"]), "value", game, dt, set())
        return ["next"]

    def boolean_branch(runtime: LogicNodeRuntime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
        value = bool(runtime._evaluate_output(str(node["id"]), "value", game, dt, set()))
        return ["true" if value else "false"]

    def if_else(runtime: LogicNodeRuntime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
        node_id = str(node["id"])
        properties = node.get("properties", {})
        raw = runtime._read_input(node_id, "condition", properties.get("condition", False), game, dt, set())
        condition = runtime._condition(raw)
        runtime._store(node_id, "value", condition)
        return ["true" if condition else "false"]

    def move(runtime: LogicNodeRuntime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
        node_id = str(node["id"])
        properties = node.get("properties", {})
        amount = float(runtime._read_input(node_id, "value", runtime.values.get("axis", 0.0), game, dt, set()))
        game.move(amount * float(properties.get("speed", 200.0)) * dt)
        return ["next"]

    registry.register("input_axis", evaluate_next)
    registry.register("get_variable", evaluate_next)
    for node_type in ("key_pressed", "key_held", "is_grounded", "compare_number", "compare_text"):
        registry.register(node_type, boolean_branch)
    registry.register("if_else", if_else)
    registry.register("move", move)
    return registry
