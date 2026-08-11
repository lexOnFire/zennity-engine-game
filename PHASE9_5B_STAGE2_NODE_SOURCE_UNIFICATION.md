# PHASE 9.5B — Stage 2: Node Registration & Source-of-Truth Unification

Status: **complete**. Do not start Stage 3 from this document.

## What was wrong

The node system had two of everything, and no answer to "which nodes exist?" —
only "which nodes exist given what happened to be imported first".

**Two mutable definition sources.** `engine/logic/node_definitions/__init__.py`
built a `NODE_DEFINITIONS` dict at import time; `engine/logic/graph_asset.py`
then mutated that same dict *and* maintained a second hand-written table,
`NODE_PORT_DEFINITIONS`. The two disagreed for **52 node types**. The
`NodeDefinitionRegistry` that was supposed to own all of this existed but was
**completely empty** — nothing ever wrote to it.

The divergence was not cosmetic. The declarative `NodeDefinition` classes used
pins named `exec` / `exec_done` / `exec_success`, while `.zlogic` assets and the
runtime executors speak `in` / `next` / `true` / `false`. Because
`graph_normalizer` and the inspector seed a node's **properties** from
`NODE_DEFINITIONS["inputs"]`, dragging `play_animation` onto the canvas produced
a node carrying `target` / `animation_name` / `force` properties while its
executor read `state`. That class of mismatch is what produced the Stage 1
regressions.

**Two runtime loading paths.** `engine/logic/runtime/nodes/__init__.py` imported
13 of the 23 shipping node modules; `LogicProvider.boot()` imported a different
set of 22 and then re-registered ~100 definitions by hand. The editor process
had **87 executors**; whole domains — dialogue, audio, camera, save/load,
pathfinding, advanced input — were simply absent unless a provider had booted.

## What it is now

```
NodeDefinition classes ─┐
_LEGACY_SEED_DEFINITIONS ├─→ NodeDefinitionRegistry ─→ NODE_DEFINITIONS      (read-only view)
_EXPLICIT_PORT_CONTRACTS ┘    (the only mutable store)  └→ NODE_PORT_DEFINITIONS (read-only view)

RUNTIME_NODE_MODULES ─→ load_runtime_node_modules() ─→ executors / evaluators
                              ▲                ▲
                    runtime/nodes/__init__   LogicProvider.boot()
```

| | Before | After |
|---|---|---|
| Mutable definition sources | 2 | **1** |
| Runtime load paths | 2 | **1** |
| `NODE_PORT_DEFINITIONS` | independent table | **derived read-only view** |
| Definitions disagreeing with the port schema | 52 | **0** |
| Executors in an editor process | 87 | **128** |
| Runtime modules loaded without a provider | 13 / 23 | **23 / 23** |
| Catalogue built at import time | yes | **no** (lazy, 8.4 ms once) |

### Key modules

- **`engine/logic/node_definitions/catalogue.py`** — the single builder. Owns the
  seed data (`_EXPLICIT_PORT_CONTRACTS`, `_LEGACY_SEED_DEFINITIONS`, component
  defaults, alias table) and `ensure_catalogue_loaded()`, which is idempotent and
  lazy.
- **`engine/logic/node_definitions/registry.py`** — `NodeDefinitionRegistry`, now
  actually populated. Holds the resolved definitions, the port schema, and owner
  metadata. `schema_drift()` returns the node ids where a definition's pins
  disagree with its port schema entry; by construction it must always be empty.
- **`engine/logic/runtime/node_loader.py`** — `RUNTIME_NODE_MODULES` and
  `load_runtime_node_modules()`. Lives inside the runtime package on purpose: the
  exporter copies `engine/logic/runtime` wholesale, so the canonical list travels
  with an exported game.
- **`engine/logic/node_system.py`** — `describe_node()`,
  `validate_node_system()`, `get_node_system_status()`. Qt-free, so the CI gate,
  a headless probe and the viewport subprocess can all call it.
- **`tools/audit_node_system.py`** — report / JSON snapshot / `--ci` gate.

### The unification decision

Where a declarative `NodeDefinition` and the explicit graph contract disagreed,
**the graph contract won**. It is what shipping assets and executors actually
speak; the declarative pins were aspirational and unreachable. The declarative
objects still contribute title, category, description and property defaults.

Consequence: the port schema is byte-identical to the pre-Stage-2 table (verified
against `tests/fixtures/stage2/registration_baseline.json`), and the 52 diverged
definitions were realigned onto it — which fixes property seeding for those
nodes. The palette's node set is unchanged: 154 definitions, same ids.

## Verification

```
python tools/audit_node_system.py --ci     # gate: parity + contract violations
python -m pytest tests/logic/stage2         # 160 tests
```

The gate fails when a definition's pins diverge from the port schema, a runtime
module on disk is missing from `RUNTIME_NODE_MODULES` (or vice versa), a module
fails to import, an executor or evaluator has no port contract, two modules claim
the same node id outside the recorded baseline, or booting `LogicProvider`
produces a registration the non-provider path lacks.

## Known issues, recorded not fixed

### Duplicate executor ownership (5 nodes)

Two modules register an executor for the same id. Load order is deterministic, so
the winner is stable and **unchanged from before Stage 2** — but the loser is
dead code, and in two cases the winner is the weaker implementation:

| node | modules | winner | note |
|---|---|---|---|
| `play_animation` | `actions_nodes`, `animation_nodes` | `animation_nodes` | winner returns `success`/`failure`, ports the contract does not declare, so the flow stops |
| `stop_animation` | `actions_nodes`, `animation_nodes` | `animation_nodes` | same |
| `set_variable` | `misc_nodes`, `scene_nodes` | `scene_nodes` | winner is the legacy shim |
| `load_game` | `save_load_nodes`, `scene_nodes` | `scene_nodes` | winner is the legacy shim |
| `has_save` | `save_load_nodes`, `scene_nodes` | `scene_nodes` | winner is a stub that always returns `false` |

Resolving these changes gameplay, which Stage 2 is not permitted to do. They are
pinned in `node_system.KNOWN_DUPLICATE_OWNERS`; the CI gate fails on any *new*
duplicate. **Stage 3 candidate.**

### Orphan graph edges (11 assets, 72 edges)

Recorded in `tests/fixtures/stage2/orphan_edge_baseline.json`. These are assets
saved against node types that no longer exist (`math.distance`, `project_get`,
`ui_get_widget`, …). Counts are **identical before and after Stage 2** — the
derived schema resolves exactly the ports the hand-written table did. Asset work,
not node-system work. Includes the known `EnemyAILogic` / `get_position.position`
issue, which is explicitly out of scope.

### `test_logic_graph_asset` — 9 pre-existing failures

Unchanged: same 9 tests, same lines, same assertions, before and after. Seven are
numeric gameplay assertions unrelated to ports. Two are port-related and worth a
Stage 3 look:

- `test_condition_nodes_expose_named_typed_ports` expects `if_else.condition` to
  be `bool`; the shipped contract says `any`. Narrowing it is a contract change.
- `test_beginner_recipe_search_builds_move_x_flow` expects `move_by` to carry
  only `x`/`y` properties. Its contract has five data pins (`velocity`,
  `delta_x`, `delta_y`, `x`, `y`) accumulated from aliases, and every data pin is
  seeded as a property. The real defect is that *a pin is not a property* —
  changing that heuristic affects every node, so it is Stage 3 work.

No test was edited to make it pass.

### Standalone export

`test_exported_game_validates_outside_the_editor` fails, as it did before Stage 2
(then: `No module named 'engine'` from `engine.animation.animation_controller`).
Stage 2 moved the failure further down the chain by shipping the catalogue as a
package; the remaining gaps (`physics_event_dispatch`, `engine.animation`) are
pre-existing exporter omissions outside this scope.

## Shadowed modules

`engine/logic/node_definitions.py` and `engine/logic/runtime.py` were removed.
Proof, not grep: the packages of the same name win import resolution; neither
file declared a top-level symbol its package does not provide; no
`spec_from_file_location` or path-based load targets them; and the exporter no
longer copies `node_definitions.py` (it now ships the package instead).

`engine/core.py` was **quarantined, not removed** — it is a deliberate fallback
for the case where `engine/core/` is not on the path, declared as such since
Sprint 1.4. Removing it would require proving that scenario cannot occur in any
distribution, which Stage 2 did not establish.
