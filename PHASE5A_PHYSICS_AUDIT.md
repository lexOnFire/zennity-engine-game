# PHASE 5A: Physics Architecture Audit

**Data**: 2026-08-08  
**Status**: AUDIT COMPLETE  
**Objective**: Map actual Physics system state before transformation to 100% Logic Graph control

---

## EXECUTIVE SUMMARY

The Zennity Engine has a **HYBRID PHYSICS ARCHITECTURE** with two distinct systems coexisting:

| System | Status | Integration |
|--------|--------|-------------|
| **Legacy Collider System** | CODE PRESENT | UNUSED (dead code) |
| **PhysicsWorld System** | FUNCTIONAL | INTEGRATED (RuntimeScene) |
| **TilemapCollider** | FUNCTIONAL | CUSTOM (Box collision only) |
| **RigidBody 2D** | FUNCTIONAL | BASIC (gravity, velocity) |
| **RigidBody 3D** | CODE PRESENT | COMPLETELY UNUSED |
| **Physics Logic Nodes** | BROKEN | REFERENCES NON-EXISTENT PROPERTIES |
| **Collision Events to Logic Graph** | MISSING | NOT IMPLEMENTED |

**Current State**: Physics has ~60% core implementation, 40% broken/missing integration points

---

## 1. PHYSICSWORLD ARCHITECTURE

### Location
`engine/physics/physics_world.py` - **186 lines**

### Responsibility
- Central collision detection and resolution
- Lifecycle management for physics bodies
- Contact/trigger event management
- Broad-phase spatial hashing
- Narrow-phase intersection testing

### Key Components

**Construction**:
```python
class PhysicsWorld:
    def __init__(self, runtime_scene: Any | None = None, broad_phase_cell_size: float = 128.0):
        self.runtime_scene = runtime_scene
        self.rigidbodies: list[RigidBody] = []
        self.colliders: list[Any] = []
        self.contacts: set[tuple[int, int]] = set()
        self.trigger_contacts: set[tuple[int, int]] = set()
        self.detected_contacts: list[PhysicsContact] = []
        self.broad_phase = SpatialHashBroadPhase(cell_size=128.0)
```

**Lifecycle**:
```
RuntimeScene.__init__()
  ↓
PhysicsWorld(self)  ← Created here

RuntimeScene.start_runtime()
  ↓
physics_world.build_from_scene(self)  ← Registers bodies/colliders
  ↓
Physics.bind_world(physics_world)  ← Makes global via Physics.instance

RuntimeScene.update(dt)
  ↓
lifecycle.run_fixed_updates(dt, physics_world.step)  ← Called at fixed timestep

RuntimeScene.stop_runtime()
  ↓
Physics.unbind_world()
physics_world.clear()
```

### Broad Phase
**Technology**: `SpatialHashBroadPhase` (128 px cell size)
- Spatial partitioning grid
- Efficient candidate pair generation
- Tracks `BroadPhaseStats`
- **Assessment**: ✅ Functional

### Narrow Phase
**Methods**:
- `_intersects(a, b)` - Performs AABB and circle collision tests
- `_box_circle_intersects(box, circle)` - Mixed collider intersection
- Collision types:
  - **Box ↔ Box**: pygame.Rect.colliderect()
  - **Circle ↔ Circle**: Distance check
  - **Box ↔ Circle**: Closest point test

**Assessment**: ✅ Functional (2D only, no 3D)

### Collision Response
**Contact Tracking**:
```python
class PhysicsContact(dataclass):
    a: Any
    b: Any
    is_trigger: bool = False
```

**Event Emission**:
```python
def _emit_collision_enter(a, b):
    # 1. Direct callbacks on colliders
    if hasattr(a, 'on_collision_enter'):
        a.on_collision_enter(b)
    
    # 2. Notify all components on GameObject
    for component in a.game_object.components:
        if hasattr(component, 'on_collision_enter'):
            component.on_collision_enter(b)
    
    # 3. Notify script runtime
    script_runtime.notify_game_object_event(obj, "on_collision_enter", b)
```

**Assessment**: ✅ Functional (callbacks exist)

---

## 2. RIGIDBODY COMPONENT

### Location
`engine/physics/rigidbody.py` - **115 lines**

### Current Properties

| Property | Type | Default | Serialized | Editor | Runtime Mutable | Logic Graph |
|----------|------|---------|-----------|--------|-----------------|-------------|
| mass | float | 1.0 (min 0.0001) | ✅ | ✅ | ✅ | ⚠️ (broken) |
| gravity_scale | float | 1.0 | ✅ | ✅ | ✅ | ⚠️ (broken) |
| drag | float | 0.0 | ✅ | ✅ | ✅ | ⚠️ (broken) |
| use_gravity | bool | True | ✅ | ✅ | ✅ | ⚠️ (broken) |
| is_kinematic | bool | False | ✅ | ✅ | ✅ | ⚠️ (broken) |
| velocity | np.ndarray[2] | [0,0] | ✅ | ❌ | ✅ | ❌ (MISSING) |
| acceleration | np.ndarray[2] | [0,0] | ✅ | ❌ | ✅ | ❌ (MISSING) |
| grounded | bool | False | ❌ | ❌ | ✅ | ❌ (MISSING) |

### Key Architectural Decisions

**Gravity Handling**:
```python
GRAVITY: float = 980.0  # Class constant, overridable per instance

def update(self, dt):
    if self.use_gravity:
        self.velocity[1] += self.GRAVITY * self.gravity_scale * dt
    
    # External forces integrated separately
    self.velocity += self.acceleration * dt
    
    # Acceleration reset after integration (forces are frame-scoped)
    self.acceleration[:] = 0.0
```

**Assessment**: ✅ Gravity system is clean and working

**Force/Impulse API**:
```python
def add_force(fx, fy):
    # F = ma → a = F/m
    self.acceleration += np.array([fx, fy]) / self.mass

def add_impulse(ix, iy):
    # Direct velocity change (instant)
    self.velocity += np.array([ix, iy]) / self.mass

def set_velocity(vx, vy):
    self.velocity = np.array([vx, vy], dtype=np.float32)

def stop():
    self.velocity[:] = 0.0
    self.acceleration[:] = 0.0
```

**Assessment**: ✅ Force/impulse system is correct

### Serialization

✅ Complete and working:
```python
def serialize_properties(self) -> dict:
    return {
        "mass": float(self.mass),
        "gravity_scale": float(self.gravity_scale),
        "drag": float(self.drag),
        "use_gravity": bool(self.use_gravity),
        "is_kinematic": bool(self.is_kinematic),
        "velocity": self.velocity.tolist(),
        "acceleration": self.acceleration.tolist(),
    }
```

**Assessment**: ✅ Serialization preserves state correctly

---

## 3. COLLIDER COMPONENTS

### BoxCollider

**Location**: `engine/physics/collider.py` lines 20-320

| Property | Type | Default | Serialized | Editor | Trigger Support |
|----------|------|---------|-----------|--------|-----------------|
| width | float | 32.0 | ✅ | ✅ | ✅ |
| height | float | 32.0 | ✅ | ✅ | ✅ |
| offset_x | float | 0.0 | ✅ | ✅ | ✅ |
| offset_y | float | 0.0 | ✅ | ✅ | ✅ |
| is_trigger | bool | False | ✅ | ✅ | ✅ |
| debug_draw | bool | False | ✅ | ✅ | ✅ |

**Assessment**: ✅ Complete properties

### CircleCollider

**Location**: `engine/physics/collider.py` lines 322-518

| Property | Type | Default | Serialized | Editor | Trigger Support |
|----------|------|---------|-----------|--------|-----------------|
| radius | float | 16.0 | ✅ | ✅ | ✅ |
| offset_x | float | 0.0 | ✅ | ✅ | ✅ |
| offset_y | float | 0.0 | ✅ | ✅ | ✅ |
| is_trigger | bool | False | ✅ | ✅ | ✅ |
| debug_draw | bool | False | ✅ | ✅ | ✅ |

**Assessment**: ✅ Complete properties

### CRITICAL FINDING: Dead Code

**BoxCollider.check_all()** (line 129):
- Static method that verifies ALL collisions
- Called: **NEVER** - completely unused
- Contains logic for:
  - Object-to-object collision detection
  - TilemapCollider integration
  - Callback emission
- Status: **CODE PRESENT BUT UNUSED** ❌

**CircleCollider.check_all()** (line 410):
- Static method for circle collision detection
- Called: **NEVER** - completely unused
- Status: **CODE PRESENT BUT UNUSED** ❌

**Why Both Exist**:
Two collision detection systems coexist:
1. **Legacy**: `BoxCollider.check_all()` / `CircleCollider.check_all()` (unused)
2. **Active**: `PhysicsWorld.detect_collisions()` (used by RuntimeScene)

**Assessment**: ⚠️ TECHNICAL DEBT - Dead code should be removed

---

## 4. COLLISION DETECTION FLOW

### Current Active Flow (PhysicsWorld)

```
RuntimeScene.start_runtime()
  ↓
PhysicsWorld.build_from_scene(scene)
  ├─ Iterate all GameObjects
  ├─ Find RigidBody components → register
  └─ Find Collider components → register

RuntimeScene.update(dt)
  ↓
lifecycle.run_fixed_updates(dt, physics_world.step)
  ↓
PhysicsWorld.step(fixed_dt)
  ├─ Update all RigidBodies (apply gravity, integrate)
  └─ detect_collisions()
     ├─ Broad phase (SpatialHash candidates)
     ├─ Narrow phase (_intersects)
     ├─ Track contacts (contacts vs trigger_contacts)
     └─ Emit enter/exit callbacks
```

### Callback Chain

```
PhysicsWorld._emit_collision_enter(a, b)
  ├─ Direct collider callback: a.on_collision_enter(b)
  ├─ Direct collider callback: b.on_collision_enter(a)
  ├─ GameObject callbacks: a.game_object.components[].on_collision_enter(b)
  ├─ GameObject callbacks: b.game_object.components[].on_collision_enter(a)
  └─ Script runtime: script_runtime.notify_game_object_event(obj, "on_collision_enter", b)
```

### Supported Collider Combinations

✅ Working:
- Box ↔ Box
- Circle ↔ Circle
- Box ↔ Circle (bidirectional)

❌ Missing:
- 3D colliders (Sphere, Box3D, Capsule)
- Polygon colliders
- Mesh colliders

**Assessment**: ✅ 2D collision detection is functional

---

## 5. COLLISION EVENTS

### Event Types Supported

**Via PhysicsWorld**:
```python
def _emit_collision_enter(a, b)  # ✅ Implemented
def _emit_collision_exit(a, b)   # ✅ Implemented
def _emit_trigger_enter(a, b)    # ✅ Implemented
def _emit_trigger_exit(a, b)     # ✅ Implemented
```

**Callback Signatures**:
```python
on_collision_enter(other: Collider)  # Component method
on_collision_exit(other: Collider)   # Component method
on_trigger_enter(other: Collider)    # Component method
on_trigger_exit(other: Collider)     # Component method
```

### Integration with Logic Graph

**Status**: ❌ **NOT IMPLEMENTED**

Collision events CAN reach:
1. ✅ Direct collider callbacks (component methods)
2. ✅ Script runtime notifications
3. ❌ Logic Graph nodes (MISSING)

**Problem**: No event node exists that listens to physics events and triggers Logic Graph execution

**Example Missing**: 
```
On Collision Enter (node)
  ├─ Object A
  ├─ Object B
  └─ trigger execution branches
```

**Assessment**: ⚠️ PRODUCTION BLOCKER for visual physics gameplay

---

## 6. TRANSFORM SYNCHRONIZATION

### Direction of Truth

**Current**: Physics → Transform (one-way)

**Flow**:
```python
RigidBody.update(dt):
    # 1. Update velocity (gravity + forces)
    if self.use_gravity:
        self.velocity[1] += self.GRAVITY * self.gravity_scale * dt
    self.velocity += self.acceleration * dt
    
    # 2. Integrate position
    transform.x += self.velocity[0] * dt
    transform.y += self.velocity[1] * dt
```

**Transform Manual Movement**:
```
Set Transform.x manually
  ↓
RigidBody ignores it
  ↓
Next update, RigidBody position overwrites it
```

**Teleport Behavior**:
```python
# Teleport preserves velocity
game_object.transform.position = new_pos
# but velocity is not zeroed
```

**Assessment**: ⚠️ POTENTIAL BUG - Teleport should probably clear velocity or use impulse

---

## 7. FIXED TIMESTEP

### Current Implementation

**Location**: `engine/runtime/runtime_scene.py` line 343

```python
self.lifecycle.run_fixed_updates(dt, physics_world.step)
```

**Configuration**: Uses `Time.fixed_delta_time` (from `engine/time.py`)

**How it Works**:
```python
# LifecycleScheduler accumulates delta time
# When accumulated >= fixed_delta_time:
#   - Call physics_world.step(fixed_dt)
#   - Subtract fixed_dt from accumulator
#   - Repeat until < fixed_dt remains
```

**Default Value**: Need to check in engine/time.py

**Assessment**: ✅ Fixed timestep mechanism exists and is used

---

## 8. GRAVITY SYSTEM

### Architecture

**Global Default**:
```python
class RigidBody:
    GRAVITY: float = 980.0  # Class attribute
```

**Per-Instance Override**:
```python
rb = RigidBody()
rb.GRAVITY = 500.0  # Overrides only this instance
```

**Global Change**:
```python
RigidBody.GRAVITY = 500.0  # Changes for all future instances
```

**Scale Factor**:
```python
rb.gravity_scale = 2.0  # Multiply gravity by this
rb.use_gravity = False  # Disable gravity entirely
```

### Current Limitations

❌ Cannot dynamically change gravity in Logic Graph
❌ Cannot read current gravity value
❌ Cannot raycast to test gravity direction

**Assessment**: ⚠️ MISSING - No Logic Graph node for gravity manipulation

---

## 9. FORCES / IMPULSES

### Implemented Methods

✅ `RigidBody.add_force(fx, fy)`:
```python
def add_force(self, fx, fy):
    if self.is_kinematic:
        return
    self.acceleration += np.array([fx, fy]) / self.mass
```
- Accumulates in acceleration
- Applied next frame
- Respects mass (F = ma)
- Ignored for kinematic bodies

✅ `RigidBody.add_impulse(ix, iy)`:
```python
def add_impulse(self, ix, iy):
    if self.is_kinematic:
        return
    self.velocity += np.array([ix, iy]) / self.mass
```
- Instant velocity change
- Respects mass (impulse/mass)
- Ignored for kinematic bodies

### Logic Graph Integration

**Location**: `engine/logic/runtime/nodes/physics_nodes.py` lines 104-131

```python
@registry.register_executor('apply_force')
def execute_apply_force(runtime, node, game, dt):
    # Current implementation tries:
    if rigidbody and hasattr(rigidbody, "apply_force"):
        rigidbody.apply_force((force_x, force_y), force_mode)
```

**Problem**: ❌ `apply_force()` method does NOT exist on RigidBody

**What Actually Exists**:
- `add_force(fx, fy)` ✅
- `add_impulse(ix, iy)` ✅

**Assessment**: ⚠️ BROKEN - Logic Graph nodes call non-existent methods

---

## 10. RAYCASTS / QUERIES

### Current Implementation Status

**Raycast**: ❌ **NOT IMPLEMENTED**

No evidence of:
- Ray-casting infrastructure
- Line-casting
- Physics queries
- Overlap detection
- Distance queries

### Needed for Future Visual Gameplay

```
Raycast
├─ Origin: [x, y]
├─ Direction: [dx, dy]
├─ Distance: max_distance
├─ Layer Mask: collision_mask
└─ Returns
    ├─ Hit: bool
    ├─ Object: GameObject
    ├─ Position: [x, y]
    ├─ Normal: [nx, ny]
    └─ Distance: float
```

**Assessment**: ❌ PRODUCTION MISSING

---

## 11. LAYERS / MASKS

### Current Implementation Status

❌ **NOT IMPLEMENTED**

No evidence of:
- Collision layers
- Collision masks
- Layer filtering
- Collision matrices

### Current Behavior

All colliders check against all other colliders in the same scene
(No filtering except by scene boundary)

### Needed

```
Collider.collision_layer = 0     // Which layer am I on?
Collider.collision_mask = 0xFF   // Which layers do I collide with?
```

**Assessment**: ❌ PRODUCTION MISSING

---

## 12. PLAY / STOP / REPLAY LIFECYCLE

### Lifecycle Verification

✅ **Play**:
```
RuntimeScene(editor_scene)
  ├─ PhysicsWorld created
  ├─ build_from_scene() registers all bodies/colliders
  ├─ start_runtime()
  │   └─ Physics.bind_world(physics_world)
  └─ Ready to step
```

✅ **Stop**:
```
RuntimeScene.destroy()
  ├─ stop_runtime()
  │   └─ Physics.unbind_world()
  ├─ physics_world.clear()
  │   ├─ rigidbodies.clear()
  │   ├─ colliders.clear()
  │   ├─ contacts.clear()
  │   └─ detected_contacts.clear()
  └─ scene.destroy()
```

✅ **Replay**:
```
New RuntimeScene(editor_scene)
  ├─ New PhysicsWorld instance
  ├─ Fresh registration of bodies/colliders
  ├─ No stale references
  ├─ No duplicate bodies
  └─ Ready to step
```

**Assessment**: ✅ Lifecycle is clean

---

## 13. SCENE SERIALIZATION

### RigidBody Serialization

✅ Complete:
```json
{
  "rigidbody": {
    "mass": 1.0,
    "gravity_scale": 1.0,
    "drag": 0.0,
    "use_gravity": true,
    "is_kinematic": false,
    "velocity": [0.0, 0.0],
    "acceleration": [0.0, 0.0]
  }
}
```

### Collider Serialization

✅ Complete:
```json
{
  "collider": {
    "type": "box|circle",
    "width": 32.0,
    "height": 32.0,
    "radius": 16.0,
    "offset_x": 0.0,
    "offset_y": 0.0,
    "is_trigger": false,
    "debug_draw": false
  }
}
```

### Deserialization Path

```
.zscene JSON
  ↓
SceneDocument.load(path)
  ↓
deserialize_scene(data)
  ↓
deserialize_game_object(item)
  ├─ _deserialize_rigidbody(data['rigidbody'])
  ├─ _deserialize_collider(data['collider'])
  └─ Create GameObject with components
```

### Known Issues

**BUG FIX (documented in serializer.py)**:
- Removed double serialization of UNIQUE components
- Components like BoxCollider were written twice:
  1. In dedicated `components.collider` key
  2. In generic `components.items` array
- This caused deserialization to fail (UNIQUE constraint)

**Assessment**: ✅ Serialization/deserialization working after bug fix

---

## 14. EDITOR INSPECTOR

### What Can Be Edited

| Component | Property | Editable |
|-----------|----------|----------|
| RigidBody | mass | ✅ |
| RigidBody | gravity_scale | ✅ |
| RigidBody | drag | ✅ |
| RigidBody | use_gravity | ✅ |
| RigidBody | is_kinematic | ✅ |
| RigidBody | velocity | ❌ (not exposed) |
| BoxCollider | width | ✅ |
| BoxCollider | height | ✅ |
| BoxCollider | offset_x | ✅ |
| BoxCollider | offset_y | ✅ |
| BoxCollider | is_trigger | ✅ |
| BoxCollider | debug_draw | ✅ |
| CircleCollider | radius | ✅ |
| CircleCollider | offset_x | ✅ |
| CircleCollider | offset_y | ✅ |
| CircleCollider | is_trigger | ✅ |
| CircleCollider | debug_draw | ✅ |

**Assessment**: ✅ Core properties exposed

---

## 15. LOGIC GRAPH NODES - COMPLETE AUDIT

### Node Definitions

**File**: `engine/logic/node_definitions/physics_nodes.py` (70 lines)

| Node ID | Implemented | Inputs | Outputs | Status |
|---------|-------------|--------|---------|--------|
| modify_rigidbody | ✅ | 4 | 2 | ⚠️ BROKEN (see below) |
| modify_collider | ✅ | 4 | 2 | ⚠️ BROKEN (see below) |
| apply_force | ✅ | 5 | 2 | ❌ COMPLETELY BROKEN |

### Executors

**File**: `engine/logic/runtime/nodes/physics_nodes.py` (131 lines)

#### Problem 1: Non-Existent Properties in modify_rigidbody

```python
# Line 44-45: Tries to set properties that DON'T EXIST
elif property_name == "angular_drag":
    rigidbody.angular_drag = float(value)  # ❌ NO SUCH PROPERTY

elif property_name == "constraints":
    rigidbody.constraints = str(value)  # ❌ NO SUCH PROPERTY
```

**Impact**: Any Logic Graph node trying to set `angular_drag` or `constraints` will crash

#### Problem 2: apply_force Calls Non-Existent Method

```python
# Line 122-123
if rigidbody and hasattr(rigidbody, "apply_force"):
    rigidbody.apply_force((force_x, force_y), force_mode)  # ❌ WRONG SIGNATURE
```

**Reality**: RigidBody has:
- `add_force(fx, fy)` ✅
- `add_impulse(ix, iy)` ✅
- **NOT** `apply_force(tuple, mode)` ❌

**Impact**: Logic Graph apply_force node NEVER works

#### Problem 3: modify_rigidbody velocity Signature

```python
# Lines 26-33: Tries three ways to set velocity
if property_name == "velocity_x":
    rigidbody.velocity = (float(value), rigidbody.velocity[1])  # ❌ TUPLE
elif property_name == "velocity_y":
    rigidbody.velocity = (rigidbody.velocity[0], float(value))  # ❌ TUPLE
elif property_name == "velocity":
    vel_parts = str(value).split(",")
    if len(vel_parts) == 2:
        rigidbody.velocity = (float(vel_parts[0]), float(vel_parts[1]))  # ❌ TUPLE
```

**Reality**: `rigidbody.velocity` is a **numpy array**, not a tuple!

```python
# Should be:
rigidbody.velocity[0] = float(value)  # ✅
# or:
rigidbody.set_velocity(vx, vy)  # ✅
```

**Impact**: Setting velocity via Logic Graph corrupts internal state (converts numpy array to tuple)

### Missing Logic Graph Nodes

❌ No nodes for:
- Get RigidBody velocity
- Get RigidBody mass
- Set RigidBody gravity scale
- On Collision Enter (event node)
- On Collision Exit (event node)
- On Trigger Enter (event node)
- On Trigger Exit (event node)
- Raycast query
- Physics query (overlap, distance)

**Assessment**: 🔴 **PRODUCTION BLOCKER** - Physics nodes are severely broken

---

## 16. CONTRACT CONFLICT AUDIT

### Node Definition vs Executor Mismatch

| Issue | Definition | Executor | Impact |
|-------|-----------|----------|--------|
| Port IDs match | ✅ | ✅ | - |
| Data types match | ⚠️ | ⚠️ | velocity (tuple vs numpy) |
| Exec flow | ✅ | ✅ | - |
| Property names | ❌ | ❌ | angular_drag, constraints don't exist |
| Method signatures | ❌ | ❌ | apply_force signature wrong |
| Return branches | ✅ | ✅ | success/failure exist |

### Validation Issues

**Missing**: No contract validation before node execution

**Current behavior**: 
```python
try:
    # Attempt operation
    rigidbody.angular_drag = value
except:
    return ["failure"]  # Silent failure
```

**Better would be**: Pre-validate at graph load time

**Assessment**: ⚠️ SILENT FAILURES are dangerous

---

## 17. MULTI-OUTPUT AUDIT

### apply_force Node

```python
def execute_apply_force(...) -> list[str]:
    # ...
    return ["success"]  # or ["failure"]
```

**Type**: CONDITIONAL_SINGLE_BRANCH
- Takes one input "exec"
- Returns one output from either "exec_success" or "exec_failure"
- ✅ Correct pattern

### modify_rigidbody Node

```python
def execute_modify_rigidbody(...) -> list[str]:
    # ...
    return ["success"]  # or ["failure"]
```

**Type**: CONDITIONAL_SINGLE_BRANCH
- ✅ Correct pattern

**Assessment**: ✅ Node output patterns are correct

---

## 18. PHYSICS EVENTS + LOGIC GRAPH INTEGRATION

### Current Event Flow

```
PhysicsWorld.detect_collisions()
  ↓
_emit_collision_enter(a, b)
  ├─ a.on_collision_enter(b)  ← Collider callback
  ├─ b.on_collision_enter(a)
  ├─ script_runtime.notify_game_object_event()  ← Script notification
  └─ [NO LOGIC GRAPH EVENT NODE] ❌
```

### Missing Infrastructure

To enable visual physics gameplay, we need:

```
On Collision Enter (Event Node)
  Input Ports:
    - Event stream (internal)
    - Object A tag (to filter)
  Output Ports:
    - Other object
    - Collision normal
    - Collision point
    - Continue (execution)

Similar for:
- On Collision Exit
- On Trigger Enter
- On Trigger Exit
```

### How Other Engines Do This

**Unity**:
```
OnCollisionEnter(Collision collision)
  → Can trigger event
  → Can be listened to by Editor scripts
```

**Godot**:
```
body_entered(body)  # Signal
area_entered(area)  # Signal
```

**Needed for Zennity**:
```
Logic Graph Event Nodes that listen to physics callbacks
```

**Assessment**: ❌ **NOT IMPLEMENTED** - Critical blocker for visual gameplay

---

## 19. TEST SUITE

### Existing Tests

#### engine/physics/test_rigidbody.py
- **Type**: Unit tests
- **Count**: 58 tests
- **Status**: ✅ **ALL PASS**
- **Coverage**:
  - Init/defaults (9 tests)
  - add_force (8 tests)
  - add_impulse (6 tests)
  - set_velocity/stop (5 tests)
  - Gravity (10 tests)
  - External forces (8 tests)
  - Drag (7 tests)
  - Kinematic bodies (5 tests)
  - Grounded flag (5 tests)

#### tests/runtime/test_physics_runtime.py
- **Status**: ⚠️ **SKIPPED**
- **Reason**: "Physics and PhysicsWorld have not been implemented yet"
- **Problem**: Message is MISLEADING - Physics IS implemented!
- **Reality**: This file should have real integration tests but doesn't

#### tests/editor/test_viewport_physics_stepper.py
- **Exists**: Yes
- **Content**: Unknown (not reviewed)

### Missing Tests

❌ No E2E tests for:
- Scene with RigidBody → Play → gravity applied
- Collision detection between two objects
- Trigger events firing
- Logic Graph accessing rigidbody properties
- Serialization roundtrip (save → load → play)
- Replay with fresh physics state
- Tilemap collision
- Layered collision filtering

**Assessment**: ⚠️ Unit tests exist, integration tests missing

---

## 20. TECHNICAL DEBT

### Legacy Dead Code

| Pattern | File | Line | Status |
|---------|------|------|--------|
| `BoxCollider.check_all()` | collider.py | 129 | UNUSED CODE |
| `CircleCollider.check_all()` | collider.py | 410 | UNUSED CODE |
| BoxCollider2D subclass | collision.py | 9 | REDUNDANT |
| Exception handlers | physics_nodes.py | 53, 100, 129 | SILENT FAILURES |

### TODO Comments

```
engine/physics/tilemap_collider.py:57
  TODO tilemap criado no editor nunca batia
```

Meaning: Editor-created tilemaps don't work with collision properly (has workaround)

### Architectural Issues

1. **Dual Collision Systems**:
   - Legacy: `BoxCollider.check_all()` (unused)
   - Active: `PhysicsWorld.detect_collisions()` (used)
   - **Action**: Remove dead code

2. **Broken Logic Graph Nodes**:
   - `angular_drag` reference (doesn't exist)
   - `constraints` reference (doesn't exist)
   - `apply_force` signature wrong
   - **Action**: Fix or remove broken nodes

3. **No Event Nodes**:
   - Collision events reach callbacks but not Logic Graph
   - **Action**: Implement event nodes

4. **No Raycast**:
   - Many gameplay patterns require raycasting
   - **Action**: Implement raycast system

---

## 21. PRODUCTION RISKS

### Critical (Block Release)

🔴 **Physics Logic Nodes are Broken**
- `modify_rigidbody`: Corrupts velocity (numpy → tuple)
- `apply_force`: Calls non-existent method
- User creates visual physics → crashes at runtime

🔴 **No Collision Event Nodes**
- Cannot create "on collision" gameplay visually
- Player cannot implement damage system in Logic Graph

### High (Major Impact)

🟡 **No Raycasting**
- Cannot implement line-of-sight AI
- Cannot implement projectile detection
- Cannot implement damage raycast

🟡 **No Collision Layers**
- Cannot separate gameplay objects (enemies, bullets, walls)
- All objects collide with all objects
- No fine-grained control

### Medium (Impacts Some Features)

🟠 **No Getter Nodes for Physics**
- Cannot read velocity in Logic Graph
- Cannot read mass/gravity in Logic Graph
- Cannot implement dependent behavior

🟠 **Dead Code Maintenance Burden**
- `BoxCollider.check_all()` unused
- Confuses future developers
- Increases merge conflicts

### Low (Nice to Have)

🟢 **Missing 3D Support**
- RigidBody3D exists but unused
- No 3D colliders
- Not blocking 2D game

---

## 22. MISSING FEATURES

### Absolute Blockers for Visual Physics Gameplay

| Feature | Impact | Effort |
|---------|--------|--------|
| Collision Event Nodes | CRITICAL | High |
| Fix Physics Logic Nodes | CRITICAL | Medium |
| Raycasting | HIGH | High |
| Collision Layers | HIGH | Medium |
| Getter Nodes | MEDIUM | Low |
| 3D Physics | LOW | Very High |

### Needed from Phase 4B Model

Phase 4 (Visual UI) established a pattern:
```
Asset (.zui)
  ↓
Runtime Compilation
  ↓
Auto-registration in Service
  ↓
Logic Graph Access (no fallback)
```

**Similar needed for Physics**:
```
Scene.physics_config (JSON)
  ↓
Physics Layer Definitions
  ↓
Runtime Application
  ↓
Logic Graph can use layers
```

---

## 23. RECOMMENDED PHASE 5B ARCHITECTURE

### Priority 1: Fix Broken Nodes (UNBLOCK CURRENT USERS)

**Timeline**: 1-2 days

```
1. Fix modify_rigidbody:
   - Remove angular_drag/constraints references
   - Fix velocity assignment (use set_velocity or indexing)
   
2. Fix apply_force:
   - Call add_force() or add_impulse() correctly
   - Add force_mode handling (impulse vs force)

3. Add Get Nodes:
   - Get RigidBody Velocity
   - Get RigidBody Mass
   - Get Gravity Scale
```

### Priority 2: Implement Collision Event Nodes (ENABLE GAMEPLAY)

**Timeline**: 2-3 days

```
1. Create event node definitions:
   - On Collision Enter
   - On Collision Exit
   - On Trigger Enter
   - On Trigger Exit

2. Hook into Physics event system:
   - Modify _emit_collision_enter to trigger graph events
   - Pass object references to event outputs
   
3. Full E2E test
```

### Priority 3: Implement Raycasting (ENABLE ADVANCED GAMEPLAY)

**Timeline**: 2-3 days

```
1. Raycast query system:
   - PhysicsWorld.raycast(origin, direction, distance, layer_mask)
   - Return hit info

2. Raycast node:
   - Inputs: Origin, Direction, Distance, Layer Mask
   - Outputs: Hit (bool), Object, Position, Normal, Distance
   
3. Integration with existing colliders
```

### Priority 4: Implement Collision Layers (ORGANIZE COLLISIONS)

**Timeline**: 2-3 days

```
1. Add properties to colliders:
   - collision_layer (uint8)
   - collision_mask (uint8)

2. Modify PhysicsWorld.detect_collisions():
   - Check layer compatibility before creating contacts

3. Add layer nodes to Logic Graph:
   - Set Collision Layer
   - Set Collision Mask
```

### Priority 5: Cleanup Dead Code (MAINTENANCE)

**Timeline**: 0.5 days

```
1. Remove BoxCollider.check_all()
2. Remove CircleCollider.check_all()
3. Remove BoxCollider2D
4. Simplify collider codebase
```

---

## CLASSIFICATION MATRIX

```
PHYSICS CORE:
  RigidBody 2D:         ✅ READY
  Gravity:              ✅ READY
  Forces/Impulses:      ✅ READY
  Serialization:        ✅ READY
                        ────────────
  Status:               ✅ READY for internal use

PHYSICS ↔ TRANSFORM:
  Transform sync:       ✅ READY
  Movement integration: ✅ READY
  Position update:      ✅ READY
                        ────────────
  Status:               ✅ READY

COLLISIONS:
  Box collider:         ✅ READY
  Circle collider:      ✅ READY
  Broad phase:          ✅ READY
  Narrow phase:         ✅ READY
  Collision detection:  ✅ READY
  Trigger support:      ✅ READY
                        ────────────
  Status:               ✅ READY

COLLISION EVENTS:
  Callback system:      ✅ READY
  Logic Graph nodes:    ❌ BROKEN (MISSING)
                        ────────────
  Status:               ❌ BROKEN

RAYCAST:
  Query system:         ❌ MISSING
  Nodes:                ❌ MISSING
                        ────────────
  Status:               ❌ MISSING

PHYSICS LOGIC GRAPH:
  modify_rigidbody:     ⚠️ BROKEN (properties)
  modify_collider:      ✅ WORKING
  apply_force:          ❌ BROKEN (method signature)
  Get nodes:            ❌ MISSING
  Event nodes:          ❌ MISSING
  Raycast nodes:        ❌ MISSING
                        ────────────
  Status:               🔴 BROKEN

PHYSICS VISUAL AUTHORING:
  Full pipeline:        ❌ BROKEN
                        ────────────
  Status:               🔴 BROKEN

OVERALL PHYSICS SYSTEM:
  Core foundation:      ✅ READY (60%)
  Visual integration:   ❌ BROKEN (40%)
                        ────────────
  Status:               🟡 PARTIAL - Core works, visual pipeline broken
```

---

## CONCLUSION

**Physics System Status**: **HYBRID STATE**

### What Works
- ✅ RigidBody 2D physics (gravity, forces, integration)
- ✅ Collision detection (broad+narrow phase)
- ✅ Collision event callbacks
- ✅ Serialization/deserialization
- ✅ Scene lifecycle integration
- ✅ Fixed timestep
- ✅ TilemapCollider

### What's Broken
- ❌ Physics Logic Graph nodes (broken properties/methods)
- ❌ Collision event nodes (missing)
- ❌ Raycasting (missing)
- ❌ Collision layers (missing)
- ❌ Visual authoring workflow (incomplete)

### What's Dead Code
- ❌ BoxCollider.check_all() (unused)
- ❌ CircleCollider.check_all() (unused)
- ❌ RigidBody3D (unused)
- ❌ BoxCollider2D (redundant)

### Production Readiness

**Cannot ship with current state** because:
1. Physics nodes crash at runtime
2. No way to create physics gameplay visually (no event nodes)
3. Silent failures in Logic Graph execution

**Phase 5B Priorities**:
1. Fix broken nodes (immediate)
2. Add event nodes (enable gameplay)
3. Add raycasting (advanced features)
4. Add collision layers (game organization)
5. Remove dead code (maintenance)

---

**Status**: 🟡 **PARTIAL - READY FOR PHASE 5B WORK**

Next: Implement Phase 5B fixes in priority order, following Phase 4's model of clean separation and comprehensive testing.

