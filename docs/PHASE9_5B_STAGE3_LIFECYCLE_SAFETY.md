# PHASE 9.5B — Stage 3: Runtime Lifecycle Safety & Play/Stop Idempotence

Status: **complete**. Do not start Stage 4 from this document.

## The defect

`Play → Stop → Play` did not return to the same initial state. The measured
proof, before any change:

```
5 LogicGraphRuntime instances created and explicitly stopped
→ 5 UI dispatcher subscriptions accumulated (one per cycle, never removed)
→ 5 of 5 runtimes still reachable after gc.collect()
```

The chain had a single root. `LogicGraphRuntime.__init__` subscribed to the
module-global `UIEventDispatcher` with a closure over `self`, and the dispatcher
had **no `unsubscribe` at all** — only `subscribe` and `emit`. So:

1. every runtime stayed permanently reachable from a module global;
2. because it was reachable, `__del__` never ran;
3. `stop()` was only ever *called* from `__del__`, so the physics and animation
   handlers it unregisters were never released either.

Twenty Play cycles meant twenty live runtimes, each pinning its graph, its
values, and the previous session's game object.

Separately, five services shipped a `reset()` API that **nothing ever called**:
`UIRuntimeService`, `UIDataBindingManager`, `UIManager`, `SceneManager` and the
UI dispatcher. A scene transition requested during Play and never executed
survived into the next session.

## Lifecycle ownership

No new manager was introduced. The owners already existed:

| layer | owner | start | stop |
|---|---|---|---|
| Play session | `engine.runtime.RuntimeManager` | `start_play` | `stop_play` |
| Scene/world | `engine.runtime.RuntimeScene` | `start_runtime` | `stop_runtime` / `destroy` |
| Logic/animation/behaviour/dialogue | `editor.runtime.ViewportRuntimeInitializer` | `start` | `stop` → `_clear_runtime_state` |
| Single graph | `engine.logic.runtime.LogicGraphRuntime` | `__init__` | `stop` |

### Subsystem teardown table

| subsystem | reset called on Stop before | now | owner |
|---|---|---|---|
| Logic graph runtimes | yes (`runtime.stop()`) | yes | `_clear_runtime_state` |
| Physics handlers | yes, via `LogicGraphRuntime.stop` | yes | `LogicGraphRuntime` |
| Animation handlers | yes, via `LogicGraphRuntime.stop` | yes | `LogicGraphRuntime` |
| UI event dispatcher | **no — no API existed** | yes | `LogicGraphRuntime.stop` + `_reset_session_services` |
| UIRuntimeService | **no** | yes | `_reset_session_services` |
| UIDataBindingManager | **no** | yes | `_reset_session_services` |
| UIManager | **no** | yes | `_reset_session_services` |
| SceneManager (pending transitions) | **no** | yes | `_reset_session_services` |
| DialogueManager | yes | yes | `_clear_runtime_state` |
| Behaviour trees | yes | yes | `_clear_runtime_state` |
| CameraManager | yes | yes | `RuntimeScene.stop_runtime` |
| AudioManager + sound cache | yes | yes | `RuntimeScene.stop_runtime` |
| Asset cache | yes | yes | `RuntimeScene.stop_runtime` |
| Input | yes | yes | `RuntimeManager._cleanup_input` |

## Changes

- **`UIEventDispatcher`** gains `unsubscribe()`, `clear()` and
  `subscriber_count()`. This is the fix that unblocks everything else.
- **`LogicGraphRuntime.stop()`** now detaches its dispatcher subscription,
  releases `_last_game` / `_implicit_target`, clears session values and resets
  the event bus. It is called explicitly by the lifecycle owner; `__del__` is
  reduced to a backstop and is no longer the mechanism.
- **`ViewportRuntimeInitializer._reset_session_services()`** resets the five
  session-scoped singletons. Every step is isolated, so one failing subsystem
  is logged and teardown continues (item 28).

## Cache classification

| cache | lifetime | bound |
|---|---|---|
| `ImageComponent._transformed_cache` | project | 256 entries |
| `InfiniteBackground._tile_cache` | project | 64 entries |
| `AudioManager._sound_cache` | play session | cleared on Stop |
| `UIRenderer._font_cache` / `_image_cache` | play session | dies with its `RuntimeScene` |
| `engine.assets` cache | play session | cleared on Stop |

Project-lifetime caches are deliberately **not** cleared on Stop — doing so
would re-decode every texture on the next Play. They need a ceiling, not a
reset, and both already have one.

## Behaviour that was audited, not changed

**Play while playing** ignores the second request and returns the existing
session (`RuntimeManager.start_play` returns early when `runtime_scene` is set).
That is the documented behaviour; a test now pins it. No gameplay semantics were
touched — Stage 3 is lifecycle only.

## Testing note

The cycle, memory and crash tests run in a **fresh interpreter**. Handler
registries, service singletons and the dispatcher are process-global, and other
tests in the session leave runtimes alive in them; an in-process baseline picks
that contamination up and the comparison stops meaning anything. Subprocess
isolation is what makes "identical to baseline" a real claim rather than a lucky
test ordering.

`weakref` is used strictly as a **detector**. Cleanup is explicit; `gc.collect()`
only reveals whether a strong reference was left behind.

## Gates

```
pytest tests/runtime/test_play_stop_idempotence.py    # CI gate, 5 cycles
pytest -m slow                                        # 20-cycle + memory stress
```
