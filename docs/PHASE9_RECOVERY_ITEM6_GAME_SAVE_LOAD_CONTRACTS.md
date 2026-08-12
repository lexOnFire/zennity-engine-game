# PHASE 9 Recovery — Item 6: game save/load node contracts

Branch: `integration/phase9-recovery`
Base: `f631c20`

---

## 1. A second split brain, and this one did nothing

`load_game` and `has_save` each had **two executors**, and the broken one won by
load order. `runtime/nodes/scene_nodes.py` held:

```python
@registry.register_executor(('game.has_save', 'has_save'))
def execute_game_has_save(runtime, node, game, dt):
    return ["false"]
```

That is the entire implementation. It never looked for a save, and `false` is
not a port the node declares. Whatever the graph wired downstream, nothing ran.

The `load_game` stub was almost as bad: it read a property called `slot` — a
name it invented — and defaulted to `"autosave"`, so the slot an author set in
the Inspector never reached the save system. It returned `["success", "next"]`,
neither of which the node declares.

The real implementations were in `save_load_nodes` all along, unreachable.

## 2. Worse: the whole file returned undeclared ports

Even `save_game` and `delete_save`, whose real executors *were* reachable,
returned the unprefixed spelling:

| node | returned | declared |
|---|---|---|
| `save_game` | `saved`, `failure` | `exec_saved`, `exec_failure` |
| `load_game` | `loaded`, `no_save`, `failure` | `exec_loaded`, `exec_no_save`, `exec_failure` |
| `delete_save` | `deleted`, `failure` | `exec_deleted`, `exec_failure` |
| `has_save` | `exists`, `not_exists`, `failure` | `exec_exists`, `exec_not_exists`, `exec_failure` |

An edge wired to the declared port would never be followed. The item is scoped
to two nodes, but the other two are the same file, the same bug and the same
one-word fix — leaving them would also have made the gate in section 6 need an
allow-list, which is what this whole phase keeps removing.

**All four now return exactly what they declare**, and every declared branch is
reachable (tested: a declared pin nothing returns is a pin the author cannot
use).

## 3. `slot` → `slot_name`

The stub's invented property had leaked into the catalogue as an explicit
default (`load_game: {"slot": "autosave"}`), so the Inspector showed a dead
field beside the live one. Removed, and saved graphs are migrated by
`_RENAMED_NODE_PROPERTIES` — the mechanism `log_message` and `play_animation`
already use. `MainMenuLogic`'s `slot: "autosave"` now arrives as `slot_name`,
which is what the executor reads.

## 4. `has_save.next` — resolved, with evidence

Item 5 left this deliberately unresolved: the node declares three outcomes, so
`next` names none of them and the generic resolver correctly refuses to pick.
The asset itself settles it:

```
check_save (game.has_save)  --next-->  ui.set_widget_enabled
                                       { widget_name: "ContinueButton",
                                         enabled: true }
```

Continue is enabled **when a save exists**, so `next` meant `exec_exists`. The
opposite reading — enable Continue when there is nothing to continue — is not a
coherent design.

Implemented as `NODE_SCOPED_OUTPUT_ALIASES`, not by loosening the generic
resolver, which must keep refusing this shape. The entry only applies when the
target is itself declared, so a stale entry cannot invent a pin, and a test
pins the downstream evidence: if `ContinueButton` stops being enabled there, the
justification must be re-examined.

Orphan edges: **72 → 71**, created 0.

## 5. Node-id canonicalization — NOT done, and why

Item 2 made the dotted scene/UI ids canonical because every piece of evidence
agreed. Here it does not:

| | assets | declarative definition | executor |
|---|---|---|---|
| `game.load_game` | 1 | **none** | **none** (it was the stub's, now deleted) |
| `load_game` | 0 | `save_load_nodes` | `save_load_nodes` |
| `game.has_save` | 1 | **none** | **none** |
| `has_save` | 0 | `save_load_nodes` | `save_load_nodes` |

In item 2 the dotted ids carried both the declaration and the runtime. Here the
dotted form exists *only* as the stub's registration — which was deleted in this
item because the stub was broken. Asset usage points one way and the entire
implementation the other.

Renaming would also split the domain: `save_game` and `delete_save` have no
dotted form at all, so a `game.` namespace for two of four save/load nodes would
be arbitrary. The alias already makes the asset load correctly, and there is no
user-visible problem to fix.

**Left as an alias, documented.** This is not the same case as item 2, and
treating it as one would be pattern-matching rather than evidence.

## 6. The wider class, recorded

The AST scan across every executor found **45 of 128** returning a flow port
their contract does not declare — `success` / `failure` / `loaded` against
`exec_*`. It is systemic, not a save/load problem.

`tests/fixtures/stage2/executor_port_mismatch_baseline.json` records them, and
the gate fails on any **new** entry *and* on any entry that has been fixed but
left in the file. The four save/load nodes are asserted absent from it.

This is a debt with a name and a bound, not an exemption. It deserves its own
item: 45 nodes is real work, and each needs its declared outcomes checked
against what the executor actually does, exactly as these four did.

## 7. Results

| | |
|---|---|
| duplicate executors on save/load nodes | 2 → **0** |
| undeclared returns on save/load nodes | 4 nodes → **0** |
| orphan edges | 72 → **71**, created 0 |
| new tests | 47 |
| recovery items 1–5 | 195 tests, still green |
| `tests/logic` | 10 before, 10 after — 0 new |
| `audit --ci` | exit 0 |
| assets touched | 0 |

Untouched as instructed: `move.speed`, `move_by`, `find_nearest_object`,
`get_object_name`, and the remaining 71 orphans outside this domain.

One more duplicate executor was found and **not** fixed here, being outside the
item's domain: `set_variable` is registered by both `misc_nodes` and
`scene_nodes`.
