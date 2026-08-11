# Phase 9.5B Stage 0 — Make Failure Visible

**Date:** 2026-08-10
**Goal:** no critical engine failure may die in silence.
**Non-goal:** changing behaviour. Stage 0 changes *visibility only*.

Follows `docs/PHASE9_5_CRASH_ERROR_AUDIT.md`. Stage 1 (node contracts) is **not** started.

---

## 1. What was built

### `engine/diagnostics/` — one implementation, shared by every process

| Module | Lines | Responsibility |
|---|---|---|
| `logging_setup.py` | 244 | `setup_logging()`, subsystem logger convention, rotating file handler |
| `ring_buffer.py` | 52 | bounded in-memory handler feeding crash-report context |
| `crash_report.py` | 255 | `logs/crash-*.log` rendering, ambient + late-bound context |
| `error_boundary.py` | 399 | `swallow()`, `report_error()`, `report_crash()`, all four process hooks |
| `__init__.py` | 74 | public API; legacy `DiagnosticsProvider`/`Service` made lazy |

The editor and the viewport subprocess now call **the same two functions**. The
editor's private `_install_crash_logging()` implementation was deleted and
replaced by a call into this layer.

### Log format

```
%(asctime)s.%(msecs)03d %(levelname)-8s [%(processName)s:%(process)d/%(threadName)s] %(name)s: %(message)s
```

Real output:

```
2026-08-10 20:10:52.417 ERROR    [Viewport:24188/MainThread] zennity.logic: Suppressed failure while execute node 'probe_node': RuntimeError: diagnostic probe
Traceback (most recent call last):
  ...
```

Every required field is present and asserted by
`tests/diagnostics/test_logging_setup.py::test_format_contains_required_fields`:
timestamp · level · process name · **pid** · thread name · subsystem · message.

### Subsystem logger convention

`get_logger("logic")` → `zennity.logic`. Registered names:

```
zennity.logic     zennity.physics    zennity.animation   zennity.ui
zennity.audio     zennity.viewport   zennity.scene       zennity.assets
zennity.dialogue  zennity.editor     zennity.runtime     zennity.diagnostics
```

`zennity` has `propagate = False`, so a host application's root logger cannot
double-print engine output. Files were **not** mass-migrated; the convention is
established and used by everything Stage 0 touched.

### Rotation

`logs/zennity.log`, `maxBytes=10 MB`, `backupCount=5` → 60 MB ceiling.
Verified by `test_rotation_creates_backups`, which uses a 2 KB test size and
asserts backups appear, are capped at 3, and that no file grows past the bound.

---

## 2. `swallow()` — the reusable boundary

```python
with swallow(log, "initialise animation for 'player'"):
    risky()
```

Control flow is **identical** to `try/except Exception: pass` — the block is
abandoned at the failure point and execution resumes after it. What changes is
that the failure is logged with context, exception type, message and traceback.

Guarantees, each covered by a test in `tests/diagnostics/test_error_boundary.py`:

| Guarantee | Test |
|---|---|
| suppresses like `except: pass` | `test_swallow_suppresses_like_except_pass` |
| abandons the block at the failure point | `test_swallow_abandons_the_block_at_the_failure_point` |
| no log line on success | `test_swallow_is_transparent_on_success` |
| `KeyboardInterrupt` still propagates | `test_keyboard_interrupt_still_propagates` |
| `SystemExit` still propagates | `test_system_exit_still_propagates` |
| `reraise=` types propagate | `test_reraise_types_propagate` |
| narrow `exc_types=` does not widen catching | `test_narrow_exc_types_do_not_widen_behaviour` |
| logs context + type + message + traceback | `test_swallow_logs_context_type_message_and_traceback` |
| a broken logger cannot break the boundary | `test_untraceable_logger_failure_does_not_escape` |

`report_error(log, context, exc)` is the variant for handlers that keep their own
recovery logic (returning a sentinel, emitting a `runtime_log` event) and only
need the failure to become visible.

### Throttling

Both accept `throttle=N`: log the 1st failure, then every Nth, reporting how many
were suppressed in between.

```
zennity.physics: dispatch physics event 'on_collision_enter' to a handler:
    ValueError: x [299 identical failures suppressed since the last report]
```

Used on per-frame / per-event paths so a permanently broken handler reports once
rather than 60 times a second.

---

## 3. Process error boundaries

### Before Stage 0

| Boundary | Editor | Viewport |
|---|---|---|
| `sys.excepthook` | ✔ | **✘** |
| `threading.excepthook` | ✘ | ✘ |
| `sys.unraisablehook` | ✘ | ✘ |
| Qt message handler | ✔ | n/a |
| `faulthandler` | ✔ | **✘** |
| logging configured | ✔ (single append-only dotfile) | **✘** |

### After Stage 0

| Boundary | Editor | Viewport |
|---|---|---|
| `sys.excepthook` | ✔ | ✔ |
| `threading.excepthook` | ✔ | ✔ |
| `sys.unraisablehook` | ✔ | ✔ |
| Qt message handler | ✔ | n/a |
| `faulthandler` (all threads) | ✔ | ✔ |
| `atexit` clean-shutdown marker | ✔ | ✔ |
| logging configured | ✔ rotating | ✔ rotating |
| crash reports | ✔ | ✔ |

`install_process_hooks()` is idempotent and is called once per process. The
viewport calls it **at the top of `run_viewport()`, before `pygame.init()`** —
verified explicitly by
`tests/integration/test_viewport_error_boundary.py::test_run_viewport_installs_its_own_boundary_source`,
because the whole point is that a `multiprocessing` child inherits none of this.

`KeyboardInterrupt` is routed to the previous hook rather than treated as a
crash. A thread raising `SystemExit` is likewise not a crash.

An `atexit` handler logs `Process exiting cleanly` and flushes the handlers, so
a process that dies *during* teardown is distinguishable from one that shut down
normally — previously the log simply stopped mid-sentence in both cases.

### The viewport frame loop

Before:
```python
except Exception:
    session.running = False        # process goes dark, no trace
```

After — same control flow, plus a crash report and an event to the editor:
```python
except Exception as exc:
    report_crash(type(exc), exc, exc.__traceback__, origin="viewport frame loop", ...)
    _send(events, {"type": "runtime_log", "level": "ERROR", "message": ...})
    _send(events, {"type": "viewport_crashed", "error": ...})
    session.running = False
```

---

## 4. Crash reports

`logs/crash-YYYYMMDD-HHMMSS.log`, written only for crash-level failures (a
process hook firing, a thread dying, the viewport frame loop aborting). Ordinary
logged-and-recovered errors go to `zennity.log` only.

Contents — all asserted by `test_report_contains_every_required_field`:

```
timestamp · origin · engine version · python version · platform · machine
process (name + pid) · thread (name + ident)
context: project · active_scene · mode (Editor/Play) · selected_object · scene_objects
exception type · message · full traceback
last 200 log records (from the ring buffer)
```

The editor registers a **context provider** that is queried at crash time, so
reports carry the live scene and Play/Editor mode rather than a stale snapshot.

Same-second collisions get a `-1`, `-2` suffix. `latest_crash_report()` orders by
`(stamp, counter)` — a plain name sort is wrong here, because
`crash-<stamp>-1.log` sorts *before* `crash-<stamp>.log` (`-` < `.`). That bug
was caught by `test_latest_crash_report_finds_the_newest` during development.

`write_crash_report()` never raises: it is called from exception hooks.

---

## 5. User-facing feedback

No modal dialogs — the audit explicitly warned against a cascade of them.

| Failure | What the user sees |
|---|---|
| any crash recorded in the editor process | status bar: *"An internal error occurred — see Console for the crash report"* (15 s) + a Console `ERROR` line with the crash-report path |
| viewport subprocess crash | status bar: *"Play Mode stopped because the viewport crashed — see Console…"* + Console `ERROR` with the error and report path |

Wiring: the viewport emits `viewport_crashed`; `editor_bootstrap_controller`
routes it to `IsolatedEditorWindow._handle_viewport_crashed_event`. Separately,
`add_crash_listener(self._on_crash_reported)` catches crashes originating inside
the editor process itself.

---

## 6. Handlers migrated

**Rule 14 respected: no blanket automated rewrite.** Each handler was read and
classified. The bridge cluster was converted with an AST pass restricted to the
exact `try: … except Exception: pass` shape, with per-handler context strings
derived from the enclosing method, and every hunk reviewed.

### P0 — 51 → 0

| File | Handlers | Approach |
|---|---|---|
| `editor/isolated_viewport.py` | 4 | boundary install + `report_crash` + `swallow` |
| `editor/runtime/viewport_runtime_initializer.py` | 8 | `report_error` alongside the existing `runtime_log` emit; `swallow` on teardown |
| `editor/runtime/native_ui.py` | 2 | `swallow` for asset parse; `DEBUG` for per-frame colour parse |
| `editor/runtime/viewport_play_commands.py` | 3 | `report_error`; hot-reload `print` → log + `runtime_log` |
| `editor/runtime/viewport_animation_updater.py` | 1 | `report_error` |
| `editor/runtime/viewport_logic_event_updater.py` | 1 | `report_error` (module detached = gameplay-visible) |
| `editor/runtime/viewport_control_commands.py` | 1 | `report_error` |
| `editor/render/sprite_overlay_renderer.py` | 1 | `DEBUG` (per-draw path) |
| `editor/visual_scripting/mini_live_viewport.py` | 1 | `report_error` at WARNING (QTimer path) |
| `engine/ai/behavior_tree_runtime.py` | 5 | log + keep the existing `ui_action_failed` event |
| `engine/behavior/graph_runtime.py` | 2 | throttled `swallow` |
| `engine/logic/runtime/core.py` | 3 | `swallow` — handler-unregister leaks must be visible |
| `engine/logic/physics_event_dispatch.py` | 1 | try/except + throttled `report_error` (hottest path) |
| `engine/logic/animation_event_dispatch.py` | 2 | throttled `swallow` |
| `engine/runtime/ui_event_dispatcher.py` | 1 | throttled `swallow` |
| `engine/runtime/runtime_manager.py` | 4 | `swallow` |
| `engine/runtime/runtime_scene.py` | 2 | `swallow` |
| `engine/runtime/script_runtime.py` | 4 | one funnel: `_record_error` now logs instead of `print` |
| `engine/core/save_manager.py` | 1 | `report_error`, sentinel unchanged |
| `engine/graphics/tilemap.py` | 1 | `report_error` |
| `engine/ui/ui_renderer.py` | 1 | `report_error` |
| `engine/logic/runtime/nodes/physics_nodes.py` | 1 | `report_error`, `exec_no_hit` unchanged |
| `engine/logic/runtime/nodes/save_load_nodes.py` | 4 | `report_error` / `swallow`; 2 bare `except:` removed |

### Bridge cluster — 31 → 0

`visual_scripting_bridge` (9+1), `diagnostics_bridge` (8+1),
`animation_studio_bridge` (7+1), `reactive_editor_bridge` (3),
plus `build_pipeline_bridge` (5) from the same family.

### Prints migrated (rule 15)

Only error/exception prints: `script_runtime._record_error`,
`viewport_play_commands` hot reload, the three bridge `open_*_document`
handlers, and the dialogue event sink. Debug prints were left alone.

---

## 7. Known defect kept visible, not fixed (rule 16)

`engine/dialogue/manager.py` calls `LogicEventBus.get_instance()`, which does not
exist. Stage 0 does **not** fix it — that is Stage 1 — but the `AttributeError`
now produces a full log entry with traceback instead of a `print()`.

`tests/diagnostics/test_dialogue_dead_bridge.py` locks this in and includes
`test_defect_still_present`, which **fails on purpose** once Stage 1 lands — the
signal to delete the file.

---

## 8. Performance

Measured on the Phase 9.5A baseline hardware (Ryzen, Python 3.12.10).

| Operation | ns/op |
|---|---|
| `try/except Exception: pass` (success path) | **44** |
| `swallow()` as `@contextlib.contextmanager` (first implementation) | 1 504 |
| **`swallow()` as a slotted class (shipped)** | **747** |

The generator-based context manager was 34× the baseline, so `swallow` was
reimplemented as a `__slots__` class with `__enter__`/`__exit__`. That halved
the cost, and the failure path is unchanged.

For the **hottest** boundary — `dispatch_physics_event`, which runs per contact
per frame — even 747 ns was not justified, so it keeps a plain `try/except` with
a throttled `report_error` in the failure branch: **zero added cost on the
success path.**

| Failure-path cost | |
|---|---|
| every failure logged (with traceback) | 835 µs |
| `throttle=300` | 5.1 µs average |

Nothing logs on a normal frame. `logger.exception()` is never called on a
success path.

---

## 9. Metrics — before / after

Re-run: `python scripts/audit_silent_exceptions.py`

| Metric | BEFORE | AFTER |
|---|---|---|
| **P0 dangerous (hot/lifecycle)** | **51** | **0** |
| **Total dangerous** | **255** | **172** |
| Total handlers | 612 | 591 |
| Broad handlers | 371 (60 %) | 343 (58 %) |
| Bare `except:` | 6 | 3 |
| Silent (no log/print/raise) | 470 | 419 |
| Body is only `pass` | 178 | 136 |
| Logged via `logging` | 21 | 58 |
| Print-only | 96 | 89 |
| SAFE | 55 | 86 |
| QUESTIONABLE | 302 | 308 |
| Files importing `logging` | 13 | 29 |

**P0 allow-list: empty.** No P0 handler was exempted.

25 handlers inside `engine/diagnostics/` are reported under a separate
`INFRASTRUCTURE` heading: an exception hook or log handler that raises would
destroy the reporting path it implements, so being defensive there is correct by
design, not a defect. The audit tool was taught to recognise this, and to
recognise `report_error` / `report_crash` / `_record_error` as observable routes.

The remaining **172 P1** are outside Stage 0's scope (they are not on hot or
lifecycle paths) and are left for a later stage, as authorised.

---

## 10. Tests

`tests/diagnostics/` (51) + `tests/integration/test_viewport_error_boundary.py` (6)
= **57 new tests, 0 failures.**

| File | Tests | Covers |
|---|---|---|
| `test_logging_setup.py` | 10 | init, handler count, **idempotency**, format fields, file write, rotation + backup cap, no-propagate, unwritable-dir fallback |
| `test_error_boundary.py` | 15 | control-flow equivalence, `KeyboardInterrupt`/`SystemExit`/`reraise`, narrow types, traceback content, throttling + bucket isolation, broken-logger safety, ring buffer |
| `test_crash_report.py` | 12 | every required field, embedded log records, live context providers, failing provider tolerated, filename format, same-second collision, newest-report ordering, never-raises, ring-buffer bounds |
| `test_thread_exceptions.py` | 10 | hooks installed + idempotent, **worker thread traceback + crash report + listener**, thread `SystemExit` not a crash, main-thread hook, `KeyboardInterrupt` not a crash, **unraisable `__del__`**, partial payload |
| `test_viewport_error_boundary.py` | 6 | viewport installs its own boundary, frame loop no longer silent, editor handles `viewport_crashed`, **real subprocess main-thread crash**, **real subprocess worker crash**, **broken-node probe** |
| `test_dialogue_dead_bridge.py` | 4 | defect still present, failure logged with traceback, does not propagate, no longer print-only |

Items 17–21 of the brief are covered by, respectively:
`test_broken_logic_node_is_reported_not_swallowed`,
`test_subprocess_*_crash_leaves_a_log_and_a_report`,
`test_worker_thread_exception_is_logged_with_traceback`,
`test_unraisable_exception_is_logged`,
`test_rotation_creates_backups`.

Item 18's requirement that no debug hook ships in production UI is satisfied: the
crash probe lives entirely in the test file, which writes and runs a throwaway
child script. No production trigger was added.

**Environment note:** every pytest run in this repository ends with
`PermissionError: [WinError 5] … pytest-current` during pytest's own temp-dir
cleanup. Confirmed pre-existing by running `tests/architecture` on an unmodified
tree. It does not affect test results.

---

## 11. Files changed

**New (9):** 4 diagnostics modules + `ring_buffer.py`, 4 test modules + 1
integration test, this document.

**Modified (26):** `engine/diagnostics/__init__.py`, the 23 P0 files, the 5
bridges, `engine/dialogue/manager.py`, `editor/isolated_editor_main.py`,
`editor/editor_bootstrap_controller.py`, and `scripts/audit_silent_exceptions.py`
(taught to recognise the new boundary API and the diagnostics layer).

---

## 12. Hard success criteria

| Criterion | Status | Evidence |
|---|---|---|
| viewport cannot crash silently | ✔ | `test_subprocess_main_thread_crash_leaves_a_log_and_a_report`; frame loop reports + notifies editor |
| worker thread cannot die silently | ✔ | `threading.excepthook` installed in both processes; `test_worker_thread_exception_writes_a_crash_report` |
| P0 swallowed exceptions eliminated | ✔ | audit: 51 → **0**, empty allow-list |
| logs persistent and rotating | ✔ | `logs/zennity.log`, 10 MB × 5; `test_rotation_creates_backups` |
| crash reports contain traceback + context | ✔ | `test_report_contains_every_required_field` |
| editor tells the user a runtime failure happened | ✔ | status bar + Console, both crash paths |
| diagnostic system shared between processes | ✔ | one `engine/diagnostics/`; the editor's private implementation was deleted |
| existing gameplay behaviour unchanged | ✔ | see §13 |

---

## 13. Regression status — **0 regressions**

Stage 0 adds logging calls; it does not alter control flow. The three shapes used
all preserve the original semantics:

- `swallow(...)` ≡ `except Exception: pass`
- `report_error(...)` added *inside* an existing handler, sentinel/return unchanged
- `report_crash(...)` added before an existing `session.running = False`

Verified by a `git worktree` of the pre-Stage-0 commit and an identical run of
every subsystem named in the brief (Scene · Logic · Physics · UI · Animation ·
Dialogue · Runtime/Play-Stop · Core · AI · Behavior):

| | BEFORE (worktree @ 58b14062) | AFTER |
|---|---|---|
| tests | 1 087 | 1 087 |
| passed | 1 065 | 1 065 |
| failed | 21 | 21 |
| skipped | 1 | 1 |

```
NEW failures introduced by Stage 0: 0
Failures gone after Stage 0:        0
Identical pre-existing failures:   21
```

The 21 failures are the **same tests, on both trees**: 9 in
`tests/logic/test_logic_graph_asset` (the node-contract defects Stage 1 will
address), 5 legacy scene round-trips, 4 runtime-pool bounds, 2 behavior-tree, 1
animation. None is touched by Stage 0.

Additionally, a full-suite run collected 3 577 tests on the baseline and 3 634
after — exactly +57, matching the new Stage 0 tests and confirming nothing was
lost from collection. (The full run is not quoted for pass counts: it repeatedly
loses xdist workers to `node down: Not properly terminated` on **both** trees, a
pre-existing instability unrelated to this work.)

A separate `git stash` check confirmed
`tests/ai/test_behavior_tree_runtime.py::test_sequence_all_success` fails
identically on the untouched `engine/ai/behavior_tree_runtime.py`.

---

*Stage 0 complete. Stage 1 (node contract convergence) is NOT started.*
