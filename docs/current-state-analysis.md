# Zennity Engine - Current State Analysis

Date: 2026-07-11

Branch reviewed: `zen/fix-phase1-tests`

## Executive Summary

The Zennity Engine has progressed from a tightly coupled 2D editor prototype into a broader engine architecture with editor runtime, Play Mode isolation, asset systems, components, inspector plugins, serialization, input, time, physics, camera, audio, animation/UI foundations, and editor polish work.

The current local state is functional and the complete test suite was last validated successfully:

```text
python -m pytest
1734 passed, 16 warnings
```

The most important current concern is not test failure. It is branch hygiene: the working tree contains many accumulated local changes, including core fixes, editor migration work, generated files, and temporary files. Before the next milestone, the changes should be reviewed and committed in small, focused commits.

## What Has Been Stabilized

The Phase1 editor has been stabilized after several important failures:

- Fixed editor startup issues around `game_viewport`.
- Avoided the crash caused by running two heavy viewport widgets with OpenGL/Pygame behavior at the same time.
- Introduced a lighter Game View path while keeping Scene View editable.
- Improved Scene/Game synchronization.
- Preserved object selection across Play/Stop.
- Kept Runtime World isolated from Editor World.
- Restored the editor test suite to a passing state.

Key files involved:

- `editor/phase1_editor.py`
- `editor/widgets/viewport_widget.py`
- `engine/runtime/runtime_scene.py`

## Recent Fixes

### Game View Objects Appearing Outside The Camera

Problem:

When pressing Play, objects could appear outside the expected Game View camera position.

Root cause:

- The runtime fallback camera did not copy the editor camera position and zoom.
- `Camera2D.main` is static/global state and could leak from the editor or previous runtime state.

Fix:

- `RuntimeScene` now isolates `Camera2D.main` during Play.
- The previous main camera is restored on Stop.
- The fallback runtime camera copies editor camera position and zoom when available.
- Runtime `Camera2D` components can become the runtime main camera.

File:

- `engine/runtime/runtime_scene.py`

### Player Falling Through Platform

Problem:

The Player fell through the platform during Play Mode.

Root cause:

`PhysicsWorld` detected contacts but did not resolve solid collisions.

Fix:

- Added simple collision resolution for `BoxCollider x BoxCollider`.
- Added simple collision resolution for `CircleCollider x CircleCollider`.
- Trigger contacts remain detection-only.

File:

- `engine/physics/physics_world.py`

### SpriteRenderer Compatibility In Tests

Problem:

Some animation tests monkey-patch `SpriteRenderer` with a fake implementation. Later editor/runtime tests could fail depending on test order.

Root cause:

The fake renderer did not fully match the component lifecycle contract expected by the editor/runtime.

Fix:

- `Editor2DScene` now creates sprite renderers through a safer helper.
- Runtime cloning normalizes cloned components with `_started`, `enabled`, and missing lifecycle methods.

Files:

- `editor_legacy/editor_2d.py`
- `engine/runtime/clone.py`

## Architecture Progress

### Editor Runtime

The project now has a clearer editor runtime direction:

- `EditorContext`
- `SelectionManager`
- `ToolManager`
- `CommandManager`
- `RuntimeManager`

This is the right architectural direction. The editor is gradually moving away from each panel owning its own state.

### Selection

Selection has improved, but legacy bridges still exist.

Current direction:

- `SelectionManager` should be the official source of selection.

Remaining compatibility:

- `selected_index` still exists in legacy scene paths.
- Some editor and viewport paths still synchronize back and forth with legacy scene selection.

This is acceptable temporarily, but should continue being reduced carefully.

### Scene Source Of Truth

The migration from `viewport.active_scene` toward `EditorContext` / `SceneModel` has started.

Improvements:

- `EditorContext` now has a scene provider.
- `editor_context.current_scene()` exists.
- `phase1_editor.py` uses `current_scene()` in important paths.
- `viewport_widget.py` started using `LegacySceneAdapter`.

Remaining issue:

`viewport.active_scene` still exists as a compatibility bridge and is still used by parts of the editor.

This should be removed gradually, not in one large refactor.

## Current Working Tree State

The branch has many local changes. Examples include:

- `editor/phase1_editor.py`
- `editor/widgets/viewport_widget.py`
- `editor/runtime/editor_context.py`
- `editor_legacy/editor_2d.py`
- `engine/runtime/runtime_scene.py`
- `engine/runtime/clone.py`
- `engine/physics/physics_world.py`

There are also untracked or generated files, including:

- `editor/runtime/legacy_scene_adapter.py`
- `editor/viewport/sprite_renderer.py`
- `scratch/`
- `test_box.py`
- `test_render.py`
- generated test images

Recommendation:

Review the working tree before committing. Separate core fixes from temporary files and unrelated changes.

## Technical Debt

### Legacy Scene Coupling

`Editor2DScene` still carries several responsibilities:

- object creation;
- editor selection compatibility;
- runtime object setup;
- draw/event behavior;
- default scene setup.

This should eventually move into cleaner models/services, but not through a large risky rewrite.

### Global Runtime State

Some systems still use static/global state:

- `Camera2D.main`;
- registries/managers;
- some runtime/editor singleton-like paths.

Recent fixes reduce risk, but the architecture should continue moving toward explicit runtime-owned state.

### Viewport Responsibility

The Viewport is better than before, but it still does more than pure drawing in some paths.

Long-term goal:

- Viewport draws and forwards input.
- EditorContext / SceneModel / tools own behavior.
- RuntimeManager owns Play Mode execution.

### Worktree Hygiene

The biggest immediate risk is not architecture. It is mixed local changes.

Before starting another phase, the current state should be cleaned into organized commits.

## Risk Assessment

| Area | Risk | Notes |
| --- | --- | --- |
| Runtime camera | Medium | Improved, but `Camera2D.main` is still global state. |
| Physics foundation | Medium | Basic collision resolution exists, but physics is still foundational. |
| Editor selection | Medium | `SelectionManager` exists, but legacy `selected_index` remains. |
| Viewport architecture | Medium | Still bridges legacy scene behavior. |
| Test stability | Low | Full suite passed with 1734 tests. |
| Worktree hygiene | High | Many local changes and generated files are mixed together. |

## Recommended Next Steps

1. Review the current diff.
2. Remove temporary/generated files only after explicit approval.
3. Keep the recent fixes in small focused commits:
   - Play/Game View camera stability;
   - Runtime `Camera2D` isolation;
   - basic physics collision resolution;
   - SpriteRenderer test-order compatibility.
4. Run the full suite again.
5. Commit and push only reviewed files.
6. Continue the `active_scene` migration in small steps.
7. Avoid starting a new major feature until the current branch is clean.

## Final Assessment

The engine is in a strong technical position for its current stage. The architecture is moving in the right direction, the test suite is green, and the recent Play Mode bugs have clear fixes.

The next priority should be stabilization discipline: clean commits, remove temporary files, and continue reducing legacy editor coupling slowly.

