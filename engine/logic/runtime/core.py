"""Executor leve e tipado dos grafos visuais ``.zlogic``."""

from __future__ import annotations

import ast
import math
import re
from copy import deepcopy
from typing import Any, Callable, Iterator, Mapping

from .registry import registry
from .output_evaluator import evaluate_output
from .debug import LogicGraphDebugMixin
from .motion import LogicGraphMotionMixin
from .execution import LogicGraphExecutionMixin
from . import nodes

try:
    from ..graph_asset import normalize_logic_graph
    from ..blackboard import BlackboardStore
    from ..event_bus import LogicEvent, LogicEventBus
except ImportError:  # Runtime autocontido exportado.
    from ..logic_graph_asset import normalize_logic_graph
    from ..logic_blackboard import BlackboardStore
    from ..logic_event_bus import LogicEvent, LogicEventBus

# Phase 5B.2: Import physics event dispatch
from ..physics_event_dispatch import register_physics_event_handler

# Phase 6B.3: Import animation event dispatch
from ..animation_event_dispatch import register_animation_event_handler


class LogicGraphRuntime(LogicGraphDebugMixin, LogicGraphMotionMixin, LogicGraphExecutionMixin):
    """Executa fluxo e resolve valores conectados sem depender de Qt/Pygame."""

    MAX_STEPS = 256

    def __init__(
        self,
        graph: Mapping[str, Any],
        blackboard: BlackboardStore | None = None,
        object_key: str = "Object",
        event_bus: LogicEventBus | None = None,
        subgraph_loader: Callable[[str], Mapping[str, Any]] | None = None,
        call_stack: tuple[str, ...] = (),
    ) -> None:
        self.graph = normalize_logic_graph(graph)
        self.object_key = str(object_key)
        self.blackboard = blackboard or BlackboardStore()
        self.blackboard.register(self.graph.get("variables", {}), self.object_key)
        self.event_bus = event_bus or LogicEventBus()
        self.subgraph_loader = subgraph_loader
        self.call_stack = tuple(str(path).casefold() for path in call_stack)
        self.nodes = {node["id"]: node for node in self.graph["nodes"]}
        self.outgoing: dict[str, list[dict[str, Any]]] = {}
        self.incoming: dict[tuple[str, str], dict[str, Any]] = {}
        for edge in self.graph["edges"]:
            self.outgoing.setdefault(edge["from_node"], []).append(edge)
            self.incoming[(str(edge["to_node"]), str(edge.get("to_port", "in")))] = edge
        for edges in self.outgoing.values():
            edges.sort(key=lambda edge: (int(edge.get("order", 0)), str(edge.get("id", ""))))
        self.variables = self.blackboard.values_for_object(self.object_key)
        self.values: dict[Any, Any] = {}
        self.executed_nodes: list[str] = []
        self.data_evaluated_nodes: list[str] = []
        self.executed_edges: list[str] = []
        self.flow_traces: list[dict[str, Any]] = []
        self._trace_sequence = 0
        from collections import deque
        self._trace_events: deque[dict[str, Any]] = deque(maxlen=512)
        self.breakpoints = {str(value) for value in self.graph.get("debug", {}).get("breakpoints", [])}
        self.breakpoint_conditions = {
            str(node_id): str(expression)
            for node_id, expression in self.graph.get("debug", {}).get("breakpoint_conditions", {}).items()
        }
        self.watch_expressions = [str(value) for value in self.graph.get("debug", {}).get("watches", [])]
        self.debug_paused = False
        self.pause_node = ""
        self.debug_condition_error = ""
        self._debug_generator: Iterator[str] | None = None
        self._debug_waiting_node: str | None = None
        self._debug_bypass_node = ""
        self._debug_game: Any = None
        self._debug_dt = 0.0
        self._last_game: Any = None
        self._last_dt = 0.0
        self._pending_custom_events: list[tuple[str, LogicEvent]] = []
        self._event_trace_pending = False
        self._subgraph_outputs: dict[str, Any] = {}
        self._timer_elapsed: dict[str, float] = {}
        self._timer_fired: set[str] = set()
        self._node_state: dict[str, dict[str, Any]] = {}
        self._persistent_motion: dict[str, dict[str, Any]] = {}
        self._implicit_target: Any = None
        self._created_event_depth = 0
        self.started = False
        self._registered_physics_handler = False  # Phase 5B.2: Track handler registration
        self._registered_animation_handler = False  # Phase 6B.3: Track handler registration

        for node in self.nodes.values() if not self.call_stack else ():
            if node.get("type") == "event_custom":
                event_name = str(node.get("properties", {}).get("name", "event")).strip()
                node_id = str(node["id"])
                self.event_bus.subscribe(event_name, lambda event, wanted=node_id: self._receive_custom_event(wanted, event))
            elif node.get("type") in {"ui.button_clicked", "button_clicked", "on_ui_click"}:
                node_id = str(node["id"])
                inputs = node.get("inputs", {}) if isinstance(node.get("inputs"), dict) else {}
                props = node.get("properties", {}) if isinstance(node.get("properties"), dict) else {}
                target_widget = str(inputs.get("widget_name", props.get("widget_name", props.get("button", "")))).strip()

                self.event_bus.subscribe("ui.button_clicked", lambda event, wanted=node_id, tw=target_widget: self._handle_ui_button_clicked(wanted, event, tw))
                self.event_bus.subscribe("click", lambda event, wanted=node_id, tw=target_widget: self._handle_ui_button_clicked(wanted, event, tw))
            # Phase 6B.3: Subscribe to animation finished nodes
            elif node.get("type") == "on_animation_finished":
                node_id = str(node["id"])
                animation_name_filter = str(node.get("properties", {}).get("animation_name", "")).strip()
                self.event_bus.subscribe(
                    "animation:finished",
                    lambda event, wanted=node_id, anim_filter=animation_name_filter:
                        self._handle_animation_finished(wanted, event, anim_filter)
                )

        # Phase 5B.2: Register physics event handler if not a subgraph
        if not self.call_stack:
            register_physics_event_handler(self._handle_physics_event)
            self._registered_physics_handler = True

        # Phase 6B.3: Register animation event handler if not a subgraph
        if not self.call_stack:
            register_animation_event_handler(self._dispatch_animation_event)
            self._registered_animation_handler = True

        self._subscribe_to_ui_dispatcher()

    def _subscribe_to_ui_dispatcher(self) -> None:
        """Listen for global UI events, keeping the handle so stop() can detach.

        The dispatcher is a module-global, so an orphaned closure here would keep
        this runtime alive forever -- and with it every physics and animation
        handler it registered.
        """
        self._ui_dispatcher_subscription: tuple[str, Any] | None = None
        try:
            from engine.runtime.ui_event_dispatcher import get_ui_event_dispatcher

            callback = self._handle_global_ui_button_clicked
            get_ui_event_dispatcher().subscribe("ui.button_clicked", callback)
            self._ui_dispatcher_subscription = ("ui.button_clicked", callback)
        except Exception:
            pass  # Dispatcher may not be available in all contexts

    def _handle_global_ui_button_clicked(self, payload: dict[str, Any]) -> None:
        """Handle global UI button click event from dispatcher (Play Mode)."""
        # Store payload for ui.button_clicked nodes to access
        # Find nodes that are waiting for this button click
        for node in self.nodes.values():
            if node.get("type") not in {"ui.button_clicked", "button_clicked", "on_ui_click"}:
                continue

            node_id = str(node["id"])
            inputs = node.get("inputs", {}) if isinstance(node.get("inputs"), dict) else {}
            props = node.get("properties", {}) if isinstance(node.get("properties"), dict) else {}
            expected_widget = str(inputs.get("widget_name", props.get("widget_name", props.get("button", "")))).strip().lower()
            clicked_widget = str(payload.get("widget_name", payload.get("button", ""))).strip().lower()

            # If this node is waiting for this button, store the payload
            if not expected_widget or expected_widget == clicked_widget:
                self.values[(node_id, "payload")] = payload

    def stop(self) -> None:
        """Release every registration and owner reference this runtime holds.

        PHASE 9.5B Stage 3: called explicitly by the lifecycle owner
        (``ViewportRuntimeInitializer._clear_runtime_state``).  ``__del__`` still
        calls it as a backstop, but cleanup must never depend on the collector --
        and could not, since the UI dispatcher subscription below was itself what
        kept the object alive.

        Safe to call repeatedly.
        """
        # Phase 9.5B Stage 3: drop the global UI dispatcher subscription first.
        subscription = getattr(self, "_ui_dispatcher_subscription", None)
        if subscription is not None:
            event_type, callback = subscription
            try:
                from engine.runtime.ui_event_dispatcher import get_ui_event_dispatcher

                get_ui_event_dispatcher().unsubscribe(event_type, callback)
            except Exception:
                pass
            self._ui_dispatcher_subscription = None

        if self._registered_physics_handler:
            try:
                from ..physics_event_dispatch import unregister_physics_event_handler
                unregister_physics_event_handler(self._handle_physics_event)
                self._registered_physics_handler = False
            except Exception:
                pass

        # Phase 6B.3: Cleanup animation event handler
        if self._registered_animation_handler:
            try:
                from ..animation_event_dispatch import unregister_animation_event_handler
                unregister_animation_event_handler(self._dispatch_animation_event)
                self._registered_animation_handler = False
            except Exception:
                pass

        # Phase 9.5B Stage 3: release owner references and per-session state so a
        # stopped runtime cannot pin the game object or the previous session's
        # values.  The graph itself is kept: stop() ends a session, it does not
        # invalidate the asset.
        try:
            self.event_bus = LogicEventBus()
            self.values.clear()
            self.executed_nodes.clear()
            self.data_evaluated_nodes.clear()
            self.executed_edges.clear()
            self.flow_traces.clear()
            self._trace_events.clear()
            self._last_game = None
            self._implicit_target = None
            self.started = False
        except Exception:
            pass

    def _record_trace(self, kind: str, **kwargs: Any) -> None:
        self._trace_sequence += 1
        event = {
            "sequence": self._trace_sequence,
            "kind": kind,
            **kwargs,
        }
        self._trace_events.append(event)

    def trace_events_since(self, sequence: int = 0) -> list[dict[str, Any]]:
        return [e for e in self._trace_events if e.get("sequence", 0) > int(sequence)]

    def __del__(self) -> None:
        """Backstop only -- the lifecycle owner calls stop() explicitly."""
        try:
            self.stop()
        except Exception:
            pass

    def run_subgraph(self, game: Any, dt: float, inputs: Mapping[str, Any]) -> dict[str, Any]:
        """Executa uma chamada reutilizável sem iniciar eventos de frame."""
        self.started = True
        self._last_game = game
        self._last_dt = float(dt)
        self.values.clear()
        self.executed_nodes.clear()
        self.executed_edges.clear()
        self._subgraph_outputs.clear()
        for node in self.nodes.values():
            if node.get("type") != "subgraph_input":
                continue
            properties = node.get("properties", {})
            name = str(properties.get("name", "input")).strip()
            self._store(str(node["id"]), "value", deepcopy(inputs.get(name, properties.get("default"))))
        budget = [self.MAX_STEPS]
        for node in self.nodes.values():
            if node.get("type") == "subgraph_start":
                self.executed_nodes.append(str(node["id"]))
                self._follow(str(node["id"]), "next", game, float(dt), budget, set())
        return deepcopy(self._subgraph_outputs)

    def start(self, game: Any) -> None:
        if self.started:
            return
        self.started = True
        self._last_game = game
        self._last_dt = 0.0
        self.values.clear()
        self.executed_nodes.clear()
        self.executed_edges.clear()
        if self.breakpoints:
            self._begin_debug_event("event_start", game, 0.0)
        else:
            self._run_event("event_start", game, 0.0)

    def update(self, game: Any, dt: float) -> None:
        self._last_game = game
        self._last_dt = float(dt)
        if not self.started:
            self.start(game)
        if self.debug_paused:
            return
        self._update_timers(game, float(dt))
        self._apply_persistent_motion(float(dt))
        self._run_key_pressed_events(game, float(dt))
        if self.breakpoints:
            if self._debug_generator is None:
                self.values.clear()
                self.executed_nodes.clear()
                self.executed_edges.clear()
                if self._pending_custom_events:
                    node_id, event = self._pending_custom_events.pop(0)
                    self._begin_debug_custom_event(node_id, event)
                else:
                    self._begin_debug_event("event_update", game, float(dt))
            else:
                self._drive_debug()
            return
        self.values.clear()
        self.executed_nodes.clear()
        self.executed_edges.clear()
        self._run_event("event_update", game, float(dt))

    def _run_key_pressed_events(self, game: Any, dt: float) -> None:
        for node in self.nodes.values():
            if node.get("type") != "event_key_pressed":
                continue
            key = str(node.get("properties", {}).get("key", "D")).strip().lower()
            if game.key_pressed(key):
                self._run_event_node(node, game, dt)



    def trigger_event(self, event_type: str, game: Any, dt: float = 0.0, payload: Any = None) -> None:
        """Dispara um evento físico enviado pelo Play Mode."""
        if not self.started:
            self.start(game)
        self._last_game = game
        self._last_dt = float(dt)
        if self.debug_paused:
            return
        self.values.clear()
        self.executed_nodes.clear()
        self.executed_edges.clear()
        if self.breakpoints:
            self._begin_debug_event(str(event_type), game, float(dt), payload)
        else:
            self._run_event(str(event_type), game, float(dt), payload)

    def _update_timers(self, game: Any, dt: float) -> None:
        for node in self.nodes.values():
            if node.get("type") != "event_timer":
                continue
            node_id = str(node["id"])
            properties = node.get("properties", {})
            repeat = bool(properties.get("repeat", False))
            if node_id in self._timer_fired and not repeat:
                continue
            seconds = max(0.001, float(properties.get("seconds", 1.0)))
            elapsed = self._timer_elapsed.get(node_id, 0.0) + max(0.0, float(dt))
            if elapsed < seconds:
                self._timer_elapsed[node_id] = elapsed
                continue
            self._timer_elapsed[node_id] = elapsed % seconds if repeat else seconds
            self._timer_fired.add(node_id)
            self._run_event_node(node, game, dt)


    def configure_variables(self, definitions: Mapping[str, Any]) -> None:
        """Registra alterações do painel Blackboard sem reiniciar o Play Mode."""
        self.graph["variables"] = deepcopy(dict(definitions))
        self.blackboard.register(self.graph["variables"], self.object_key)
        self.variables = self.blackboard.values_for_object(self.object_key)


    def restart(self, game: Any, dt: float = 0.0) -> None:
        """Reinicia variáveis e fluxo, avançando novamente até o primeiro breakpoint."""
        self.blackboard.reset_object(self.object_key)
        self.variables = self.blackboard.values_for_object(self.object_key)
        self.values.clear()
        self.executed_nodes.clear()
        self.executed_edges.clear()
        self.debug_paused = False
        self.pause_node = ""
        self.debug_condition_error = ""
        self._debug_generator = None
        self._debug_waiting_node = None
        self._debug_bypass_node = ""
        self._pending_custom_events.clear()
        self._timer_elapsed.clear()
        self._timer_fired.clear()
        self._node_state.clear()
        self._persistent_motion.clear()
        self._implicit_target = None
        self.started = False
        self.start(game)
        if not self.debug_paused:
            self.update(game, float(dt))

    def hot_reload(self, new_graph: Mapping[str, Any]) -> None:
        """Substitui o grafo em tempo de execução mantendo o estado das variáveis (Blackboard)."""
        self.graph = normalize_logic_graph(new_graph)
        self.nodes = {node["id"]: node for node in self.graph["nodes"]}
        self.outgoing = {}
        self.incoming = {}
        for edge in self.graph["edges"]:
            self.outgoing.setdefault(edge["from_node"], []).append(edge)
            self.incoming[(str(edge["to_node"]), str(edge.get("to_port", "in")))] = edge
        for edges in self.outgoing.values():
            edges.sort(key=lambda edge: (int(edge.get("order", 0)), str(edge.get("id", ""))))
        # We also need to re-register variables in case they changed, but preserve existing values
        self.blackboard.register(self.graph.get("variables", {}), self.object_key)
        self.variables = self.blackboard.values_for_object(self.object_key)

    # Phase 6B.3: Animation Event Handling
    def _dispatch_animation_event(
        self,
        owner_object: Any,
        animation_name: str,
        event_name: str,
        frame_index: int,
        elapsed_time: float,
    ) -> None:
        """Phase 6B.3: Dispatch animation event to LogicEventBus."""
        if owner_object is None:
            return

        # Get the object name to match against owner
        owner_name = getattr(owner_object, "name", None)
        if owner_name != self.object_key:
            return

        # Emit to LogicEventBus for animation event nodes
        payload = {
            "owner_object": owner_object,
            "animation_name": animation_name,
            "event_name": event_name,
            "frame_index": frame_index,
            "elapsed_time": elapsed_time,
        }
        self.event_bus.emit("animation:event", payload=payload, source=owner_name)

    def _handle_animation_event(
        self,
        node_id: str,
        event: LogicEvent,
        event_name_filter: str,
        animation_name_filter: str,
    ) -> None:
        """Handle animation event received from bus."""
        if event.payload is None or not isinstance(event.payload, dict):
            return

        # Apply event name filter
        event_name = str(event.payload.get("event_name", "")).strip()
        if event_name_filter and event_name != event_name_filter:
            return

        # Apply animation name filter
        animation_name = str(event.payload.get("animation_name", "")).strip()
        if animation_name_filter and animation_name != animation_name_filter:
            return

        # Store event data for node outputs
        self.values[(node_id, "owner_object")] = event.payload.get("owner_object")
        self.values[(node_id, "animation_name")] = event_name
        self.values[(node_id, "event_name")] = event_name
        self.values[(node_id, "frame_index")] = int(event.payload.get("frame_index", 0))
        self.values[(node_id, "elapsed_time")] = float(event.payload.get("elapsed_time", 0.0))

        # Mark node for execution
        if node_id not in self.executed_nodes:
            self.executed_nodes.append(node_id)
            for edge in self.outgoing.get(node_id, []):
                if edge.get("from_port") == "exec":
                    self._run_edge(edge, self._last_game, self._last_dt)

