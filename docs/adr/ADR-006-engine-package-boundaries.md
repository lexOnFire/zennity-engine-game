# ADR-006: Engine package boundaries

## Status

Accepted

## Context

The engine grew from root-level modules into domain packages. Audio and input
were still single files, while the intended public layout also named explicit
boundaries for events, serialization, utilities, and editor integration.
Several requested asset filenames already had richer implementations under
different names.

## Decision

- `engine.audio` and `engine.input` are packages and retain their existing
  public imports.
- `engine.core` owns application lifecycle and fundamental runtime types.
- `engine.assets` owns loading, metadata, cache lifetime, and asset adapters.
- `engine.events` and `engine.serialization` expose canonical public APIs while
  their mature implementations remain in their current owning modules.
- `engine.editor_support` is only an integration boundary. Qt widgets and
  editor workflows remain under `editor`.
- Compatibility modules are retained until their consumers migrate. New
  implementations must not be added to those shims.

Aliases such as `AssetManager` and `AssetCache` point to
`RuntimeAssetManager`; they do not create parallel managers or caches.

## Consequences

The requested package tree is available without breaking existing
`engine.audio` or `engine.input` users. The architecture gains stable public
paths, while follow-up migrations can remove legacy root shims incrementally.
Some implementation filenames intentionally remain more specific than the
conceptual target tree.
