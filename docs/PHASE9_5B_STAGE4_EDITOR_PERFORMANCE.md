# PHASE 9.5B — Stage 4: Editor Responsiveness & Performance Hardening

Status: **partial — the Logic Graph P0 is closed; other areas were measured but
not optimised.** Do not start Stage 5 from this document.

## Rule followed

Optimise only where measurement proves cost. Everything below was measured
first; areas that measured cheap were left alone deliberately.

## The Logic Graph load was quadratic — confirmed, then fixed

Measured with `scripts/benchmark_editor_performance.py`:

| nodes | before | after | speedup | `refresh_connections` before → after |
|---:|---:|---:|---:|:--|
| 10 | 145 ms | 91 ms | 1.6× | 10 → 2 |
| 100 | 2 517 ms | 542 ms | 4.6× | 100 → 2 |
| 200 | 8 040 ms | 1 133 ms | 7.1× | 200 → 2 |
| 400 | 31 394 ms | 2 687 ms | **11.7×** | 400 → 2 |
| 500 | — | 2 572 ms | — | → 2 |
| 1000 | **never finished** | 6 055 ms | — | → 2 |

Time ratio when the node count doubles: **3.19× / 3.90× before**, **2.09× /
2.37× / 2.35× after**. Quadratic to roughly linear.

### Root causes

1. **`LogicNodeItem.itemChange`** called `refresh_connections()` on every
   `ItemPositionHasChanged`. Placing a node fires that, so a load did one full
   walk of every edge and every node *per node*. `set_graph` already had a
   `_loading_graph` flag and already called `refresh_connections()` once at the
   end — the handler simply never consulted it.

2. **The same handler called `mark_dirty()` per node**, so merely *opening* a
   graph marked it unsaved. That was a correctness bug hiding inside the
   performance bug; it is now 0 calls and `_dirty` stays `False` after a load.

3. **`graph_validator` cycle detection was recursive.** Once loading got fast
   enough to reach validation on a 1000-node chain, it raised `RecursionError`
   instead of validating. Converted to an explicit stack; traversal order and
   the resulting cycle set are unchanged, verified against graphs with and
   without cycles at 50 and 1000 nodes.

### The fix

`LogicGraphEditor.bulk_update()` — a re-entrant context manager. Inside it,
`request_connection_refresh()` records that a refresh is owed; exactly one
refresh runs when the outermost block exits. `set_graph` wraps its item
construction in it.

Node positions are still written back to the graph data during the bulk block,
and the trailing refresh reflects the final state of every node and edge — so
nothing is skipped, only deduplicated. A test asserts all 99 edges of a
100-node graph are rendered after a bulk load.

## Measured and deliberately left alone

- **`AssetDatabase` scan** — ~10 ms for ~716 paths. Not a bottleneck; touching
  it would be speculative work.
- **Sprite/background caches** — already bounded at 256/64 (Stage 3 audit).

## Not done in this stage

Startup profiling (`-X importtime`, the numpy cost), Inspector and Hierarchy
rebuild counts, scene-open breakdown at 1000/5000 objects, pan/zoom frame cost,
thumbnail threading, and Play/Stop latency were **not measured or changed**.
The Logic Graph was the P0 with a confirmed 11.7× win available; the rest of the
brief is open work, and this document should not be read as covering it.

## Regression strategy

The tests in `tests/performance/` assert **call counts and growth ratios**, not
milliseconds. A wall-clock threshold is a flaky gate on shared CI hardware; the
refresh count is the invariant that actually encodes the algorithm. The one
timing test uses a deliberately generous 3.2× ceiling — it exists to catch a
return to quadratic behaviour, not to police variance.

```
pytest tests/performance/                                # CI gate
python scripts/benchmark_editor_performance.py           # numbers, on demand
python scripts/benchmark_editor_performance.py --sizes 500,1000
```

## Manual validation still required

Numbers do not answer "does it *feel* faster". Please exercise: open a small
graph, open a large one, pan and zoom, edit a node, switch objects in the
Inspector, drag in the Hierarchy, and Play/Stop.
