# PHASE 7B.7.3: DIALOGUE PRODUCTION HARDENING - IN PROGRESS

**Status**: IMPLEMENTATION STARTED  
**Date**: 2026-08-08

---

## OBJECTIVES

8 refinements needed for Production Ready:

1. ✅ **Owner Routing Same-ID** - STARTED
2. ⏳ **Asset Choice Workflow** - TODO
3. ⏳ **Scene Cleanup** - TODO
4. ⏳ **Play/Stop/Play Reset** - TODO
5. ⏳ **Dialogue Event → LogicEventBus** - TODO
6. ⏳ **Old Test Migration** - TODO
7. ⏳ **Full Regression** - TODO
8. ⏳ **Success Criteria Validation** - TODO

---

## WORK IN PROGRESS

### 1. Owner Routing Same-ID - ✅ STARTED

**Change**: Composite key `(owner_id, session_id)` instead of single `session_id`

**Allows**:
```python
Guard:
  _sessions[("Guard", "talk")] = session
  
Merchant:
  _sessions[("Merchant", "talk")] = session
  
# Coexist independently
```

**Implementation Progress**:
- ✅ `DialogueManager.__init__()` updated
- ✅ `start_inline()` updated for composite key
- ⏳ `start_asset()` needs update
- ⏳ `get_state()` needs update
- ⏳ `choose()` needs update
- ⏳ `close()` needs update
- ⏳ All other methods need composite key support

**Commit**: Intermediate commit for start_inline() conversion

---

## TODO (Remaining Work)

### 2. Complete Composite Key Migration
Update remaining methods in DialogueManager:
- `start_asset()` - use composite key
- `get_state()` - accept composite key or owner_id+session_id
- `choose()` - use composite key
- `close()` - use composite key
- `_handle_dialogue_event()` - route via composite key
- All references to `_active_session_id`
- All references to `_owner_sessions`

### 3. Asset Choice Workflow
Validate complete flow:
```
.zdialogue loads
→ speech node
→ choice node available
→ manager.choose(owner_id, session_id, index)
→ DialogueSession.choose(index) executes
→ branches correctly
→ event fires
→ end node reached
```

### 4. Scene Cleanup
Implement hook in scene manager:
```python
on_scene_unload():
    manager = get_dialogue_manager()
    # Close all sessions (or only from this owner)
    # Clear pending choices
    # Clear owner mappings
    # Notify UI to hide panels
```

### 5. Play/Stop/Play Reset
Implement stop handler:
```python
def stop():
    manager = get_dialogue_manager()
    manager._sessions.clear()
    manager._active_session_id = None
    manager._owner_sessions.clear()
    manager._choice_callbacks.clear()
```

### 6. Dialogue Event Routing
Connect DialogueSession events to LogicEventBus:
```python
def _handle_dialogue_event(self, event_name, payload):
    from engine.logic.event_bus import LogicEventBus
    bus = LogicEventBus.get_instance()
    
    # Route event to owner's graph
    owner_id = self._find_owner_for_event()
    bus.emit(f"dialogue:{event_name}", payload)
```

### 7. Old Test Migration (Phase 7B.7)
Update tests to use DialogueManager:
- Remove expectations of `_dialogue_sessions` dict
- Use `DialogueManager.get_state()`
- Use `DialogueManager.choose()`
- Validate via `DialogueSession` type checking

### 8. Full Regression
Run complete test suite:
```
Phase 7B.1 - Registry
Phase 7B.2 - Input
Phase 7B.3 - Camera
Phase 7B.4 - Scenes
Phase 7B.5 - Save/Load
Phase 7B.6 - Audio
Phase 7B.7 - Old dialogue (migrated)
Phase 7B.7.1 - Consolidation validation
Phase 7B.7.2 - Architecture validation
Phase 7B.7.3 - Production hardening (this)

UI
Physics
Animation
Variables
Scene
Save/Load
Audio

Expected: 0 FAIL, 0 SKIP, 0 NEW REGRESSIONS
```

---

## Success Criteria

✅ COMPLETE WHEN:

- [  ] Owner routing: same dialog_id, different owners coexist
- [  ] Asset choice: DialogueSession.choose() works on loaded assets
- [  ] Scene cleanup: DialogueManager clears on unload
- [  ] Play/Stop/Play: Full reset on stop
- [  ] Event routing: Dialogue events reach correct Logic Graph owner
- [  ] Old tests: All Phase 7B.7 tests updated and PASS
- [  ] Regression: 0 FAIL across all phases
- [  ] Classification: PRODUCTION READY ✅

---

## Next Session

Continue from where we left off:
1. Complete composite key migration in all DialogueManager methods
2. Implement remaining 6 features
3. Full regression validation
4. Final acceptance

---

## Architecture (Unchanged)

```
PlayLogicAPI → DialogueManager → DialogueSession

Owner routing: composite key (owner_id, session_id)
Canonical state: DialogueSession only
No parallel dict systems
```

---

## Files Modified So Far

- `engine/dialogue/manager.py` - Composite key implementation (partial)

---

## Estimated Remaining Effort

Low-to-medium. All changes are additive/structural, no fundamental architecture rework.
The composite key change is surgical and contained to DialogueManager.
