# PHASE 5B.2: Physics Collision/Trigger Event Nodes

**Data**: 2026-08-08  
**Status**: 🟡 **IN PROGRESS** - Phase 5B.2.1 (Event Dispatch Audit) Complete
**Phase**: Enabling 100% visual collision/trigger gameplay

---

## PHASE 5B.2.1: EVENT DISPATCH AUDIT — COMPLETE

### Architecture Overview

**Event Flow Chain**:
```
PhysicsWorld._emit_collision_enter()
    ↓
script_runtime.notify_game_object_event(obj, "on_collision_enter", other)
    ↓
ScriptRuntime.notify_game_object_event()
    ├─ Find script instances for game_object
    ├─ Call instance.behaviour.on_collision_enter(other)
    └─ [NEW] Dispatch to Logic Graph event bus
        ↓
        LogicGraphRuntime.event_bus.publish("collision_enter", payload)
        ↓
        All subscribed event_custom nodes receive event
```

### Existing Event System (event_custom)

**Node Definition**:
```python
"event_custom": {
    "id": "event_custom",
    "title": "Custom Event",
    "category": "Events",
    "inputs": [],                                    # No exec input
    "outputs": [("next", "flow"), ("payload", "any")]  # Flow + data
}
```

**LogicGraphRuntime initialization**:
```python
def __init__(self, graph, blackboard=None, ...):
    self.event_bus = event_bus or LogicEventBus()  # Central bus
    
    # Subscribe all event_custom nodes to their named events
    for node in self.nodes.values():
        if node.get("type") != "event_custom":
            continue
        event_name = str(node.get("properties", {}).get("name", "event")).strip()
        node_id = str(node["id"])
        self.event_bus.subscribe(event_name, 
            lambda event, wanted=node_id: self._receive_custom_event(wanted, event))
```

**Event Reception**:
```python
def _receive_custom_event(self, node_id: str, event: LogicEvent) -> None:
    # Trigger node execution with event payload
```

### How to Reuse

Collision events should:
1. ✅ Use the same `LogicEventBus` infrastructure
2. ✅ Dispatch with event names like "collision_enter", "collision_exit", etc.
3. ✅ Use `LogicEvent` payload structure
4. ✅ Create corresponding event_custom nodes (or dedicated collision event nodes)
5. ✅ No parallel dispatcher needed

### Integration Point

**In ScriptRuntime.notify_game_object_event()**:
```python
def notify_game_object_event(self, game_object, method_name, other):
    # Existing: notify scripts
    for instance in list(self.instances.values()):
        if instance.behaviour.game_object is not game_object:
            continue
        method = getattr(instance.behaviour, method_name, None)
        if method is None:
            continue
        try:
            method(other)
    
    # NEW: Dispatch to Logic Graph event bus
    if method_name in ("on_collision_enter", "on_collision_exit", "on_trigger_enter", "on_trigger_exit"):
        event_name = method_name.replace("on_", "")  # "collision_enter"
        payload = LogicEvent(event_name, {"other_object": other, ...})
        self._dispatch_to_logic_graph(game_object, payload)
```

---

## PHASE 5B.2.2: EVENT PAYLOAD CANONICAL

### PhysicsEventPayload Structure

When a collision event fires on GameObject A:

```python
class PhysicsCollisionEventPayload:
    event_type: str                  # "collision_enter" | "collision_exit"
    self_object: GameObject          # A
    other_object: GameObject         # B
    self_collider: Collider          # A's collider
    other_collider: Collider         # B's collider
    is_trigger: bool                 # False for collisions, True for triggers
    timestamp: float                 # Frame when event fired
```

### Serialization for Logic Graph

Logic Graph outputs need JSON-serializable types:

```python
# Event dispatched to Logic Graph
{
    "event_name": "collision_enter",
    "self_object": {
        "id": "game_obj_id_1",
        "name": "Player",
        "ref": game_object_ref  # Direct Python reference, not JSON
    },
    "other_object": {
        "id": "game_obj_id_2",
        "name": "Enemy",
        "ref": other_game_object_ref
    },
    "is_trigger": False
}
```

### Node Payload Outputs

Event nodes expose:

```
On Collision Enter
├─ exec (EXEC pin)           → triggers execution
├─ self_object (OBJECT)      → A (implicit owner)
├─ other_object (OBJECT)     → B (data pin)
├─ self_collider (OBJECT)    → A's collider
└─ other_collider (OBJECT)   → B's collider
```

---

## STATUS: AUDIT COMPLETE

✅ Event dispatch infrastructure exists
✅ event_bus pattern ready to extend
✅ Reuse same LogicGraphRuntime
✅ No parallel dispatcher needed
✅ Integration point: ScriptRuntime.notify_game_object_event()

**Next Steps**:
- Phase 5B.2.3: Define 4 event nodes (collision enter/exit, trigger enter/exit)
- Phase 5B.2.4: Wire PhysicsWorld → event dispatch
- Phase 5B.2.5-17: Implementation, testing, E2E

---

**Status**: 🟢 Ready for Phase 5B.2.3 (Node Definitions)
