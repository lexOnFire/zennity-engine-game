# Phase 9.5A — Engine Stability Audit

**Date:** 2026-08-10
**Branch:** `fix/executor-port-contract`
**Scope:** read-only audit. No production code was modified.
**Tooling:** `scripts/audit_node_system.py`, `scripts/audit_silent_exceptions.py`,
`scripts/audit_large_files.py` (all created by this phase, all read-only).

Companion documents:
- `docs/PHASE9_5_NODE_SYSTEM_AUDIT.md`
- `docs/PHASE9_5_CRASH_ERROR_AUDIT.md`
- `docs/PHASE9_5_PERFORMANCE_BASELINE.md`
- `docs/PHASE9_5_REFACTOR_ROADMAP.md`

---

## 0. Codebase shape

| Metric | Value |
|---|---|
| Production `.py` files (`engine/` + `editor/`) | 639 |
| Production LOC | 90 060 |
| `engine/` modules | 324 |
| `editor/` modules | 327 |
| `editor_legacy/` modules (excluded from production counts) | 16 |
| Test files / test functions | 346 / 3 510 |
| Files > 500 lines | 26 |
| Files > 1000 lines | 1 |
| Files > 2000 lines | 0 |

**Headline:** the codebase is *not* suffering from god-files. It is suffering from
**contract drift between parallel subsystems** and from **near-total loss of error
visibility** (255 exceptions are swallowed with no trace whatsoever). The "engine feels
heavy / crashes without warning" symptom is explained far better by these two facts
than by file size or asset indexing.

---

## 1. Subsystem status matrix

Legend — STATUS: `READY` (works, observable, has lifecycle) / `PARTIAL` (works, gaps) /
`FRAGILE` (works by accident or with known silent failure modes) / `BROKEN`.

| # | Subsystem | STATUS | Owner (main module) | Global state | Threads | Lifecycle | Error handling | Known risks |
|---|---|---|---|---|---|---|---|---|
| 1 | Application startup | PARTIAL | `editor/isolated_editor_main.py` | NO | Yes (mp.Process) | explicit | good (only place with `sys.excepthook`) | 2.0 s cold import; numpy is 48 % of it |
| 2 | Editor bootstrap | PARTIAL | `editor/editor_bootstrap_controller.py`, `EditorBridgeOrchestrator` | YES (8 `instance()` singletons) | Qt timers | mixed | partial | bridges have 10/10 and 9/9 dangerous handlers |
| 3 | Project loading | PARTIAL | `editor/runtime/editor_context.py` | NO | NO | explicit | partial | `Path.cwd()` used as project root in 2 places |
| 4 | Asset database / index | READY | `engine/assets/asset_database.py`, `editor/assets_panel_controller.py` | NO | QFileSystemWatcher + 220 ms debounce | explicit (`install`/`uninstall`) | partial | full tree rebuild per refresh, but state is preserved and it costs ~10 ms |
| 5 | Scene lifecycle | PARTIAL | `engine/core/scene_manager.py`, `engine/scene/scene_serializer.py` | YES (`SceneManager.instance()`) | NO | mixed | partial | `SceneManager.reset()` exists but is never called on Stop |
| 6 | Viewport lifecycle | FRAGILE | `editor/isolated_viewport.py`, `editor/runtime/viewport_session.py` | NO (separate process) | mp.Process | explicit | **silent** | 4 swallowed handlers in `run_viewport()` itself — the process can die mute |
| 7 | Play / Stop | FRAGILE | `editor/runtime/viewport_play_commands.py` → `viewport_runtime_initializer.py` | YES | NO | explicit but **incomplete** | partial | see §4 — 6 subsystems have no teardown |
| 8 | Logic Graph | FRAGILE | `engine/logic/runtime/core.py` (811 L) | YES (2 registries) | NO | explicit | partial | **167 node contract violations**; see node audit |
| 9 | Physics | PARTIAL | `engine/physics/physics_world.py` (570 L) | YES (module-level handler list) | NO | explicit | partial | `physics_event_dispatch` handlers unregistered in a `try/except: pass` |
| 10 | Animation | PARTIAL | `engine/animation/animator.py`, `engine/logic/animation_event_dispatch.py` | YES (module-level handler list) | NO | explicit | partial | same unregister-swallow pattern as physics |
| 11 | UI | FRAGILE | `engine/ui/runtime_service.py`, `ui_manager.py`, `runtime_components.py` | YES (3 singletons) | NO | **implicit** | partial | `UIRuntimeService.reset()` / `UIManager.reset()` / `UIDataBindingManager.reset()` all exist and none is called on Stop |
| 12 | Dialogue | FRAGILE | `engine/dialogue/manager.py` | YES (`get_dialogue_manager()`) | NO | explicit (only subsystem reset on Stop) | **silent** | **broken event bridge** — calls `LogicEventBus.get_instance()`, which does not exist; the `AttributeError` is caught and printed |
| 13 | Save / Load | PARTIAL | `engine/core/save_manager.py` | YES (`get_save_manager()`) | NO | implicit | partial | returns `False` sentinel on failure with no log |
| 14 | Audio | PARTIAL | `engine/audio/__init__.py` | YES (class-level `_sound_cache`) | pygame mixer | explicit start/stop | partial | `_sound_cache` is unbounded and never cleared |
| 15 | Prefabs | READY | `engine/prefabs/`, `engine/logic/runtime/nodes/prefab_nodes.py` | NO | NO | explicit | partial | contract violations on `create_object` / `clone_object` |
| 16 | Inspector | PARTIAL | `editor/premium_inspector_panel.py`, `editor/inspector_controller.py` | NO | NO | implicit | partial | `refresh_inspector()` called from 6 mutation sites; full rebuild each time |
| 17 | Hierarchy | PARTIAL | `editor/premium_hierarchy_panel.py` | NO | NO | implicit | partial | `refresh_objects()` does `tree.clear()` + full rebuild and **loses expansion + scroll state** |
| 18 | Asset Browser | READY | `editor/assets/project_browser.py`, `editor/assets_panel_controller.py` | NO (bounded 256-entry icon cache) | QTimer + watcher | explicit | partial | best-behaved panel in the editor; use as the reference pattern |
| 19 | Background threads | PARTIAL | 28 files | — | 28 | mixed | **silent** | 15 files start timers/threads with no matching stop; `threading.excepthook` absent |
| 20 | Global registries | FRAGILE | `NodeRegistry`, `NodeDefinitionRegistry`, `MetadataManager`, `component_registry` | YES | NO | implicit (import-time) | partial | two competing node registries; registration happens at import time |
| 21 | Singleton services | FRAGILE | 18 accessors (see §3) | YES | NO | mixed | partial | only 1 of 5 resettable singletons is reset on Stop |
| 22 | Event systems | FRAGILE | 5 parallel buses (see §5) | YES | NO | mixed | partial | one bridge between them is dead code |
| 23 | Timers | PARTIAL | 24 files using `QTimer` | NO | Qt event loop | mixed | partial | 7 files create timers with no `.stop()` anywhere |
| 24 | Resource caches | PARTIAL | `engine/ui/runtime_components.py`, `ui_renderer.py`, `audio` | YES | NO | implicit | n/a | 3 unbounded caches; `sprite_performance_patch.py` **removes** eviction |
| 25 | Shutdown | FRAGILE | `editor/isolated_editor_main.py` | — | mp.Process | explicit-ish | partial | no `atexit`, no `threading.excepthook`; QThreads started without join |

**Tally:** READY 3 · PARTIAL 13 · FRAGILE 9 · BROKEN 0

---

## 2. Module / package shadowing (silent dead code)

Python resolves a package before a sibling module of the same name. Two files in the
tree are therefore **unreachable and permanently dead**, while still being edited and
read by humans:

| Dead file | Lines | Shadowed by |
|---|---|---|
| `engine/logic/node_definitions.py` | **837** | `engine/logic/node_definitions/` |
| `engine/core.py` | 36 | `engine/core/` |

Verified at runtime:

```
>>> import engine.logic.node_definitions as m; m.__file__
.../engine/logic/node_definitions/__init__.py
```

`engine/logic/node_definitions.py` is the 3rd largest file in the entire codebase and
it has never executed. This is a strong candidate for the "I fixed it and nothing
changed" class of confusion.

Deliberate deprecation shims (these emit `warnings.warn()` at import and are *correct*):
`engine/component.py`, `engine/scene_manager.py`, `engine/graphics/renderer2d.py`,
`engine/graphics/tilemap.py`, `editor/phase1_editor.py`, `editor/premium_panels.py`.

---

## 3. Global state and singletons

**184 module-level mutable globals across 146 files.** The overwhelming majority are
`CONST_CASED` literal dicts used as lookup tables — technically mutable but treated as
read-only data. They are classified **SAFE SERVICE** and are not a priority.

**18 singleton accessors:**

| Accessor | Classification | Notes |
|---|---|---|
| `engine/core/context.py::EngineContext.current()` | SAFE SERVICE | context object, scoped |
| `engine/application.py::current()` | SAFE SERVICE | |
| `engine/time.py::current()` | SAFE SERVICE | |
| `engine/core/scene_manager.py::SceneManager.instance()` | **NEEDS LIFECYCLE** | `reset()` exists, never called on Stop |
| `engine/ui/runtime_service.py::instance()` | **NEEDS LIFECYCLE** | `reset()` exists, never called on Stop |
| `engine/ui/ui_manager.py::instance()` | **NEEDS LIFECYCLE** | `reset()` called only from `SceneManager`, not from Play/Stop |
| `engine/ui/data_binding.py::instance()` | **NEEDS LIFECYCLE** | `reset()` exists, never called anywhere |
| `engine/dialogue/manager.py::get_dialogue_manager()` | SAFE SERVICE | the one singleton correctly reset on Stop |
| `engine/core/save_manager.py::get_save_manager()` | NEEDS LIFECYCLE | no reset |
| `engine/logic/node_definitions/registry.py::get_registry()` | **RISKY GLOBAL STATE** | competes with `engine/logic/runtime/registry.py::registry` |
| `engine/logic/runtime/registry.py::registry` (module global) | **RISKY GLOBAL STATE** | populated by import side effects; see node audit |
| `editor/core/action_system.py::instance()` | SAFE SERVICE | editor-lifetime |
| `editor/core/editor_application.py::instance()` | SAFE SERVICE | editor-lifetime |
| `editor/core/theme_manager.py::instance()` | SAFE SERVICE | editor-lifetime |
| `editor/workspace/document_framework.py::instance()` | SAFE SERVICE | editor-lifetime |
| `editor/workspace/tool_registry.py::instance()` | SAFE SERVICE | editor-lifetime |
| `editor/runtime/bidirectional_debug_bridge.py::instance()` | NEEDS LIFECYCLE | holds per-Play debug state |
| `editor/runtime/execution_analysis_framework.py::instance()` | NEEDS LIFECYCLE | holds per-Play trace state |
| `editor/visual_scripting/runtime_explain_mode.py::instance()` | NEEDS LIFECYCLE | holds per-Play state |

**SAFE SERVICE 10 · NEEDS LIFECYCLE 6 · RISKY GLOBAL STATE 2.**

### Import-time side effects
53 module-level calls across 18 modules perform real work at import. The significant ones:

- `engine/logic/node_definitions/__init__.py` — runs `_populate_declarative_node_definitions()`
  and `_populate_node_definitions()`, importing 20 submodules and instantiating a
  `MetadataManager`. Cost: **138 ms** just to `import`.
- `engine/core/component_registry.py` — 6 `register()` calls.
- `editor/gizmos/gizmo_registry.py` — 5 `register()` calls.
- `engine/logic/graph_asset.py` — 5 mutations of `NODE_PORT_DEFINITIONS` at import.

These make registration order significant and untestable in isolation.

---

## 4. Play / Stop lifecycle

### Play path (verified)

```
viewport_play_commands._play()
  ├── snapshot edit state         (state.edit_snapshot = deepcopy(self.objects))
  ├── reset_physics()
  ├── clear_hud()
  ├── start_logic(blackboard)
  │     └── viewport_runtime_initializer.start()
  │           ├── _create_logic_services()   → BlackboardStore + fresh LogicEventBus
  │           └── per object:
  │                 ├── _initialize_animation()   (AnimatorControllerRuntime)
  │                 ├── _initialize_behavior()    (BehaviorGraphRunner / ControllerRunner)
  │                 ├── _initialize_dialogue()    (DialogueSession)
  │                 └── _initialize_logic()       (LogicGraphRuntime per graph)
  ├── start_audio()
  └── emit play_state
```

### Stop path (verified)

```
viewport_play_commands  "stop"
  ├── stop_audio()
  └── stop_logic() → runtime_initializer.stop(active_contacts)
        ├── _clear_runtime_state()
        │     ├── behavior_runners[*].stop(api)      ✔
        │     ├── logic_runtimes[*][*].stop()        ✔ (unregisters physics + animation handlers)
        │     ├── clear: logic_runtimes, logic_modules, logic_apis,
        │     │          animator_controllers, behavior_runners,
        │     │          initialized_ids, animator_event_signatures   ✔
        │     └── get_dialogue_manager().reset()     ✔
        ├── active_contacts.clear()                  ✔
        └── emit logic_trace_clear                   ✔
```

### Teardown checklist — what is missing

| Subsystem | Torn down on Stop? | Reset API available? |
|---|---|---|
| Logic graph runtimes | ✔ | — |
| Behavior runners | ✔ | — |
| Animator controllers | ✔ | — |
| Dialogue manager | ✔ | — |
| Physics event handlers | ✔ (but inside `try/except: pass`) | — |
| Animation event handlers | ✔ (but inside `try/except: pass`) | — |
| Active contacts | ✔ | — |
| **`UIRuntimeService`** | ✘ | `UIRuntimeService.reset()` exists |
| **`UIManager`** | ✘ | `UIManager.reset()` exists |
| **`UIDataBindingManager`** | ✘ | `UIDataBindingManager.reset()` exists |
| **`SceneManager`** | ✘ | `SceneManager.reset()` exists |
| **State-machine node state** | ✘ | none — lives in `runtime._node_state`, freed with the runtime, but `create_state_machine` stores into module scope |
| **Particle systems** | ✘ | none |
| **Pathfinding / follow-path state** | ✘ | none |
| **Camera follow / shake** | ✘ | none — camera stays shaking/following after Stop |
| **Audio `_sound_cache`** | ✘ (by design, but unbounded) | none |
| **Debug/trace singletons** (3 editor ones) | ✘ | none |

**Conclusion:** Stop tears down the *graph* layer correctly and leaves the *service*
layer dirty. Symptom to expect: second and subsequent Play sessions behave differently
from the first (stale UI bindings, camera still following a destroyed object, HUD
values carried over). This matches the reported "engine behaves unpredictably during
prolonged use".

---

## 5. Event systems — divergence measurement

Five independent event mechanisms, none unified:

| System | Module | Sync/queued | Ownership | Cleanup | Dedup | Thread safety |
|---|---|---|---|---|---|---|
| `LogicEventBus` | `engine/logic/event_bus.py` (73 L) | **queued** (`deque`, `dispatch()` drains, cap 128/frame) | per-Play instance, created in `_create_logic_services` | implicit (dropped with the instance) | yes — `subscribe` rejects duplicate callbacks | none (single-threaded by assumption) |
| `EventBus` | `engine/event_bus.py` (187 L) | sync | global | none | no | none |
| Physics event dispatch | `engine/logic/physics_event_dispatch.py` | **sync**, module-level handler list | module global | explicit `unregister_*` — wrapped in `except: pass` | no | none |
| Animation event dispatch | `engine/logic/animation_event_dispatch.py` | **sync**, module-level handler list | module global | explicit `unregister_*` — wrapped in `except: pass` | no | none |
| Qt signals | throughout `editor/` | sync (same-thread) / queued (cross-thread) | per-widget | `disconnect()` in 1 controller only | Qt-level | Qt-managed |

Plus two aliasing shims: `engine/core/event_bus.py` (9 L, re-exports `engine/event_bus.py`)
and `engine/events/__init__.py` (6 L, re-exports the same). Three import paths for one class.

### Broken bridge (confirmed defect)

`engine/dialogue/manager.py:326` does:

```python
from engine.logic.event_bus import LogicEventBus
bus = LogicEventBus.get_instance()      # AttributeError — no such classmethod
```

Verified: `hasattr(LogicEventBus, 'get_instance') == False`. The resulting
`AttributeError` is caught by `except Exception as e: print(...)` at line 341.

**Effect:** dialogue events have never reached Logic Graphs. The feature fails silently
into stdout. This is the archetype of the problem this phase exists to find.

---

## 6. Thread / worker inventory

28 files create threads, timers, watchers or subprocesses. No `threading.excepthook` is
installed anywhere, so **an exception in any worker thread is written to stderr and
otherwise vanishes**.

| Kind | Count | Notes |
|---|---|---|
| `QTimer` | 24 files | 7 have no `.stop()` anywhere in the file |
| `QThread` | 1 file (`editor/wizards/build_wizard_dock.py`, x3) | `.start()` with no `.quit()`/`.wait()` — **can outlive shutdown** |
| `QFileSystemWatcher` | 1 file (`editor/assets_panel_controller.py`) | correctly uninstalled |
| `multiprocessing.Process` | `editor/isolated_editor_main.py` → viewport | correct; queues use `cancel_join_thread` (commit `4f28c5a8`) |
| `ThreadPoolExecutor` | 0 | — |

**Files that start something and never stop it:**
`editor/animation_studio/animation_studio_dock.py`, `editor/assets_panel_controller.py`,
`editor/autosave_manager.py`, `editor/editor_session_controller.py`,
`editor/material_graph/preview_widget.py`, `editor/profiler/profiler_dock.py`,
`editor/scene_autosave_controller.py`, `editor/visual_scripting/mini_live_viewport.py`,
`editor/visual_scripting/visual_profiler_widget.py`, `editor/widgets/game_viewport.py`,
`editor/widgets/render_pipeline_profiler.py`, `editor/widgets/viewport_gizmo_drag.py`,
`editor/widgets/viewport_widget.py`, `editor/wizards/build_wizard_dock.py`.

Only `build_wizard_dock.py` (QThread) can genuinely survive shutdown; the QTimer cases
die with their parent widget but keep firing callbacks against partially-torn-down
state during teardown — a plausible source of the "crash on close" class of report.

---

## 7. Import / dependency direction

**Good news:** `engine` → `editor` violations: **0**. The layering rule is respected.

```
        EDITOR   (327 modules)  ── may depend on ──►  ENGINE
        ENGINE   (324 modules)  ── depends on ────►   nothing above it   ✔
```

**Bad news:** the layering *within* each side has collapsed into one giant cycle.

| Finding | Count |
|---|---|
| engine → editor imports | 0 ✔ |
| module-level import cycles (SCC) | 4 |
| package-level cycles | 2 |

**Cycle 1 — the big one (24 modules, all of `engine`'s core):**
`animation_controller ↔ animator ↔ audio ↔ script_component ↔ core ↔ component ↔
component_registry ↔ engine ↔ scene ↔ scene_manager ↔ game_object ↔ active_camera ↔
camera ↔ camera_manager ↔ material_property_animator ↔ renderer ↔ tilemap ↔ collider ↔
rigidbody ↔ tilemap_collider ↔ tilemap ↔ dialogue_manager ↔ runtime_components ↔ ui_binder`

This is why 18 of `engine`'s packages form a single package-level SCC. It is held
together by deferred (function-local) imports; it works, but it means no part of
`engine` can be imported, tested, or reasoned about in isolation, and import order
is load-bearing.

**Cycle 2:** `engine.graphs.core.node ↔ engine.graphs.core.pin` (2 modules).
**Cycle 3:** `editor.widgets.logic_graph.{blackboard_mixin, group_item, items} ↔ editor.widgets.logic_graph_editor` (4).
**Cycle 4:** `editor.visual_scripting.{dock_workspace_sync ↔ visual_scripting_dock}` (2).

### Proposed dependency direction

```
   ┌─────────────────────────────────────────────┐
   │  EDITOR       editor/*                      │  may import RUNTIME + ENGINE
   ├─────────────────────────────────────────────┤
   │  RUNTIME      engine/logic/runtime,         │  may import ENGINE
   │               engine/runtime, engine/ai     │
   ├─────────────────────────────────────────────┤
   │  ENGINE       engine/core, game_object,     │  may import CONTRACTS only
   │               physics, graphics, ui, audio  │
   ├─────────────────────────────────────────────┤
   │  CONTRACTS    engine/core/metadata,         │  imports nothing internal
   │               node/pin definitions, types   │
   └─────────────────────────────────────────────┘
```

Breaking cycle 1 means extracting a CONTRACTS layer: `Component`, `Transform`,
`GameObject` protocol, and the metadata/pin types must not import concrete
`physics`/`graphics`/`ui`. That is the single highest-leverage architectural change
available, and it is a **P1**, not a P0 — nothing is currently broken by it.

---

## 8. Duplicated subsystems

| # | Duplication | Evidence | Verdict |
|---|---|---|---|
| 1 | **4 graph frameworks** | `engine/logic` (11 993 L, the real one), `engine/graphs` (713 L), `engine/plugins/logic` (874 L, 37 node classes), `engine/graph` (227 L) | 1 814 L of parallel graph machinery not used by the shipping Logic Graph pipeline |
| 2 | **2 node registries** | `engine/logic/node_definitions/registry.py::NodeDefinitionRegistry` (canonical/legacy resolver, 233 L) vs `engine/logic/runtime/registry.py::NodeRegistry` (executors/evaluators, 61 L) | neither knows about the other; `sync_logic_registry_to_metadata` is the fragile bridge |
| 3 | **2 node registration paths** | `engine/logic/runtime/nodes/__init__.py` imports **14** modules; `LogicProvider.boot()` imports **22** and then hand-registers ~110 definitions across 250 lines | divergent — see node audit §2 |
| 4 | **2 DialogueManager classes** | `engine/dialogue/manager.py` (440 L) and `engine/ui/dialogue_manager.py` (292 L) | both live; `engine/ui/__init__.py` exports the UI one |
| 5 | **3 import paths for `EventBus`** | `engine/event_bus.py`, `engine/core/event_bus.py`, `engine/events/__init__.py` | 2 are shims |
| 6 | **2 visual-scripting node sets** | `engine/scripting/visual_scripting_nodes.py` defines `IfElseNode`, `SetPositionNode`, `LogMessageNode` — same names as `engine/logic/node_definitions/*` | shadow set, unused by the runtime |
| 7 | **`play_animation` defined twice** | `node_definitions/actions_nodes.py:7` and `node_definitions/animation_nodes.py:6`, **same id, different ports** | see node audit — this is a P0 |
| 8 | **Dead shadowed modules** | `engine/logic/node_definitions.py` (837 L), `engine/core.py` (36 L) | unreachable |

**Duplicated subsystems: 8.**

---

## 9. Dead code candidates

215 top-level symbols are defined exactly once and never named again anywhere in
production *or* tests. **These must not be deleted blindly** — a large subset are node
definition classes that are discovered reflectively:

```python
# engine/logic/node_definitions/__init__.py::_collect_declarative_definitions
for value in vars(module).values():
    definition = getattr(value, "__node_definition__", None)
```

So `GetAnimationTimeNode`, `OnCollisionEnterNode`, `PauseAnimationNode`, etc. *are*
live — they are just never referenced by name. Classification:

| Class | Count (approx) | Action |
|---|---|---|
| Reflectively-discovered node definitions | ~120 | **KEEP** — but note they bypass `LogicProvider.boot`'s explicit list, which is the root of registration divergence |
| `EngineProvider` subclasses never registered (`AnimationProvider`, `AssetProvider`, `PluginProvider`, `LocalizationProvider`) | 4 | **INVESTIGATE** — providers that exist but are never booted |
| Unused editor widgets (`CollapsibleSection`, `MeshRendererWidget`, `DocumentationDock`, `ViewportDock`, `StudioWindow`, `FixedStudioWindow`) | 6 | **DEPRECATE** candidates |
| Unused graph-framework entry points (`GraphSerializer`, `import_legacy_zlogic`) | 2 | tied to duplication #1 |
| Genuinely orphaned helpers (`install_gizmo_runtime`, `install_viewport_selection_api`, `cleanup_editable_objects`, `get_node_group_path`, `get_all_groups`, `SetTransformPropertyCommand`, `SelectedKeyframe`, `TextRenderer`) | 8 | **REMOVE** candidates (pending confirmation) |
| Remainder | ~75 | needs per-symbol review |

**Dead code candidates (high confidence): 20.** Nothing has been deleted.

---

## 10. Memory / resource caches

| Cache | Bounded? | Evicted? | Cleared on Stop? |
|---|---|---|---|
| `editor/assets_panel_controller.py::_ICON_CACHE` | ✔ 256 | ✔ FIFO | n/a |
| `engine/ui/runtime_components.py::ImageComponent._surface_cache` | ✔ 128 | ✔ `OrderedDict` | ✘ |
| `engine/ui/runtime_components.py::ImageComponent._transformed_cache` | ✔ 256 | ✔ | ✘ |
| `engine/ui/runtime_components.py::InfiniteBackground._tile_cache` | ✔ 64 | ✔ | ✘ |
| `engine/runtime/production_runtime.py::_cache` | ✔ MB budget | ✔ LRU | n/a |
| **`engine/audio/__init__.py::_sound_cache`** | ✘ | ✘ | ✘ |
| **`engine/ui/ui_renderer.py::_font_cache`** | ✘ | ✘ | ✘ |
| **`engine/ui/ui_renderer.py::_image_cache`** | ✘ | ✘ | ✘ |
| `engine/ui/panel.py::_surf_cache` | single surface | n/a | ✘ |
| `engine/localization/manager.py::_caches` | per-locale | ✘ | n/a |

**Active regression:** `engine/ui/sprite_performance_patch.py` replaces the bounded
`OrderedDict` caches with plain `dict`s:

```python
ImageComponent._transformed_cache = {}     # line 48
InfiniteBackground._tile_cache     = {}     # line 114
```

The eviction code in `runtime_components.py` relies on `OrderedDict.popitem(last=False)`.
Once this patch is applied, those two caches grow without bound for the rest of the
session. **Three unbounded caches + one patch that un-bounds two more.**

---

## 11. UI responsiveness — heavy work on the UI thread

| Operation | Thread | Measured / assessed | Freeze risk |
|---|---|---|---|
| Asset rescan (`glob` 716 paths) | UI | 9.9 ms | LOW |
| `.zscene` JSON parse (22 files) | UI | 5.1 ms | LOW |
| `.zlogic` JSON parse (56 files) | UI | 9.6 ms | LOW |
| `import engine.logic.node_definitions` | UI, at startup | **137.7 ms** | MEDIUM — one-off |
| `import numpy` (pulled by `engine/core/component.py`) | UI, at startup | **151 ms standalone / ~951 ms cumulative cold** | **HIGH** — 48 % of a 2.0 s startup |
| Thumbnail generation (`QPixmap.scaled`) | UI | cached at 256 entries | LOW |
| Hierarchy full rebuild | UI | O(objects) per selection change | MEDIUM at scale |
| Inspector full rebuild | UI | called from 6 mutation sites | MEDIUM |
| Logic Graph validation | UI | not benchmarked (needs Qt) | UNKNOWN |
| Scene compilation on Play | UI → then IPC to viewport process | `deepcopy(self.objects)` | MEDIUM |

The asset database is **not** the source of the perceived heaviness at this project
size (716 assets). Startup import cost and per-Play `deepcopy` are the real candidates.

---

## 12. Safe mode — feasibility

**Verdict: feasible and cheap (~1 day).** The editor already has the necessary seams:

| Requirement | Seam that already exists |
|---|---|
| don't open last scene | `EditorContext(Path.cwd())` + explicit `.zscene` open — engine already starts blank (known behaviour) |
| don't start Play | Play is command-driven via `viewport_play_commands`; simply reject `"play"` |
| don't load optional plugins | `EngineProvider` / `bootstrap.py::_topological_sort` — skip non-core providers |
| don't execute Logic Graph | `LogicProvider.boot()` is a single provider; omit it |
| don't restore docks | dock state restore is in `EditorBootstrapController` |

Proposed: `python -m editor.isolated_editor_main --safe-mode`, threaded through
`EditorBootstrapController` as a single `SafeModeConfig` dataclass. **Proposal only —
not implemented.**

---

## 13. Diagnostics window — proposal

`Help → Diagnostics`, read-only, refreshed on demand. `engine/diagnostics/` already
exists as a home. Panels:

| Panel | Data source (already available) |
|---|---|
| Engine | version, Python, OS, platform, `EngineContext.current()` services |
| Project | root path, asset count, last full rescan timestamp |
| Scene | active scene, object count, component histogram |
| Logic Graph | `len(registry.executors)`, `len(registry.evaluators)`, definitions count, **live contract-violation count** (reuse `scripts/audit_node_system.py` logic) |
| Physics | body count, contact count, handler count in `physics_event_dispatch` |
| UI | `UIManager` widget count, cache sizes for the 3 unbounded caches |
| Memory | `tracemalloc` snapshot, per-cache entry counts |
| Threads | `threading.enumerate()`, QTimer inventory, viewport process alive/PID |
| Events | `LogicEventBus.recent` (already retains the last 12 events), queue depth, subscriber counts |

**Proposal only — not implemented.**

---

## 14. Test suite audit

| Category | Test functions |
|---|---|
| unit / other | 1 750 |
| integration | 806 |
| editor | 627 |
| runtime | 327 |
| **Total** | **3 510** |

Structural assertions (`assert hasattr` / `isinstance` / `callable` / `in dir()`): **258**.

**Gap analysis.** 3 510 tests coexist with 167 node contract violations, a dead
`LogicEventBus.get_instance()` call, and a completely dead 837-line module. This is the
signature of a suite that verifies **structure** (does the symbol exist, does the dict
have the key) rather than **behaviour** (does a graph authored in the editor actually
execute end-to-end). Only 327 tests are runtime-flavoured, against 11 993 lines of
`engine/logic`.

The highest-value test to add is not a unit test — it is the contract test that
`scripts/audit_node_system.py` already implements. Wiring it into CI as an assertion
(`violations == 0`) would have caught every P0 in this report.

---

## 15. Scores

| Dimension | Score | Rationale |
|---|---|---|
| **ENGINE STABILITY** | **4/10** | no crashes from bad architecture, but 255 swallowed exceptions mean failures present as "nothing happened" |
| **ARCHITECTURE ORGANIZATION** | **5/10** | layering rule (engine ⊁ editor) is clean and respected; undermined by a 24-module cycle, 4 parallel graph frameworks and 2 dead shadowed modules |
| **NODE SYSTEM** | **3/10** | 167 contract violations, 2 registries, 2 registration paths, a duplicated node id with conflicting ports |
| **ERROR OBSERVABILITY** | **2/10** | 470/612 handlers silent; 13 files use `logging`, 138 `print()` calls; no crash report, no log rotation, no thread excepthook |
| **LIFECYCLE SAFETY** | **4/10** | graph layer teardown is correct; service layer leaks across every Play/Stop cycle |
| **EDITOR RESPONSIVENESS** | **6/10** | asset pipeline is fast and well-behaved; startup is 2.0 s of which numpy is half; hierarchy/inspector do full rebuilds |
| **MAINTAINABILITY** | **5/10** | file sizes are healthy and tests are numerous; but duplication and reflective registration make change-impact unpredictable |

---

*End of Phase 9.5A stability audit. No production code was modified.*
