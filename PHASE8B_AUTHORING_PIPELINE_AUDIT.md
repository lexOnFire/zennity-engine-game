# PHASE 8B — CANONICAL AUTHORING PIPELINE AUDIT

## Objective

Map the **COMPLETE AUTHORING PIPELINE** for each Zennity asset format.

For each format, identify:
- **CREATE**: Which editor/API creates it?
- **SAVE**: Which serializer saves it?
- **OPEN**: Which deserializer loads it?
- **EDIT**: Which editor UI modifies it?
- **RUNTIME**: Which loader/runtime consumes it?

No cells can be "assumed". Every gap is a missing feature.

---

## .zscene (Scene Files)

### Status: 🟡 MOSTLY COMPLETE

| Phase | Component | Status | Location |
|-------|-----------|--------|----------|
| **CREATE** | New Scene (File menu) | ✅ Exists | `MainWindow.action_new_scene()` |
| **CREATE** | Add GameObject (Hierarchy + button) | ✅ Exists | `HierarchyDock.add_gameobject()` |
| **SAVE** | EditorScenePersistence | ✅ Verified | `editor/scene_persistence.py` |
| **OPEN** | SceneDeserializer | ✅ Verified | `engine/scene/scene_serializer.py` |
| **EDIT** | Hierarchy panel | ✅ Exists | `editor/hierarchy_dock.py` |
| **EDIT** | Inspector panel | ✅ Exists | `editor/inspector_dock.py` |
| **RUNTIME** | RuntimeScene | ✅ Verified | `engine/runtime/runtime_scene.py` |

### Known Issues

- Legacy vs canonical JSON format migration needed
- Metadata (ui, blackboard) must be preserved during save/load

### Phase 8B Requirement

✅ No missing pieces. Can proceed.

---

## .zlogic (Logic Graphs)

### Status: 🔴 INCOMPLETE

| Phase | Component | Status | Location | Issue |
|-------|-----------|--------|----------|-------|
| **CREATE** | Logic Graph Editor | ✅ Exists | `editor/logic_workspace_controller.py` | Works, but no validation |
| **SAVE** | LogicGraphSerializer | ✅ Exists | `engine/logic/serialization/graph_serializer.py` | Unclear if complete |
| **OPEN** | LogicGraphDeserializer | ✅ Exists | `engine/logic/serialization/graph_deserializer.py` | Unclear if complete |
| **EDIT** | Visual node editor | ✅ Exists | `editor/visual_scripting/` | Works in editor |
| **COMPILE** | LogicGraphCompiler | 🟡 Exists | `engine/logic/runtime/compiler.py` | Returns errors but unclear format |
| **RUNTIME** | LogicGraphRuntime | ✅ Verified | `engine/logic/runtime/core.py` | Loads + executes |

### Known Issues

- **Compilation errors not standardized**: Current benchmark shows "13 ERRORS 14 WARNINGS" but error format/list unclear
- **No validation hook in editor**: Graph can be invalid JSON but editor doesn't catch it until play time
- **Serializer compatibility**: Unclear if editor serializer matches runtime deserializer exactly

### Critical Gap: Logic Graph Validation

**REQUIRED FOR PHASE 8B**:

```python
# What we need in Logic Graph Editor:
def compile_and_validate():
    """
    1. Serialize graph
    2. Deserialize graph
    3. Run compiler
    4. Show errors in editor UI BEFORE play
    5. Prevent save if errors > 0
    """
```

Currently: No pre-play validation in editor UI.

### Phase 8B Requirement

❌ **MISSING**: In-editor compilation validation UI

Must add before canonical authoring test.

---

## .zui (UI Assets)

### Status: 🟡 MOSTLY COMPLETE

| Phase | Component | Status | Location | Issue |
|-------|-----------|--------|----------|-------|
| **CREATE** | UI Builder dock | ✅ Exists | `editor/ui_builder/` | Exists but unclear if all features work |
| **EDIT** | UI Builder editor | ✅ Exists | `editor/ui_builder/` | Widget placement, properties |
| **SAVE** | UIAssetSerializer | 🟡 Unclear | `engine/ui/serialization/` | Unclear if complete |
| **OPEN** | UIAssetLoader | ✅ Verified | `engine/ui/asset_loader.py` | Works (Phase 8A fix) |
| **COMPILE** | UIRuntimeCompiler | ✅ Verified | `engine/ui/runtime_compiler.py` | Works (Phase 8A fix) |
| **RUNTIME** | Canvas + Widgets | ✅ Verified | `engine/ui/` | Renders correctly |

### Known Issues

- **UIAssetSerializer**: Serialization pipeline from editor to `.zui` file unclear
- **UI Builder to .zui pipeline**: Does UI Builder write `.zui` or does a separate serializer?

### Phase 8B Requirement

❌ **MISSING**: Verify UI Builder → .zui save pipeline

Must trace: UI Builder edits → serializer → `.zui` file on disk.

---

## .zanim (Animation Assets)

### Status: 🔴 INCOMPLETE

| Phase | Component | Status | Location | Issue |
|-------|-----------|--------|----------|-------|
| **CREATE** | Animation Studio dock | ✅ Exists | `editor/animation_studio/` | Exists |
| **EDIT** | Animation timeline editor | ✅ Exists | `editor/animation_studio/` | Keyframe editing |
| **SAVE** | AnimationAssetSerializer | 🟡 Unclear | `engine/animation/serialization/` | Unclear if complete |
| **OPEN** | AnimationAssetLoader | ✅ Verified | `engine/animation/asset_loader.py` | Can load `.zanim` files |
| **RUNTIME** | AnimatorRuntime | ✅ Verified | `engine/animation/runtime/` | Plays animations |

### Known Issues

- **Pipeline from Studio → .zanim**: Unclear how edits become files
- **No reference .zanim file** to examine saved format

### Phase 8B Requirement

❌ **MISSING**: Verify Animation Studio → .zanim save pipeline

Must trace and document.

---

## .zprfb (Prefab Assets)

### Status: 🔴 INCOMPLETE

| Phase | Component | Status | Location | Issue |
|-------|-----------|--------|----------|-------|
| **CREATE** | Save as Prefab (Hierarchy context menu) | ✅ Exists | `editor/hierarchy_controller.py` | Exists |
| **SAVE** | PrefabSerializer | 🟡 Unclear | `engine/prefab/serialization/` | Unclear if complete |
| **OPEN** | PrefabDeserializer | 🟡 Unclear | `engine/prefab/` | Unclear if tested |
| **EDIT** | Prefab mode in editor | ❓ Unknown | ? | Do we have prefab edit mode? |
| **INSTANTIATE** | PrefabInstantiator | ✅ Exists | `engine/prefab/` | Creates instances |
| **RUNTIME** | Prefab runtime loader | ✅ Verified | `engine/prefab/` | Loads instances |

### Known Issues

- **No prefab edit mode**: Can you double-click a `.zprfb` to edit it in place?
- **Serializer verification**: No test of .zprfb save/load roundtrip

### Phase 8B Requirement

❌ **MISSING**: Prefab edit/save/load roundtrip verification

---

## .zcontroller (Animator Controller Assets)

### Status: 🔴 NOT MAPPED

No canonical authoring pipeline identified.

| Phase | Status | Notes |
|-------|--------|-------|
| **CREATE** | ❓ | Do we have an animator controller editor? |
| **SAVE** | ❓ | How are animator states saved? |
| **OPEN** | ❓ | How are they loaded? |
| **EDIT** | ❓ | Can user edit in UI? |
| **RUNTIME** | ✅ | Runtime loads (`engine/animation/animator.py`) |

### Phase 8B Requirement

❌ **SKIP FOR NOW**: Not needed for minimal CanonicalGameplayTest

Defer to Phase 8C if animation is needed.

---

## .zdialogue (Dialogue Assets)

### Status: 🔴 NOT MAPPED

No canonical authoring pipeline identified.

| Phase | Status | Notes |
|-------|--------|-------|
| **CREATE** | ❓ | Do we have a dialogue editor? |
| **SAVE** | ❓ | How are dialogues saved? |
| **OPEN** | ❓ | How are they loaded? |
| **EDIT** | ❓ | Can user edit in UI? |
| **RUNTIME** | ❓ | Does runtime load dialogues? |

### Phase 8B Requirement

❌ **SKIP FOR NOW**: Not needed for minimal CanonicalGameplayTest

Defer to Phase 8C if dialogue is needed.

---

## SUMMARY TABLE

| Format | CREATE | SAVE | OPEN | EDIT | RUNTIME | Phase 8B Ready |
|--------|--------|------|------|------|---------|-----------------|
| `.zscene` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ **YES** |
| `.zlogic` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ Missing editor validation UI |
| `.zui` | ✅ | 🟡 Unclear | ✅ | ✅ | ✅ | ❌ Verify save pipeline |
| `.zanim` | ✅ | 🟡 Unclear | ✅ | ✅ | ✅ | ❌ Verify save pipeline |
| `.zprfb` | ✅ | 🟡 Unclear | 🟡 Unclear | ❓ Unknown | ✅ | ❌ Verify save/load/edit |
| `.zcontroller` | ❓ | ❓ | ❓ | ❓ | ✅ | ❌ **SKIP** |
| `.zdialogue` | ❓ | ❓ | ❓ | ❓ | ❓ | ❌ **SKIP** |

---

## CRITICAL BLOCKERS FOR PHASE 8B

### Blocker 1: Logic Graph Editor Validation

**Current**: No in-editor compilation feedback
**Required**: Red error UI showing compilation failures before play

**Fix Location**: `editor/logic_workspace_controller.py` or `editor/visual_scripting_dock.py`

### Blocker 2: Prefab Save/Load Verification

**Current**: Unclear if save and load round-trip correctly
**Required**: Manual test + verification

**Test**: 
```
1. Create scene with GameObject
2. Add components (Transform, SpriteRenderer, RigidBody)
3. Right-click → Save as Prefab
4. Close scene
5. Create new scene
6. Drag prefab into hierarchy
7. Verify components exist
8. Save and reload scene
9. Verify prefab instance is correct
```

### Blocker 3: UI Asset Save Pipeline

**Current**: Unclear if UI Builder saves correctly to `.zui`
**Required**: Trace and document

**Test**:
```
1. Open UI Builder
2. Create simple layout
3. Save
4. Close
5. Examine .zui file (should be valid JSON)
6. Reopen scene
7. Verify UI appears
```

---

## RECOMMENDED NEXT STEPS

1. **Fix Blocker 1**: Add Logic Graph validation UI to editor
2. **Test Blocker 2**: Manually verify prefab round-trip
3. **Test Blocker 3**: Manually verify UI asset pipeline
4. **Then**: Proceed to CanonicalGameplayTest implementation

---

**Logged**: 2026-08-08  
**Audit Status**: INCOMPLETE (identified gaps for Phase 8B gates)
