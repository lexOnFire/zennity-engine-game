# PHASE 7B.1: LOGIC GRAPH REGISTRY DISPATCHER CONSOLIDATION - PLAN

**Status**: PRE-IMPLEMENTATION  
**Date**: 2026-08-08  
**Scope**: Consolidate hardcoded dispatcher to use registry as canonical execution path  

---

## CRITICAL AUDIT FINDINGS

### Dispatch Health

| Metric | Value |
|--------|-------|
| **Total Registered** | 132 (71 executors + 61 evaluators) |
| **Currently Hardcoded** | 62 nodes |
| **UNREACHABLE** | 78 nodes (59% of system) |
| **Status** | CRITICAL |

### Unreachable by System

| System | Executors | Evaluators | Impact |
|--------|-----------|-----------|--------|
| Input | 3 | 3 | Cannot use keyboard input visually |
| Camera | 1 | 5 | Cannot control camera visually |
| Audio | 1 | 4 | Cannot play sounds visually |
| Animation | 2 | 9 | Some animation nodes broken |
| Physics | 6 | 15 | Some physics nodes broken |
| UI | 6 | 8 | Dynamic UI creation broken |
| Variables | 1 | 1 | Get variable sometimes fails |
| Other | 12 | 11 | Various nodes |
| **TOTAL** | **32** | **46** | **78 nodes** |

---

## CURRENT ARCHITECTURE (BROKEN)

```
Logic Graph Node (e.g., "set_position")
      ↓
_execute(node)
      ↓
if node_type == "set_position":
    # Handle hardcoded
    elif node_type == "move":
        # Handle hardcoded
        elif node_type == ...  # 98 branches total
            ↓
If branch found: execute
If branch not found: return ["next"] (SILENT FAILURE)
      ↓
returned ports (may be wrong)
      ↓
_follow() continues
```

**Problem**: 78 nodes have executors in registry but no hardcoded branch → silent failures.

---

## PROPOSED ARCHITECTURE (FIXED)

```
Logic Graph Node
      ↓
_execute(node)
      ↓
1. Try registry executor
   executor = registry.get_executor(node_type)
   if executor exists:
       result = executor(self, node, game, dt)
       return result
       
2. Check if special node (event, subgraph, debug)
   if is_special_node(node_type):
       return _execute_special(...)
       
3. Diagnose missing node
   else:
       log error, return ["failure"]
```

**Benefit**: 78 previously broken nodes now work. No silent failures.

---

## IMPLEMENTATION STRATEGY

### Phase 1: New Helper Methods

Add three new methods to `LogicGraphRuntime`:

**1. `_try_registry_executor(node, game, dt) -> (found, ports)`**
- Look up executor in registry
- Execute if found
- Handle exceptions gracefully
- Validate returned ports
- Return (True, ports) if found, else (False, [])

**2. `_is_special_node(node_type) -> bool`**
- Identify nodes needing special handling:
  - Subgraph nodes (call_subgraph, subgraph_input, subgraph_return)
  - Event nodes (event_custom, on_collision_enter, etc.)
  - Debug nodes (log_message)
- Return True for these, False for regular action nodes

**3. `_execute_special(node, game, dt) -> ports`**
- Preserve original hardcoded logic for special nodes
- Handle subgraph execution lifecycle
- Return appropriate ports

### Phase 2: Refactor `_execute()`

Replace 98-branch hardcoded dispatcher with:

```python
def _execute(self, node, game, dt):
    node_type = str(node["type"])

    # Primary: Registry dispatch
    found, ports = self._try_registry_executor(node, game, dt)
    if found:
        return ports

    # Secondary: Special nodes
    if self._is_special_node(node_type):
        return self._execute_special(node, game, dt)

    # Error: Unknown node
    return self._diagnose_missing_executor(node_type, node)
```

**Changes**:
- Delete 98 if/elif branches
- Replace with 3-branch dispatcher
- Keep all special node logic intact
- Add error diagnostics

**Code Reduction**:
- Before: ~440 lines (if/elif chain)
- After: ~40 lines (dispatcher) + ~200 lines (helpers)
- Net: **Cleaner, more maintainable**

### Phase 3: Validation & Regression Testing

**Must Pass**:
- All existing hardcoded nodes still work identically
- 78 unreachable nodes now execute properly
- No port validation errors
- No new infinite loops
- No new exceptions

**Test Coverage**:

```
Unit Tests:
- test_registry_executor_is_called_before_legacy()
- test_executor_exception_returns_failure()
- test_invalid_port_return_is_caught()
- test_special_node_not_executed_as_action()
- test_pure_node_uses_evaluator_not_executor()

Regression Tests:
- test_physics_nodes_still_work()
- test_animation_nodes_still_work()
- test_ui_nodes_still_work()
- test_transform_nodes_still_work()
- test_variables_still_work()
- test_prefab_spawn_still_works()

Smoke Tests:
- test_cross_system_graph_execution()
- test_unreachable_executors_now_work()
```

---

## DETAILED IMPLEMENTATION

### Step 1: Add Helper Method - Registry Dispatch

```python
def _try_registry_executor(
    self,
    node: Mapping[str, Any],
    game: Any,
    dt: float
) -> tuple[bool, list[str]]:
    """
    Try executing node via registry executor.

    Returns:
        (found, ports): (True, result_ports) if executor exists
                       (False, []) if not found
    """
    node_type = str(node["type"])
    executor = self.registry.executors.get(node_type)

    if executor is None:
        return False, []

    try:
        ports = executor(self, node, game, dt)

        # Validate ports
        if not isinstance(ports, list):
            # Handle non-list returns
            return True, (["next"] if ports else [])

        # Validate each port exists in node definition
        # (can add optional validation here)

        return True, ports

    except Exception as e:
        # Log executor error for debugging
        node_id = str(node.get("id", "unknown"))
        print(
            f"[LogicRuntime] Executor error in {node_type} "
            f"(id={node_id}): {type(e).__name__}: {e}"
        )
        # Return failure port, not exception
        return True, ["failure"]
```

### Step 2: Add Helper Method - Special Node Identification

```python
def _is_special_node(self, node_type: str) -> bool:
    """
    Check if node requires special runtime handling.

    Special categories:
    - Subgraph lifecycle (call_subgraph, etc.)
    - Event subscriptions (event_*, on_*)
    - Debug (log_message)
    """
    special_types = {
        # Subgraph nodes
        "call_subgraph",
        "subgraph_input",
        "subgraph_return",

        # Event nodes (don't execute, just fire)
        "event_custom",
        "event_collision_enter",
        "event_collision_exit",
        "event_trigger_enter",
        "event_trigger_exit",
        "on_animation_event",
        "on_animation_finished",
        "on_collision_enter",
        "on_collision_exit",

        # Debug
        "log_message",
    }

    return node_type in special_types
```

### Step 3: Add Helper Method - Execute Special Nodes

```python
def _execute_special(
    self,
    node: Mapping[str, Any],
    game: Any,
    dt: float
) -> list[str]:
    """
    Execute special nodes with custom lifecycle.

    Preserves original hardcoded logic.
    """
    node_type = str(node["type"])
    node_id = str(node.get("id", "unknown"))
    properties = node.get("properties", {})
    if not isinstance(properties, Mapping):
        properties = {}

    # --- SUBGRAPH NODES ---
    if node_type == "subgraph_input":
        # Event source - no execution
        return []

    if node_type == "subgraph_return":
        # Already handled in _follow()
        return []

    if node_type == "call_subgraph":
        # [Original hardcoded logic from current _execute()]
        subgraph_id = str(properties.get("graph_id", ""))
        target = self._read_target(node_id, game, dt, set())

        if subgraph_id in self.graphs:
            subgraph = self.graphs[subgraph_id]

            # Save execution context
            prev_target = self._implicit_target
            self._implicit_target = target

            try:
                # Execute subgraph
                for entry_id in subgraph.entry_nodes:
                    self._follow(entry_id, "exec", game, dt, 1000, set())
            finally:
                self._implicit_target = prev_target

            return ["next"]
        else:
            return ["failure"]

    # --- EVENT NODES (all return empty) ---
    if node_type.startswith("event_") or node_type.startswith("on_"):
        return []

    # --- DEBUG ---
    if node_type == "log_message":
        message = str(
            self._read_input(
                node_id, "message",
                properties.get("message", ""),
                game, dt, set()
            )
        )
        print(f"[LogicGraph] {message}")
        return ["next"]

    # Shouldn't reach here
    return ["failure"]
```

### Step 4: Refactor `_execute()`

Replace the entire 98-branch if/elif chain with:

```python
def _execute(
    self,
    node: Mapping[str, Any],
    game: Any,
    dt: float
) -> list[str]:
    """
    Execute a Logic Graph node.

    Dispatch order:
    1. Registry executor (primary)
    2. Special node handler (secondary)
    3. Error diagnosis (fallback)

    Returns:
        List of output port names to follow
    """
    node_type = str(node["type"])

    # 1. PRIMARY: Try registry executor
    found, ports = self._try_registry_executor(node, game, dt)
    if found:
        return ports

    # 2. SECONDARY: Special runtime nodes
    if self._is_special_node(node_type):
        return self._execute_special(node, game, dt)

    # 3. ERROR: Unknown node type
    node_id = str(node.get("id", "unknown"))
    print(
        f"[LogicRuntime] ERROR: Unknown node type '{node_type}' "
        f"(id={node_id}). Node will be skipped."
    )
    return ["failure"]
```

---

## MIGRATION CHECKLIST

- [ ] Add `_try_registry_executor()` method
- [ ] Add `_is_special_node()` method
- [ ] Add `_execute_special()` method
- [ ] Refactor `_execute()` (delete 98 branches, replace with dispatcher)
- [ ] Ensure registry is imported and initialized
- [ ] Add error diagnostics to all paths
- [ ] Run all existing tests
- [ ] Verify no regressions
- [ ] Run smoke test (cross-system graph)
- [ ] Commit with message

---

## EXPECTED OUTCOMES

### Immediate (after refactoring)

✅ **Registry becomes canonical dispatcher**  
✅ **78 unreachable nodes become reachable**  
✅ **All existing tests pass**  
✅ **Error messages are clear**  
✅ **Code is ~10x simpler**  

### Enabled by Consolidation

✅ **Input nodes work** (Phase 7B.2 can implement)  
✅ **Camera nodes work** (Phase 7B.3 can implement)  
✅ **Audio nodes work** (Phase 7B.4 can implement)  
✅ **Save/Load works** (Phase 7B.5 can implement)  
✅ **Dialogs work** (Phase 7B.6 can implement)  
✅ **Particles work** (Phase 7B.7 can implement)  

---

## RISK ANALYSIS

### Low Risk

- **Special node logic preserved**: Subgraph/event nodes don't change
- **Executor signatures unchanged**: Registry executors already exist
- **Fallback error path**: Unknown nodes fail clearly instead of silently

### Medium Risk

- **All logic changes at once**: Single method refactor affects entire system
- **Mitigation**: Comprehensive regression testing before commit

### No Risk

- **Backward compatibility**: No API changes
- **External behavior**: Same inputs → same outputs
- **Data structure**: No change to node format

---

## TESTING STRATEGY

### Unit Tests (New File)

```python
# tests/integration/test_phase7b1_registry_dispatch.py

def test_registry_executor_called_for_known_node():
    """Verify registry executor is invoked for known nodes."""
    node = {"id": "1", "type": "set_position", "properties": {...}}
    result = runtime._execute(node, game, 0.016)
    assert result == ["next"]

def test_unknown_node_returns_failure():
    """Verify unknown nodes fail gracefully."""
    node = {"id": "1", "type": "nonexistent_node", "properties": {}}
    result = runtime._execute(node, game, 0.016)
    assert result == ["failure"]

def test_executor_exception_caught():
    """Verify executor exceptions don't crash."""
    # Mock executor that raises
    node = {"id": "1", "type": "set_position", ...}
    result = runtime._execute(node, game, 0.016)
    assert result == ["failure"]

def test_special_node_returns_empty():
    """Verify event nodes return empty port."""
    node = {"id": "1", "type": "on_animation_event", ...}
    result = runtime._execute(node, game, 0.016)
    assert result == []

def test_subgraph_execution_preserved():
    """Verify subgraph execution logic unchanged."""
    node = {"id": "1", "type": "call_subgraph", "properties": {"graph_id": "sub1"}}
    result = runtime._execute(node, game, 0.016)
    assert result == ["next"]
```

### Regression Tests

Run full test suite:
```bash
pytest tests/integration/test_phase*.py -v
```

Expected: All pass without modification.

### Smoke Test

Execute graph with multiple systems:
```
On Start
  ├─ Set Position (Transform)
  ├─ Play Animation (Animation)
  ├─ Set Variable (Variables)
  ├─ Apply Force (Physics)
  └─ Set UI Text (UI)

All nodes should execute via registry.
```

---

## COMMIT PLAN

**Branch**: feature/registry-dispatcher-consolidation  
**Commit message**:

```
Phase 7B.1: Logic Graph Registry Dispatcher Consolidation

Replace 98-branch hardcoded dispatcher with registry-based dispatch.

CHANGES:
- Add _try_registry_executor() helper
- Add _is_special_node() helper  
- Add _execute_special() helper
- Refactor _execute() to use registry as primary dispatcher

IMPACT:
- 78 unreachable nodes (59%) now reachable
- Code complexity reduced by ~10x
- Error handling improved
- All existing tests pass (0 regressions)

ENABLED:
- Input system now executable
- Camera system now executable
- Audio system now executable
- Save/Load system now executable
- Dialog system now executable
- Particle system now executable

BLOCKED: None
```

---

## SUCCESS CRITERIA (Phase 7B.1 Complete)

✅ Registry executors called in canonical path  
✅ 78 unreachable nodes have execution paths  
✅ Special nodes (subgraph, events) continue working  
✅ All existing tests pass  
✅ No new regressions  
✅ Error messages are clear  
✅ Code is simplified  
✅ Input/Camera/Audio/Audio/Save/Load/Particles/Dialogs nodes now reachable  

---

## NEXT STEPS

After Phase 7B.1 completes:
- Phase 7B.2: Implement Input system (keyboard, gamepad)
- Phase 7B.3: Implement Camera system (follow, shake, zoom)
- Phase 7B.4: Implement Audio system (play, stop, volume)
- Phase 7B.5: Implement Scene Loading (load_scene, change_scene)
- Phase 7B.6: Implement Save/Load system
- Phase 7B.7: Implement Dialogue system
- Phase 7B.8: Implement Particle system

Each will now execute via the consolidated registry dispatcher.
