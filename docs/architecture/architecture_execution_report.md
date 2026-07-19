# Zennity Engine — Architecture Execution Report

## Scope

This document records the first completed architecture stabilization delivery derived from the architectural audit tracked in issue #10.

The work was intentionally executed as a compatibility-first refactor. The editor UI, scene serialization format, Qt/Pygame process boundary, viewport protocol, Play Mode behavior, and existing visual appearance were not redesigned in this delivery.

## Completed changes

### 1. Application-layer boundary

A new `editor.application` package now owns editor-domain state independently from Qt and Pygame.

Added:

- `EditorState`
- `SceneManager`
- `CommandHistory`
- reversible scene commands

This establishes the dependency direction required for the long-term decomposition:

```text
Qt/Pygame adapters -> application services -> scene data
```

The application layer does not import Qt or Pygame.

### 2. EditorState

`EditorState` centralizes session state that was previously stored directly on the main editor window, including:

- selected object name;
- scene path and scene document;
- Inspector update guard;
- snap state;
- Play Mode state;
- runtime-object lookup lifecycle.

This creates a stable seam for progressively reducing `IsolatedEditorWindow` without a high-risk rewrite.

### 3. SceneManager

`SceneManager` now provides a single owner for the editable scene snapshot and its name index.

Implemented behaviors:

- defensive scene snapshots;
- full scene replacement;
- initial-scene reset;
- object lookup;
- add, remove, and rename operations;
- duplicate-name validation;
- empty-name validation;
- consistent rebuilding of the name index.

This removes the need for future features to mutate both a list and a separate lookup dictionary manually.

### 4. Command Pattern foundation

A framework-independent command system was introduced with:

- `EditorCommand` protocol;
- `CommandHistory`;
- `RenameObjectCommand`;
- `AddObjectCommand`;
- `RemoveObjectCommand`.

The history implementation guarantees:

- commands are added to history only after successful execution;
- a new command invalidates the redo branch;
- undo and redo replay the same domain operation;
- history can be cleared at scene/session boundaries.

This is the first step toward making commands the only legal mutation path in the editor.

### 5. Automated tests

Focused tests were added for:

- editor session state;
- scene ownership and indexing;
- duplicate and invalid names;
- reset and defensive snapshots;
- command execution;
- undo and redo;
- redo invalidation;
- restoration of removed objects;
- failed-command history integrity.

## Architectural decisions

### Compatibility before decomposition

The existing `IsolatedEditorWindow` remains operational as the integration shell. Services are introduced first and call sites will migrate in small groups. This avoids mixing structural change with UI redesign.

### Commands before Undo/Redo replacement

The legacy snapshot stacks should not be deleted until every relevant mutation has a command equivalent. During migration, compatibility aliases and adapters are permitted, but new editor mutations should use commands.

### Spatial Hash before QuadTree

For the physics broad phase, Spatial Hash remains the recommended first implementation because it is simpler to update for dynamic 2D objects, easier to benchmark, and lower risk than introducing a tree structure during editor decomposition.

### Execution plans before JIT

Visual logic optimization should first compile graph dictionaries into reusable execution plans. JIT or static Python generation should only be evaluated after profiling confirms that dispatch remains the dominant cost.

## Remaining roadmap

The following work remains intentionally outside this first delivery:

1. Wire `IsolatedEditorWindow` to `EditorState` and `SceneManager` through compatibility properties.
2. Migrate object create, delete, rename, transform, component, and asset assignment mutations to commands.
3. Replace full-scene Undo/Redo snapshots after command coverage is complete.
4. Split viewport input, renderer, camera, selection, and gizmo responsibilities.
5. Add Transform dirty propagation and cached local/world matrices.
6. Introduce render extraction, render queue, culling, and transformed-surface caching.
7. Add Spatial Hash broad-phase collision and benchmark it against the current pair scan.
8. Split `LogicGraphRuntime` into execution context, execution plan, event dispatch, debug session, and node operations.
9. Replace process-global lifecycle references with session-scoped services.
10. Add strict asset caching, explicit disposal, and safe script reload lifecycle.

## Validation policy

Every subsequent architecture PR must meet these conditions:

- no visual redesign mixed with structural refactoring;
- no scene format break without a migration path;
- no new test skip used to hide a regression;
- Python 3.10, 3.11, and 3.12 remain supported;
- Ruff remains clean;
- Windows export smoke remains green;
- performance claims include benchmark evidence;
- each PR is independently revertible.

## Risk assessment

Current risk of this delivery is low because the new services are isolated from Qt, Pygame, serialization, and viewport IPC. The main remaining risk is integration drift: while the window still owns legacy fields, future changes could bypass the new services. The next architecture PR should therefore connect the window to the application layer before adding unrelated editor features.

## GitHub tracking

- Architecture roadmap: issue #10
- First implementation: PR #11
- Working branch: `refactor/editor-state-scene-manager`

## Conclusion

The complete multi-version architecture roadmap is not a single safe code change. This delivery establishes the first production-grade boundary needed to execute it without destabilizing the release branch. The editor now has testable state ownership, deterministic scene indexing, and the beginning of a unified command mutation path.
