# Editor Decomposition Plan

## Goal

Reduce the responsibilities of `IsolatedEditorWindow` without changing scene
formats, viewport IPC, editor appearance, or Play Mode behavior in one large
rewrite.

## Dependency direction

```text
Qt widgets / Pygame viewport
        -> application services
        -> scene document and commands
        -> engine runtime abstractions
```

The application and document layers must not import Qt or Pygame.

## Phase 1: state ownership

- `EditorState` owns transient session state such as selection, scene path,
  Inspector update guards, snap state, and Play Mode state.
- `SceneManager` owns the editable object collection and its name index.
- Existing fields in `IsolatedEditorWindow` remain temporarily as compatibility
  aliases while call sites migrate in small commits.

## Phase 2: command boundary

All scene mutations will move behind commands with `execute`, `undo`, and
`redo`. Snapshot-based history remains available during migration but stops
being the primary mutation mechanism.

Initial commands:

- CreateObjectCommand
- DeleteObjectCommand
- RenameObjectCommand
- MoveObjectCommand
- RotateObjectCommand
- ScaleObjectCommand
- AddComponentCommand
- RemoveComponentCommand
- AssignAssetCommand

## Phase 3: viewport decomposition

Split input, selection, gizmos, rendering, camera, and IPC command processing
while preserving the current process boundary.

## Safety rules

1. One architectural responsibility per PR.
2. No visual redesign mixed with structural extraction.
3. No scene serialization changes without migration tests.
4. Every extraction must preserve or increase test coverage.
5. Performance changes require before/after benchmark data.
6. Keep CI green on Python 3.10, 3.11, and 3.12.

## Acceptance criteria for Phase 1

- Application-layer modules import without Qt or Pygame.
- Scene indexing rejects duplicate or empty names.
- Snapshots crossing process/UI boundaries are defensive copies.
- Selection and Play Mode state are independently testable.
- Existing editor behavior remains unchanged until call sites are migrated.
