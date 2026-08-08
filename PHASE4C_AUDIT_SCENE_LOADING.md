# PHASE 4C AUDIT: Scene Loading Pipeline

**Data**: 2026-08-08  
**Status**: Audit Complete  
**Objective**: Find exact integration point for Scene.ui processing

---

## DISCOVERY: Real Scene Loading Pipeline

### Step 1: Scene File on Disk (.zscene)

**Example**:
```json
{
  "format_version": 2,
  "scene_name": "Game",
  "objects": [...],
  "ui": "Assets/UI/HUD.zui"
}
```

**Location**: User provides path to .zscene file

---

### Step 2: SceneDocument.load() 

**File**: `engine/scene/scene_document.py:66`

```python
@classmethod
def load(cls, path: str | Path) -> "SceneDocument":
    return cls.from_json(Path(path).read_text(encoding="utf-8"))
```

**What it does**:
- Reads .zscene JSON from disk
- Creates immutable SceneDocument wrapper
- Preserves ALL fields including "ui"

**Payload Access**:
```python
doc = SceneDocument.load("Game.zscene")
payload = doc.to_dict()  # Returns complete dict with "ui" field
ui_asset_path = payload.get("ui")  # "Assets/UI/HUD.zui"
```

---

### Step 3: Scene Deserialization

**File**: `engine/scene/scene_serializer.py:456`

```python
def deserialize_scene(data: dict[str, Any]) -> dict[str, Any]:
    """Deserialize .zscene data into a scene data model."""
    blackboard = data.get("blackboard")
    return {
        "format_version": int(data.get("format_version", ...)),
        "scene_name": str(data.get("scene_name", ...)),
        "engine_version": str(data.get("engine_version", ...)),
        "blackboard": dict(blackboard) if isinstance(blackboard, dict) else {...},
        "objects": [
            deserialize_game_object(item)
            for item in data.get("objects", [])
        ],
    }
```

**CRITICAL OBSERVATION**:
- `deserialize_scene()` processes "objects" key
- **Ignores "ui" key completely**
- Returns scene dict WITHOUT "ui" field
- This is where Phase 4C needs to integrate

---

### Step 4: GameObject Creation

**File**: `engine/scene/scene_serializer.py:348`

```python
def deserialize_game_object(data: dict[str, Any]) -> GameObject:
    """Build a GameObject from .zscene object data."""
    obj = GameObject(
        name=str(data.get("name", "GameObject")),
        ...
    )
    # ... assigns components
```

**What it does**:
- Creates GameObject for each "objects" entry
- Assigns components (Transform, Rigidbody, Camera, etc.)
- **Does NOT handle "ui" field**

---

### Step 5: RuntimeScene Creation & Lifecycle

**File**: `engine/runtime/runtime_manager.py:54`

```python
def start_play(self, editor_scene: Any) -> RuntimeScene:
    """Inicia o Play Mode."""
    if self.runtime_scene is not None:
        return self.runtime_scene
    
    Input.bind_manager(self.input)
    self._input_bound = True
    try:
        self.runtime_scene = RuntimeScene(editor_scene)  # <-- HERE
        self.runtime_scene.start_runtime()
        self._set_state(RuntimeState.PLAYING)
```

**File**: `engine/runtime/runtime_scene.py:14-32`

```python
class RuntimeScene:
    """Isolated Play Mode scene built from an editor scene."""
    
    def __init__(self, editor_scene: Any) -> None:
        self.editor_scene = editor_scene
        self.scene = type(editor_scene)()  # Create runtime scene instance
        self.scene.start()
        self._clone_editor_objects()  # Clones GameObjects
        self._copy_scene_state()      # Copies scene state
        
    def _clone_editor_objects(self) -> None:
        """Clones all editor GameObjects to runtime."""
        objs = getattr(self.editor_scene, "editable_objects", None)
        if objs is None:
            objs = getattr(self.editor_scene, "game_objects", [])
        for editor_obj in list(objs):
            runtime_obj = clone_game_object(editor_obj)
            # ... add to scene
```

**What it does**:
- Creates isolated runtime scene
- Clones all GameObjects
- Does NOT process Scene.ui field

---

### Step 6: on_runtime_start() Lifecycle Hook

**File**: `engine/runtime/runtime_scene.py:139-217`

```python
def start_runtime(self) -> None:
    if self._runtime_started:
        return
    
    # ... setup defaults (camera, audio)
    
    self.physics_world.build_from_scene(self)
    Physics.bind_world(self.physics_world)
    self.script_runtime.start(components)
    
    for component in components:
        self.lifecycle.register(
            LifecycleEntry(
                ...
                start=lambda component=component: 
                    self._call_component_hook(component, "on_runtime_start"),  # <-- HOOK
                ...
            )
        )
    
    self.lifecycle.start()  # Triggers on_runtime_start()
```

**What it does**:
- Registers all components to lifecycle scheduler
- Calls on_runtime_start() for each component
- UIRuntimeService auto-registers widgets here

---

### Step 7: Stop/Cleanup

**File**: `engine/runtime/runtime_manager.py:81`

```python
def stop_play(self) -> None:
    """Para o Play Mode."""
    if self.state == RuntimeState.STOPPED and self.runtime_scene is None:
        return
    self.runtime_scene.destroy()
    self.runtime_scene = None
```

**File**: `engine/runtime/runtime_scene.py:226`

```python
def stop_runtime(self) -> None:
    if not self._runtime_started:
        return
    self.lifecycle.stop()
    self.script_runtime.instances.clear()
    self.lifecycle.clear()
    self._runtime_started_components.clear()
    # ... cleanup
```

**What it does**:
- Calls on_runtime_stop() hooks
- Components call destroy() (which unregisters from UIRuntimeService)
- Scene cleaned up

---

## INTEGRATION POINT IDENTIFIED

### Current Flow (Phase 4B)
```
SceneDocument.load(.zscene)
  ↓
deserialize_scene()  ← "ui" field IGNORED
  ↓
GameObjects created (only from "objects" key)
  ↓
RuntimeScene(editor_scene)
  ↓
start_runtime()
  ↓
on_runtime_start() hooks called
  ↓
UIRuntimeService auto-registers components
```

### Phase 4C Flow (After Integration)
```
SceneDocument.load(.zscene)
  ↓
[NEW] Check if payload["ui"] exists
  ↓
[NEW] UIAssetLoader.load(ui_path)
  ↓
[NEW] UIRuntimeCompiler.compile(ui_doc)
  ↓
[NEW] Create UI GameObjects and attach to scene
  ↓
deserialize_scene()  ← Now includes UI-generated objects
  ↓
GameObjects created (both from "objects" + UI-generated)
  ↓
RuntimeScene(editor_scene)
  ↓
start_runtime()
  ↓
on_runtime_start() hooks called  ← UI components auto-register
  ↓
UIRuntimeService has both regular + UI widgets
```

---

## OWNERSHIP ARCHITECTURE

### Chosen Design: Dedicated UICanvas GameObject

Every Scene with Scene.ui will automatically have:

```
Scene
└── __UICanvas__  (hidden, runtime-generated)
    ├── HealthBar (GameObject)
    │   └── ProgressBarComponent (component)
    ├── ScoreLabel (GameObject)
    │   └── LabelComponent (component)
    └── StartButton (GameObject)
        └── ButtonComponent (component)
```

**Rationale**:
- Consistent with engine's GameObject hierarchy model
- Each UI widget is a first-class GameObject (supports hierarchy, transforms, etc.)
- Components are properly attached (follow engine patterns)
- Easy to enumerate and destroy on unload
- UICanvas marked runtime_hidden so not shown in editor

---

## SOURCE OF TRUTH

**Definitive principle**:
```
.zui = authoring source of truth

Scene.ui field references .zui path
  ↓
On Play, .zui is loaded fresh
  ↓
.zscene does NOT carry redundant copy of widget properties
  ↓
If HUD.zui changes:
  - Next Play loads new version automatically
  - No .zscene re-serialization needed
  - No cache invalidation needed
```

---

## ERROR HANDLING CONTEXT

When Scene.ui processing fails:

```
Error occurs during:
  UIAssetLoader.load(Scene.ui_path)
  OR
  UIRuntimeCompiler.compile(ui_doc)
```

Error message includes:
- Scene name (e.g., "Game.zscene")
- Asset path (e.g., "Assets/UI/HUD.zui")
- Specific error reason (e.g., "Duplicate widget name: HealthBar")

**Result**: User can immediately identify which Scene+Asset combo failed

---

## PATH RESOLUTION

**Relative paths**:
```
Scene.ui = "Assets/UI/HUD.zui"
  ↓
Resolved relative to Path.cwd() (project root)
  ↓
Must exist on disk before Play
```

**UIAssetLoader already handles this**:
```python
loader = UIAssetLoader(project_root=Path.cwd())
doc = loader.load("Assets/UI/HUD.zui")  # Relative
```

---

## LIFECYCLE SUMMARY

### Play Start
1. RuntimeManager.start_play(editor_scene)
2. RuntimeScene.__init__(editor_scene)
   - [NEW] Check Scene for "ui" field
   - [NEW] If exists: Load + compile + create UI GameObjects
   - Clone all GameObjects (including UI-generated)
   - Copy scene state
3. RuntimeScene.start_runtime()
   - Register components to lifecycle
   - Call on_runtime_start() on ALL components
   - UI components auto-register in UIRuntimeService
   - lifecycle.start()

### Play Update
- RuntimeManager.update() calls RuntimeScene.update()
- Components receive on_runtime_update() hooks
- Logic Graph can access UIRuntimeService

### Play Stop
- RuntimeManager.stop_play()
- RuntimeScene.destroy()
  - stop_runtime() calls lifecycle.stop()
  - All components receive on_runtime_stop()
  - UI components auto-unregister via destroy()
  - Scene cleaned up

### Replay
- New RuntimeScene created
- New UI GameObjects generated
- Fresh UIRuntimeService registrations
- No stale references

---

## INTEGRATION CHECKLIST

| Task | File | Location | Action |
|------|------|----------|--------|
| Check Scene.ui field | RuntimeScene.__init__ | Line 14-32 | Add UI detection |
| Load .zui asset | RuntimeScene.__init__ | Line 14-32 | Call UIAssetLoader |
| Compile widgets | RuntimeScene.__init__ | Line 14-32 | Call UIRuntimeCompiler |
| Create UI GameObjects | RuntimeScene.__init__ | After compile | Create GameObject + Component pairs |
| Add to scene | RuntimeScene.__init__ | After creation | Self.scene._add_go() or self.scene.game_objects.append() |
| Error handling | RuntimeScene.__init__ | Wrap in try/except | Clear diagnostics with Scene context |

---

## FILES REQUIRING MODIFICATION

| File | Modification | Impact |
|------|--------------|--------|
| `engine/runtime/runtime_scene.py` | Add UI loading in __init__ | Single point of integration |
| `engine/ui/asset_loader.py` | Already complete | No changes needed |
| `engine/ui/runtime_compiler.py` | Already complete | No changes needed |
| `engine/ui/runtime_components.py` | Already has on_runtime_start | No changes needed |
| `engine/ui/runtime_service.py` | Already handles registration | No changes needed |

**Total files to modify**: 1 (RuntimeScene)

---

## SUMMARY

**Integration Point**: `RuntimeScene.__init__()` after scene instantiation, before object cloning

**What needs to happen**:
```python
class RuntimeScene:
    def __init__(self, editor_scene: Any) -> None:
        self.editor_scene = editor_scene
        self.scene = type(editor_scene)()
        self.scene.start()
        
        # [NEW] Process Scene.ui if present
        self._compile_and_attach_ui()
        
        self._clone_editor_objects()  # Now includes UI-generated objects
        self._copy_scene_state()
```

**Complexity**: Low (one method, clear dependencies, uses existing Phase 4B components)

**Risk**: Very low (Phase 4B components already tested; only integration is new)

---

**Status**: Ready for Phase 4C.2 implementation
