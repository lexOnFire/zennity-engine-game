# NEW _execute() method for Phase 7B.1 Registry Dispatcher Consolidation
# Replace the 445-line hardcoded version (lines 841-1284) with this:

def _execute(self, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """
    Execute a Logic Graph node (Phase 7B.1 - Registry Dispatcher).

    Dispatch order:
    1. Registry executor (primary path) - 71 executors available
    2. Special runtime nodes (secondary) - subgraph, events only
    3. Error diagnosis (fallback) - clear diagnostics

    Returns:
        List of output port names to follow execution
    """
    node_type = str(node["type"])
    node_id = str(node.get("id", "unknown"))

    # ===== PRIMARY: Try registry executor =====
    found, ports = self._try_registry_executor(node, game, dt)

    if found:
        # Executor found (either succeeded or failed)
        if ports is None:
            # Contract violation or exception - return failure
            return ["failure"]

        # Validate ports against node definition
        if not self._validate_returned_ports(node_type, node_id, ports):
            return ["failure"]

        return ports

    # ===== SECONDARY: Special runtime nodes =====
    if self._is_special_runtime_node(node_type):
        return self._execute_special_node(node, game, dt)

    # ===== ERROR: Unknown node type =====
    print(
        f"[LogicRuntime ERROR] Unknown node type '{node_type}' (id={node_id}). "
        f"No executor in registry and not a special node. Execution halted.",
        file=sys.stderr
    )
    return ["failure"]
