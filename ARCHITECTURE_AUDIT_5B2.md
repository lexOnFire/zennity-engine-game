# Architecture Audit: Phase 5B.2 Event System

**Date**: 2026-08-08  
**Scope**: Physics event dispatch vs LogicEventBus vs Custom events  
**Goal**: Validate unified vs parallel event architecture  

---

## 1. COMPARATIVE ANALYSIS

### LogicEventBus (existing, custom events)

**Location**: `engine/logic/event_bus.py`

```python
class LogicEventBus:
    _queue: deque[LogicEvent]          # ✅ Queueing
    _dispatching: bool                 # ✅ Reentrancy protection
    _subscribers: dict[name, callbacks] # ✅ Dedup
    recent: list[events]               # ✅ Event history
    MAX_EVENTS_PER_DISPATCH = 128      # ✅ Deadletter limit
    
    def subscribe(name, callback)      # ✅ Registrar
    def emit(name, payload, source)    # ✅ Enqueue
    def dispatch()                     # ✅ Flush queue
```

**Characteristics**:
- **Ownership**: Per-runtime (each LogicGraphRuntime has one)
- **Lifetime**: Tied to LogicGraphRuntime
- **Subscription**: Registered per event name (casefold)
- **Unsubscribe**: Manual removal (never implemented)
- **Event Format**: LogicEvent(name, payload, source)
- **Reentrancy**: Protected by _dispatching flag
- **Cleanup**: None (subscribers leak)

### physics_event_dispatch (new, Phase 5B.2)

**Location**: `engine/logic/physics_event_dispatch.py`

```python
_physics_event_handlers: list[Callable]    # ❌ Global list
                                           # ❌ No queueing
                                           # ❌ No reentrancy protection
                                           # ❌ No dedup
                                           # ❌ No event history
                                           # ❌ No deadletter limit

def register_physics_event_handler(cb)     # Direct append
def dispatch_physics_event(obj, method, c) # Synchronous iteration
```

**Characteristics**:
- **Ownership**: Global registry
- **Lifetime**: Manual (register/unregister)
- **Subscription**: Callback list (no namespace)
- **Unsubscribe**: Manual removal required
- **Event Format**: (game_object, method_name, collider)
- **Reentrancy**: UNPROTECTED
- **Cleanup**: Manual unregister (error-prone)

---

## 2. DIVERGENCE MATRIX

| Aspect | LogicEventBus | physics_event_dispatch |
|--------|---------------|------------------------|
| Ownership | Per-runtime | Global |
| Queueing | ✅ Yes | ❌ No |
| Reentrancy Protected | ✅ Yes | ❌ No |
| Dedup Subscriptions | ✅ Yes | ❌ No |
| Event History | ✅ Yes | ❌ No |
| Deadletter Limit | ✅ Yes (128) | ❌ No |
| Event Format | LogicEvent | Tuple (obj, str, collider) |
| Cleanup | ⚠️ Manual | ⚠️ Manual |
| Lifecycle | Runtime-tied | Manual register/unregister |

**VERDICT: PARALLEL REGISTRIES** ❌

physics_event_dispatch is NOT an adapter over LogicEventBus.
It is an independent, unprotected global registry.

---

## 3. RISK ANALYSIS

### 3.1 Reentrancy Risk

**Scenario**: Physics event triggers graph that modifies physics

```
Frame N:
  PhysicsWorld.detect_collisions()
    ├─ _emit_collision_enter(A, B)
    │   ├─ dispatch_physics_event(A, "on_collision_enter", B)
    │   │   ├─ RuntimeA._handle_physics_event()
    │   │   │   ├─ Executes graph
    │   │   │   │   ├─ [Destroy B] ← PHYSICS CHANGE
    │   │   │   │   └─ PhysicsWorld.unregister_collider(B)
    │   │   │   │       ├─ Removes B from world
    │   │   │   │       └─ Clears contacts with B
    │   │   │   └─ Returns from _handle_physics_event
    │   │   └─ continue with RuntimeB handler
    │   │       ├─ RuntimeB._handle_physics_event() ← B DESTROYED
    │   │       └─ B.game_object is gone
    │   │
    │   └─ _notify_game_object(B, ...) ← B IS DEAD
    │
    └─ Continue iterating contacts
```

**Status**: Potentially unsafe - no protection
**Mitigation**: Handler catches exceptions (line 36: `except Exception: pass`)
**But**: Executor might crash before catching, leaving graph in bad state

### 3.2 Lifecycle Risk

**Scenario**: Play/Stop/Play without cleanup

```
Play 1:
  LogicGraphRuntime(player_graph)
    └─ register_physics_event_handler(self._handle_physics_event)
       └─ _physics_event_handlers = [handler_1]

Stop:
  LogicGraphRuntime destroyed
  _physics_event_handlers still = [handler_1] ← ORPHANED
  handler_1.__self__ is dead

Play 2:
  LogicGraphRuntime(player_graph)
    └─ register_physics_event_handler(self._handle_physics_event)
       └─ _physics_event_handlers = [handler_1_orphan, handler_2]
       
Physics event fires:
  dispatch_physics_event()
    └─ for handler in [handler_1_orphan, handler_2]:
       ├─ handler_1_orphan(obj, method, collider)  ← CALLS DEAD OBJECT
       │   └─ self._handle_physics_event() ← AttributeError
       │       └─ except Exception: pass (swallows error)
       └─ handler_2(obj, method, collider) ← OK
```

**Status**: Cleanup is BROKEN
**Impact**: Orphaned handlers accumulate, errors swallowed

### 3.3 Consistency Risk

**Different event systems have different semantics**:

```
Custom Events:
  emit("damage", {"amount": 10})
    ├─ Enqueued
    ├─ Dispatched in controlled order
    ├─ Reentrancy protected
    └─ Only subscribers receive

Physics Events:
  dispatch_physics_event(player, "on_collision", enemy)
    ├─ Synchronous
    ├─ All handlers called immediately
    ├─ Reentrancy NOT protected
    └─ Every handler receives
```

Future events (Animation, Input) will have their own patterns, fragmenting the system.

---

## 4. CURRENT CLEANUP AUDIT

### Play/Stop/Play Test

Created test case to verify cleanup:

```python
# Test in test_phase5b2_physics_event_nodes.py
class TestSubscriptionCleanup:
    def test_handler_registration_and_unregistration(self):
        def handler1(obj, method, collider): pass
        def handler2(obj, method, collider): pass

        register_physics_event_handler(handler1)
        register_physics_event_handler(handler2)
        assert len(_physics_event_handlers) == 2

        unregister_physics_event_handler(handler1)
        assert len(_physics_event_handlers) == 1

        unregister_physics_event_handler(handler2)
        assert len(_physics_event_handlers) == 0  ✅ PASS
```

**Finding**: Manual unregister works IF called.
**Problem**: LogicGraphRuntime never calls it on destruction.

### Missing: Automatic Cleanup on Stop

LogicGraphRuntime has no destructor or stop() method.
When scene stops or runtime is deleted, handlers remain.

```python
# engine/logic/runtime/core.py
class LogicGraphRuntime:
    def __init__(...):
        if not self.call_stack:
            register_physics_event_handler(self._handle_physics_event)  ✓
        # NO cleanup/destructor!
```

---

## 5. REENTRANCY TEST RESULTS

**Test Case**: Collision triggers graph that destroys object

```python
# Simulated in test
collision_enter → graph executes → [Destroy B] → physics state changes
```

**Result**: Exception swallowed, handler continues
**Why it works**: Physics world is already iterating; destruction queued for later cleanup
**Risk**: If destroy happens DURING iteration, iterator gets invalidated

**No crash observed because**:
1. destroy() is queued (doesn't happen immediately)
2. exceptions are caught
3. Physics world finishes iteration before cleanup

**But this is FRAGILE**.

---

## 6. OWNER ROUTING AUDIT

Current implementation:
```python
def _handle_physics_event(self, game_object, method_name, other_collider):
    owner_name = getattr(game_object, "name", None)
    if owner_name != self.object_key:
        return  # ✅ Owner check
```

**Finding**: Owner routing is CORRECT
**Mechanism**: Each handler checks if game_object.name == its own object_key
**Guarantee**: Only matching graph executes

**Example verification** (from tests):
```python
Player collision → 
  Player handler checks: "player" == "player" ✓ EXECUTES
  Enemy handler checks: "enemy" == "player" ✗ IGNORES
```

✅ **Owner routing is safe and working**

---

## CONSOLIDATED VERDICT

### Architecture Classification

**PARALLEL REGISTRIES - NOT UNIFIED**

Two independent event systems coexist:

```
LogicEventBus:
  - Queued
  - Reentrancy protected
  - Per-runtime
  - For custom events

physics_event_dispatch:
  - Synchronous
  - No reentrancy protection
  - Global registry
  - For physics events
```

### Risk Summary

| Issue | Severity | Current Status |
|-------|----------|-----------------|
| Reentrancy | ⚠️ Medium | Handled by exception swallowing (fragile) |
| Cleanup (Stop) | ⚠️ Medium | BROKEN - no automatic unregister |
| Lifecycle | ⚠️ Medium | Manual register/unregister required |
| Consistency | ⚠️ Low | Works, but two different patterns |
| Owner routing | ✅ Safe | Works correctly |
| Payload fidelity | ✅ Safe | Rich data preserved |

### Test Coverage

**12/12 Phase 5B.2 tests PASS** ✓
**22/22 Phase 5B.1 regression tests PASS** ✓

Tests do NOT cover:
- ❌ Orphaned handler accumulation (Play/Stop/Play)
- ❌ Reentrancy with real physics mutations
- ❌ Memory leaks from handler retention

---

## RECOMMENDATION

### Immediate: Fix Critical Cleanup Issue

Add automatic unregister on LogicGraphRuntime destruction:

```python
# engine/logic/runtime/core.py
class LogicGraphRuntime:
    def __init__(...):
        if not self.call_stack:
            register_physics_event_handler(self._handle_physics_event)
            self._registered_physics_handler = True
    
    def __del__(self):
        if hasattr(self, '_registered_physics_handler') and self._registered_physics_handler:
            unregister_physics_event_handler(self._handle_physics_event)
```

OR provide explicit cleanup:

```python
def stop(self):
    if not self.call_stack and hasattr(self, '_registered_physics_handler'):
        unregister_physics_event_handler(self._handle_physics_event)
```

### Future: Consolidate to Single Event Bus

After Phase 5B.3 (Raycast), consider:

```python
# Option: Unified event topic system
class LogicEventBus:
    def emit(self, name: str, payload: Any, source: str, topic: str = "custom"):
        # topic: "physics", "input", "animation", "custom"
        # All events queued, same reentrancy protection
        # Payload wrapped: LogicEvent(topic:name, payload, source)
```

This would converge all event types to single infrastructure.

---

## CLOSURE

**EVENT ARCHITECTURE: PARALLEL REGISTRIES FOUND**

- LogicEventBus is unified and safe
- physics_event_dispatch is parallel and manual
- Owner routing works correctly
- Payload is rich and preserved
- **CRITICAL**: Cleanup is broken (no automatic unregister)

**Recommendation**: Fix cleanup issue before Phase 5B.3.
Tests still pass because scenarios don't stress Play/Stop/Play lifecycle.

