# PHASE 9 Recovery — Item 1: canonical node catalogue foundation

Branch: `integration/phase9-recovery`
Base: `c904527b` (Stage 2/2.1/3/4/4.1 + the item 9B test infrastructure)

---

## 1. Why this is a rebuild

The `integration/phase9-stabilization` lineage carrying integration items 1–8
was never pushed — `git push` returns 403 for this session and the GitHub App
cannot create refs — and it went away with its container. The architectural
decisions from that work are known and were re-applied directly; nothing was
replayed commit by commit from the transcript.

The base is the durable Stage 2 lineage, so this item starts from a catalogue
that is already unified into `NodeDefinitionRegistry`. What it did not have was
discovery, ownership enforcement, or the Stage 1 declarative modules.

## 2. Declarative modules

| | |
|---|---|
| `*_nodes.py` on disk before | 20 |
| declared in the hand-written tuple | 20 |
| **on disk after** | **23** |
| **auto-discovered** | **23** |
| import failures | 0 |

`math_nodes.py`, `logic_nodes.py` and `scene_nodes.py` are Stage 1 work. They
exist on `origin/fix/executor-port-contract` and were absent here, so 17 nodes
were missing from the palette:

```
absolute_number  add_number     and            clamp_number   delta_time
divide_number    find_nearest_object           get_object_name
get_position     join_text      multiply_number  not          or
random_number    subgraph_input subtract_number  to_text
```

Definitions: **154 → 171**. Nothing was removed.

## 3. Discovery replaces the module list

`DECLARATIVE_DEFINITION_MODULES` was a tuple maintained by hand. That is a
second source of truth about which modules exist, and it fails in the quietest
possible way: a module is added to the package, nothing imports it, and it
simply does not exist as far as the palette is concerned — no error, because
nothing ever compared the tuple to the directory. The three Stage 1 modules were
exactly that case.

It is now `glob("*_nodes.py")`, sorted for a stable build order and cached per
process so two builds in one process cannot disagree. The name is kept, so
callers importing it are unaffected.

Import failures are **recorded and logged**, never swallowed:
`DECLARATIVE_IMPORT_FAILURES` maps module name to reason. The old code had a
bare `except Exception: continue`, and it mattered immediately — the three
Stage 1 modules failed to import on first contact, and the recorded reason is
what identified why (section 6).

The gate test is generic: it compares the catalogue against the directory at
run time, so a module added later is covered without editing the test. Named
assertions for the Stage 1 modules exist too, but as illustration, not as the
gate.

## 4. Ownership belongs to the registry

`set_definition_owner` used to be a plain dict write, so a second module
claiming an id silently took it over. That is how `play_animation` came to exist
twice with incompatible port contracts — the palette showing one, the
MetadataManager holding the other.

Now: a second claimant records a conflict and **does not** take ownership, the
same module reclaiming its own id is a no-op (discovery and catalogue builds are
idempotent and get re-run in tests), and `assert_no_duplicate_definitions()`
raises `DuplicateNodeDefinitionError` naming the id and both modules. The
catalogue calls it once every owner is known — a conflict is not knowable until
both claimants have been seen.

Conflicts live in the registry beside the ownership they contradict. Stage 1
kept `_DEFINITION_OWNERS` and `_DEFINITION_CONFLICTS` as module globals next to
a second owner table; two structures describing one fact is the failure being
fixed, so they are not recreated. A test asserts they do not come back.

`DuplicateNodeDefinitionError` stays importable from
`engine.logic.node_definitions` — the public spelling Stage 1 uses.

## 5. Compatibility view

`NODE_DEFINITIONS` remains, derived from the registry, and rejects
`__setitem__`, `__delitem__`, `update`, `pop` and `clear`. Verified by test
rather than assumed.

## 6. Two things the brief did not anticipate

**`NodeDefinition` had to accept three fields.** The Stage 1 modules declare
`execution_model`, `dynamic_exec_prefixes` and `deprecated`; this lineage's
dataclass has none of them, so all three modules failed to import with a
`TypeError` and three whole domains stayed out of the palette. The fields are
now accepted and stored, and **nothing reads them** — what the catalogue does
with `execution_model` is the execution-model item's decision, not this one.

**Stage 1's `scene_nodes` declares the dotted ids.** `scene.load_scene`,
`app.quit`, `ui.button_clicked` and `ui.set_widget_enabled` are aliases on this
lineage, and this lineage's rule is that an alias never gets its own definition,
palette entry or port contract. Letting them through produced exactly what that
rule prevents: two palette rows per operation, and three new orphan edges in
`MainMenuLogic.zlogic` because the alias contract's entry pin is `exec` where
the asset says `in`.

So the harvest skips ids that are currently aliases and parks the declarations
in `ALIASED_DECLARATIVE_DEFINITIONS`. This **preserves the base's existing
policy** rather than deciding a new one. Which spelling should be canonical is a
real question — the shipping assets use the dotted form exclusively — but it
belongs to the node-id alias item, and the declarations are kept so that item
does not have to re-derive them.

## 7. Baseline regenerated

`tests/fixtures/stage2/registration_baseline.json` → `definition_ids` and
`counts.definitions` only. 17 added, 0 removed, every one owned by a Stage 1
module. The rest of the fixture is not re-measured here, and the provenance is
recorded in the file's own `_comment`.

## 8. Results

| | |
|---|---|
| `tests/logic` | 10 failures before, 10 after — **0 new** |
| new tests | 34, all passing |
| `tools/audit_node_system.py --ci` | exit 0 |
| repository mutation guard | pass |
| `git status` | clean of `Assets/` |

The 10 pre-existing `tests/logic` failures are untouched and belong to later
items (aliases, execution model, animation contracts, port normalization,
gameplay semantics). The five duplicate *executor* registrations the audit
reports are a recorded baseline about the runtime, not about definitions, and
are out of scope here.

## 9. Differences from the first integration

1. Ownership is recorded under the **bare module name** (`math_nodes`), not the
   dotted path — that is the spelling Stage 1's public API reports.
2. `ALIASED_DECLARATIVE_DEFINITIONS` did not exist before; the first integration
   resolved the alias/palette question inside its item 1, which mixed two
   decisions. Here the two are separated.
3. `NodeDefinition` gained the three declared fields as inert storage. The first
   integration hit the same wall later, when the projection dropped
   `execution_model` and `deprecated` silently.
