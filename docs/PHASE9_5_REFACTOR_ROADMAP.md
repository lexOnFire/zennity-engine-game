# Phase 9.5 — Refactor Roadmap

**Date:** 2026-08-10
**Status:** proposal awaiting authorization. **Nothing in this document has been executed.**

Derived from:
- `docs/PHASE9_5_ENGINE_STABILITY_AUDIT.md`
- `docs/PHASE9_5_NODE_SYSTEM_AUDIT.md`
- `docs/PHASE9_5_CRASH_ERROR_AUDIT.md`
- `docs/PHASE9_5_PERFORMANCE_BASELINE.md`

Priorities are assigned by **user-visible damage**, not by implementation difficulty, as
instructed. Several P0 items are small; several P3 items are large.

---

## Final report card

```
ENGINE STABILITY          4/10
ARCHITECTURE ORGANIZATION 5/10
NODE SYSTEM               3/10
ERROR OBSERVABILITY       2/10
LIFECYCLE SAFETY          4/10
EDITOR RESPONSIVENESS     6/10
MAINTAINABILITY           5/10
```

```
NODE SYSTEM
  definitions          = 154   (declarative 126 / legacy dict 154)
  executors            = 132
  evaluators           =  64
  contract violations  = 167
  duplicates           =   2 node IDs, 4 display names, 0 executor/evaluator IDs
  legacy               =  26 markers; 8 dotted aliases; 4 deprecated event nodes

SILENT EXCEPTIONS
  total                = 612
  dangerous            = 255   (P0 51 / P1 204)

LARGE FILES
  >500                 =  26
  >1000                =   1
  >2000                =   0

GLOBAL MUTABLE SERVICES = 18 singletons  (SAFE 10 / NEEDS LIFECYCLE 6 / RISKY 2)
                          + 184 module-level mutable globals (mostly const tables)

THREADS                 = 28 files
  unsafe                = 15 (start without stop);
                          1 genuinely able to outlive shutdown (QThread, build_wizard_dock)

DEAD CODE CANDIDATES    = 20 high-confidence  (215 unreferenced symbols, most
                          reflectively-registered node classes — NOT dead)

DUPLICATED SUBSYSTEMS   = 8
```

---

## TOP 10 P0 / P1 ISSUES

| # | Pri | Issue | Evidence | Impact |
|---|---|---|---|---|
| 1 | **P0** | **`next` / `exec_done` exec-port split across 45 nodes.** Definitions declare `exec_done`; executors return `["next"]`; `core.py:553,616` matches ports by exact string; no alias table exists. | 45 `EXEC_PORT_MISMATCH` + 45 `UNREACHABLE_EXEC_PORT`. All 56 project `.zlogic` files use `next` (137 edges); `exec_done` appears 0 times. | Any graph authored from today's palette **stops dead at the first affected node**, silently. This is the "nodes do nothing" bug. |
| 2 | **P0** | **`play_animation` and `stop_animation` are each defined twice with different port contracts.** `actions_nodes.py` (`state` → `exec_done`) vs `animation_nodes.py` (`target`+`animation_name` → `exec_success`/`exec_failure`). Reflective harvest gives the palette one version; `LogicProvider.boot()` registers the other into `MetadataManager`; the executor reads `state`. | Node audit §3.2 | Split-brain on a core gameplay node. The palette shows pins the executor never reads. |
| 3 | **P0** | **Viewport subprocess has no error boundary at all.** `editor/isolated_viewport.py::run_viewport()` contains 4 broad handlers, 3 of them bare `pass`. The crash-logging installer is only called in the parent process. | Crash audit §2, §3 | The process most likely to crash is the only one with zero diagnostics. Viewport dies mute. |
| 4 | **P0** | **255 dangerous exception handlers; 51 on hot/lifecycle paths.** 77 % of all 612 handlers leave no trace. Only 21 use the `logging` module. | Crash audit §1 | Every failure presents as "nothing happened". This is the root cause of the entire "silent exceptions / unpredictable engine" complaint. |
| 5 | **P0** | **`threading.excepthook` absent.** No worker-thread exception is ever attributed. 15 files start timers/threads without stopping them. | Crash audit §3; stability §6 | Silent worker death; teardown-time callbacks against half-destroyed state. |
| 6 | **P1** | **Two node registration paths that disagree.** `runtime/nodes/__init__.py` imports 14 modules; `LogicProvider.boot()` imports 22 and hand-registers ~110 definitions over 250 lines. | Node audit §2 | Audio, camera, dialogue, touch, particles, pathfinding, save/load, state-machine and UI-binding nodes have **no executor** on the non-provider path. Behaviour depends on how the process started. |
| 7 | **P1** | **Play/Stop leaks the entire service layer.** `UIRuntimeService.reset()`, `UIManager.reset()`, `UIDataBindingManager.reset()`, `SceneManager.reset()` all exist and none is called on Stop. Camera follow/shake, particles and pathfinding have no teardown at all. | Stability §4 | 2nd and later Play sessions differ from the 1st. Camera keeps following a destroyed object; HUD values persist. |
| 8 | **P1** | **Dialogue → Logic Graph event bridge is dead code.** `manager.py:326` calls `LogicEventBus.get_instance()`, which does not exist; the `AttributeError` is swallowed and printed. Verified. | Crash audit §5 | Dialogue events have never reached Logic Graphs. Perfect illustration of #4. |
| 9 | **P1** | **Logic Graph editor load is O(n²).** 100 nodes = 1.8 s, 500 nodes = **37 s**, 1000 nodes = timeout. `refresh_connections()` runs once per inserted node; 150 nodes produce 11 475 `setHtml()` calls. | Perf baseline §2 | Caps authorable game size; the primary measured source of "engine feels heavy". |
| 10 | **P1** | **33 runtime handlers have no definition — including every math and logic node.** `add_number`, `multiply_number`, `clamp_number`, `and`, `or`, `not`, `join_text`, `to_text` all execute but are absent from the palette. | Node audit §3.3 | Arithmetic and boolean logic are **unauthorable in the visual editor** despite working at runtime. |

**Runners-up (P1, not in the top 10):** the dead shadowed `engine/logic/node_definitions.py`
(837 lines that have never executed); the 24-module `engine` import cycle; the 4 parallel
graph frameworks (1 814 lines).

---

## RECOMMENDED REFACTOR ORDER

Sequenced so that each stage makes the next one safe. **Observability comes before
correctness, because you cannot verify a fix you cannot see.**

---

### Stage 0 — Make failure visible (P0) · ~2–3 days · lowest risk · ✅ **CONCLUÍDO**

No behaviour changes. Purely additive.

1. **Add `engine/diagnostics/logging_setup.py`** — central logger factory with subsystem
   categories, `RotatingFileHandler` (`logs/zennity.log`, 5 × 10 MB), and
   `%(threadName)s` in the format.
2. **Add `engine/diagnostics/report.py::swallow(logger, context)`** — a context manager
   with identical control flow to `except Exception: pass`, plus one `log.exception()`.
3. **Install boundaries in `editor/isolated_viewport.py`** (currently zero):
   `sys.excepthook`, `threading.excepthook`, `sys.unraisablehook`, `faulthandler`.
4. **Extend `editor/isolated_editor_main.py`**: add `threading.excepthook`,
   `sys.unraisablehook`, `atexit`, and move the log from `.zennity_crash.log` to `logs/`.
5. **Add the crash-report writer** — `logs/crash-YYYYMMDD-HHMMSS.log` with the fields
   specified in the crash audit §6, fed by a 200-entry in-memory ring buffer.
6. **Convert the 51 P0 handlers** to `with swallow(...)`. Then the
   `editor/runtime/*_bridge.py` cluster (31), then `engine/core/engine.py` (9).
7. **Surface errors in the UI** — non-blocking status-bar message plus a console-panel
   entry whenever a crash report is written.

**Exit criterion:** run a Play session with a deliberately broken node; the failure
appears in the console panel, in `logs/zennity.log`, and in a crash report.

**Why first:** stages 1–5 all involve changing behaviour in a codebase where 77 % of
failures are invisible. Fixing that blind is how regressions get shipped.

---

### Stage 1 — Node contract convergence (P0) · ~3–5 days · ✅ **CONCLUÍDO**

8. **Add `engine/logic/port_aliases.py`** — one canonical alias table
   (`exec_done ↔ next`, `exec_success ↔ next`, `true/false ↔ grounded/airborne`, etc.),
   consulted by both `graph_normalizer` (on load) and `core._follow` (on dispatch).
   **This resolves 90 of the 167 violations without touching 45 executors and without
   invalidating a single saved asset.**
9. **Fix `sequence`** — `return ["then_{index}"]` is an un-interpolated f-string.
10. **Resolve the `play_animation` / `stop_animation` duplicates.** Pick one contract,
    delete the loser, migrate any affected assets.
11. **Wire in the existing `NodeDefinitionRegistry` conflict detection.** It already
    implements `detect_conflicts()` and `NodeDefinitionConflictError`. Make duplicate-id
    registration a hard, loud failure at boot.
12. **Add the 33 missing definitions** — starting with `math_nodes` and `string_nodes`,
    which unlock arithmetic and boolean authoring.
13. **Fix `log_message`** — it reads a non-existent `text` port, so the log node cannot
    log a connected value. This degrades every debugging session.
14. **Add `tests/test_node_contracts.py`** asserting
    `audit_node_system.violations == 0` (with an explicit, shrinking allow-list).
    Wire `scripts/audit_node_system.py --json` into CI.

**Exit criterion:** contract violations drop from 167 to a documented allow-list; a
newly authored graph using palette pins executes end to end.

---

### Stage 2 — Registration unification (P1) · ~2–3 days

15. **Single registration path.** Delete the hand-written 250-line block in
    `LogicProvider.boot()`; make `runtime/nodes/__init__.py` import all 23 modules and
    have the provider harvest definitions reflectively — one mechanism, not two.
16. **Delete `output_evaluator.py`'s "Fallback for isolated tests" branch** once the
    dual path is gone.
17. **Delete the shadowed dead modules:** `engine/logic/node_definitions.py` (837 L) and
    `engine/core.py` (36 L). Verified unreachable.
18. **Make catalogue construction lazy** — remove the import-time side effects from
    `node_definitions/__init__.py` (137.7 ms of startup).

**Exit criterion:** `len(registry.executors)` is identical whether or not
`LogicProvider` booted.

---

### Stage 3 — Lifecycle safety (P1) · ~2–3 days

19. **Add an explicit teardown checklist** to `viewport_runtime_initializer.stop()`:
    `UIRuntimeService.reset()`, `UIManager.reset()`, `UIDataBindingManager.reset()`,
    `SceneManager.reset()`, camera follow/shake stop, particle stop, pathfinding stop,
    and the 3 editor debug singletons.
20. **Replace the `except: pass` around physics/animation handler unregistration** with
    `swallow(...)` from Stage 0 — accumulating stale handlers is a real leak.
21. **Add `tests/test_play_stop_idempotence.py`** — run 5 Play/Stop cycles and assert
    that handler counts, UI widget counts and cache sizes return to their baseline.
22. **Audit the 15 start-without-stop timer files**; add `stop()` in `closeEvent`.
    Give `build_wizard_dock.py`'s QThreads an explicit `quit()` + `wait()`.
23. **Bound the 3 unbounded caches** (`_sound_cache`, `_font_cache`, `_image_cache`) and
    **fix `sprite_performance_patch.py`**, which replaces bounded `OrderedDict` caches
    with plain `dict`s and silently disables eviction.

**Exit criterion:** the 5-cycle Play/Stop test passes with zero residual state.

---

### Stage 4 — Editor responsiveness (P1/P2) · ~2 days

24. **Add a bulk-load guard to `LogicGraphEditor.set_graph()`** suppressing
    `refresh_connections`, `refresh_target_hints` and `refresh_text` until the load
    completes. Target: 500 nodes from 37 s to < 0.8 s.
25. **Defer the numpy import** in `engine/core/component.py`, or replace `Transform`'s
    3-element arrays with `__slots__` floats. Target: startup 2.00 s → < 1.0 s.
26. **Preserve Hierarchy expansion + scroll state** — port the pattern already working in
    `assets_panel_controller.py::refresh()` into `premium_hierarchy_panel.py:147`.
27. **Instrument the unmeasured metrics** in the performance baseline (project open,
    scene open, Play start/stop, memory across cycles, inspector rebuild count).

**Exit criterion:** every "target" column in the performance baseline §7 is met or has a
recorded reason it was not.

---

### Stage 5 — Organization and duplication (P2) · ~1–2 weeks

28. **Resolve the 4 parallel graph frameworks.** Confirm `engine/graphs` (713 L),
    `engine/plugins/logic` (874 L) and `engine/graph` (227 L) are unused by the shipping
    pipeline, then remove or explicitly quarantine them.
29. **Resolve the 2 `DialogueManager` classes** (`engine/dialogue/manager.py` vs
    `engine/ui/dialogue_manager.py`).
30. **Collapse the alias clusters** — 5 ids for "load scene", 3 for "quit", 3 for
    "UI click", 2 for "UI enable", 2 for "set variable". Keep executors for backward
    compatibility; hide the aliases from the palette.
31. **Deprecate the 4 duplicate-display-name event nodes**
    (`event_collision_enter` vs `on_collision_enter`, etc.) — keep loading, hide from palette.
32. **Merge the fragmented palette categories** — Physics is split across 5 categories
    (19 nodes), Animation across 3 (14). No category exceeds 30, so nothing needs
    *splitting*; the problem is fragmentation, not size.
33. **Reorganize into `engine/logic/nodes/<domain>/{definition,runtime}.py`** — co-locating
    definition and runtime makes contract drift visible in a single file diff.
    **Do this last**, once contracts are converged, so the move is mechanical.
34. **Triage the 20 high-confidence dead-code candidates.** Note that ~120 of the 215
    unreferenced symbols are reflectively-registered node classes and are **live** —
    do not bulk-delete on the audit's raw output.

---

### Stage 6 — Architecture (P2/P3) · ~2–3 weeks · defer

35. **Break the 24-module `engine` import cycle** by extracting a CONTRACTS layer
    (`Component`, `Transform`, `GameObject` protocol, metadata/pin types) that imports
    nothing concrete. This is the highest-leverage structural change available, and also
    the highest-risk. Nothing is currently broken by the cycle — it is a
    maintainability tax, not a defect.
36. **Break the 3 smaller cycles** (`graphs.core.node ↔ pin`; the `logic_graph` mixin
    cycle; `visual_scripting` dock cycle).
37. **Unify the 5 event systems** — only after Stage 3 proves the lifecycle is sound.
    Retire the 2 `EventBus` re-export shims first as a cheap down-payment.
38. **Add `--safe-mode`** (stability audit §12 — feasible, ~1 day, all seams exist).
39. **Add `Help → Diagnostics`** (stability audit §13), surfacing live contract-violation
    counts from Stage 1's tooling.

---

### Stage 7 — Test strategy (P2) · ongoing

40. **Rebalance the suite.** 3 510 tests coexist with 167 contract violations, a dead
    event bridge and an 837-line module that has never executed. That is a suite
    verifying *structure* (258 `hasattr`/`isinstance` assertions), not *behaviour*.
41. **Add end-to-end authoring tests**: author a graph through the editor API → save →
    load → Play → assert observable effect. Only 327 of 3 510 tests are runtime-flavoured
    against 11 993 lines of `engine/logic`.
42. **Promote the three audit scripts to CI gates** with ratcheting thresholds so none of
    these metrics can regress.

---

## Effort and sequencing summary

| Stage | Theme | Priority | Est. | Risk | Blocks |
|---|---|---|---|---|---|
| 0 | Observability | P0 | 2–3 d | very low | everything | ✅ concluído |
| 1 | Node contracts | P0 | 3–5 d | medium | 2 | ✅ concluído |
| 2 | Registration unification | P1 | 2–3 d | medium | 5 |
| 3 | Lifecycle safety | P1 | 2–3 d | medium | — |
| 4 | Responsiveness | P1/P2 | 2 d | low | — |
| 5 | Organization | P2 | 1–2 w | medium | 6 |
| 6 | Architecture | P2/P3 | 2–3 w | **high** | — |
| 7 | Tests | P2 | ongoing | low | — |

**Stages 0–4 (~2 weeks) address every P0 and every P1.** Stages 5–7 are maintainability
work that can be scheduled against feature pressure.

---

## Explicitly out of scope for Phase 9.5

Per the phase brief, and reaffirmed here:

- No new features.
- No Large Scale Simulation.
- No Ant Colony.
- No file moves (Stage 5 item 33 is a *proposal*).
- No legacy deletion (all legacy is *classified*, not removed).
- No automatic refactoring.

---

## What Phase 9.5A actually changed

Three new read-only audit tools:

| File | Purpose |
|---|---|
| `scripts/audit_node_system.py` | node counts, contract violations, registration divergence, category/palette analysis, file organization; `--json` for CI |
| `scripts/audit_silent_exceptions.py` | handler classification (SAFE/QUESTIONABLE/DANGEROUS), P0/P1 ranking, error-boundary probes, logging inventory |
| `scripts/audit_large_files.py` | large files, global state, singletons, threads, import direction, cycles, import-time side effects |

Five audit documents under `docs/PHASE9_5_*.md`.

**Zero production files were modified.**

---

*Awaiting authorization before any of the above is implemented.*
