# Phase 9.5 — Crash & Error Observability Audit

**Date:** 2026-08-10
**Tool:** `scripts/audit_silent_exceptions.py` (read-only, re-runnable)

> Reproduce with:
> ```bash
> python scripts/audit_silent_exceptions.py --top 40
> ```

---

> ## ⚠ SUPERSEDED IN PART — Phase 9.5B Stage 0 has been implemented
>
> The findings below describe the state **before** remediation. They are kept
> verbatim as the baseline record. Stage 0 (`docs/PHASE9_5B_STAGE0_OBSERVABILITY.md`)
> has since closed the P0 set and built the shared observability layer.
>
> | Metric | This audit (before) | After Stage 0 |
> |---|---|---|
> | **P0 dangerous (hot/lifecycle)** | **51** | **0** |
> | Total dangerous | 255 | 172 |
> | Total handlers | 612 | 591 |
> | Bare `except:` | 6 | 3 |
> | Silent handlers | 470 | 419 |
> | Body is only `pass` | 178 | 136 |
> | Logged via `logging` | 21 | 58 |
> | SAFE | 55 | 86 |
> | Files importing `logging` | 13 | 29 |
> | `sys.excepthook` | editor only | editor **+ viewport** |
> | `threading.excepthook` | ABSENT | **installed in both processes** |
> | `sys.unraisablehook` | ABSENT | **installed in both processes** |
> | `faulthandler` | editor only | editor **+ viewport** |
> | Rotating logs | ABSENT | **`logs/zennity.log`, 10 MB × 5** |
> | Crash reports | ABSENT | **`logs/crash-*.log` with context + traceback** |
> | Viewport subprocess boundary | **NONE** | full boundary + crash notification to editor |
> | `atexit` shutdown marker | ABSENT | **installed in both processes** |
> | User-facing failure feedback | ABSENT | status bar + Console panel |
>
> **Still open (deliberately, out of Stage 0 scope):** 172 P1 dangerous handlers,
> 89 print-only handlers, and the broken `LogicEventBus.get_instance()` call in
> §5 — which is now *logged with a traceback* but not yet *fixed* (Stage 1).
>
> The audit tool was updated alongside Stage 0 to recognise the new boundary API
> (`report_error` / `report_crash` / `write_crash_report`) as observable, and to
> count the 25 deliberately-defensive handlers inside `engine/diagnostics/`
> under a separate `INFRASTRUCTURE` heading rather than as defects.

---

## 1. Silent exception audit — exact numbers

Scope: `engine/` + `editor/`, excluding `__pycache__`, `tests/`, `editor_legacy/`,
`scratch/`, `demos/`, `examples/` and `test_*.py`.

```
TOTAL exception handlers:            612
TOTAL broad exception handlers:      371   (60%)
  bare `except:`                       6
SILENT (no log, no print, no raise): 470   (77%)
  of which body is only `pass`:      178
LOGGED (via the logging module):      21   (3%)
PRINTED only (not a real log):        96
RETHROWN:                             26
```

### Classification

| Verdict | Count | Rule |
|---|---|---|
| **DANGEROUS** | **255** | broad handler (`except:` / `except Exception`) that neither logs, prints, nor re-raises — the error vanishes completely |
| **QUESTIONABLE** | **302** | broad handler that only `print()`s, or returns a falsy sentinel without re-raising, or a narrow handler that swallows silently |
| **SAFE** | **55** | logs via the `logging` module and/or re-raises |

**Only 55 of 612 handlers (9 %) leave any durable trace.**

Split by severity:

| Priority | Count | Definition |
|---|---|---|
| **P0** | **51** | DANGEROUS on a hot path or lifecycle path (`update`, `tick`, `render`, `execute`, `dispatch`, `start`, `stop`, `load`, `save`, `boot`, `shutdown`, `on_*`) |
| **P1** | **204** | DANGEROUS elsewhere |

### P0 list — swallowed exceptions on hot / lifecycle paths

| File:line | Function | Handler |
|---|---|---|
| `editor/isolated_viewport.py:62` | `run_viewport()` | `except Exception` **[pass]** |
| `editor/isolated_viewport.py:87` | `run_viewport()` | `except Exception` |
| `editor/isolated_viewport.py:92` | `run_viewport()` | `except Exception` **[pass]** |
| `editor/isolated_viewport.py:96` | `run_viewport()` | `except Exception` **[pass]** |
| `editor/render/sprite_overlay_renderer.py:64` | `SpriteOverlayRenderer` | `except Exception` [returns sentinel] |
| `editor/runtime/native_ui.py:199` | `NativeUIRenderer` | `except Exception` **[pass]** |
| `editor/runtime/native_ui.py:356` | `NativeUIRenderer` | `except Exception` **[pass]** |
| `editor/runtime/viewport_animation_updater.py:81` | `ViewportAnimationUpdater` | `except Exception` |
| `editor/runtime/viewport_control_commands.py:105` | `ViewportAudioCommandHandler` | `except Exception` |
| `editor/runtime/viewport_logic_event_updater.py:52` | `ViewportLogicEventUpdater` | `except Exception` |
| `editor/runtime/viewport_play_commands.py:182` | `ViewportPlayCommandHandler` | `except Exception` |
| `editor/runtime/viewport_play_commands.py:197` | `ViewportPlayCommandHandler` | `except Exception` |
| `editor/runtime/viewport_runtime_initializer.py:85,114,133,152,161,177,231,279` | `ViewportRuntimeInitializer` | 8 handlers, 5 of them `[pass]` |
| `editor/visual_scripting/mini_live_viewport.py:1170` | `RuntimeVisualizationPanelWidget` | `except Exception` **[pass]** |
| `engine/ai/behavior_tree_runtime.py:654,675,697,732,767` | `BehaviorTreeRuntime` | 5 handlers |
| `engine/behavior/graph_runtime.py:83` | `BehaviorGraphRunner` | `except Exception` **[pass]** |
| `engine/behavior/graph_runtime.py:658` | `BehaviorGraphRunner` | **bare `except:`** **[pass]** |
| `engine/core/save_manager.py:131` | `SaveManager` | `except Exception` [returns sentinel] |
| `engine/graphics/tilemap.py:185` | `LegacyTilemapRenderer` | `except Exception` |
| *(31 more — see `--top 60`)* | | |

### Densest offenders

| File | Handlers | Dangerous |
|---|---|---|
| `editor/runtime/visual_scripting_bridge.py` | 11 | **10** |
| `editor/runtime/diagnostics_bridge.py` | 10 | **9** |
| `engine/core/engine.py` | 11 | **9** |
| `editor/runtime/viewport_runtime_initializer.py` | 10 | **8** |
| `editor/runtime/animation_studio_bridge.py` | 9 | **8** |
| `editor/runtime/asset_drag_drop.py` | 7 | **7** |
| `engine/components/script_component.py` | 7 | **6** |
| `editor/widgets/generic_graph_editor.py` | 8 | **6** |
| `engine/ai/behavior_tree_runtime.py` | 8 | **5** |
| `editor/runtime/reactive_editor_bridge.py` | 8 | **4** |

The `editor/runtime/*_bridge.py` family is the worst cluster: **31 dangerous handlers
across 4 files.** These bridges are precisely the seam between editor and running game
— the place a user most needs to be told something failed. Every failure there is
currently invisible.

`engine/core/engine.py` with 9 dangerous handlers out of 11 is the second-worst: the
engine's own core loop cannot report its own failures.

---

## 2. Crash-path map

Where an unhandled exception goes, per execution context:

| Context | Boundary that exists | What the user sees | Verdict |
|---|---|---|---|
| **Qt event loop** (editor main process) | `sys.excepthook` + `qInstallMessageHandler` in `editor/isolated_editor_main.py` | traceback appended to `.zennity_crash.log`, echoed to stderr, **no dialog, no status bar message** | PARTIAL |
| **Qt slot callbacks** | PySide6 catches and prints; excepthook is *not* always invoked for slots | nothing | **FRAGILE** |
| **Pygame runtime** (viewport subprocess) | **none** — `isolated_viewport.py` installs no excepthook | viewport freezes or the process exits; parent sees a dead process | **P0** |
| **Play Mode** | the 51 P0 handlers above | "nothing happens" | **P0** |
| **Background workers** | **`threading.excepthook` is ABSENT** | thread dies, stderr only | **P0** |
| **QThread** (`build_wizard_dock.py`) | none | build silently never completes | P1 |
| **Asset loading** | `except Exception: pass` in several loaders | asset silently missing | P1 |
| **Scene loading** | 8 handlers in `viewport_runtime_initializer` | object silently not initialized | **P0** |
| **Logic Graph execution** | `core.py` has 10 handlers, 3 dangerous; `_execute` errors are emitted as `runtime_log` events in *some* paths | inconsistent — some errors surface in the console panel, most do not | PARTIAL |
| **UI rendering** | `native_ui.py:199,356` both `[pass]` | widget silently not drawn | **P0** |
| **Physics update** | handler unregister wrapped in `except: pass` | stale handlers accumulate | P1 |
| **Animation update** | `viewport_animation_updater.py:81` | frame silently skipped | P1 |

### The three highest-value crash paths

**1. `editor/isolated_viewport.py::run_viewport()` — the viewport process entry point
has 4 broad handlers, 3 of them bare `pass`.** This function *is* the process. An
exception here means the game view goes blank or the process dies with no diagnostic
whatsoever, in a subprocess that has **no `sys.excepthook`, no `faulthandler`, and no
logging configuration** — none of the boundaries installed in
`isolated_editor_main.py` are inherited, because the crash-logging installer is never
called in the child.

**2. `viewport_runtime_initializer` — 8 dangerous handlers on the Play path.** Each
`_initialize_*` failure is swallowed per-object. A scene where 3 of 20 objects fail to
initialize their logic starts and *looks* fine.

**3. `threading.excepthook` absent + 14 files that start timers/threads without
stopping them.** Any worker exception is unattributable.

---

## 3. Central error boundary — probe results

| Probe | Result |
|---|---|
| `sys.excepthook` | **FOUND** — 1 file: `editor/isolated_editor_main.py` |
| `threading.excepthook` | **ABSENT** |
| `sys.unraisablehook` | **ABSENT** |
| `qInstallMessageHandler` | **FOUND** — 1 file: `editor/isolated_editor_main.py` |
| `faulthandler.enable()` | **FOUND** — 1 file: `editor/isolated_editor_main.py` |
| `EditorExceptionHandler` class | **ABSENT** |
| `CrashReporter` class | **ABSENT** |
| `logging.basicConfig` | **FOUND** — 1 file: `editor/isolated_editor_main.py` |
| `RotatingFileHandler` / `logging.FileHandler` | **ABSENT** |
| `atexit` | **ABSENT** |

### What exists today

`editor/isolated_editor_main.py::_install_crash_logging(project_root)`:

```python
log_path = project_root / ".zennity_crash.log"
_CRASH_LOG_HANDLE = log_path.open("a", encoding="utf-8", buffering=1)
logging.basicConfig(level=INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                    handlers=[logging.StreamHandler(_CRASH_LOG_HANDLE)], force=True)
faulthandler.enable(file=_CRASH_LOG_HANDLE, all_threads=True)
sys.excepthook = excepthook            # logs CRITICAL + traceback, then chains to default
qInstallMessageHandler(qt_message_handler)
```

This is a genuinely good foundation. Its gaps:

| Gap | Impact |
|---|---|
| Installed **only in the editor main process** — the viewport subprocess gets nothing | the process most likely to crash is the one with no boundary |
| Single append-only file, **no rotation** | grows forever |
| `%(threadName)s` not in the format string | cannot attribute a failure to a worker |
| No `threading.excepthook` | worker exceptions bypass it |
| No `atexit` | shutdown failures unrecorded |
| Log lives at the **project root** as a dotfile, not in `logs/` | easy to miss, ships with the project |
| No structured crash report | no engine version, scene, Play/Editor mode, or recent-log context |
| No user-facing surface | the user is never told a log was written |

**There is no central error boundary in the engine at all** — `engine/` installs
nothing. A headless or exported build has zero error capture.

---

## 4. Logging architecture

| Question | Answer |
|---|---|
| Is there a central logger? | **No.** `logging.basicConfig` is called once, in the editor entry point. |
| Is there a log file? | Yes — `.zennity_crash.log` at the project root, editor process only. |
| Rotating logs? | **No.** |
| Subsystem categories? | **No.** 13 files import `logging`; most use `logging.getLogger(__name__)` inconsistently or call the root logger. |
| Timestamps? | Yes (`%(asctime)s`). |
| Thread name? | **No.** |
| Stack traces? | Only from `sys.excepthook` and the 21 handlers using `logger.exception`. |
| Log levels? | Format supports them; only `INFO`+ is emitted; no runtime level control. |

### `print()` vs `logging`

```
production files importing `logging`:  13   (of 639)
total print() calls in production:    138
handlers that only print():            96
```

Top `print()` offenders:

| File | print() calls |
|---|---|
| `engine/localization/validator.py` | 17 |
| `editor/widgets/logic_graph/items.py` | 11 |
| `engine/dialogue/manager.py` | 9 |
| `engine/logic/runtime/nodes/dynamic_ui_nodes.py` | 7 |
| `engine/core/save_manager.py` | 5 |
| `engine/logic/provider.py` | 5 |
| `engine/logic/runtime/nodes/camera_nodes.py` | 5 |
| `engine/logic/runtime/nodes/input_advanced_nodes.py` | 5 |
| `engine/logic/runtime/nodes/state_machine_nodes.py` | 5 |
| `editor/runtime/viewport_logic_api.py` | 5 |
| *(+ 5 more with 4 each)* | |

`print()` from the **viewport subprocess** goes to a pipe the editor does not surface.
Every one of those 96 print-only handlers is, in practice, silent.

`engine/logic/provider.py` prints `"LogicProvider.boot EXECUTADO!"` and
`"Registered executor {type_id}"` on every boot — debug output shipped as behaviour.

---

## 5. Worked example — how a feature dies silently

This is the exact mechanism the audit exists to expose, found in production:

`engine/dialogue/manager.py:320-341`

```python
try:
    from engine.logic.event_bus import LogicEventBus
    bus = LogicEventBus.get_instance()          # AttributeError
    ...
    bus.emit(f"dialogue:{event_name}", event_data)
except ImportError:
    print(f"[DialogueManager] Event: {event_name} ...")
except Exception as e:
    print(f"[DialogueManager._handle_dialogue_event] Error: {e}")   # ← lands here
```

Verified: `hasattr(LogicEventBus, "get_instance") is False`.

Every dialogue event raises `AttributeError`, is caught by the broad handler, and is
printed to a stream nobody reads. **Dialogue events have never reached Logic Graphs.**
There is no test failure, no red flag, no log entry — the feature simply does not work
and the codebase reports success.

Multiply this pattern by 255 dangerous handlers.

> **Stage 0 update.** This exact call site is now:
> ```python
> except Exception as exc:
>     report_error(_log, f"route dialogue event {event_name!r} to the LogicEventBus "
>                        f"(owner={owner_id}, session={session_id})", exc)
> ```
> The `AttributeError` produces a full log entry with a traceback. **The defect
> itself is unfixed** — that is Stage 1 — and
> `tests/diagnostics/test_dialogue_dead_bridge.py` locks in that it stays
> visible until then.

---

## 6. Proposed crash-logging architecture (proposal only — not implemented)

### Files

```
<project>/logs/
    zennity.log                        rotating, 5 x 10 MB
    crash-YYYYMMDD-HHMMSS.log          one per unhandled exception
```

### Log format

```
%(asctime)s.%(msecs)03d  %(levelname)-8s  [%(threadName)s]  %(name)s: %(message)s
```

with `name` = subsystem category: `zennity.editor.viewport`, `zennity.engine.logic`,
`zennity.engine.physics`, `zennity.engine.ui`, `zennity.assets`, `zennity.runtime`.

### Crash report contents

```
timestamp
engine version              (from pyproject.toml)
python version, OS, platform
project root
active scene
Play / Editor mode
process                     (editor | viewport)
thread name
exception type + message
full traceback
last 200 log entries        (in-memory ring buffer)
loaded subsystem inventory  (executors, evaluators, definitions, contract violations)
```

### Installation points

| Point | Boundary |
|---|---|
| `editor/isolated_editor_main.py` | `sys.excepthook`, `threading.excepthook`, `sys.unraisablehook`, Qt handler, `faulthandler`, `atexit` |
| **`editor/isolated_viewport.py`** | the same set, in the child process — **currently missing entirely** |
| `engine/` headless entry | `sys.excepthook` + `threading.excepthook` |
| Qt slots | a `@guard_slot` decorator that logs and shows a non-blocking status message |

### Handler remediation policy

Do **not** mass-delete `except: pass`. Instead:

1. Add a shared `engine/diagnostics/report.py::swallow(logger, context)` context manager.
2. Replace `except Exception: pass` with `with swallow(log, "initialize animation"):` —
   same control flow, one `log.exception()` line, zero behaviour change.
3. Convert the 51 P0 sites first, then the `editor/runtime/*_bridge.py` cluster (31), then
   `engine/core/engine.py` (9).

This turns 255 invisible failures into 255 log lines without changing a single
control-flow decision — the safest possible first move.

---

## 7. Summary

```
SILENT EXCEPTIONS
  total handlers          = 612
  broad                   = 371  (60%)
  bare except             =   6
  silent                  = 470  (77%)
  body is only `pass`     = 178
  logged via logging      =  21  (3%)
  print-only              =  96
  rethrown                =  26

  DANGEROUS               = 255
  QUESTIONABLE            = 302
  SAFE                    =  55

  P0 (hot/lifecycle path) =  51
  P1                      = 204

CENTRAL ERROR BOUNDARY
  sys.excepthook          = 1 file  (editor main process only)
  threading.excepthook    = ABSENT
  unraisablehook          = ABSENT
  Qt message handler      = 1 file
  faulthandler            = 1 file
  CrashReporter           = ABSENT
  log rotation            = ABSENT
  atexit                  = ABSENT
  viewport subprocess     = NO BOUNDARY AT ALL

LOGGING
  files importing logging =  13 / 639
  print() calls           = 138
```

**ERROR OBSERVABILITY SCORE: 2/10** (at the time of this audit).

The engine does not crash more than comparable projects — it crashes *quietly*, and it
degrades even more quietly. The reported symptom "crashes without warning / silent
exceptions" is not a perception problem; it is an accurate description of a codebase
where 77 % of error handlers leave no trace.

### Post-Stage-0 score: **6/10**

What lifted it: both processes now have a complete error boundary, logs are
persistent and rotating, crashes produce structured reports with context and
traceback, worker threads and `__del__` failures are recorded, and the user is
told when something failed. Every P0 is closed.

What still caps it at 6: **172 P1 dangerous handlers** and **89 print-only
handlers** remain outside hot and lifecycle paths, and there is no Diagnostics
window yet (stability audit §13). Reaching 8+ needs the P1 sweep; reaching 9+
needs in-editor diagnostics.

---

*Original audit was read-only. Remediation is recorded in
`docs/PHASE9_5B_STAGE0_OBSERVABILITY.md`.*
