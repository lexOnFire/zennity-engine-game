# PHASE 9 Recovery — Item 5: port normalization

Branch: `integration/phase9-recovery`
Base: `f5d9a7b`

---

## 1. Why `in → exec` is the wrong rule

Measured across every shipping `.zlogic` before writing any code:

| port | direction | edges | node types | wrong for |
|---|---|---|---|---|
| `in` | input | 302 | 47 | **3** |
| `exec` | input | 18 | 7 | 0 |
| `next` | output | 245 | 35 | **1** |

A global `in → exec` rename would rewrite 299 correct edges in order to fix 3.
`move_by` really declares `in`; `play_animation` really declares `exec`. Neither
is "the legacy spelling" — which one is right depends entirely on the node, so
the node's own contract is the only thing that can decide.

That is the whole design: **resolution is relative to the contract**, never
global.

## 2. One source of truth

`engine/logic/port_aliases.py` did not exist on this lineage — there was no port
normalization of any kind. It now holds the only one:

```python
resolve_input_port(port, declared_flow_inputs)
resolve_output_port(port, declared_flow_outputs)
```

A rewrite happens only when all three hold: the saved name is a flow synonym,
the node does not declare it, and the node declares exactly one synonym of its
own. Anything else is returned untouched.

Node-id aliases stay where item 2 put them, in the catalogue. `resolve_node_id`
maps node identity; these map pin names. The two are never mixed.

## 3. What it refuses to do

**Guess.** A node with two flow inputs gets no rewrite. There is no evidence for
choosing between them, and a silent wrong guess reconnects an edge to the wrong
branch — worse than leaving it visibly orphaned. `is_ambiguous_input` /
`is_ambiguous_output` make the case reportable.

**Touch data pins.** Only names in the synonym sets are ever considered, so
`value`, `target`, `state` and friends are never folded into a flow pin. Tested
per name, not assumed.

**Invent an outcome.** The output synonyms deliberately exclude every semantic
branch — `exec_failure`, `true`, `false`, `exec_exists`, `grounded`, `held`. A
module-level guard fails at import if a synonym is ever also an outcome.

## 4. Order

```
raw graph
  → node-id normalization        (item 2)
  → canonical NodeDefinition lookup
  → port normalization           (this item, against that definition)
  → contract validation / orphan detection / runtime construction
```

Ports after ids, not before: `load_scene` resolves to `scene.load_scene`, and
only that definition can say which entry pin the edge should land on. A test
drives exactly that case.

## 5. What was repaired

**6 edges, 0 created. Orphan edges 76 → 72.**

| node | saved | canonical | n | asset | reason |
|---|---|---|---|---|---|
| `play_animation` | `in` | `exec` | 3 | `ZennityRun/PlayerMovement.zlogic` | one declared flow input |
| `play_animation` | `in` | `exec` | 1 | `PlayerCombatLogic.zlogic` | one declared flow input |
| `load_game` | `in` | `exec` | 1 | `MainMenuLogic.zlogic` | one declared flow input |
| `start_behavior_tree` | `in` | `exec` | 1 | `tocaLogic.zlogic` | one declared flow input |

The four `play_animation` edges are the blocker item 4.2 created deliberately
when it made `exec` canonical. **Item 4.2 is now COMPLETE.**

No asset was edited: normalization is in memory, and a test reads every shipping
graph's bytes before and after to prove opening one changes nothing on disk. A
graph *saved* after loading does serialize the canonical port.

## 6. What was deliberately not repaired

**`has_save.next` — a real mismatch, not an alias.** The node declares
`exec_exists` / `exec_not_exists` / `exec_failure`. An edge saved as `next`
names no outcome in particular, so attaching it to one would pick a behaviour
silently.

Worse, its executor is:

```python
@registry.register_executor(('game.has_save', 'has_save'))
def execute_game_has_save(runtime, node, game, dt):
    return ["false"]
```

`false` is not a declared port either. `load_game` has the same shape — it
returns `["success", "next"]` and declares `exec_loaded` / `exec_no_save` /
`exec_failure`. This is a **contract/executor mismatch of exactly the kind item
4.2 fixed for the animation nodes**, and no amount of port aliasing repairs it.
It needs its own reconciliation item, with the same evidence-first treatment.

**`game.load_game` / `game.has_save` node-id canonicalization — deferred.**
Recounted here: dotted 1 use each, plain 0 each — the same pattern that made the
scene/UI ids canonical in item 2. But section 11 asks for the decision only if
*everything* is unambiguous, and it is not: canonicalising the id would put a
nicer label on a node whose contract and executor disagree. The measurement is
recorded; the decision belongs with the contract fix.

**Data pins with nowhere to go.** `get_position.in`, `subtract_number.in`,
`vector2.in`, `if_else.value` — those nodes declare no flow input at all, so the
saved name cannot resolve anywhere. They stay in the baseline as the asset-
authoring bugs they are.

## 7. Results

| | |
|---|---|
| shipping graphs | 56, all load, normalize and build a runtime |
| orphan edges | 76 → **72**, created **0** |
| data pins altered | **0** |
| ambiguous aliases | 0 encountered in shipping assets |
| new tests | 33 |
| `tests/logic` | 10 before, 10 after — 0 new |
| `audit --ci` | exit 0 |
| item 4.2 | **COMPLETE** |
| assets touched | 0 |

Still open and untouched, as instructed: `move.speed` 100 vs 200, `move_by`
`x/y` vs `delta_x/delta_y`, and the two runtime gaps `find_nearest_object` /
`get_object_name`.
