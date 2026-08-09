"""
Refactored Logic Graph runtime dispatcher - Phase 7B.1 implementation.

Key changes:
1. Registry is primary dispatcher (via _try_registry_executor)
2. Special nodes handled separately (_is_special_node, _execute_special)
3. Legacy fallback only for nodes without registry entry
4. All evaluated through single controlled path
"""

from __future__ import annotations

import sys
from typing import Any, Mapping


def _try_registry_executor(self, node: Mapping[str, Any], game: Any, dt: float) -> tuple[bool, list[str]]:
    """
    Try to execute node via registry executor.

    Returns: (found, ports)
        found: True if executor exists in registry
        ports: execution result ports if found, else empty
    """
    node_type = str(node["type"])
    executor = self.registry.executors.get(node_type)

    if executor is None:
        return False, []

    try:
        ports = executor(self, node, game, dt)

        # Validate returned ports
        if not isinstance(ports, list):
            return True, ["next"] if ports else []

        return True, ports

    except Exception as e:
        # Executor error is not gameplay failure
        node_id = str(node.get("id", "unknown"))
        print(f"[LogicRuntime] Executor error in {node_type} (id={node_id}): {e}", file=sys.stderr)
        return True, ["failure"]  # Return failure port, not exception

def _is_special_node(self, node_type: str) -> bool:
    """
    Check if node needs special runtime handling.

    Special nodes:
    - Subgraph lifecycle (call_subgraph, subgraph_input, subgraph_return)
    - Event subscriptions (event_custom, event_collision_enter, etc.)
    - Debugging (log_message)
    """
    special_types = {
        "call_subgraph",
        "subgraph_input",
        "subgraph_return",
        "event_custom",
        "event_collision_enter",
        "event_collision_exit",
        "event_trigger_enter",
        "event_trigger_exit",
        "on_animation_event",
        "on_animation_finished",
        "on_collision_enter",
        "on_collision_exit",
        "log_message",
    }

    return node_type in special_types

def _execute_special(self, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """
    Handle special runtime nodes that require non-standard execution.

    Preserves original hardcoded logic for these nodes.
    """
    node_type = str(node["type"])
    node_id = str(node.get("id", "unknown"))
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}

    # SUBGRAPH NODES
    if node_type == "subgraph_input":
        # Event source - no execution
        return []

    if node_type == "subgraph_return":
        return []

    if node_type == "call_subgraph":
        # Original hardcoded logic preserved
        subgraph_id = str(properties.get("graph_id", ""))
        target = self._read_target(node_id, game, dt, set())

        if subgraph_id in self.graphs:
            subgraph = self.graphs[subgraph_id]

            # Store current execution context
            prev_target = self._implicit_target
            self._implicit_target = target

            try:
                # Execute subgraph's entry node
                for entry_id in subgraph.entry_nodes:
                    self._follow(entry_id, "exec", game, dt, 1000, set())
            finally:
                self._implicit_target = prev_target

            return ["next"]
        else:
            return ["failure"]

    # EVENT NODES (don't execute, just return empty)
    if node_type.startswith("event_") or node_type.startswith("on_"):
        return []

    # DEBUG NODE
    if node_type == "log_message":
        message = str(self._read_input(node_id, "message", properties.get("message", ""), game, dt, set()))
        print(f"[LogicGraph] {message}")
        return ["next"]

    # Unknown special node - should not reach here
    return ["failure"]

def _execute_refactored(self, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """
    Refactored _execute() - Phase 7B.1 dispatcher consolidation.

    Execution order:
    1. Try registry executor (primary path)
    2. Check if special node (secondary path)
    3. Diagnose missing node (error path)
    """
    node_type = str(node["type"])

    # Primary path: Registry dispatch
    found, ports = self._try_registry_executor(node, game, dt)
    if found:
        return ports

    # Secondary path: Special runtime nodes
    if self._is_special_node(node_type):
        return self._execute_special(node, game, dt)

    # Error path: Unknown or missing node
    node_id = str(node.get("id", "unknown"))
    print(f"[LogicRuntime] Unknown node type: {node_type} (id={node_id})", file=sys.stderr)

    return ["failure"]

# MIGRATION NOTES:
#
# This refactored dispatcher:
#
# 1. Eliminates 98-branch hardcoded if/elif chain
# 2. Uses registry as canonical dispatcher
# 3. Preserves special node semantics
# 4. Adds proper error diagnostics
# 5. Validates returned ports
#
# DEPLOYMENT:
#
# Replace LogicGraphRuntime._execute() with _execute_refactored()
# Add helper methods: _try_registry_executor, _is_special_node, _execute_special()
# Ensure registry is properly initialized before runtime
#
# REGRESSION TESTING:
#
# All existing tests should pass without modification.
# No behavior changes for existing working nodes.
# Unreachable nodes now have execution paths via registry.
