# PHASE 8B — CANONICAL GAMEPLAY TEST PLAN

## Objective

Create `CanonicalGameplayTest.zscene` using **ONLY** canonical editor UIs and serializers.

No hand-written JSON. No schema assumptions. No bypassed APIs.

**Success**: A playable micro-game that proves:
- Scene creation works
- Object/component configuration works  
- Logic graphs compile and execute
- Physics/collision works
- Camera follows player
- UI renders
- All assets persist and reload

---

## GOLDEN RULE

### ✅ ALLOWED

- Click buttons in editor UIs
- Use dialogs and pickers
- Edit fields in Inspector
- Draw/place objects in viewport
- Compile graphs in editor
- Save files via File menu
- Open files via File menu

### ❌ BANNED

- Edit JSON directly
- Construct objects via Python code
- Assume JSON schema
- Bypass serializers
- Hardcode asset paths
- Create files outside editor

---

## CHECKPOINT STRUCTURE

After each capability, **STOP and wait for user approval** before proceeding.

| Checkpoint | What | Expected | Blocker |
|------------|------|----------|---------|
| A | Scene + objects load | ✅ Blank viewport → objects appear | No |
| B | Player WASD movement | ✅ Press W/A/S/D → player moves | Yes (logic graph) |
| C | Collision detection | ✅ Player hits wall → stops | No (physics works) |
| D | Camera follow | ✅ Player moves → camera tracks | No |
| E | Enemy with health | ✅ Enemy object exists, health stat | No |
| F | Player attack | ✅ Press SPACE → raycast → enemy hurt | Yes (logic graph) |
| G | HUD display | ✅ Health bar shows | No (UI renderer) |
| H | Full reload cycle | ✅ Save → close → open → play again | No |

---

## STEP-BY-STEP CANONICAL AUTHORING

### STEP 1: CREATE SCENE (File → New)

**Action**: File menu → New Scene

**Expected**: 
- Blank viewport
- Empty hierarchy
- `.zscene` file created

**Verify**:
```json
{
  "format_version": 2,
  "scene_name": "CanonicalGameplayTest",
  "objects": []
}
```

**Next**: Checkpoint A prep

---

### STEP 2: ADD MAIN CAMERA (via Hierarchy)

**Action**: Hierarchy → + (Add GameObject) → Camera

**Expected**:
- Camera appears in hierarchy
- Viewport shows scene through camera

**In Inspector**:
- Transform: x=0, y=0, z=0
- Camera: active=true, zoom=1.0

**Save Scene**: File → Save

**Verify**:
```json
{
  "objects": [
    {
      "id": "main_camera",
      "name": "MainCamera",
      "components": {
        "items": [
          {"type": "Camera", "active": true, "zoom": 1.0}
        ]
      }
    }
  ]
}
```

**Checkpoint A Reached** ✅

---

### STEP 3: ADD PLAYER QUAD

**Action**: Hierarchy → + → Sprite

**Name**: "Player"

**In Inspector**:
- Transform: x=0, y=0, w=36, h=48
- SpriteRenderer: color=(88, 117, 255)
- RigidBody: use_gravity=true, mass=1.0
- Collider: type=box

**Save**: File → Save

**Verify**: Player quad appears centered in viewport

**Expected .zscene**:
```json
{
  "objects": [
    {...camera...},
    {
      "id": "player",
      "name": "Player",
      "transform": {"x": 0, "y": 0, "w": 36, "h": 48},
      "components": {
        "items": [
          {"type": "SpriteRenderer", "color": [88, 117, 255]},
          {"type": "RigidBody", "use_gravity": true},
          {"type": "Collider", "type": "box"}
        ]
      }
    }
  ]
}
```

---

### STEP 4: ADD WALL (Floor)

**Action**: Hierarchy → + → Sprite

**Name**: "Wall"

**In Inspector**:
- Transform: x=0, y=150, w=600, h=32
- SpriteRenderer: color=(91, 194, 100)
- RigidBody: is_kinematic=true
- Collider: type=box

**Save**: File → Save

---

### STEP 5: CREATE PLAYER MOVEMENT LOGIC GRAPH

**Action**: Right-click Player → Add Component → Logic Graph

**In component field**: Create new logic graph (or browse for existing)

**Save**: Creates `Assets/Logic/PlayerMovementLogic.zlogic`

---

### CHECKPOINT B: PLAYER MOVEMENT SETUP

**BEFORE proceeding**: User must test

**Test**:
1. File → Save scene
2. Play button
3. Expected: Viewport shows Player quad, Wall quad, Camera active
4. User presses W/A/S/D
5. **Expected**: Nothing happens yet (logic graph not created)

**Wait for user approval** to proceed with logic graph creation.

---

### STEP 6: EDIT PLAYER MOVEMENT LOGIC GRAPH (IN EDITOR)

**Action**: Double-click PlayerMovementLogic component → opens Logic Graph Editor

**Inside editor, create**:

**Node 1**: Input.GetAxis("Horizontal")
- Output: float value

**Node 2**: Input.GetAxis("Vertical")  
- Output: float value

**Node 3**: Math.MakeVector2
- Input1: Horizontal value
- Input2: Vertical value
- Output: Vector2 direction

**Node 4**: Math.Multiply (scale movement)
- Input1: Vector2 direction
- Input2: 5.0 (speed)
- Output: Vector2 movement

**Node 5**: Rigidbody.SetVelocity
- Input: Vector2 movement
- Target: Self (Player)

**Connect**:
```
Update event
├─ GetAxis(Horizontal) → MakeVector2
├─ GetAxis(Vertical) → MakeVector2
└─ MakeVector2 → Multiply → SetVelocity
```

**Compile**: Click Compile button in editor

**Expected**: 0 ERRORS, 0 WARNINGS

**Save**: File → Save (graph auto-saves)

---

### CHECKPOINT C: COMPILE + VISUAL VERIFICATION

**Test**:
1. Close logic editor
2. Play button
3. Press W/A/S/D
4. **Expected**: Player moves in viewport
5. Stop Play

**Wait for user approval** to add collision.

---

### STEP 7: TEST COLLISION (NO NEW SETUP NEEDED)

**Action**: Just play

**Test**:
1. Play button
2. Press W (move right) toward wall
3. **Expected**: Player stops before wall (collision prevents penetration)

**If collision fails**:
- Check Wall has RigidBody (is_kinematic=true)
- Check Wall has Collider
- Check Player has Collider
- Physics should be automatic

---

### CHECKPOINT D: COLLISION WORKING

**Wait for user approval** to add camera follow.

---

### STEP 8: CAMERA FOLLOW (SIMPLE)

**Action**: Add to MainCamera component logic

Option A: Add Camera Follow script
- Create `Assets/Logic/CameraFollowLogic.zlogic`
- Add component to MainCamera
- Create logic: position = player.position + offset

Option B: In inspector, set:
- Camera.follow_target = "Player" (if this field exists)

**Test**:
1. Play button
2. Move player far from center
3. **Expected**: Camera stays centered on player

---

### CHECKPOINT E: CAMERA FOLLOWS

**Wait for user approval** to add enemy.

---

### STEP 9: ADD ENEMY

**Action**: Hierarchy → + → Sprite

**Name**: "Enemy"

**In Inspector**:
- Transform: x=300, y=0, w=36, h=36
- SpriteRenderer: color=(255, 0, 0)
- RigidBody: is_kinematic=true
- Collider: type=box

**Add custom stat** (if supported):
- Data component or Logic variable: health=100

**Save**: File → Save

---

### CHECKPOINT F: ENEMY LOADED

**Wait for user approval** to implement attack.

---

### STEP 10: PLAYER ATTACK LOGIC GRAPH

**Action**: Add to Player's existing `PlayerMovementLogic` or create new `PlayerAttackLogic`

**Inside editor**:

**Node 1**: Input.GetKeyDown("Space")
- Output: bool

**Node 2**: Raycast
- Origin: Player.transform.position
- Direction: Player.transform.forward (or right vector)
- Distance: 100
- Output: hit object

**Node 3**: Conditional
- Input: raycast hit != null
- If true: proceed

**Node 4**: GetComponent("EnemyHealth")
- Input: hit object
- Output: health component

**Node 5**: Health.Damage
- Input: 25 damage
- Target: enemy health component

**Connect**:
```
Update
└─ GetKeyDown(Space) → Raycast → Conditional → Damage
```

**Compile**: 0 ERRORS

**Save**: Graph

---

### CHECKPOINT G: ATTACK WORKS

**Test**:
1. Play button
2. Move player close to enemy
3. Press SPACE
4. Repeat 4 times
5. **Expected**: Enemy health goes 100 → 75 → 50 → 25 → 0

**Wait for user approval** to add HUD.

---

### STEP 11: CREATE SIMPLE HUD

**Action**: Hierarchy → + (Add GameObject) → Canvas

**Name**: "HUD"

**In Inspector**:
- Canvas: render_mode=ScreenSpace

**Inside Canvas** (hierarchy children):
- Add Label widget: "Health: 100"

**Save**: File → Save

---

### STEP 12: CONNECT HUD TO PLAYER HEALTH

Option A: Simple for now
- Hard-code display in update logic graph

Option B: Via UI Builder (if available)
- Create `.zui` file
- Bind to player health variable

**For Phase 8B minimum**: Option A (simpler, less dependencies)

**Test**:
1. Play button
2. Verify HUD shows "Health: 100"
3. Take damage (shoot self with raycast)
4. **Expected**: HUD updates to "Health: 75" etc.

---

### CHECKPOINT H: HUD WORKING

**Wait for user approval** to test full save/load cycle.

---

### STEP 13: FULL RELOAD CYCLE

**Action**: 

1. Play button - verify game works
2. Stop Play
3. File → Save Scene
4. Close scene
5. File → Open CanonicalGameplayTest.zscene
6. Play button again
7. **Expected**: Everything still works (scene reloaded correctly)

---

## SUCCESS CRITERIA

When all checkpoints pass:

- [ ] Checkpoint A: Scene + objects
- [ ] Checkpoint B: Player movement compiles
- [ ] Checkpoint C: Player moves (WASD works)
- [ ] Checkpoint D: Collision works (player stops at wall)
- [ ] Checkpoint E: Camera follows player
- [ ] Checkpoint F: Enemy object exists with health stat
- [ ] Checkpoint G: Attack works (enemy health decreases)
- [ ] Checkpoint H: HUD displays health
- [ ] Reload cycle: Save/close/open/play works

---

## EXPECTED FILES

After all steps, `CanonicalGameplayTest` directory contains:

```
Assets/
├─ Scenes/
│  └─ CanonicalGameplayTest.zscene     ← master scene file
├─ Logic/
│  ├─ PlayerMovementLogic.zlogic       ← WASD input + velocity
│  ├─ PlayerAttackLogic.zlogic         ← Space attack raycast
│  └─ CameraFollowLogic.zlogic         ← camera tracking
└─ UI/
   └─ HUD.zui                           ← health bar display (optional)
```

All created via editor UIs. All serialized through canonical APIs.

---

## FAILURE MODES

If any step fails:

| Failure | Root Cause | Fix |
|---------|-----------|-----|
| Player doesn't move | Logic graph didn't compile | Check console errors, fix graph |
| Player moves but through wall | Collider missing | Add collider via Inspector |
| Camera doesn't follow | Camera follow logic not added | Add `CameraFollowLogic` component |
| HUD doesn't appear | Canvas not rendering | Check Canvas render_mode, layer |
| Save/load breaks | Serializer bug | File bug report with .zscene snapshot |

---

## DELIVERABLES FOR PHASE 8B

**Do not implement full Phase 8B yet.**

First deliver to user:

1. ✅ **PHASE8A_BENCHMARK_LOG.md** — Document why Phase 8A failed
2. ✅ **PHASE8B_AUTHORING_PIPELINE_AUDIT.md** — Map canonical pipelines
3. ✅ **PHASE8B_CANONICAL_GAMEPLAY_TEST_PLAN.md** — This document

Then wait for user feedback:
- Identify which blockers to fix first
- Get approval to implement Phase 8B

---

**Planned**: 2026-08-08  
**Status**: AWAITING USER APPROVAL
