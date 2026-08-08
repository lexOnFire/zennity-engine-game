# PHASE 3: Implementation Plan (3C-3H)

## Current Status
- ✓ Phase 3A: Evaluator is correct (test artifact eliminated)
- ✓ Phase 3B: Canonical contract = PURE DATA NODE
- ⏳ Phase 3C: Migration (não editar assets manualmente)
- ⏳ Phase 3D: Consolidate NODE_DEFINITIONS
- ⏳ Phase 3E: Dual flow output (proibir return multiple)
- ⏳ Phase 3F: ProgressBar real path (verificar cadeia)
- ⏳ Phase 3G: UIRuntimeService (API central)
- ⏳ Phase 3H: Mandatory tests (8 testes obrigatórios)

---

## Phase 3C: Migration (Não editar assets manualmente)

### Problema
Hoje: Editar `.zlogic` manualmente de `in` → `exec`
Errado: Assets legados não funcionam
Certo: Criar migration automática

### Solução

#### Step 1: Define Legacy Aliases
```python
# engine/logic/runtime/nodes/legacy_migration.py

LEGACY_PORT_ALIASES = {
    "get_progress_bar_value": {
        "inputs": {
            "in": "widget_name",  # Legacy "in" → dataflow "widget_name"
        },
        "outputs": {
            "next": None,  # Remove legacy flow ports
            "exec_success": None,
            "exec_not_found": None,
            "exec_failure": None,
        },
    },
    # Add other nodes as needed
}

def migrate_edge_ports(edge: dict, node_type: str) -> dict:
    """Convert legacy edge ports to canonical form."""
    if node_type not in LEGACY_PORT_ALIASES:
        return edge
    
    aliases = LEGACY_PORT_ALIASES[node_type]
    
    # Migrate from_port (source node output)
    from_port = edge.get("from_port", "")
    if from_port in aliases.get("outputs", {}):
        new_port = aliases["outputs"][from_port]
        if new_port:
            edge = {**edge, "from_port": new_port}
        # else: remove edge (None means port no longer exists)
    
    # Migrate to_port (target node input)
    to_port = edge.get("to_port", "")
    if to_port in aliases.get("inputs", {}):
        new_port = aliases["inputs"][to_port]
        if new_port:
            edge = {**edge, "to_port": new_port}
    
    return edge
```

#### Step 2: Integrate in Graph Loader
```python
# engine/logic/runtime/graph_loader.py (hypothetical)

def load_logic_graph(graph_data: dict) -> dict:
    """Load and migrate graph to canonical form."""
    
    # Build node type map
    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    
    # Migrate edges
    edges = []
    for edge in graph_data.get("edges", []):
        to_node_id = edge.get("to_node")
        to_node = nodes.get(to_node_id, {})
        node_type = to_node.get("type", "")
        
        # Apply migration
        edge = migrate_edge_ports(edge, node_type)
        
        # Filter out removed edges (None ports)
        if edge.get("to_port") and edge.get("from_port"):
            edges.append(edge)
    
    # Return migrated graph
    return {
        **graph_data,
        "edges": edges,
    }
```

#### Step 3: Auto-Save Migrated Format
```python
# When saving graph after load, use canonical format only

def save_logic_graph(graph: dict, path: str):
    """Save graph in canonical format (never legacy)."""
    
    # At this point, graph is already migrated
    # Just save it
    with open(path, 'w') as f:
        json.dump(graph, f, indent=2)
    
    # No legacy ports in saved file
```

#### Step 4: Tests for Migration
```python
def test_migrate_legacy_edge_in_to_widget_name():
    """Legacy 'in' port should migrate to dataflow."""
    edge = {
        "from_node": "event_update",
        "from_port": "next",
        "to_node": "get_pb_value",
        "to_port": "in",
        "kind": "flow",
    }
    
    migrated = migrate_edge_ports(edge, "get_progress_bar_value")
    
    # Should convert to dataflow
    assert migrated["to_port"] == "widget_name"
    assert migrated["kind"] == "data"  # or stay "flow"? depends on design

def test_legacy_flow_outputs_removed():
    """Legacy 'next' port should be removed from outputs."""
    edge = {
        "from_node": "get_pb_value",
        "from_port": "next",  # Legacy flow output
        "to_node": "set_hud",
        "to_port": "in",
    }
    
    migrated = migrate_edge_ports(edge, "get_progress_bar_value")
    
    # Should be removed (no successor)
    assert migrated["from_port"] is None or filtered out
```

---

## Phase 3D: Consolidate NODE_DEFINITIONS

### Problema
Hoje: NODE_DEFINITIONS + class-based definitions = confusão
Solução: NODE_DEFINITIONS gerado automaticamente

### Implementação

#### Step 1: Register all canonical definitions
```python
# engine/logic/node_definitions/__init__.py

from engine.logic.node_definitions.ui_nodes import GetProgressBarValueNode_def
from engine.logic.node_definitions.ui_binding_nodes import BindUIToVariableNode_def
# ... import all canonical definitions

CANONICAL_DEFINITIONS = {
    GetProgressBarValueNode_def.id: GetProgressBarValueNode_def,
    BindUIToVariableNode_def.id: BindUIToVariableNode_def,
    # ...
}
```

#### Step 2: Generate legacy NODE_DEFINITIONS
```python
def build_legacy_node_definitions(canonical: dict) -> dict:
    """Generate legacy NODE_DEFINITIONS from canonical definitions."""
    
    legacy_nodes = {}
    
    for node_id, node_def in canonical.items():
        legacy_nodes[node_id] = {
            "id": node_id,
            "title": node_def.title_key,
            "category": node_def.category_key,
            "inputs": [
                (pin.id, pin.pin_type.value)
                for pin in node_def.inputs
            ],
            "outputs": [
                (pin.id, pin.pin_type.value)
                for pin in node_def.outputs
            ],
            "properties": {
                pin.id: pin.default_value
                for pin in node_def.inputs
                if pin.default_value is not None
            },
        }
    
    return legacy_nodes

# Build at startup
NODE_DEFINITIONS = build_legacy_node_definitions(CANONICAL_DEFINITIONS)
```

#### Step 3: Mark legacy NODE_DEFINITIONS as read-only
```python
# Prevent manual edits
NODE_DEFINITIONS.update = lambda *args, **kwargs: (
    raise RuntimeError("NODE_DEFINITIONS is auto-generated. Edit canonical definitions instead.")
)
```

---

## Phase 3E: Dual Flow Output Prohibition

### Implementação

#### Step 1: Update get_progress_bar_value executor
```python
@registry.register_executor('get_progress_bar_value')
def execute_get_progress_bar_value(runtime, node, game, dt):
    """Pure data node - no executor needed."""
    # Do nothing
    return []  # No outputs (pure node has no flow)

# Or unregister entirely:
# (Don't register executor for pure data nodes)
```

#### Step 2: Validate single output per node
```python
def validate_executor_outputs(node_type: str, outputs: list[str]):
    """Ensure executor returns only valid single output."""
    
    if not outputs:
        return  # Pure node
    
    if len(outputs) > 1:
        raise RuntimeError(
            f"Node {node_type} returned multiple outputs: {outputs}. "
            f"Executor must return exactly one output port."
        )

# In core.py _execute():
next_ports = executor(self, node, game, dt)
validate_executor_outputs(node_type, next_ports)
```

#### Step 3: Test for single branch execution
```python
def test_executor_returns_single_output():
    """Executor must return list with 0 or 1 element."""
    
    # Pure node
    result = execute_get_progress_bar_value(...)
    assert result == []
    
    # Impure node returns one
    result = execute_some_action(...)
    assert len(result) == 1
```

---

## Phase 3F: ProgressBar Real Path (Verificar cadeia)

### Rastrear completo:

```
[1] UI Builder
    ├─ User creates ProgressBar widget
    ├─ Sets: name="comida", value=75.0, max_value=100.0
    └─ Saves to ???

[2] Serialization
    ├─ Format: ???
    ├─ Location: ???
    └─ Structure: ???

[3] .zscene / .zui file
    ├─ Contents: ???
    └─ ProgressBar represented as: ???

[4] Play Mode Load
    ├─ Deserializer reads: ???
    └─ Creates runtime object: ???

[5] Hydration
    ├─ Populates: game._world[???]
    ├─ Or: UIRuntimeService.widgets[???]
    └─ Reference: ???

[6] Logic Graph Access
    ├─ evaluate_get_progress_bar_value called
    ├─ Searches in: game._world, game.objects, runtime.variables
    └─ Finds: class ProgressBar? dict? component?

[7] Value Read
    ├─ widget.value accessed
    ├─ Type: float? int? property?
    └─ Result: 75.0 ✓
```

### Investigation required:

1. Where is "comida" ProgressBar created in real game?
2. How is it serialized?
3. Where does it live at runtime?
4. How does Logic Graph find it?

---

## Phase 3G: UIRuntimeService (API Central)

### Criar service:

```python
class UIRuntimeService(IService):
    """Central service for UI widget access."""
    
    def __init__(self):
        self._widgets: dict[str, Any] = {}
    
    def register_widget(self, identifier: str, widget: Any):
        """Register a widget for Logic Graph access."""
        self._widgets[identifier] = widget
    
    def resolve_widget(self, identifier: str) -> Any | None:
        """Resolve widget by identifier."""
        return self._widgets.get(identifier)
    
    def get_property(self, widget_id: str, property_name: str) -> Any:
        """Get widget property."""
        widget = self.resolve_widget(widget_id)
        if widget is None:
            return None
        return getattr(widget, property_name, None)
    
    def set_property(self, widget_id: str, property_name: str, value: Any):
        """Set widget property."""
        widget = self.resolve_widget(widget_id)
        if widget is None:
            return
        setattr(widget, property_name, value)
```

### Update get_progress_bar_value to use service:

```python
def evaluate_get_progress_bar_value(runtime, node_id, port, node, game, dt, resolving):
    """Use UIRuntimeService instead of heuristic search."""
    
    widget_name = runtime._read_input(node_id, "widget_name", "progress", game, dt, resolving)
    
    # Get service
    context = EngineContext.current()
    ui_service = context.services.get(UIRuntimeService)
    
    # Resolve and get property
    if ui_service:
        value = ui_service.get_property(widget_name, "value")
    else:
        # Fallback to old heuristic (for backward compat)
        value = _fetch_progress_bar_value(runtime, widget_name, game)
    
    return value
```

---

## Phase 3H: Mandatory Tests (8 obrigatórios)

```python
test_1_pure_evaluator()           # ProgressBar.value without flow
test_2_connected_dataflow()        # Value → Compare Number
test_3_legacy_asset_migration()    # Old ports → new ports
test_4_save_after_migration()      # No legacy ports in saved file
test_5_single_flow_branch()        # Only one branch executed
test_6_not_found()                 # None when widget not found
test_7_ui_builder_end_to_end()     # Real UI creation → Logic access
test_8_type_safety()               # Reject invalid objects
```

---

## Success Criteria Summary

All must pass:
- ✓ evaluator returns 75.0
- ✓ dataflow pipeline works
- ✓ legacy graphs load
- ✓ migrated to canonical format
- ✓ no dual output execution
- ✓ UIRuntimeService resolves widgets
- ✓ 8 mandatory tests pass
- ✓ no regressions

---

## Effort Estimate

- Phase 3C (Migration): 2 hours
- Phase 3D (Consolidate definitions): 1 hour
- Phase 3E (Dual output fix): 30 minutes
- Phase 3F (ProgressBar path investigation): 1 hour
- Phase 3G (UIRuntimeService): 1.5 hours
- Phase 3H (Tests + verification): 2 hours

**Total: ~8 hours** (can be done in parallel sections)

---

## Next: Begin Phase 3C Implementation
