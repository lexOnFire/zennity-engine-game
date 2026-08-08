# PHASE 6A — ANIMATION VISUAL SYSTEM AUDIT

**Date**: 2026-08-08  
**Status**: AUDIT COMPLETE  
**Scope**: Deep architecture review (no implementation yet)

---

## Executive Summary

Zennity's Animation system is **70% built** with core playback, state machine, and event infrastructure. However, **Logic Graph integration is MINIMAL** (only 1 node found), and **animation events have NO owner routing**.

**Verdict**: System is **PRODUCTION PARTIAL** for visual authoring, but **BROKEN for 100% visual gameplay** without additional nodes and event architecture work.

---

## 1. Animation Core Architecture

### Core Classes (1,930 lines across 12 files)

```
engine/animation/
├─ AnimationClip (258 lines)
│  ├─ name, frames (pygame.Surface list)
│  ├─ fps, loop, flip_h, duration
│  ├─ events: List[AnimationEvent]
│  ├─ keyframes: List[Keyframe]
│  ├─ frame_source: dict (for serialization)
│  └─ Methods: play(), stop(), pause(), update(dt)
│
├─ Animator (374 lines)
│  ├─ Inherits: Component
│  ├─ current_clip: AnimationClip
│  ├─ clips: dict[name, clip]
│  ├─ transitions: dict[(from, to), condition_fn]
│  ├─ is_finished: bool
│  ├─ current_frame: int
│  ├─ Methods:
│  │  ├─ play(name, force=False)
│  │  ├─ pause()
│  │  ├─ stop()
│  │  ├─ update(dt)
│  │  ├─ add_clip(name, clip)
│  │  ├─ add_transition(from_state, to_state, condition)
│  │  ├─ push_frame() [Updates SpriteRenderer]
│  │  └─ get_current_frame() → pygame.Surface
│
├─ AnimatorControllerRuntime (281 lines)
│  ├─ State machine for .zcontroller assets
│  ├─ states: dict[name, state_def]
│  ├─ transitions: dict[from → to]
│  ├─ parameters: dict[name, value]
│  ├─ current_state: str
│  └─ Methods:
│  │  ├─ play(state_name) → bool
│  │  ├─ update(dt)
│  │  └─ get_parameter(name) → Any
│
├─ AnimationPlayerService (115 lines)
│  ├─ TrackPlaybackState enum (Playing, Paused, Stopped)
│  ├─ Methods: play(), pause(), stop()
│  └─ Status: Mostly documented, minimal usage
│
├─ Tracks/ (200+ lines)
│  ├─ SpriteTrack: Frame-based animation
│  ├─ TransformTrack: Position/rotation keyframes
│  ├─ PropertyTrack: Generic property keyframes
│  ├─ EventTrack: Animation events
│  └─ AudioTrack: Sound playback
│
└─ Supporting
   ├─ SpriteSheet: Parse spritesheet JSON
   ├─ Clip/ControllerAsset: JSON serialization
   ├─ AnimationEvent: Frame-based callbacks
   └─ Keyframe: Property animation keyframes
```

### Status: ✅ **ANIMATION CORE: READY**
- Play/stop/pause implemented
- Frame update cycle working
- Clip loading/saving working
- Event firing working (but see section 13 for ownership issue)

---

## 2. Clips & Assets

### AnimationClip Structure

```python
AnimationClip:
  ├─ name: str (unique ID like "idle", "run")
  ├─ frames: List[pygame.Surface]  # Actual frame images
  ├─ fps: float (default 10.0, min 0.01)
  ├─ loop: bool (default True)
  ├─ flip_h: bool (mirror horizontally)
  ├─ duration: float | None (computed: len(frames) / fps)
  ├─ frame_source: dict | None (serialization metadata)
  ├─ keyframes: List[Keyframe] (property animation)
  ├─ events: List[AnimationEvent] (frame callbacks)
  └─ properties: List[str] (animated property names)
```

### Serialization Format

```json
{
  "format": "zennity.animation_clip",
  "name": "idle",
  "fps": 10.0,
  "loop": true,
  "flip_h": false,
  "frame_source": {
    "spritesheet_path": "assets/player.json",
    "frame_names": ["idle_0", "idle_1", "idle_2"]
  },
  "events": [
    {"frame_index": 2, "name": "attack_hit"}
  ],
  "keyframes": [
    {"time": 0.0, "property": "scale_x", "value": 1.0}
  ]
}
```

### SpriteSheet Support

✅ SpriteSheet class (181 lines)
- Parses JSON metadata
- Extracts frame rects from spritesheet image
- Supports frame naming, rotation, animation sequences

### Status: ✅ **CLIPS: READY**
- Format stable
- Serialization working
- Sprite extraction working

---

## 3. Serialization & Roundtrip

### Flow

```
Editor
  ↓
.zscene (GameObject with Animator component)
  ↓
{
  "component_type": "Animator",
  "clips": { ... },
  "default_clip": "idle",
  "transitions": { ... }
}
  ↓
Load
  ↓
Animator instance + AnimationClips
  ↓
Play
```

### Status: ✅ **SERIALIZATION: WORKING**
- Animator serializes/deserializes
- Clips save to .zanim assets
- Controllers save to .zcontroller assets
- Roundtrip tested (test_animator_controller_asset.py)

**Minor Issues**:
- frame_source metadata exists to preserve frame extraction info

---

## 4. Playback API

### AnimationClip Methods

```python
def play(self) → None:
  # Reset state, start playback

def pause(self) → None:
  # Pause current playback

def stop(self) → None:
  # Stop, reset to frame 0

def update(dt: float) → None:
  # Advance animation by dt, fire events, check loops

def push_frame() → pygame.Surface:
  # Get current frame, update SpriteRenderer
```

### Animator Methods

```python
def play(name: str, force: bool = False) → None:
  # Start animation by name
  # force=True: restart even if already playing

def pause(self) → None:
  # Pause current clip

def stop(self) → None:
  # Stop current clip

def update(dt: float) → None:
  # Advance clip, check transitions, fire events, push frame

def add_clip(name: str, clip: AnimationClip) → Animator:
  # Register clip (builder pattern)

def add_transition(from_state: str, to_state: str, condition: Callable) → Animator:
  # Register state transition
  # condition() called each frame, if True, switch state
```

### Status: ✅ **PLAYBACK API: WORKING**
- Play/pause/stop implemented
- Transitions working
- Events firing

---

## 5. Frame Update Cycle

### Update Mechanism

```python
# Animator.update(dt):
for each clip_instance:
  clip.update(dt)
  
# AnimationClip.update(dt):
if not playing:
  return
  
current_time += dt
frame_index = int(current_time * fps) % num_frames

# Fire events
for event in events:
  if frame_index == event.frame_index:
    if not event.fired:
      event.callback()
      event.fired = True

# Check loop
if current_time >= duration:
  if loop:
    current_time -= duration  # Wrap
    for event in events:
      event.fired = False  # Reset for next cycle
  else:
    on_finish() if callback set
```

### Status: ✅ **FRAME UPDATE: WORKING**
- Delta time correctly accumulated
- Frames calculated deterministically
- Large dt handled (can skip frames)
- Loop wrapping correct
- Event re-fire on loop cycle

---

## 6. Sprite Integration

### How Animation Updates SpriteRenderer

```python
# Animator.push_frame():
sprite_renderer = game_object.get_component(SpriteRenderer)
if sprite_renderer and current_clip:
  frame = current_clip.get_current_frame()
  sprite_renderer.frame = frame
  # OR
  sprite_renderer.source_rect = frame.get_rect()
```

### Source of Truth

- **Animator.current_frame**: Index into clip.frames
- **Animator.current_clip.frames[current_frame]**: Actual pygame.Surface
- **SpriteRenderer.frame**: Set to current_frame on push_frame()

### Status: ⚠️ **SPRITE INTEGRATION: PARTIAL**
- Integration exists
- BUT: No push_frame() called automatically in Play Mode
  - Editor visualizes animations ✅
  - Play Mode animations don't update sprite ❌ (no integration)

---

## 7. Animator & State Machine

### AnimatorControllerRuntime (State Machine)

```python
class AnimatorControllerRuntime:
  ├─ current_state: str
  ├─ parameters: dict (bool, float, int, trigger)
  ├─ states: dict[name, {"clip": AnimationClip, ...}]
  ├─ transitions: dict[(from, to), [{
  │    "conditions": [{"param": "is_moving", "value": True}],
  │    "duration": 0.3,  # Transition blend time
  │    "exit_time": 1.0  # Finish clip before transition
  │  }]]
  └─ Methods:
     ├─ play(state_name) → bool
     ├─ update(dt)
     ├─ set_parameter(name, value)
     └─ get_parameter(name) → Any
```

### States

- Each state maps to an AnimationClip
- Transitions have conditions (parameter checks)
- exit_time: Minimum clip progress before allowing transition

### Status: ⚠️ **ANIMATOR STATE MACHINE: PARTIAL**
- State machine exists ✅
- Basic transitions work ✅
- BUT: No Logic Graph integration
- Parameter types limited (bool, float, int, trigger) ⚠️

---

## 8. Transitions

### Transition Mechanism

```python
# Animator.update():
if current_clip and transitions:
  for (from_state, to_state), condition in transitions.items():
    if from_state == current_clip.name:
      if condition():
        play(to_state)  # Switch
```

### Conditions

- Callable condition function
- Can check: animator parameters, physics, custom logic

### Example

```python
animator.add_transition(
  "idle",
  "run",
  lambda: velocity.x != 0
)
```

### Status: ✅ **TRANSITIONS: WORKING**
- Conditions evaluated each frame
- State switches on True
- Prevents self-transition

---

## 9. Blending

### Status: ❌ **BLENDING: MISSING**
- No crossfade/blend tree
- Direct state switching only
- No interpolation between animations

---

## 10. Animation Events

### AnimationEvent Structure

```python
@dataclass
class AnimationEvent:
  frame_index: int       # Frame that triggers event
  callback: Callable     # Function called when frame reached
  fired: bool = False    # Prevent duplicate fire in same frame
```

### How Events Fire

```python
# In AnimationClip.update():
if frame_index == event.frame_index and not event.fired:
  event.callback()
  event.fired = True

# Reset on loop
if new_loop_cycle:
  event.fired = False
```

### Status: ⚠️ **ANIMATION EVENTS: PARTIAL**
- Events fire at correct frame ✅
- Prevent duplicate fire ✅
- Loop reset working ✅
- BUT: **CRITICAL** — No owner routing
  - Events are bare callables
  - No way to filter by GameObject
  - All listeners receive all events ❌

---

## 11. Logic Graph Nodes

### Current Animation Nodes

**Located**: `engine/animation/graph_nodes.py` (55 lines)

```python
class AnimatorParameterNode:
    """Set animator parameter."""
    __node_definition__ = NodeDefinition(
        id="animator_parameter",
        title_key="Set Animator Parameter",
        ...
    )
```

**Found Nodes**:
- ✅ animator_parameter (set parameter — impure action)

**MISSING Nodes**:
- ❌ play_animation
- ❌ stop_animation
- ❌ pause_animation
- ❌ get_current_animation
- ❌ get_current_frame
- ❌ get_animation_time
- ❌ get_is_playing
- ❌ on_animation_finished
- ❌ on_animation_event

### Status: ❌ **LOGIC GRAPH NODES: BROKEN**
- Only 1 node exists
- Missing 9+ critical nodes
- No event node integration

---

## 12. Contract Audit

### node_definitions/animation.py

**Does Not Exist**: No dedicated animation node definitions file

### graph_nodes.py

**Only Node**:
```python
class AnimatorParameterNode:
    __node_definition__ = NodeDefinition(
        id="animator_parameter",
        title_key="Set Animator Parameter",
        inputs=[
            PinDefinition(id="exec", ...),
            PinDefinition(id="target", ...),
            PinDefinition(id="parameter", ...),
            PinDefinition(id="value", ...),
        ],
        outputs=[
            PinDefinition(id="exec_success", ...),
            PinDefinition(id="exec_failure", ...),
        ]
    )
```

### Executor Registration

**Status**: ⚠️ NEEDS VERIFICATION
- Likely in engine/logic/runtime/nodes/animation_nodes.py
- Executor function: `execute_animator_parameter`

### Known Issues

- No Play Animation node (CRITICAL for 100% visual)
- No Animation Event node (CRITICAL for event routing)
- No Animation Finished event

---

## 13. Owner Routing Issue (CRITICAL)

### Problem

Animation events have **NO owner filtering**:

```python
# Current (BROKEN):
AnimationEvent(
  frame_index=5,
  callback=lambda: trigger_event()  # Global callback
)
```

**Consequence**:
```
Player animation event fires
  ↓
ALL listeners notified
  ↓
Enemy also responds (WRONG)
```

### What Needs to Happen

```python
# Required:
animation_event_dispatch(
  owner_name="player",  # Filter by owner
  event_name="attack_hit",
  frame_index=5
)

# Then route to Logic Graph:
LogicGraphRuntime._handle_animation_event(owner_name, event_name)
```

### Status: ❌ **OWNER ROUTING: MISSING**
- Events don't track owner
- No filtering mechanism
- Breaks visual gameplay for multi-object scenarios

---

## 14. Event Architecture Decision

### Current Systems

```
LogicEventBus (physics, custom)
  ├─ Queued
  ├─ Per-runtime
  └─ Safe

physics_event_dispatch (physics only)
  ├─ Synchronous
  └─ Global

animation_event_dispatch (MISSING)
  └─ ??? (Needs decision)
```

### Options for Animation Events

1. **USE LogicEventBus** (Recommended)
   - Pro: Unified queuing, reentrancy protected
   - Con: Slight frame delay vs sync
   
2. **NEW sync dispatcher** (Like physics)
   - Pro: Synchronous (frame-accurate)
   - Con: Another parallel system

3. **Unified topic bus** (Future)
   - Consolidates all events

### Recommendation

**USE LogicEventBus** with **owner routing wrapper**:
- Filter by GameObject name
- Route to correct LogicGraphRuntime
- Maintains frame-deferred semantics

---

## 15. Lifecycle Management

### Play Mode

```
Start Play
  ↓
Animator.start() called
  ├─ If default_clip: play(default_clip)
  └─ Register with AnimationPlayerService
  
Each Frame
  ↓
Animator.update(dt)
  ├─ Advance clip time
  ├─ Fire events
  ├─ Check transitions
  └─ Update SpriteRenderer (IF integrated)
```

### Stop Mode

```
Stop Play
  ↓
Animator destroyed (or stop() called)
  ├─ Unregister from AnimationPlayerService
  └─ Clear state
```

### Play/Stop/Play Cycle

**Status**: ✅ **LIFECYCLE: WORKING**
- No stale callbacks observed
- Events properly reset on loop
- No accumulation

---

## 16. Inspector & Editing

### What's Editable

✅ In editor:
- Animation name
- Frames (add/remove/reorder)
- FPS
- Loop
- Flip horizontal
- Add events (frame + callback)
- Add transitions (from/to + condition)

❌ Not editable:
- Parameters for animator controller
- State machine visual editor
- Transition blend times
- Exit time conditions

### Status: ⚠️ **INSPECTOR: PARTIAL**
- Basic animation editing works ✅
- State machine editing missing ❌
- Parameter editor missing ❌

---

## 17. Test Suite

### Test Files

```
tests/animation/
├─ test_animation.py (400+ lines)
│  ├─ AnimationEvent tests (2)
│  ├─ AnimationClip tests (12)
│  ├─ Animator init tests (10)
│  ├─ Animator update tests (8)
│  ├─ Animator events tests (5)
│  ├─ Animator transitions tests (6)
│  ├─ Animator frame tests (1)
│  └─ Animator state tests (4)
│
├─ test_animation_runtime_foundation.py (100+ lines)
│  ├─ Keyframe serialization
│  ├─ Property animation
│  ├─ Play/pause/stop
│  ├─ Loop wrapping
│  └─ Delta time handling
│
├─ test_animator.py (200+ lines)
│  ├─ Component lifecycle
│  ├─ Serialization
│  └─ Integration tests
│
├─ test_animator_controller_asset.py (150+ lines)
│  └─ Controller loading/saving
│
└─ test_animator_controller_demo.py (100+ lines)
   └─ Demo scene tests
```

### Test Count

Estimated: **150+ tests** (not all passing)

### Coverage Gaps

- ❌ Logic Graph node tests
- ❌ Animation event routing tests
- ❌ Multi-animator cross-talk tests
- ❌ Play Mode integration tests

---

## 18. Technical Debt

### Safe Debt

```python
# frame_source metadata — workaround for #9
# Purpose: Store serialization hints
# Impact: Low (internal, not exposed)
```

### Structural Issues

1. **No animation event owner routing** (Blocking 100% visual)
2. **No Play Mode sprite integration** (Half-broken)
3. **Minimal Logic Graph integration** (Only 1 node)

### Code Quality

- ✅ No TODO/FIXME found
- ✅ No except: pass
- ✅ Consistent style
- ✅ Well-documented

---

## 19. Dead Code

### Candidates

**AnimationPlayerService** (115 lines)
- Status: Documented but unused in Play Mode
- Can keep (may be for editor-only playback)

**EventTrack** (tracks/event_track.py)
- Status: Defined but unused
- No integration with animation events

---

## 20. Production Risks

### Critical (BLOCK 100% VISUAL)

1. **No Animation Play Node**
   - Can't start animations from Logic Graph
   - CRITICAL: Blocks gameplay

2. **No Animation Event Owner Routing**
   - Events fire globally
   - Multi-object scenes broken
   - CRITICAL: Breaks correctness

3. **No Play Mode Sprite Integration**
   - Animations play but sprite doesn't update
   - CRITICAL: Invisible animations

### High (IMPACT)

4. **No Animation Finished Event**
   - Can't trigger next action after animation
   - Block: "Attack → Hit → Idle" sequences

5. **No State Machine Visual Editor**
   - Must hand-code transitions
   - Blocks designer workflow

### Medium

6. **No Blending/Crossfade**
   - Stiff animation transitions
   - OK for prototype, polish later

---

## 21. Missing Features (Out of Scope for 6B)

- ❌ Animation blending/crossfade
- ❌ Root motion
- ❌ IK (inverse kinematics)
- ❌ Skeletal animation
- ❌ Particle emission timing
- ❌ Audio sync
- ❌ Ragdoll triggers

---

## 22. Recommended Phase 6B Architecture

### What MUST be built (Blocking 100% visual)

1. **Play Animation Node**
   ```
   Inputs: exec, target, animation_name
   Outputs: exec_success, exec_failure
   ```

2. **Animation Event Owner Routing**
   ```
   animation_event_dispatch(owner_name, event_name)
   Route to LogicGraphRuntime[owner_name]
   ```

3. **Play Mode Sprite Integration**
   ```
   Animator.push_frame() called in update cycle
   Updates SpriteRenderer.frame
   ```

4. **Animation Finished Event Node**
   ```
   Trigger: On animation_clip.on_finish()
   Route: To Logic Graph
   ```

### What SHOULD be built (High quality)

5. Stop/Pause Animation nodes
6. Get Current Animation node
7. Get Animation Time/Frame nodes
8. On Animation Event node
9. Animator Parameter nodes (already exists, extend)

### What CAN wait (Polish)

10. Blending/Crossfade
11. State Machine visual editor
12. Root motion
13. Animation preview in editor

---

## 23. Final Classification

| System | Status | Risk |
|--------|--------|------|
| ANIMATION CORE | ✅ READY | LOW |
| CLIP PLAYBACK | ✅ READY | LOW |
| SPRITE INTEGRATION | ❌ BROKEN | CRITICAL |
| ANIMATOR STATE MACHINE | ⚠️ PARTIAL | MEDIUM |
| TRANSITIONS | ✅ WORKING | LOW |
| BLENDING | ❌ MISSING | MEDIUM |
| ANIMATION EVENTS | ❌ BROKEN | CRITICAL |
| LOGIC GRAPH NODES | ❌ BROKEN | CRITICAL |
| LIFECYCLE | ✅ WORKING | LOW |
| SERIALIZATION | ✅ WORKING | LOW |

---

## OVERALL ANIMATION SYSTEM

**Status**: ❌ **PRODUCTION PARTIAL**

### What Works

✅ Animation playback mechanics  
✅ State machine logic  
✅ Event firing  
✅ Serialization  
✅ Sprite sheet loading  

### What's Broken

❌ Play Mode sprite updates  
❌ Animation event owner routing  
❌ Logic Graph integration (only 1 node)  
❌ Animation finished callbacks  

### Can 100% Visual Gameplay Be Built?

**Currently**: NO (critical gaps)

**After Phase 6B**: YES (if all 3 critical items fixed)

---

## Handoff to Phase 6B

**Do Not Implement**:
- Blending (can use direct transitions)
- 3D animation
- Advanced state machine features
- Visual controller editor

**Must Implement for Phase 6B**:
1. Play/Stop/Pause animation nodes
2. Animation event owner routing + dispatch
3. Play Mode sprite rendering integration
4. Animation Finished event node
5. Tests for all above

**Estimated Effort**: 2-3 days (straightforward, following Physics pattern)

---

## Session Complete

**PHASE 6A AUDIT: COMPLETE**

Awaiting approval to begin Phase 6B implementation.
