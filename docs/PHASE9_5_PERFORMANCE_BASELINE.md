# Phase 9.5 — Performance Baseline

**Date:** 2026-08-10
**Purpose:** record measurements *before* any optimization, so Phase 9.5B can be judged
against numbers rather than impressions.

---

## 0. Environment

| | |
|---|---|
| OS | Windows 11 Pro, build 10.0.29639 |
| CPU | AMD64 Family 25 Model 80 (Zen 3), 16 logical cores |
| Python | 3.12.10 |
| PySide6 | 6.11.1 |
| pygame-ce | 2.5.7 (SDL 2.32.10) |
| Project | 716 asset paths, 22 `.zscene`, 56 `.zlogic` |
| Qt platform for benchmarks | `offscreen` |
| Method | `time.perf_counter()`, median of n runs, warm filesystem cache |

**Caveat.** Offscreen Qt removes GPU compositing cost, so the graph-editor numbers below
are a *lower bound* on real-world time. Everything else is unaffected.

---

## 1. Startup

### Cold import of the editor entry point

```
python -X importtime -c "import editor.isolated_editor_main"
```

| Module | Cumulative | Share |
|---|---|---|
| **`editor.isolated_editor_main` (total)** | **1 997 931 µs ≈ 2.00 s** | 100 % |
| `editor.interface_smoke_test` | 1 541 033 µs | 77 % |
| └ `editor.widgets.logic_graph_editor` | 1 467 404 µs | 73 % |
| └ `editor.widgets.logic_graph.items` | 1 422 875 µs | 71 % |
| └ `engine.logic.graph_asset` → `engine` → `engine.core` | 1 406 207 µs | 70 % |
| └ `engine.game_object` → `engine.core.component` | 954 149 µs | 48 % |
| **└ `numpy`** | **951 065 µs** | **48 %** |
| `pygame` | 202 802 µs | 10 % |
| `PySide6.QtCore` | 117 571 µs | 6 % |
| `engine.ui.runtime_components` | 172 925 µs | 9 % |

**Headline: `numpy` is 48 % of editor startup.**

It is pulled in by a single import at `engine/core/component.py:73`, used only to store
3-element `float32` vectors in `Transform`:

```python
self._position = np.array([x, y, z], dtype=np.float32)
self._rotation = np.array([rx, ry, rz], dtype=np.float32)
self._scale    = np.array([sx, sy, sz], dtype=np.float32)
```

Because `engine.core.component` sits inside the 24-module engine import cycle,
*everything* transitively imports numpy — including the Qt editor, which never does
vector math.

### Standalone module costs

| Operation | Median |
|---|---|
| `import numpy` | 151.0 ms |
| `import pygame` | 80.3 ms |
| `import engine.logic.node_definitions` (cold) | **137.7 ms** |
| `import engine.logic.runtime.core` (after the above) | ~0 ms |
| `QApplication()` construction (offscreen) | 165.5 ms |

`engine.logic.node_definitions` costs 137.7 ms at *import time* because
`__init__.py` runs `_populate_declarative_node_definitions()` (20 submodule imports) and
`_populate_node_definitions()` (instantiates a `MetadataManager`) as import side effects.
It produces 154 catalogue entries.

### Startup summary

| Metric | Baseline |
|---|---|
| Editor cold import (no window) | **2.00 s** |
| ├ numpy | 0.95 s (48 %) |
| ├ pygame | 0.20 s (10 %) |
| ├ node definition catalogue | 0.14 s (7 %) |
| └ PySide6 + editor widgets | ~0.71 s (35 %) |
| `QApplication()` | +0.17 s |
| **Estimated time to first window** | **~2.2 s + widget construction** |

Not measured: full GUI startup to interactive, project open, and scene open through the
real UI — these require an interactive session. They should be added to this baseline
before Phase 9.5B closes.

---

## 2. Logic Graph editor — the dominant performance defect

Benchmark: a linear chain of `log_message` nodes, `LogicGraphEditor.set_graph()`,
offscreen Qt, one fresh process per size.

| Nodes | `set_graph()` | per node | 20 zoom steps |
|---:|---:|---:|---:|
| 10 | **79.6 ms** | 7.96 ms | 0.7 ms |
| 100 | **1 813 ms** | 18.13 ms | 0.6 ms |
| 150 | **4 563 ms** | 30.42 ms | 0.6 ms |
| 500 | **37 376 ms (37.4 s)** | 74.75 ms | 0.2 ms |
| 1000 | **> 110 s (timed out)** | — | — |

Per-node cost grows linearly with graph size ⇒ **total cost is O(n²)**.

- 100 nodes: **1.8 seconds** — noticeable stall.
- 500 nodes: **37 seconds** — the editor is indistinguishable from hung.
- 1000 nodes: did not complete within 110 s.

Panning and zooming are fine (sub-millisecond); the cost is entirely in *loading*.

### Root cause (cProfile, n = 150)

```
ncalls  tottime  cumtime  function
 11475    1.089    1.089  QGraphicsTextItem.setHtml
 23100    0.833    0.833  QGraphicsTextItem.setPlainText
 11475    0.375    0.697  engine/logic/code_preview.py:11  node_code_preview
   151    0.189    3.908  logic_graph/editor_mixins/canvas_mixin.py:124  refresh_connections
780300    0.163    0.266  engine/logic/code_preview.py:7   _value
26850/4500 0.137   3.901  logic_graph/items.py:647  itemChange
 11475    0.125    2.515  logic_graph/items.py:599  refresh_text
   151    0.121    0.125  QGraphicsScene.itemsBoundingRect
   151    0.081    0.778  logic_graph/target_hints.py:9  refresh_target_hints
```

**`refresh_connections()` is called 151 times for a 150-node graph** — once per node
inserted, rather than once after the load completes. It is triggered through
`LogicItem.itemChange` (`items.py:647`) firing on every scene insertion.

Each of those 151 passes re-runs `refresh_target_hints()` and `refresh_text()` over
*every* node already in the scene. Result for 150 nodes:

- **11 475 `setHtml()` calls** (150 × 76.5) — should be 150
- **23 100 `setPlainText()` calls** — should be ~300
- **11 475 `node_code_preview()` calls** — should be 150
- **780 300 `_value()` calls**
- **1 503 594 `dict.get()` calls**

`itemsBoundingRect()` is also recomputed 151 times.

**Assessment.** This is the strongest single explanation for "the engine feels heavy".
It is not a distributed architectural cost — it is one missing batch guard. A
`begin_bulk_load()` / `end_bulk_load()` flag around `set_graph()` that suppresses
`refresh_connections`, `refresh_target_hints` and `refresh_text` until the load finishes
should convert O(n²) to O(n) and bring 500 nodes from 37 s to well under 1 s.

Project graphs today are small, so this is currently latent — but it caps how large a
game the engine can author, and it degrades continuously as graphs grow.

---

## 3. Asset pipeline

| Operation | Median | Verdict |
|---|---|---|
| `glob` full asset rescan (716 paths) | **9.9 ms** | fast |
| Parse all 22 `.zscene` (JSON) | **5.1 ms** | fast |
| Parse all 56 `.zlogic` (JSON) | **9.6 ms** | fast |
| Asset panel refresh debounce | 220 ms (`QTimer`, single-shot) | appropriate |
| Icon cache | 256 entries, FIFO eviction, keyed on `(path, mtime_ns, size)` | correct |

### Asset database questionnaire

| Question | Answer |
|---|---|
| Full rescan or incremental? | Full rescan of the tree on refresh — but it costs 10 ms |
| File watcher? | Yes — `QFileSystemWatcher` on directories and files |
| Debounced? | Yes — 220 ms single-shot `QTimer`, plus `_refresh_if_idle` guard |
| Hash-based invalidation? | No |
| mtime-based? | Yes, for the icon cache key |
| Thumbnail cache? | Yes, bounded at 256 |
| UI state preserved across refresh? | Yes — selection and expanded set are saved and restored |

**Conclusion: the perceived heaviness does not come from asset indexing.** At 716 assets
the whole pipeline is ~25 ms. `editor/assets_panel_controller.py` is the best-engineered
panel in the editor (explicit `install()`/`uninstall()`, debouncing, bounded cache,
state preservation) and should be the template other panels copy.

---

## 4. Runtime micro-benchmarks

| Operation | Median | Note |
|---|---|---|
| `Transform.position` setter × 10 000 (numpy) | **5.8 ms** (0.58 µs/set) | allocates a `np.array` per assignment |
| plain tuple assignment × 10 000 (reference) | 0.7 ms (0.07 µs/set) | 8.3× faster |

Per-call the numpy cost is negligible; the case against it is the **151 ms import tax on
every process** including the editor, not the arithmetic. At 1 000 moving objects × 60 fps
the setter costs ~35 ms/s of CPU — measurable but not dominant.

---

## 5. Panel refresh behaviour

| Panel | Strategy | Preserves state? | Assessment |
|---|---|---|---|
| **Asset Browser** | full rebuild, debounced 220 ms | ✔ selection + expansion | good |
| **Hierarchy** (`premium_hierarchy_panel.py:147`) | `self.tree.clear()` + full rebuild | ✘ **expansion and scroll lost** | matches the previously-reported "hierarchy reorder/reset" bug |
| **Inspector** (`_update_inspector`) | full rebuild, called from 6 distinct mutation sites (`inspector_controller.py:245,373,439`, `inspector_controller_ui_media.py:94`, `behavior_tree_inspector_controller.py:106,218`) | ✘ | rebuilds on every property edit |

`refresh_objects()` in full:

```python
def refresh_objects(self, objects):
    self.tree.blockSignals(True)
    self.tree.clear()                    # ← destroys all expansion + scroll state
    root = QTreeWidgetItem(self.tree, ["MainScene", "", ""])
    ...
```

The Asset Browser already solves exactly this problem 40 lines away in
`assets_panel_controller.py::refresh()` by capturing `selected_path` and the `expanded`
set before rebuilding. Porting that pattern to the Hierarchy is a small, contained fix.

Inspector rebuild frequency was not instrumented (needs an interactive session); it is
recorded as a known unmeasured item.

---

## 6. Memory

Not measured at the process level — `psutil` is not installed in this environment and
introducing a dependency was out of scope for a read-only audit.

What is known structurally (see the stability audit §10):

| Cache | Bounded |
|---|---|
| `_ICON_CACHE` (asset panel) | ✔ 256 |
| `ImageComponent._surface_cache` | ✔ 128 |
| `ImageComponent._transformed_cache` | ✔ 256 |
| `InfiniteBackground._tile_cache` | ✔ 64 |
| `production_runtime._cache` | ✔ MB budget, LRU |
| **`engine/audio/__init__.py::_sound_cache`** | ✘ unbounded |
| **`engine/ui/ui_renderer.py::_font_cache`** | ✘ unbounded |
| **`engine/ui/ui_renderer.py::_image_cache`** | ✘ unbounded |

**Active regression:** `engine/ui/sprite_performance_patch.py:48,114` replaces the
bounded `OrderedDict` caches with plain `dict`s, disabling the `popitem(last=False)`
eviction in `runtime_components.py`. When that patch is applied, two previously bounded
caches become unbounded for the remainder of the session.

**To add to this baseline:** `tracemalloc` snapshots at editor idle, after project open,
and after 5 Play/Stop cycles. The Play/Stop delta is the number that matters, given the
service-layer leaks documented in the stability audit §4.

---

## 7. Baseline table (record these; compare after 9.5B)

| Metric | Baseline (2026-08-10) | Target |
|---|---|---|
| Editor cold import | **2.00 s** | < 1.0 s (defer numpy) |
| └ numpy share | **48 %** | 0 % at import |
| Node definition catalogue build | 137.7 ms | < 40 ms (lazy) |
| `QApplication()` | 165.5 ms | unchanged |
| Asset rescan (716 paths) | 9.9 ms | unchanged |
| Parse 22 `.zscene` | 5.1 ms | unchanged |
| Parse 56 `.zlogic` | 9.6 ms | unchanged |
| **Graph editor open, 10 nodes** | **79.6 ms** | < 50 ms |
| **Graph editor open, 100 nodes** | **1 813 ms** | **< 150 ms** |
| **Graph editor open, 500 nodes** | **37 376 ms** | **< 800 ms** |
| **Graph editor open, 1000 nodes** | **> 110 s (timeout)** | **< 2 s** |
| Graph pan / zoom (any size) | < 1 ms | unchanged |
| `Transform.position` set | 0.58 µs | 0.10 µs (tuple/slots) |
| Project open time | *not measured* | instrument |
| Scene open time | *not measured* | instrument |
| Play start / Stop time | *not measured* | instrument |
| Memory idle / Play / after 5 Play cycles | *not measured* | instrument |
| Inspector rebuilds per property edit | *not measured* | instrument |

---

## 8. Findings, ranked by impact

1. **P1 — Logic Graph editor load is O(n²).** 37 s for 500 nodes. Cause:
   `refresh_connections()` fires once per inserted node via `items.py:647 itemChange`,
   each pass re-rendering every existing node's HTML. Fix: bulk-load guard.
2. **P2 — numpy is 48 % of a 2 s startup**, imported by `engine/core/component.py` for
   3-element vectors and dragged into the Qt editor by the engine import cycle.
   Fix: lazy import, or replace `Transform` vectors with `__slots__` floats.
3. **P2 — node definition catalogue costs 137.7 ms at import time** through module-level
   side effects. Fix: make catalogue construction lazy and explicit.
4. **P2 — Hierarchy panel discards expansion and scroll state** on every refresh. Fix:
   copy the Asset Browser's existing state-preservation code.
5. **P3 — three unbounded caches**, plus a patch that un-bounds two more.
6. **P3 — `Transform` allocates a numpy array per position write** (8.3× a tuple).

**Asset indexing is explicitly cleared** as a cause of perceived heaviness.

---

*Read-only audit. No production code was modified.*
