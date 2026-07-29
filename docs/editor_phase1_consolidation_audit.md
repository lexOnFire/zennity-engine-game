# Phase 1 Editor Consolidation Audit

Generated: 2026-07-29

## Scope

The official editor entrypoint is `editor.phase1_main`.

`editor.studio_main` is no longer an independent editor. It is a compatibility launcher that redirects to `editor.phase1_main`, so the useful Studio-era work now lives in shared editor modules:

- `editor.runtime.tool_manager`
- `editor.runtime.viewport_*`
- `editor.viewport`
- `editor.gizmos`
- `editor.runtime.editor_bridge_orchestrator`
- `editor.visual_scripting`
- `editor.animation_studio`

## Classification

| Area | Current State | Decision | Notes |
|:---|:---|:---|:---|
| `phase1_main.py` | Official entrypoint, still owned bootstrap logic directly | Improve | Now delegates to `editor.editor_app.application`.
| `studio_main.py` | Compatibility redirect only | Discard later | Keep until old launch commands are no longer used.
| Tool shortcuts | Spread between toolbar actions and controller logic | Migrate | Centralized in `ShortcutService`.
| Tool Manager | Mature runtime service exists | Keep | Continue using as source of truth for embedded/editor widgets.
| Q/W/E/R | Present in Phase 1 isolated editor | Keep and standardize | Now registered through `ShortcutService`.
| Ctrl+D/Ctrl+Z/Ctrl+Y/Delete | Present in edit menu/controller | Keep and standardize | Now registered in the shared shortcut map.
| F focus selected | Missing in isolated viewport command path | Migrate | Added as `focus_selected`.
| G grid toggle | Missing in isolated viewport command path | Migrate | Added as `toggle_grid`.
| Viewport pan/zoom | Present in isolated viewport navigation | Keep | Middle mouse pan and wheel zoom already live in runtime.
| Snap | Present in isolated viewport control commands | Keep | Continue improving controls/UI.
| Animation | Integrated into detached Animator workspace | Keep | Old floating dock shell was removed in prior cleanup.
| Visual Graph | Modern hub is central | Keep | Behavior Tree, Dialogue, Material, Animator graph remain hub modes.
| UI Builder / Build / Diagnostics | Internal tools, not primary menu entries | Improve later | Keep code, do not expose as top-level visual clutter.
| Legacy windows/premium editor | Compatibility/reference paths | Discard later | Do not evolve as independent editors.

## Migration Rules

- Migrate architecture, not whole files.
- Keep `phase1_main.py` thin.
- New orchestration belongs under `editor/editor_app`.
- Shared services belong under `editor/services`.
- Mature runtime controllers stay in `editor/runtime` until a larger folder move is safe.
- Legacy launchers remain redirects until all external references are gone.

## Completed In This Pass

- Added `editor/editor_app/application.py` and `editor/editor_app/bootstrap.py`.
- Made `editor/phase1_main.py` a thin official entrypoint.
- Added `editor/services/shortcut_service.py`.
- Added `editor/controllers/tool_controller.py`.
- Moved tool activation out of `EditorCommandController`.
- Connected Phase 1 tool activation to `EditorContext.tools`.
- Standardized shortcuts:
  - `Q` select
  - `W` move
  - `E` rotate
  - `R` scale
  - `Ctrl+D` duplicate
  - `Ctrl+Z` undo
  - `Ctrl+Y` redo
  - `Delete` delete
  - `F` focus selected
  - `G` toggle grid
- Added isolated viewport commands for `focus_selected` and `toggle_grid`.

## Next Blocks

1. Move scene/hierarchy/inspector orchestration behind controller facades without changing behavior.
2. Make `ToolManager` the single source of truth for isolated editor tool state, not only embedded editor widgets.
3. Expand viewport command tests for focus, grid, snap and selection.
4. Consolidate Animation, Visual Graph, Behavior Tree, Dialogue, UI Builder and Material Graph under a single Phase 1 workspace registry.
5. Mark legacy editor windows as reference-only, then remove them after all useful behavior is represented in Phase 1.
