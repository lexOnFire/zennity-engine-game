# PHASE 9 Recovery — Item 3: execution model and projection fidelity

Branch: `integration/phase9-recovery`
Base: `20a2656`

---

## 1. Inventory, before changing anything

**`engine/logic/contracts.py` did not exist on this lineage.** `ExecutionModel`
is Stage 1's, and Stage 1 is not integrated, so the brief's "prefer
contracts.ExecutionModel" meant porting the enum rather than importing it.

**Two vocabularies, exactly as expected — plus a third problem.** The catalogue
derived `pure` / `event` / `terminal` / `branch` / `flow` from a node's pins.
The declarative modules declare `pure_data` (13 nodes) and `terminal` (1).
Nothing translated between them, and **nothing read the declared value at all**:
`registry.set_execution_model` was only ever called with the derived result. A
node could declare `pure_data`, be classified `pure`, and no code path would
notice they disagreed.

**Three annotations the brief assumed were present are not.** `event_source`,
`deprecated=True` and `dynamic_exec_prefixes` live in Stage 1's
`animation_nodes`, `physics_nodes`, `flow_nodes` and `misc_nodes` — different
files from this lineage's, and importing those wholesale would drag their pin
contracts along, which is precisely the collision that consumed the lost
integration's item 8. They were not imported.

## 2. One vocabulary

`engine/logic/contracts.py` now holds it:

| model | meaning |
|---|---|
| `ACTION` | an executor runs it and returns the exec ports to follow |
| `EVENT_SOURCE` | flow originates here; the frame loop dispatches it, no executor expected |
| `TERMINAL` | flow legitimately stops; the executor returns `[]` on purpose |
| `PURE_DATA` | no exec pins at all; an evaluator resolves it on demand |

`branch` is deliberately gone: branching is how an ACTION continues, not a kind
of node, and nothing ever consumed the distinction.

**Declared beats derived.** A declaration carries intent the pins cannot:
`restart_scene` has a flow output and is still TERMINAL, because the scene it
would continue into no longer exists. Derivation is the fallback for everything
undeclared, and it is structural — `derive_execution_model` looks only at pins.

Result across the catalogue: `action` 123, `pure_data` 40, `event_source` 17,
`terminal` 4. Nothing outside the four.

## 3. Event sources, without an allow-list

"Definition with no executor" is not one situation, so `classify_runtime_coverage()`
splits it by the recorded model and the deprecated flag:

| group | n | |
|---|---|---|
| backed by a runtime | 166 | |
| `event_source_without_executor` | 5 | `event_start`, `event_update`, `event_timer`, `event_key_pressed`, `event_object_created` |
| `deprecated_without_runtime` | 2 | `animate_value`, `wait_until_condition` |
| `missing_runtime` | 2 | `find_nearest_object`, `get_object_name` |

No node id appears anywhere in that function, and a test proves it by parsing
the source and checking that no node id appears as an **executable** string
literal — docstrings may name examples, comparisons may not.

The two genuine gaps arrived with Stage 1's `scene_nodes` in recovery item 1;
their executors live on the Stage 1 runtime lineage, which is not integrated.
Implementing them is gameplay work and out of scope, so the gap is recorded as a
test rather than hidden.

## 4. Deprecated, revalidated

The brief said not to assume Stage 1's evidence still holds. Measured here:

| node | executor | evaluator | asset uses |
|---|---|---|---|
| `animate_value` | none | none | 0 |
| `wait_until_condition` | none | none | 0 |

Same conclusion, so `deprecated=True` is declared on both. They are marked, not
deleted: the definition documents an intent that was never implemented. The
validator reports them by **the flag**, never by id.

## 5. Projection fidelity

Three fields were declared and dropped in `_definition_to_legacy`:
`execution_model`, `deprecated`, `dynamic_exec_prefixes`. Fixing those three by
hand only protects against the three that already happened, so the guarantee is
generic: every field on `NodeDefinition` must appear in `PROJECTED_FIELDS`, with
the value the projection must hold, or in `UNPROJECTED_FIELDS` with a reason. A
field added tomorrow and forgotten fails the suite until someone decides.

`execution_model` and `dynamic_exec_prefixes` are emitted **only when actually
declared**, and the test asserts they are *absent* otherwise — an unconditional
default would make every node look explicitly classified and suppress derivation
for the entire catalogue.

`test_the_guard_detects_a_dropped_field` removes a projected field from the
projection, runs the suite in a subprocess and asserts it goes red, restoring
the file in a `finally`. A fidelity test that only ever passes is
indistinguishable from one that checks nothing.

## 6. One more second-source-of-truth removed

`DYNAMIC_PORT_NODES` was a hand-maintained table naming the same fact the
`dynamic_exec_prefixes` field carries. The prefixes are now declared on the
nodes that own them — `sequence` (`then_`) and `create_prefab` (`param_`) — and
the catalogue derives the table from the declarations, keeping a seed only for
the nodes with no declarative definition. This surfaced because the fidelity
test refuses to pass vacuously: nothing declared the field, so the check had no
subject.

## 7. Results

| | |
|---|---|
| `tests/logic` | 10 before, 10 after — 0 new |
| new tests | 47 (31 execution model, 16 projection fidelity) |
| items 1 and 2 | 74 tests, still green |
| `audit --ci` | exit 0 |
| assets touched | 0 |

Two `tests/logic/stage2` assertions were updated: they asserted `flow`, `event`,
`pure` and `branch`, the superseded vocabulary. That is the deliverable of this
item, not a test bent to pass.

## 8. Out of scope, classified not fixed

`play_animation` / `stop_animation`, port aliases, the `MainMenuLogic` orphan
edges, `game.load_game` / `game.has_save` canonicalisation, `move.speed`,
`move_by` — untouched. The two runtime gaps in section 3 are recorded, not
implemented.
