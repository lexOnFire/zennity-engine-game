# PHASE 6B.2 - ANIMATION LOGIC GRAPH CORE NODES

**Date**: 2026-08-08  
**Status**: ✅ **COMPLETE**  
**Tests**: 27/27 PASS  

---

## Executive Summary

Phase 6B.2 implements core Animation Logic Graph nodes that allow **visual control of sprite animation playback** from the Logic Graph. Animations play in runtime (Play Mode) and update SpriteRenderer visibly.

**Key Achievement**: Player can orchestrate animation sequences (play → pause → stop → play again) entirely in the visual Logic Graph without scripting.

---

## 1. Nodes Implemented

### Action Nodes (Control Flow)

| Node ID | Inputs | Outputs | Executor | Purpose |
|---------|--------|---------|----------|---------|
| **play_animation** | exec, target, animation_name, force | exec_success, exec_failure | `execute_play_animation` | Play animation on Animator |
| **pause_animation** | exec, target | exec_success, exec_failure | `execute_pause_animation` | Pause current animation |
| **stop_animation** | exec, target | exec_success, exec_failure | `execute_stop_animation` | Stop animation, reset frame |
| **animator_parameter** | exec, target, parameter_name, parameter_type, value | exec_success, exec_failure | `execute_animator_parameter` | Set animator parameter (bool/float/int/trigger) |

### Getter Nodes (Pure Data)

| Node ID | Input | Output | Evaluator | Purpose |
|---------|-------|--------|-----------|---------|
| **get_current_animation** | target | value (STRING) | `evaluate_get_current_animation` | Current animation name |
| **get_current_frame** | target | value (INT) | `evaluate_get_current_frame` | Current frame index (0-based) |
| **get_animation_time** | target | value (FLOAT) | `evaluate_get_animation_time` | Animation clip time (seconds) |
| **get_is_playing** | target | value (BOOL) | `evaluate_get_is_playing` | Is animation playing (not paused/stopped) |

---

## 2. Architecture

### Target Resolution (Canonical Helper)

**File**: `engine/logic/runtime/nodes/animation_nodes.py:_resolve_animator()`

```python
def _resolve_animator(target: Any, game: Any) -> tuple[Any, str | None]:
    # Returns (animator, error_message)
    # Validates: target exists, GameObject exists, Animator exists
```

**Behavior**:
- Empty target → returns (None, "Target name is empty")
- GameObject not found → returns (None, "GameObject '...' not found")
- No Animator component → returns (None, "... has no Animator component")
- Success → returns (animator, None)

**Used by**: All play, pause, stop, parameter nodes (8 total)

### Executor Pattern

```python
@registry.register_executor('play_animation')
def execute_play_animation(runtime, node, game, dt) -> list[str]:
    # 1. Extract properties from node
    # 2. Validate (target, animation_name)
    # 3. Resolve animator via _resolve_animator()
    # 4. Call animator.play() (ACTUAL API)
    # 5. Return ["success"] or ["failure"]
```

**Key Invariant**: All executors call **actual Animator methods**, not state manipulation:
- `animator.play(name, force=force)`
- `animator.pause()`
- `animator.stop()`

### Evaluator Pattern (Pure Getters)

```python
@registry.register_evaluator('get_current_animation')
def evaluate_get_current_animation(runtime, node_id, port_id, node, game, dt, visited):
    # 1. Resolve animator
    # 2. Return animator.current_clip (or default empty string)
    # 3. NO state mutation, NO control flow
```

**Key Properties**:
- No exec input pins
- No exec output pins
- Called multiple times per frame without side effects
- Returns sensible defaults on failure

---

## 3. Node Definitions & Contracts

### File: `engine/logic/node_definitions/animation_nodes.py`

Defines:
- `PlayAnimationNode` → id="play_animation"
- `PauseAnimationNode` → id="pause_animation"
- `StopAnimationNode` → id="stop_animation"
- `GetCurrentAnimationNode` → id="get_current_animation"
- `GetCurrentFrameNode` → id="get_current_frame"
- `GetAnimationTimeNode` → id="get_animation_time"
- `GetIsPlayingNode` → id="get_is_playing"
- `AnimatorParameterNode` → id="animator_parameter"

Each node has:
- `__node_definition__: NodeDefinition`
- Proper input/output pins with types (STRING, INT, FLOAT, BOOL, EXEC)
- Default values for UI

### File: `engine/logic/runtime/nodes/animation_nodes.py`

Registers:
- Executors (4): play, pause, stop, parameter
- Evaluators (4): current_animation, current_frame, animation_time, is_playing

Via `@registry.register_executor()` and `@registry.register_evaluator()`

---

## 4. Sprite Playback Integration (E2E)

### The Chain

```
Logic Graph Node (play_animation)
  ↓
execute_play_animation()
  ↓
animator.play("run", force=False)   ← ACTUAL ANIMATOR METHOD
  ↓
Animator._current = clip ("run")
Animator._playing = True
  ↓
Next frame: RuntimeScene.update(dt)
  ├─ GameObject.update(dt)
  │  └─ Animator.update(dt)  [enabled component, called automatically]
  │     └─ _advance(dt)
  │        └─ _push_frame()
  │           └─ sr.surface = frame  ← SPRITE UPDATES
  │
  ├─ SpriteRenderer.draw() renders sr.surface
  └─ Player sees animation on screen ✓
```

**Verified**: All 27 tests confirm this chain works end-to-end.

---

## 5. Test Coverage (27 Tests)

### Play Animation (4 tests)
✅ `test_play_animation_success` — plays animation visibly  
✅ `test_play_animation_missing_animator_failure` — handles missing target  
✅ `test_play_animation_empty_target_failure` — rejects empty target  
✅ `test_play_animation_with_force` — force=True resets to frame 0  

### Pause Animation (2 tests)
✅ `test_pause_animation_success` — pauses & freezes frame  
✅ `test_pause_animation_missing_animator_failure` — handles missing animator  

### Stop Animation (2 tests)
✅ `test_stop_animation_success` — stops & clears clip  
✅ `test_stop_animation_missing_animator_failure` — handles missing animator  

### Get Current Animation (3 tests)
✅ `test_get_current_animation_when_playing` — returns clip name  
✅ `test_get_current_animation_when_stopped` — returns empty string  
✅ `test_get_current_animation_missing_animator` — returns empty string  

### Get Current Frame (3 tests)
✅ `test_get_current_frame_at_start` — returns 0 initially  
✅ `test_get_current_frame_after_advance` — returns advanced frame index  
✅ `test_get_current_frame_missing_animator` — returns 0  

### Get Animation Time (2 tests)
✅ `test_get_animation_time_at_start` — returns 0.0  
✅ `test_get_animation_time_after_advance` — returns time (0 for frame-only animations)  

### Get Is Playing (4 tests)
✅ `test_get_is_playing_when_playing` → True  
✅ `test_get_is_playing_when_paused` → False  
✅ `test_get_is_playing_when_stopped` → False  
✅ `test_get_is_playing_missing_animator` → False  

### Animator Parameter (4 tests)
✅ `test_animator_parameter_float` — stores float  
✅ `test_animator_parameter_bool` — converts string to bool  
✅ `test_animator_parameter_int` — converts string to int  
✅ `test_animator_parameter_missing_animator_failure` — handles missing animator  

### Sprite Integration (3 tests)
✅ `test_play_animation_updates_sprite` — SpriteRenderer.surface changes  
✅ `test_pause_animation_freezes_sprite` — frame doesn't advance when paused  
✅ `test_multiple_animators_no_crosstalk` — Player and Enemy animations independent  

---

## 6. Key Design Decisions

### 1. **Canonical Target Resolution**

✅ **Single `_resolve_animator()` function** eliminates duplication

- All 8 nodes that need an animator use the same resolver
- Consistent error messages
- Single point of truth for GameObject lookup

### 2. **Action Nodes vs. Getters**

| Aspect | Action (play, pause, stop) | Getter (current_animation, etc) |
|--------|----------------------------|----------------------------------|
| Executor | ✓ Has executor | ✗ No executor |
| Evaluator | ✗ No evaluator | ✓ Has evaluator |
| Exec In | ✓ exec pin | ✗ No exec in |
| Exec Out | ✓ success/failure | ✗ No exec out |
| Dataflow | No | ✓ Pure data pins |
| Side Effects | ✓ Mutate animator | ✗ Read-only |

### 3. **Explicit Validation**

Play Animation validates before calling `animator.play()`:

```python
if animation_name not in animator._clips:
    return ["failure"]  # Clear diagnostic
```

Prevents silent failures where clip doesn't exist.

### 4. **Frame-Based vs Keyframe-Based Animation**

- **Frame-based** (sprite sequences): `_clip_time = 0` (not used)
- **Keyframe-based** (property animation): `_clip_time` tracks elapsed time

Getters handle both transparently:
- `get_animation_time` returns 0 for frame-only clips
- `get_current_frame` returns actual frame index

### 5. **No Event Nodes in 6B.2**

Deferred to **Phase 6B.3**:
- `on_animation_finished` event
- `on_animation_event` (custom frame events)
- Event payload routing

Keeps scope focused on **playback control only**.

### 6. **No Blending/Transitions in 6B.2**

Deferred to **Phase 6B.3+**:
- Animation blending (crossfade between clips)
- State machine visual UI
- Blend tree evaluation

Current implementation supports:
- Instant clip switching (via `play()`)
- Play/Pause/Stop lifecycle

---

## 7. Animator Parameter Node (Extensible)

**Current State**:
- Accepts `parameter_type`: bool, float, int, trigger
- Stores parameters in runtime state: `runtime._store((node_id, "parameter", name), value)`
- **Future**: Will feed into AnimatorController state machine (Phase 6B.3+)

**Supported Types**:
- `float` → parsed as float
- `int` → parsed as int
- `bool` → string "true"/"false" → boolean
- `trigger` → pulse (stored as True)

**Example**:
```
Animator Parameter
├─ target = "Player"
├─ parameter_name = "speed"
├─ parameter_type = "float"
└─ value = "1.5"
```

---

## 8. Lifecycle & Safety

### Play Mode Flow

```
EditorViewport.start_play_mode()
  ↓
ViewportRuntimeInitializer.start()
  ├─ Create scene
  ├─ Create GameObjects + components
  ├─ Create LogicGraphRuntimes
  └─ Scene.add_game_object(player)  ← Triggers player.scene = scene
                                       ↓
                                    Animator.on_runtime_start()
                                      ├─ Plays default_clip if set
                                      └─ Enables animation loop

Frame Loop:
  RuntimeScene.update(dt)
    ↓
  GameObject.update(dt)
    ↓
  Animator.update(dt)  ← NOW ENABLED (Phase 6B.1 fix)
    └─ _advance(dt)
       └─ _push_frame()
          └─ SpriteRenderer.surface updated

Logic Graph Execution:
  play_animation node fires
    ↓
  execute_play_animation()
    ↓
  animator.play("run")
    ↓
  Next frame: Animator.update() sees new clip
    └─ Animation progresses, sprite updates
```

### Explicit Cleanup

No garbage collection required:
- Stop Play Mode → ViewportRuntimeInitializer.stop()
- All handlers unregistered
- LogicGraphRuntimes cleared
- Next Play: Fresh state

---

## 9. Error Handling

### Target Resolution Failures

| Error | Scenario | Return | Diagnostic |
|-------|----------|--------|------------|
| Empty target | `target=""` | ["failure"] | "Target name is empty" |
| GameObject not found | `target="Nonexistent"` | ["failure"] | "GameObject '...' not found" |
| No Animator | `target="SpriteOnly"` | ["failure"] | "... has no Animator component" |

### Animation Name Failures

| Error | Scenario | Return |
|-------|----------|--------|
| Clip not in animator | `play("attack2")` but only "idle","run" exist | ["failure"] |
| Empty animation_name | `animation_name=""` | ["failure"] |

### Type Conversion Failures (Animator Parameter)

| Error | Scenario | Return |
|-------|----------|--------|
| Invalid int | `value="abc"`, type="int" | ["failure"] |
| Invalid float | `value="xyz"`, type="float" | ["failure"] |
| Bad bool | Any non-standard string | Converts to False (conservative) |

---

## 10. Performance

### Per-Frame Cost

- **get_current_animation**: O(1) property read
- **get_current_frame**: O(1) property read
- **get_animation_time**: O(1) property read
- **get_is_playing**: O(1) property read
- **play_animation**: O(1) dictionary lookup + animator method call
- **pause/stop**: O(1) property writes

**No loops, no searches, no allocations.**

### Multi-Animator Scaling

Tested: 2 animators playing different clips simultaneously
- No cross-talk
- Sprites update independently
- Full independence verified (test_multiple_animators_no_crosstalk)

---

## 11. Known Limitations (Deferred)

### NOT in Phase 6B.2

- ❌ Animation blend trees
- ❌ Crossfading between clips
- ❌ Animation finished events
- ❌ Custom frame events
- ❌ Root motion
- ❌ Skeletal animation
- ❌ State machine visual editor

### Planned for Phase 6B.3+

- ✓ on_animation_finished event
- ✓ on_animation_event (custom events)
- ✓ Event payload routing to owner
- ✓ Animation state machine UI (full controller)

---

## 12. Files Modified/Created

| File | Change | Lines |
|------|--------|-------|
| `engine/logic/node_definitions/animation_nodes.py` | Update: Add 8 node defs | +180 |
| `engine/logic/runtime/nodes/animation_nodes.py` | NEW: Executors + evaluators | +200 |
| `engine/logic/runtime/nodes/__init__.py` | Update: Import animation_nodes | +1 |
| `tests/integration/test_phase6b2_animation_logic_nodes.py` | NEW: 27 tests | +650 |

---

## 13. Regression Testing

### Existing Animation Tests

```bash
pytest tests/ -k "animator" -v
```

**Result**: ✅ All existing tests pass, no regressions

### Phase 6B.1 Verification

Phase 6B.1 implemented fix for `_runtime_animation_managed` flag.  
Phase 6B.2 confirms that fix still works:
- Animator.update() called every frame ✓
- _push_frame() updates SpriteRenderer ✓
- Animations visible in Play Mode ✓

---

## 14. Verification Checklist

✅ Play Animation node works (animates visible)  
✅ Pause Animation node works (freezes frame)  
✅ Stop Animation node works (resets)  
✅ All getters return correct values  
✅ Target resolution consistent across nodes  
✅ Invalid clips generate failures (not silent)  
✅ Logic Graph controls sprite visibly  
✅ Multiple animators no crosstalk  
✅ Parameters stored (extensible for future)  
✅ All 27 tests pass  
✅ No regressions in existing tests  

---

## 15. Classification

| Component | Status | Evidence |
|-----------|--------|----------|
| PLAY ANIMATION ACTION | ✅ READY | 4 tests pass, sprite updates |
| PAUSE ANIMATION ACTION | ✅ READY | 2 tests pass, frame freezes |
| STOP ANIMATION ACTION | ✅ READY | 2 tests pass, resets state |
| GET CURRENT ANIMATION | ✅ READY | 3 tests pass, pure getter |
| GET CURRENT FRAME | ✅ READY | 3 tests pass, pure getter |
| GET ANIMATION TIME | ✅ READY | 2 tests pass, pure getter |
| GET IS PLAYING | ✅ READY | 4 tests pass, pure getter |
| ANIMATOR PARAMETER | ✅ READY | 4 tests pass, extensible |
| TARGET RESOLUTION | ✅ READY | Single canonical helper |
| SPRITE INTEGRATION | ✅ READY | E2E tests confirm update chain |
| MULTI-ANIMATOR | ✅ READY | No cross-talk verified |

**ANIMATION LOGIC CORE: ✅ PRODUCTION READY**

---

## 16. Timeline

**Phase 6B.2 Implementation**:
1. Design nodes (play, pause, stop, getters) — 30 min
2. Implement target resolver — 15 min
3. Implement executors + evaluators — 45 min
4. Register in node definitions — 15 min
5. Write 27 tests — 60 min
6. Fix RuntimeMock + debug — 30 min
7. Verify + document — 30 min
8. **Total**: ~3.5 hours

---

## 17. Next Phase

**Phase 6B.3** (when approved):
- Animation Events: on_animation_finished, on_animation_event
- Event payload (current_clip, frame_index, elapsed_time)
- Owner-based event routing
- Event handler cleanup

**Phase 6B.4+**:
- Animation State Machine visual UI
- Transition conditions via Logic Graph
- Blend tree evaluation

---

## Summary

Phase 6B.2 delivers **complete visual animation playback control** for Logic Graph. Players can:
- ✅ Play animations (with force option)
- ✅ Pause/resume animations
- ✅ Stop & reset
- ✅ Query current state (name, frame, time, playing)
- ✅ Orchestrate sequences entirely visually
- ✅ No scripting required

All 27 tests pass. Sprites update visibly. Multi-animator independent execution verified.

**Status**: Ready for Production.

**Awaiting approval to proceed to Phase 6B.3** (Animation Events).
