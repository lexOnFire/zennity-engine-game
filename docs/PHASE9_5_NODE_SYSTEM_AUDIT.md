# Phase 9.5 — Node System Audit

**Date:** 2026-08-10
**Tool:** `scripts/audit_node_system.py` (read-only; re-runnable; `--json` for CI)
**Scope:** the Logic Graph node system — definitions, executors, evaluators, registries,
palette, serialization, contracts, legacy.

> Reproduce every number in this document with:
> ```bash
> python scripts/audit_node_system.py
> ```

---

---

> ## ⚠ RESOLVIDO — Phase 9.5B Stage 1 foi implementado
>
> O conteúdo abaixo descreve o estado **antes** da correção e é mantido como
> registro da baseline. Ver `docs/PHASE9_5B_STAGE1_NODE_CONTRACTS.md`.
>
> | Métrica | Esta auditoria | Depois do Stage 1 |
> |---|---:|---:|
> | **CONTRACT VIOLATIONS** | **167** | **0** (+2 avisos) |
> | EXEC_PORT_MISMATCH | 45 | **0** |
> | UNREACHABLE_EXEC_PORT | 45 | **0** |
> | NO_DEFINITION | 33 | **0** |
> | DATA_PORT_MISMATCH | 24 | **0** |
> | INPUT_PORT_MISMATCH | 13 | **0** |
> | NO_RUNTIME | 7 | **0** |
> | IDs de nó duplicados | 2 | **0** |
> | Definições | 154 | 175 |
> | Executores / Avaliadores | 132 / 64 | 133 / 64 |
>
> **Porta canônica de sucesso: `next`.** Decisão registrada em
> `engine/logic/port_aliases.py` com a evidência que a sustenta.
>
> **Correções ao próprio relatório:**
> * O "bug do `sequence`" (§3.1) **não existia** — o nó sempre usou f-string
>   corretamente. Era falso positivo da ferramenta de auditoria, agora corrigida.
> * Os 5 `event_*` listados como `NO_RUNTIME` eram falsos positivos estruturais;
>   agora são classificados por `execution_model = EVENT_SOURCE` em vez de uma
>   lista de exceções hardcoded.
>
> **Ainda aberto para Stage 2:** `NODE_PORT_DEFINITIONS` em `graph_asset.py` é
> uma **quarta** tabela de portas mantida à mão, descoberta durante a regressão;
> os 2 registries e os 2 caminhos de registro continuam como estavam.

---

## 1. Counts

```
TOTAL NODE DEFINITIONS (resolved):   154
  declarative NodeDefinition objs:   126
  legacy NODE_DEFINITIONS entries:   154
EXECUTORS:                           132
EVALUATORS:                           64
PURE DATA NODES:                      20
FLOW NODES:                          118
EVENT NODES:                          16
```

| Question | Answer |
|---|---|
| Nodes with a definition but no executor **and** no evaluator | **7** |
| Runtime handlers with no definition | **33** |
| Duplicate executor IDs (same id registered twice) | 0 |
| Duplicate evaluator IDs | 0 |
| Duplicate display names | 4 |
| Duplicate node **IDs across definition modules** | **2** (`play_animation`, `stop_animation`) |
| Legacy / deprecated source markers | 26 |
| **NODE CONTRACT VIOLATIONS** | **167** |

---

## 2. Architecture — how a node gets registered

There are **two registries** and **two registration paths**, and they disagree.

### The two registries

| Registry | Module | Holds | Populated by |
|---|---|---|---|
| `NodeDefinitionRegistry` | `engine/logic/node_definitions/registry.py` (233 L) | canonical + legacy *definitions*, with conflict detection | `get_registry()` — **and essentially nothing calls `register_canonical()`** |
| `NodeRegistry` | `engine/logic/runtime/registry.py` (61 L) | `executors` / `evaluators` dicts | `@registry.register_executor(...)` decorators, at import time |

`NodeDefinitionRegistry` has a full conflict-detection design (`detect_conflicts()`,
`NodeDefinitionConflictError`, canonical→legacy resolution). It is effectively unused:
the actual definition catalogue is the plain module-level dict
`engine/logic/node_definitions/__init__.py::NODE_DEFINITIONS`, populated by reflection.
**The safety machinery that would have caught the duplicate `play_animation` exists and
is not wired in.**

### The two registration paths

```
PATH A — implicit, import-time, reflective
  engine/logic/runtime/core.py:15   `from . import nodes`
    └── engine/logic/runtime/nodes/__init__.py  imports 14 of 23 modules

PATH B — explicit, boot-time, hand-written
  LogicProvider.boot()
    ├── imports 22 of 23 runtime node modules
    └── hand-registers ~110 definitions across ~250 lines of manager.register(...)
```

**Divergence measured:**

| Path | modules imported |
|---|---|
| `runtime/nodes/__init__.py` | **14** |
| `LogicProvider.boot()` | **22** |
| modules on disk | **23** |

Not imported by `runtime/nodes/__init__.py`:
`audio_advanced_nodes`, `camera_nodes`, `dialog_nodes`, `input_advanced_nodes`,
`particle_nodes`, `pathfinding_nodes`, `save_load_nodes`, `state_machine_nodes`,
`ui_binding_nodes` — **9 modules.**

Not imported by `LogicProvider.boot()`: `ui_nodes` — **1 module.**

**Consequence.** Any entry point that reaches the runtime through
`engine.logic.runtime.core` *without* booting `LogicProvider` (isolated tests, the
production runtime, tooling) gets executors for 14 modules only. Audio, camera,
dialogue, touch input, particles, pathfinding, save/load, state machines and UI binding
nodes have **no executor** on that path. `output_evaluator.py` even documents this with
a `# Fallback for isolated tests` branch. Two different node systems depending on how
you started.

### Definition harvesting is reflective

```python
# node_definitions/__init__.py::_collect_declarative_definitions
for value in vars(module).values():
    definition = getattr(value, "__node_definition__", None)
    ...
    NODE_DEFINITIONS[node_id] = _definition_to_legacy(definition)   # last write wins
```

Modules are walked in the fixed `_DECLARATIVE_MODULES` order. `actions_nodes` precedes
`animation_nodes`, so **`animation_nodes` wins every id collision**. There is no
warning, no conflict check, no log line.

---

## 3. NODE CONTRACT VIOLATIONS: 167

| Kind | Count | Meaning |
|---|---|---|
| `EXEC_PORT_MISMATCH` | 45 | executor returns an exec port the definition does not declare |
| `UNREACHABLE_EXEC_PORT` | 45 | definition declares an exec output the executor never returns |
| `NO_DEFINITION` | 33 | runtime handler exists, no definition → invisible in the palette |
| `DATA_PORT_MISMATCH` | 24 | executor `_store`s a value on an undeclared output port |
| `INPUT_PORT_MISMATCH` | 13 | executor `_read_input`s a port that is neither an input nor a property |
| `NO_RUNTIME` | 7 | definition in the palette, nothing executes it |

### 3.1 P0 — the `next` / `exec_done` split (45 + 45 violations)

This is the single largest defect in the engine.

**The definitions say** (`node_definitions/actions_nodes.py:20`):
```python
PinDefinition(id="exec_done", label_key="Pronto", pin_type=PinType.EXEC)
```

**The executors say** (`runtime/nodes/actions_nodes.py`, and 44 others):
```python
return ["next"]
```

**The runtime matches exec ports by exact string** — `engine/logic/runtime/core.py:553`
and `:616`:
```python
if str(edge.get("from_port", "next")) != port:
    continue
```

There is **no alias table anywhere**. Verified: `graph_normalizer.py` and
`graph_migration.py` contain no `exec_done` mapping.

**Why the project still works today.** Every saved `.zlogic` asset predates the
declarative definitions. Measured across all 56 project assets:

```
from_port counts: next=137, value=100, None=83, true=47, exec=18,
                  other=9, object=5, false=4, ... exec_done=0
```

**Zero saved edges use `exec_done`.** Old graphs work because they were authored when
the palette emitted `next`.

**Why authoring feels broken.** A node dragged from the palette *today* renders an
output pin labelled "Pronto" with id `exec_done`. Connecting it saves
`from_port: "exec_done"`. The executor returns `["next"]`. `_follow` finds no matching
edge. **The chain stops dead, silently, with no error, no log, and no visual feedback.**

This precisely explains "nodes that do nothing" and "engine behaves unpredictably".
The current branch is named `fix/executor-port-contract`, so this is known — this audit
quantifies it at **45 affected nodes**.

Affected nodes (`EXEC_PORT_MISMATCH`, abbreviated): `add_component`,
`bind_ui_to_blackboard`, `call_subgraph`, `clone_object`, `create_object`,
`create_prefab`, `destroy_after_time`, `emit_event`, `get_continuous_motion`,
`get_progress_bar_value`, `get_ui_widget_property`, `get_variable`, `input_axis`,
`is_grounded`, `jump`, `key_held`, `key_pressed`, `log_message`, `move`, `move_by`,
`patrol_axis`, `pause_continuous_motion`, `play_animation`, `play_animation_asset`,
`play_sound`, `read_key_axis`, `remove_component`, `resume_continuous_motion`,
`rotate`, `sequence`, `set_active`, `set_sprite`, `set_ui_progress_bar`, `set_ui_text`,
`set_ui_visible`, `set_variable`, `start_behavior_tree`, `start_continuous_motion`,
`start_texture_scroll`, `stop_animation`, `stop_continuous_motion`,
`stop_texture_scroll`, `update_continuous_motion` (+2).

Three sub-flavours beyond plain `next`↔`exec_done`:

- **boolean-branch nodes** return `["true","false"]` but declare domain-specific pins:
  `is_grounded` declares `grounded`/`airborne`; `key_held` declares `held`/`released`;
  `key_pressed` declares only `exec_pressed`.
- **`sequence`** returns the *literal unformatted string* `"then_{index}"` — an
  un-interpolated f-string bug — while declaring `next`, `then_0`, `then_1`.
- **`create_object` / `clone_object` / `create_prefab`** return `limit_reached`, which
  no definition declares at all.

### 3.2 P0 — `play_animation` / `stop_animation` defined twice with different contracts

| | `node_definitions/actions_nodes.py:7` | `node_definitions/animation_nodes.py:6` |
|---|---|---|
| id | `play_animation` | `play_animation` |
| inputs | `exec`, **`state`** (str, "Idle") | `exec`, **`target`** (str, "player"), **`animation_name`** (str, "idle") |
| outputs | `exec_done` | `exec_success`, `exec_failure` |

The reflective harvest gives the palette the **animation_nodes** version
(`target`/`animation_name`). `LogicProvider.boot()` explicitly registers the
**actions_nodes** version into `MetadataManager`. The executor reads `state`:

```
[INPUT_PORT_MISMATCH] play_animation: executor reads ['state'] not in inputs/properties
```

So: the palette offers pins the executor never reads, the executor reads a pin the
palette never renders, and the two registries hold different definitions of the same
id. Same story for `stop_animation`. **Split-brain on a core gameplay node.**

### 3.3 P1 — 33 runtime handlers with no definition (invisible nodes)

These execute correctly if a graph references them, but they cannot be discovered in
the palette. Several are clearly dotted-namespace aliases of an existing node:

| Group | IDs |
|---|---|
| math (no definitions at all) | `add_number`, `subtract_number`, `multiply_number`, `divide_number`, `clamp_number`, `absolute_number`, `random_number` |
| logic | `and`, `or`, `not` |
| string | `join_text`, `to_text` |
| scene — **5 aliases for one action** | `load_scene`, `open_scene`, `scene_load`, `scene.load`, `scene.load_scene` |
| quit — **3 aliases** | `exit_game`, `quit_game`, `app.quit` |
| UI — **4 aliases / 2 actions** | `button_clicked`, `ui.button_clicked`, `on_ui_click`, `set_ui_enabled`, `ui.set_widget_enabled` |
| save | `game.has_save`, `game.load_game` |
| object | `get_position`, `get_object_name`, `find_nearest_object`, `find_tag` |
| misc | `delta_time`, `subgraph_input`, `variables.set` |

An entire **math and logic node category has no definitions** — meaning arithmetic and
boolean nodes do not appear in the Logic Graph palette at all, despite working at
runtime. That is a significant authoring gap, not just a cosmetic one.

### 3.4 P1 — 7 definitions with no runtime

| Node | Note |
|---|---|
| `event_start` | handled structurally by `core.py` (`_follow(..., "next")` at frame 0), not via the registry |
| `event_update` | same |
| `event_timer` | same |
| `event_key_pressed` | same |
| `event_object_created` | same |
| **`animate_value`** | no special-casing found — appears genuinely non-functional |
| **`wait_until_condition`** | no special-casing found — appears genuinely non-functional |

The five `event_*` entries are false positives of the audit heuristic (they are
dispatched by the runtime's frame loop, not the node registry) and are documented here
so the tool's output is not misread. `animate_value` and `wait_until_condition` are
real gaps.

### 3.5 P2 — 24 `DATA_PORT_MISMATCH`

Executors `_store()` values on ports the definition does not expose, so the value is
computed and then unreachable from the graph. Examples:

- `raycast` stores `hit`, `hit_normal`, `hit_point` — declares `hit_object`,
  `hit_point_x/y`, `hit_normal_x/y`, `hit_distance`. The scalar-split ports are declared;
  the vector ports the executor actually writes are not.
- `create_state_machine` stores `current_state`, `machine_id`; declares
  `machine_id_out`, `initial_state_out` — a naming convention applied to the definition
  but never to the executor.
- `save_game` / `load_game` store `slot_name`; declare `slot_name_out`.
- `camera_shake` stores `shaking`; declares neither.
- `get_continuous_motion` stores `active`, `paused`, `speed`, `x`, `y`; declares
  `velocity_x`, `velocity_y`.

The `_out` suffix pattern shows a rename was applied to definitions and never
propagated to the runtime.

### 3.6 P2 — 13 `INPUT_PORT_MISMATCH`

Executor reads a port that does not exist, so `_read_input` always falls through to its
default. The node silently uses the wrong value:

`clone_object` reads `name`; `compare_text` reads `other`; `create_object` reads
`source`; `get_continuous_motion` / `pause_continuous_motion` /
`resume_continuous_motion` / `stop_continuous_motion` / `update_continuous_motion` read
`movement`; `log_message` reads `text`; `move` reads `value`; `move_by` reads `x`,`y`;
`patrol_axis` reads `minimum`,`maximum`; `play_animation` reads `state`.

`log_message` reading a non-existent `text` port means **the log node cannot log a
connected value** — it can only print its literal property. That alone degrades every
debugging session in the editor.

---

## 4. Palette / category UX

No category exceeds 30 nodes, so **no category needs splitting**. The problem is the
opposite: 29 categories for 154 nodes, several of them near-duplicates.

| Category | Nodes | |
|---|---|---|
| Components | 13 | |
| Action | 12 | |
| Events | 11 | |
| Movement | 10 | |
| UI | 9 | |
| Objects | 7 | |
| Input | 7 | |
| Animation | 6 | |
| Animation/Getters | 6 | ← fragment |
| Flow | 6 | |
| Logic/UI Dynamic | 6 | ← fragment, overlaps `UI` |
| Physics/Getters | 6 | ← fragment |
| Camera | 5 | |
| StateManagement | 5 | |
| Audio | 4 | |
| Dialog | 4 | |
| Physics | 4 | |
| Navigation | 4 | |
| Physics/Events | 4 | ← fragment |
| Physics/Layers | 4 | ← fragment |
| Persistence | 4 | |
| Values | 3 | |
| Particles | 3 | |
| Condition | 2 | ← overlaps `Flow`, `Logic` |
| Animation/Events | 2 | ← fragment |
| Logic | 2 | ← overlaps `Flow`, `Condition` |
| Variables | 2 | ← overlaps `Values` |
| Graphs | 2 | |
| Physics/Queries | 1 | ← fragment |

**Physics is split across 5 categories** (`Physics`, `/Getters`, `/Events`, `/Layers`,
`/Queries`) totalling 19 nodes. **Animation across 3** (`Animation`, `/Getters`,
`/Events`) totalling 14. Neither would exceed 30 if merged with sub-headers.

Note also: `_definition_to_legacy` contains `category = {"Actions": "Action"}.get(...)`
— a hardcoded singular/plural patch, evidence of ad-hoc category drift.

### Confusing / duplicate names

**4 exact duplicate display names**, each a legacy-vs-modern pair of the same event:

| Display name | IDs |
|---|---|
| "On Collision Enter" | `event_collision_enter`, `on_collision_enter` |
| "On Collision Exit" | `event_collision_exit`, `on_collision_exit` |
| "On Trigger Enter" | `event_trigger_enter`, `on_trigger_enter` |
| "On Trigger Exit" | `event_trigger_exit`, `on_trigger_exit` |

A user sees two identical entries in the palette and cannot tell which one works.

**Semantic redundancies** (the "Set Value / Set Variable / Update Variable" class the
brief predicted):

| Cluster | Members |
|---|---|
| variable writes | `set_variable`, `variables.set` |
| UI binding | `bind_ui_to_variable`, `bind_ui_to_blackboard`, `update_ui_binding` |
| scene loading | `load_scene`, `open_scene`, `scene_load`, `scene.load`, `scene.load_scene`, `restart_scene` |
| quitting | `exit_game`, `quit_game`, `app.quit` |
| UI click | `button_clicked`, `ui.button_clicked`, `on_ui_click` |
| UI enable | `set_ui_enabled`, `ui.set_widget_enabled` |
| key input | `key_pressed`, `key_held`, `is_key_pressed`, `event_key_pressed`, `wait_key_release` |
| animation play | `play_animation`, `play_animation_asset` |

The dotted forms (`scene.load`, `ui.button_clicked`, `app.quit`, `game.has_save`,
`variables.set`) are a distinct, older naming convention living alongside the
snake_case one.

---

## 5. File organization

### Definitions — `engine/logic/node_definitions/`

| File | Lines | Nodes | Domain |
|---|---|---|---|
| `physics_nodes.py` | 382 | 18 | physics + getters + events + layers + queries |
| `animation_nodes.py` | 320 | 15 | animation + animator + getters + events |
| `actions_nodes.py` | 257 | 12 | mixed: animation, audio, sprite, transform, lifecycle, log, BT |
| `registry.py` | 233 | 0 | unused registry |
| `dynamic_ui_nodes.py` | 203 | 8 | runtime UI creation |
| `movement_nodes.py` | 190 | 10 | movement + continuous motion |
| `__init__.py` | 184 | 0 | catalogue assembly + import-time side effects |
| `event_nodes.py` | 140 | 7 | comparisons + input (misnamed) |
| `misc_nodes.py` | 133 | 7 | variables, subgraphs, sequence, HUD, events |
| `input_advanced_nodes.py` | 114 | 5 | touch/swipe/pinch |
| `camera_nodes.py` | 110 | 5 | camera |
| `pathfinding_nodes.py` | 100 | 4 | navigation |
| `dialog_nodes.py` | 93 | 4 | dialogue |
| `save_load_nodes.py` | 91 | 4 | persistence |
| `audio_advanced_nodes.py` | 89 | 4 | audio |
| `ui_nodes.py` | 80 | 4 | static UI |
| `flow_nodes.py` | 77 | 4 | control flow |
| `particle_nodes.py` | 72 | 3 | particles |
| `prefab_nodes.py` | 66 | 3 | spawning |
| `state_machine_nodes.py` | 118 | 5 | FSM |
| `components_nodes.py` | 40 | 2 | add/remove component |
| `ui_binding_nodes.py` | 42 | 2 | UI↔variable binding |

### Runtime — `engine/logic/runtime/nodes/`

| File | Lines | Nodes |
|---|---|---|
| `physics_nodes.py` | 569 | 18 |
| `dynamic_ui_nodes.py` | 371 | 8 |
| `animation_nodes.py` | 354 | 13 |
| `misc_nodes.py` | 260 | **22** |
| `movement_nodes.py` | 201 | 11 |
| `ui_nodes.py` | 176 | 4 |
| `prefab_nodes.py` | 169 | 4 |
| `state_machine_nodes.py` | 157 | 5 |
| `dialog_nodes.py` | 147 | 4 |
| `save_load_nodes.py` | 145 | 4 |
| `actions_nodes.py` | 143 | 12 |
| `pathfinding_nodes.py` | 138 | 4 |
| `input_advanced_nodes.py` | 136 | 5 |
| `scene_nodes.py` | 123 | **19** |
| `event_nodes.py` | 107 | 7 |
| `camera_nodes.py` | 103 | 5 |
| `ui_binding_nodes.py` | 91 | 2 |
| `audio_advanced_nodes.py` | 84 | 4 |
| `particle_nodes.py` | 72 | 3 |
| `flow_nodes.py` | 57 | 4 |
| `math_nodes.py` | 52 | 7 |
| `components_nodes.py` | 50 | 2 |
| `string_nodes.py` | 22 | 2 |
| `__init__.py` | 14 | 0 |

**No god files.** The largest is 569 lines. The organization problem is *asymmetry*, not
size:

| Asymmetry | Detail |
|---|---|
| Runtime-only modules | `math_nodes` (7), `scene_nodes` (19), `string_nodes` (2) — **28 nodes with no definition file** |
| Definition-only modules | none |
| `scene_nodes.py` | 123 lines, 19 registrations — almost entirely aliases |
| `misc_nodes.py` | 22 nodes, no coherent domain |
| `actions_nodes.py` | mixes animation, audio, sprite, transform, lifecycle, logging, behavior trees |

### Target structure (proposal — do not move yet)

```
engine/logic/nodes/
  <domain>/
    definition.py      # NodeDefinition objects
    runtime.py         # executors + evaluators
```
with domains: `core, flow, math, string, logic, entity, input, physics, animation,
ui, audio, scene, dialogue, save, camera, navigation, particles, prefab, state`.

Co-locating definition and runtime in one folder per domain makes contract drift
**visible in a single file diff**. Adding `math`, `string` and `scene` definition files
closes the 28-node palette gap. **Nothing has been moved.**

---

## 6. Legacy classification

26 legacy/deprecated source markers found. Classified:

| Item | Class | Rationale |
|---|---|---|
| `NODE_DEFINITIONS` legacy dict format (`[(id, type)]` tuples) | **KEEP** | it is the live palette source; renaming it would be cosmetic churn |
| `engine/logic/node_definitions.py` (837 L, shadowed) | **REMOVE** | unreachable; proven dead |
| `engine/logic/legacy_visual_script.py` (`LEGACY_NODE_TYPES`, `LEGACY_PORTS`) | **KEEP** | needed to open old assets |
| `engine/logic/runtime/graph_migration.py` (201 L) | **KEEP** | asset migration |
| `NodeDefinitionRegistry` canonical/legacy machinery | **MIGRATE** | the conflict detection is exactly what is needed for §3.2 — wire it in rather than delete it |
| `event_collision_enter` / `_exit`, `event_trigger_enter` / `_exit` | **DEPRECATE** | superseded by `on_collision_*` / `on_trigger_*`; keep loading, hide from palette |
| Dotted aliases: `scene.load`, `scene.load_scene`, `ui.button_clicked`, `ui.set_widget_enabled`, `app.quit`, `game.has_save`, `game.load_game`, `variables.set` | **DEPRECATE** | keep the executor for old assets, hide from palette, pick one canonical id each |
| `load_scene` / `open_scene` / `scene_load` | **MIGRATE** | collapse to one id + alias table |
| `exit_game` / `quit_game` | **MIGRATE** | collapse to one id + alias table |
| `on_ui_click` / `button_clicked` | **MIGRATE** | collapse |
| `engine/scripting/visual_scripting_nodes.py` (`IfElseNode`, `SetPositionNode`, `LogMessageNode`) | **REMOVE** | shadow copies unused by the runtime |
| `engine/plugins/logic/nodes.py` (619 L, 37 classes) | **INVESTIGATE → likely REMOVE** | parallel framework, unreferenced by the Logic Graph pipeline |
| `engine/graphs/` (713 L) + `engine/graph/` (227 L) | **INVESTIGATE → likely REMOVE** | ditto |
| `_definition_to_legacy` category patch `{"Actions": "Action"}` | **MIGRATE** | fix at source |
| `output_evaluator.py` "Fallback for isolated tests" branch | **MIGRATE** | symptom of the dual registration path; disappears once registration is unified |

**Nothing has been removed or deprecated. This is a classification only.**

---

## 7. Serialization / migration / compiler

| Stage | Module | Status |
|---|---|---|
| Asset format | `.zlogic` JSON — `nodes[]`, `edges[]`, `properties{}` | READY |
| Load / save | `engine/logic/graph_asset.py` (580 L) | PARTIAL — 5 import-time mutations of `NODE_PORT_DEFINITIONS` |
| Normalization | `engine/logic/graph_normalizer.py` | PARTIAL — defaults `from_port` to `"next"`; **no port alias table** |
| Migration | `engine/logic/runtime/graph_migration.py` (201 L) | READY — but does not address the `exec_done` split |
| Validation | `engine/logic/graph_validator.py` | PARTIAL — does not detect contract violations |
| Compiler | none — the runtime interprets the graph directly each frame | by design |
| Runtime dispatch | `core.py::_execute` → `MetadataManager` → `registry` fallback | FRAGILE — two lookup paths |

**Serialization anomaly:** 83 edges across the project's `.zlogic` assets have
`from_port: null`. `graph_normalizer.py:203` coerces these to `"next"`, so they work by
accident. They should be normalized on save.

**The missing piece is a port alias table.** One table, consulted by both
`graph_normalizer` (on load) and `core._follow` (on dispatch), resolves §3.1 for all 45
nodes without touching 45 executors or invalidating a single saved asset.

---

## 8. Summary

```
definitions        = 154
declarative        = 126
legacy dict        = 154
executors          = 132
evaluators         =  64
pure data nodes    =  20
flow nodes         = 118
event nodes        =  16

contract violations = 167
  exec port mismatch      45
  unreachable exec port   45
  no definition           33
  data port mismatch      24
  input port mismatch     13
  no runtime               7

duplicate node IDs       =   2   (play_animation, stop_animation)
duplicate display names  =   4
duplicate executor IDs   =   0
duplicate evaluator IDs  =   0
legacy markers           =  26
registration paths       =   2   (14 modules vs 22 modules)
node registries          =   2
parallel graph frameworks=   4
```

**NODE SYSTEM SCORE: 3/10** (na data desta auditoria; **7/10** após o Stage 1 — contratos convergidos e sob gate de CI; limitado por 2 registries, 2 caminhos de registro e a 4ª tabela de portas, todos escopo do Stage 2).

The node system works for graphs authored before the declarative definitions landed and
degrades silently for anything authored since. The fix is not a rewrite: one alias
table plus one unified registration path plus wiring in the already-written conflict
detector addresses 90+ of the 167 violations.

---

*Read-only audit. No production code was modified.*
